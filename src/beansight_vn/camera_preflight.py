from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEVICE_LINE = re.compile(r"\[(?P<index>\d+)\]\s+(?P<name>.+)$")


@dataclass(frozen=True, slots=True)
class CameraDevice:
    index: int
    name: str


@dataclass(frozen=True, slots=True)
class CameraSpec:
    semantic_name: str
    index: int
    device_name: str


def parse_avfoundation_devices(output: str) -> list[CameraDevice]:
    """Parse the video section printed by ffmpeg's AVFoundation backend."""
    devices: list[CameraDevice] = []
    in_video_section = False
    for line in output.splitlines():
        if "AVFoundation video devices" in line:
            in_video_section = True
            continue
        if "AVFoundation audio devices" in line:
            break
        if not in_video_section:
            continue
        match = DEVICE_LINE.search(line)
        if match:
            devices.append(CameraDevice(int(match.group("index")), match.group("name").strip()))
    return devices


def list_avfoundation_devices(ffmpeg: str = "ffmpeg") -> list[CameraDevice]:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
        check=False,
    )
    devices = parse_avfoundation_devices(result.stderr)
    if not devices:
        raise RuntimeError(
            "ffmpeg did not report any AVFoundation video devices. Install ffmpeg, "
            "connect the cameras, and grant the terminal camera permission."
        )
    return devices


def resolve_semantic_camera(
    devices: list[CameraDevice],
    semantic_name: str,
    name_match: str,
    explicit_index: int | None = None,
) -> CameraSpec:
    if explicit_index is not None:
        matches = [device for device in devices if device.index == explicit_index]
    else:
        needle = name_match.casefold()
        matches = [device for device in devices if needle in device.name.casefold()]
    if len(matches) != 1:
        candidates = ", ".join(f"{d.index}:{d.name}" for d in devices) or "none"
        raise ValueError(
            f"{semantic_name!r} must resolve to exactly one camera; found {len(matches)}. "
            f"Available devices: {candidates}"
        )
    match = matches[0]
    return CameraSpec(semantic_name=semantic_name, index=match.index, device_name=match.name)


def _probe_camera(
    spec: CameraSpec,
    *,
    width: int,
    height: int,
    target_fps: float,
    fourcc: str,
    duration_s: float,
    output_dir: Path,
) -> dict[str, Any]:
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - exercised only without the optional extra
        raise RuntimeError("Install the camera extra: pip install -e '.[camera]'") from exc

    cap = cv2.VideoCapture(spec.index, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap.release()
        return {**asdict(spec), "passed": False, "error": "could not open camera"}

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, target_fps)

    started = time.monotonic()
    deadline = started + duration_s
    attempted = 0
    successful = 0
    brightness_sum = 0.0
    sample_frame = None
    previous_frame_at: float | None = None
    longest_gap_s = 0.0
    while time.monotonic() < deadline:
        attempted += 1
        ok, frame = cap.read()
        now = time.monotonic()
        if not ok or frame is None:
            continue
        successful += 1
        brightness_sum += float(frame.mean())
        # AVFoundation cameras can return a black startup frame before auto-exposure settles.
        # Keep the latest successful frame so the saved visual evidence represents the end of the
        # soak rather than device initialization.
        sample_frame = frame
        if previous_frame_at is not None:
            longest_gap_s = max(longest_gap_s, now - previous_frame_at)
        previous_frame_at = now

    elapsed_s = time.monotonic() - started
    actual = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "reported_fps": float(cap.get(cv2.CAP_PROP_FPS)),
    }
    cap.release()

    image_path: str | None = None
    if sample_frame is not None:
        target = output_dir / f"{spec.semantic_name}.jpg"
        cv2.imwrite(str(target), sample_frame)
        image_path = str(target)

    effective_fps = successful / elapsed_s if elapsed_s else 0.0
    failed_reads = attempted - successful
    expected_frames = target_fps * elapsed_s
    estimated_dropped_frames = max(0.0, expected_frames - successful)
    estimated_dropped_rate = estimated_dropped_frames / expected_frames if expected_frames else 1.0
    return {
        **asdict(spec),
        "requested": {
            "width": width,
            "height": height,
            "fps": target_fps,
            "fourcc": fourcc,
        },
        "actual": actual,
        "duration_s": elapsed_s,
        "attempted_reads": attempted,
        "successful_reads": successful,
        "failed_reads": failed_reads,
        "failed_read_rate": failed_reads / attempted if attempted else 1.0,
        "estimated_dropped_frames": estimated_dropped_frames,
        "estimated_dropped_rate": estimated_dropped_rate,
        "effective_fps": effective_fps,
        "mean_brightness": brightness_sum / successful if successful else 0.0,
        "longest_frame_gap_s": longest_gap_s,
        "sample_image": image_path,
        "passed": successful > 0,
    }


