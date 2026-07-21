from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from .camera_attestation import preflight_sha256

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
PLACEHOLDER = re.compile(r"(?:REPLACE|RECORD|TODO)(?:_|\b)", re.IGNORECASE)
ReferencePosition = Literal["begin", "end"]


@dataclass(frozen=True, slots=True)
class CameraIdentity:
    role: str
    model: str
    index: int
    preflight_session_id: str | None


@dataclass(frozen=True, slots=True)
class CaptureSettings:
    width: int = 640
    height: int = 480
    fps: float = 30.0
    fourcc: str = "MJPG"
    image_format: str = "PNG"
    png_compression: int = 3
    # 90 frames (~3 s at 30 fps): hardware auto-exposure needs this after a scene
    # change (measured 2026-07-21: 30 frames left a first capture ~80 mean-points
    # hot; the next converged). 5 was enough only for locked exposure.
    warmup_frames: int = 90


FIXED_CAPTURE_SETTINGS = CaptureSettings()


@dataclass(frozen=True, slots=True)
class OperatorSettingsSnapshot:
    content: dict[str, Any]
    sha256: str


@dataclass(frozen=True, slots=True)
class CapturedPng:
    data: bytes
    width: int
    height: int
    channels: int
    camera_reported: dict[str, float | int | None]


@dataclass(frozen=True, slots=True)
class CaptureResult:
    image_path: Path
    metadata_path: Path
    metadata: dict[str, Any]


class CaptureBackend(Protocol):
    def capture_png(self, camera: CameraIdentity, settings: CaptureSettings) -> CapturedPng: ...