def run_preflight(
    top: CameraSpec,
    wrist: CameraSpec,
    *,
    output_dir: Path,
    width: int = 640,
    height: int = 480,
    fps: float = 30.0,
    fourcc: str = "MJPG",
    duration_s: float = 1800.0,
    min_effective_fps: float = 27.0,
    max_failed_read_rate: float = 0.01,
    max_estimated_dropped_rate: float = 0.10,
) -> dict[str, Any]:
    if top.index == wrist.index:
        raise ValueError("top and wrist resolved to the same physical camera")
    if len(fourcc) != 4:
        raise ValueError("fourcc must contain exactly four characters")
    output_dir.mkdir(parents=True, exist_ok=True)

    reports: dict[str, dict[str, Any]] = {}
    errors: dict[str, BaseException] = {}

    def worker(spec: CameraSpec) -> None:
        try:
            reports[spec.semantic_name] = _probe_camera(
                spec,
                width=width,
                height=height,
                target_fps=fps,
                fourcc=fourcc,
                duration_s=duration_s,
                output_dir=output_dir,
            )
        except BaseException as exc:  # retain both thread failures for the report
            errors[spec.semantic_name] = exc

    threads = [threading.Thread(target=worker, args=(spec,), daemon=True) for spec in (top, wrist)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if errors:
        details = "; ".join(f"{name}: {error}" for name, error in sorted(errors.items()))
        raise RuntimeError(f"camera preflight failed: {details}")

    for report in reports.values():
        report["passed"] = bool(
            report["passed"]
            and report["effective_fps"] >= min_effective_fps
            and report["failed_read_rate"] <= max_failed_read_rate
            and report["estimated_dropped_rate"] <= max_estimated_dropped_rate
            and report["actual"]["width"] == width
            and report["actual"]["height"] == height
            and report["mean_brightness"] >= 5.0
        )
    result = {
        "schema_version": "1.0",
        "passed": len(reports) == 2 and all(report["passed"] for report in reports.values()),
        "thresholds": {
            "min_effective_fps": min_effective_fps,
            "max_failed_read_rate": max_failed_read_rate,
            "max_estimated_dropped_rate": max_estimated_dropped_rate,
        },
        "cameras": reports,
    }
    (output_dir / "camera_preflight.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve and soak-test semantic top/wrist cameras."
    )
    parser.add_argument("--top-match", default="C920")
    parser.add_argument("--wrist-match", default="C270")
    parser.add_argument("--top-index", type=int)
    parser.add_argument("--wrist-index", type=int)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--fourcc", default="MJPG")
    parser.add_argument("--duration", type=float, default=1800.0)
    parser.add_argument("--min-effective-fps", type=float, default=27.0)
    parser.add_argument("--max-failed-read-rate", type=float, default=0.01)
    parser.add_argument("--max-estimated-dropped-rate", type=float, default=0.10)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--output", type=Path, default=Path("results/camera_preflight"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    devices = list_avfoundation_devices(args.ffmpeg)
    top = resolve_semantic_camera(devices, "top", args.top_match, args.top_index)
    wrist = resolve_semantic_camera(devices, "wrist", args.wrist_match, args.wrist_index)
    result = run_preflight(
        top,
        wrist,
        output_dir=args.output,
        width=args.width,
        height=args.height,
        fps=args.fps,
        fourcc=args.fourcc,
        duration_s=args.duration,
        min_effective_fps=args.min_effective_fps,
        max_failed_read_rate=args.max_failed_read_rate,
        max_estimated_dropped_rate=args.max_estimated_dropped_rate,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