def _require_identifier(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(
            f"{name} must start with an ASCII letter or digit and contain only "
            "letters, digits, '.', '_', or '-' (maximum 128 characters)"
        )
    return value


def load_preflight(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read camera preflight JSON {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("camera preflight JSON must contain an object")
    return value


def validate_preflight_top(preflight: Mapping[str, Any]) -> CameraIdentity:
    """Return the current semantic top-camera identity, or fail closed."""
    if preflight.get("passed") is not True:
        raise ValueError("camera preflight report did not pass")
    cameras = preflight.get("cameras")
    if not isinstance(cameras, Mapping):
        raise ValueError("camera preflight report is missing its cameras object")
    top = cameras.get("top")
    if not isinstance(top, Mapping):
        raise ValueError("camera preflight report is missing the semantic top camera")
    if top.get("passed") is not True:
        raise ValueError("semantic top camera did not pass preflight")
    if top.get("semantic_name") != "top":
        raise ValueError("preflight cameras.top is not semantically identified as top")

    model = top.get("device_name")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("semantic top camera is missing its device model")
    normalized_model = model.casefold()
    if "c270" in normalized_model:
        raise ValueError("refusing C270 wrist camera for perception capture")
    if "c920" not in normalized_model:
        raise ValueError("semantic top camera must be a C920")

    index = top.get("index")
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("semantic top camera index must be a non-negative integer")
    preflight_session_id = preflight.get("session_id")
    if preflight_session_id is not None and (
        not isinstance(preflight_session_id, str) or not preflight_session_id.strip()
    ):
        raise ValueError("camera preflight session_id must be a non-empty string when present")
    return CameraIdentity(
        role="top",
        model=model,
        index=index,
        preflight_session_id=preflight_session_id,
    )


def _validate_locked_setting(name: str, value: Any, *, allow_auto: bool = False) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"operator settings {name!r} must be an object")
    mode = value.get("mode")
    allowed_modes = {"manual", "locked"} | ({"auto"} if allow_auto else set())
    if not isinstance(mode, str) or mode.casefold() not in allowed_modes:
        expected = "'manual', 'locked', or 'auto'" if allow_auto else "'manual' or 'locked'"
        raise ValueError(f"operator settings {name!r}.mode must be {expected}")
    if allow_auto and mode.casefold() == "auto":
        # macOS AVFoundation re-enables C920 auto-exposure on every stream open,
        # so a recorded number would be fiction. Auto is honest only with null.
        if value.get("value") is not None:
            raise ValueError(
                f"operator settings {name!r} in auto mode must record value null; "
                "the hardware ignores operator-entered values"
            )
        return
    setting = value.get("value")
    if isinstance(setting, bool) or not isinstance(setting, (int, float, str)):
        raise ValueError(f"operator settings {name!r}.value must be a scalar value")
    if isinstance(setting, float) and not math.isfinite(setting):
        raise ValueError(f"operator settings {name!r}.value must be finite")
    if isinstance(setting, str) and not setting.strip():
        raise ValueError(f"operator settings {name!r}.value must be non-empty")
    if isinstance(setting, str) and PLACEHOLDER.match(setting.strip()):
        raise ValueError(f"operator settings {name!r}.value still contains a placeholder")


def validate_operator_settings(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("operator settings JSON must contain an object")
    for name in ("focus", "exposure", "white_balance"):
        if name not in value:
            raise ValueError(f"operator settings are missing {name!r}")
        # Exposure may be hardware-auto: macOS AVFoundation force-reverts the C920
        # to auto-exposure on every open (verified 2026-07-21), so only focus and
        # white balance can honestly claim a locked value.
        _validate_locked_setting(name, value[name], allow_auto=(name == "exposure"))

    frequency = value.get("power_line_frequency")
    if isinstance(frequency, bool) or not isinstance(frequency, (int, float)):
        raise ValueError("operator settings power_line_frequency must be numeric 50")
    if not math.isfinite(float(frequency)) or float(frequency) != 50.0:
        raise ValueError("operator settings power_line_frequency must be 50 Hz")

    for name in ("controller", "version", "notes"):
        if name in value and not isinstance(value[name], str):
            raise ValueError(f"operator settings optional field {name!r} must be a string")
    for name in ("controller", "version"):
        if name in value and (not value[name].strip() or PLACEHOLDER.match(value[name].strip())):
            raise ValueError(f"operator settings optional field {name!r} must be recorded exactly")
    return value


def load_operator_settings(path: str | Path) -> OperatorSettingsSnapshot:
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise ValueError(f"could not read operator settings JSON {source}: {exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"operator settings file is not valid UTF-8 JSON: {exc}") from exc
    content = validate_operator_settings(value)
    return OperatorSettingsSnapshot(
        content=content,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def artifact_paths(
    output_dir: str | Path,
    *,
    session_id: str,
    bean_id: str | None,
    reference_position: ReferencePosition | None,
) -> tuple[Path, Path]:
    root = Path(output_dir)
    if reference_position is None:
        if bean_id is None:
            raise ValueError("bean_id is required for a canonical bean capture")
        stem = _require_identifier("bean_id", bean_id)
        directory = root / "canonical"
    else:
        if reference_position not in {"begin", "end"}:
            raise ValueError("reference_position must be 'begin' or 'end'")
        if bean_id is not None:
            raise ValueError("neutral reference captures must not have a bean_id")
        stem = f"{_require_identifier('session_id', session_id)}__neutral_{reference_position}"
        directory = root / "references"
    return directory / f"{stem}.png", directory / f"{stem}.json"


def _assert_targets_available(*paths: Path) -> None:
    existing = [path for path in paths if os.path.lexists(path)]
    if existing:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"refusing to overwrite existing capture artifact: {names}")


def _stage_bytes(target: Path, data: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    with temporary.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return temporary


def _unlink_quietly(path: Path) -> None:
    with suppress(OSError):
        path.unlink(missing_ok=True)


def _write_artifact_pair(
    image_path: Path,
    image_bytes: bytes,
    metadata_path: Path,
    metadata_bytes: bytes,
) -> None:
    """Publish complete files without overwriting; the metadata sidecar is the commit marker."""
    _assert_targets_available(image_path, metadata_path)
    image_temporary: Path | None = None
    metadata_temporary: Path | None = None
    image_published = False
    try:
        image_temporary = _stage_bytes(image_path, image_bytes)
        metadata_temporary = _stage_bytes(metadata_path, metadata_bytes)
        # Hard-linking staged files publishes complete inodes and fails rather than replacing an
        # artifact created by a concurrent capture. Both files live on the same filesystem.
        os.link(image_temporary, image_path)
        image_published = True
        try:
            os.link(metadata_temporary, metadata_path)
        except BaseException:
            _unlink_quietly(image_path)
            image_published = False
            raise
    except FileExistsError as exc:
        if image_published:
            _unlink_quietly(image_path)
        raise FileExistsError("refusing to overwrite an existing capture artifact") from exc
    finally:
        if image_temporary is not None:
            _unlink_quietly(image_temporary)
        if metadata_temporary is not None:
            _unlink_quietly(metadata_temporary)


def _utc_timestamp(clock: Callable[[], datetime]) -> str:
    captured_at = clock()
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("capture clock must return a timezone-aware datetime")
    return captured_at.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _validate_captured_png(frame: CapturedPng) -> None:
    if frame.width != FIXED_CAPTURE_SETTINGS.width or frame.height != FIXED_CAPTURE_SETTINGS.height:
        raise ValueError(
            f"camera returned {frame.width}x{frame.height}; require full 640x480 capture"
        )
    if frame.channels != 3:
        raise ValueError(f"camera frame must have exactly 3 channels; got {frame.channels}")
    if not frame.data.startswith(PNG_SIGNATURE):
        raise ValueError("capture backend did not return PNG bytes")
    if len(frame.data) <= len(PNG_SIGNATURE):
        raise ValueError("capture backend returned an empty PNG")


def capture_perception(
    preflight: Mapping[str, Any],
    *,
    operator_settings: OperatorSettingsSnapshot,
    output_dir: str | Path,
    session_id: str,
    lot_id: str,
    geometry_id: str,
    backend: CaptureBackend,
    bean_id: str | None = None,
    reference_position: ReferencePosition | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CaptureResult:
    session_id = _require_identifier("session_id", session_id)
    lot_id = _require_identifier("lot_id", lot_id)
    geometry_id = _require_identifier("geometry_id", geometry_id)
    if bean_id is not None:
        bean_id = _require_identifier("bean_id", bean_id)
    validate_operator_settings(operator_settings.content)
    if not re.fullmatch(r"[0-9a-f]{64}", operator_settings.sha256):
        raise ValueError("operator settings sha256 must be a lowercase 64-character digest")
    camera = validate_preflight_top(preflight)
    image_path, metadata_path = artifact_paths(
        output_dir,
        session_id=session_id,
        bean_id=bean_id,
        reference_position=reference_position,
    )
    # Fail before opening hardware when the bean/reference already has an artifact.
    _assert_targets_available(image_path, metadata_path)

    frame = backend.capture_png(camera, FIXED_CAPTURE_SETTINGS)
    _validate_captured_png(frame)
    image_sha256 = hashlib.sha256(frame.data).hexdigest()
    relative_image_path = image_path.relative_to(metadata_path.parent).as_posix()
    canonical = reference_position is None
    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "capture_kind": "canonical_bean" if canonical else "neutral_reference",
        "canonical": canonical,
        "reference_position": reference_position,
        "session_id": session_id,
        "bean_id": bean_id,
        "lot_id": lot_id,
        "geometry_id": geometry_id,
        "preflight_sha256": preflight_sha256(dict(preflight)),
        "camera_role": camera.role,
        "camera_model": camera.model,
        "camera_index": camera.index,
        "camera": {
            "role": camera.role,
            "model": camera.model,
            "index": camera.index,
            "preflight_session_id": camera.preflight_session_id,
        },
        "capture_settings": {
            "requested": {**asdict(FIXED_CAPTURE_SETTINGS), "lossless": True},
            "frame": {
                "width": frame.width,
                "height": frame.height,
                "channels": frame.channels,
            },
            "camera_reported": frame.camera_reported,
        },
        "operator_settings": {
            "provenance": "operator_recorded",
            "hardware_verified_by_capture": False,
            "sha256": operator_settings.sha256,
            "content": operator_settings.content,
        },
        "image_path": relative_image_path,
        "path": relative_image_path,
        "image_sha256": image_sha256,
        "sha256": image_sha256,
        "image_bytes": len(frame.data),
        "captured_at_utc": _utc_timestamp(clock),
    }
    metadata_bytes = (
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    _write_artifact_pair(image_path, frame.data, metadata_path, metadata_bytes)
    return CaptureResult(image_path=image_path, metadata_path=metadata_path, metadata=metadata)


class OpenCVCaptureBackend:
    """Open the preflight-selected index and return one lossless, full-resolution PNG."""

    def capture_png(self, camera: CameraIdentity, settings: CaptureSettings) -> CapturedPng:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - depends on optional hardware extra
            raise RuntimeError("Install the camera extra: pip install -e '.[camera]'") from exc

        capture = cv2.VideoCapture(camera.index, cv2.CAP_AVFOUNDATION)
        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"could not open semantic top camera at index {camera.index}")
        try:
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*settings.fourcc))
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.height)
            capture.set(cv2.CAP_PROP_FPS, settings.fps)

            frame = None
            for _ in range(settings.warmup_frames + 1):
                ok, candidate = capture.read()
                if ok and candidate is not None:
                    frame = candidate
            if frame is None:
                raise RuntimeError("semantic top camera did not return a frame")
            if frame.ndim != 3:
                raise RuntimeError(f"camera returned malformed frame shape {frame.shape}")
            height, width, channels = (int(value) for value in frame.shape)
            if width != settings.width or height != settings.height:
                raise RuntimeError(
                    f"camera returned {width}x{height}; require {settings.width}x{settings.height}"
                )
            encoded_ok, encoded = cv2.imencode(
                ".png",
                frame,
                [cv2.IMWRITE_PNG_COMPRESSION, settings.png_compression],
            )
            if not encoded_ok:
                raise RuntimeError("OpenCV failed to encode the captured frame as PNG")
            reported = {
                "width": float(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": float(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": float(capture.get(cv2.CAP_PROP_FPS)),
                "fourcc_code": int(capture.get(cv2.CAP_PROP_FOURCC)),
            }
            return CapturedPng(
                data=encoded.tobytes(),
                width=width,
                height=height,
                channels=channels,
                camera_reported=reported,
            )
        finally:
            capture.release()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture one canonical C920 perception image or one neutral session reference."
        )
    )
    parser.add_argument("preflight", type=Path, help="passed camera_preflight.json")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--lot-id", required=True)
    parser.add_argument("--geometry-id", required=True)
    capture_kind = parser.add_mutually_exclusive_group(required=True)
    capture_kind.add_argument("--bean-id")
    capture_kind.add_argument("--neutral", choices=("begin", "end"))
    return parser


def main(
    argv: list[str] | None = None,
    *,
    backend: CaptureBackend | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = capture_perception(
            load_preflight(args.preflight),
            operator_settings=load_operator_settings(args.settings),
            output_dir=args.output,
            session_id=args.session_id,
            lot_id=args.lot_id,
            geometry_id=args.geometry_id,
            bean_id=args.bean_id,
            reference_position=args.neutral,
            backend=backend or OpenCVCaptureBackend(),
            clock=clock,
        )
    except (FileExistsError, OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(result.metadata_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
