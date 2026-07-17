from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import math
import re
import subprocess
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_CAMERAS = ("observation.images.top", "observation.images.wrist")
EXPECTED_LEROBOT_VERSION = "0.6.0"
EXPECTED_LEROBOT_REVISION = "30da8e687a6dfc617fcd94afc367ac7071c376ce"
EXPECTED_RECORDING_PATCH_SHA256 = (
    "8480712f0b3485968557e0a648f47a7cd54f0edebba8fd9981c5f88301bdb01f"
)
IMMUTABLE_REVISION = re.compile(r"[0-9a-f]{40}")
DEFAULT_RECORDING_PATCH = (
    Path(__file__).resolve().parents[2]
    / "patches"
    / "lerobot-v0.6.0-macos-serial-encoding.patch"
)


@dataclass(slots=True)
class ValidationReport:
    dataset: str
    revision: str | None = None
    frames_checked: int = 0
    camera_keys: list[str] = field(default_factory=list)
    action_std: list[float] = field(default_factory=list)
    episode_lengths: dict[str, int] = field(default_factory=dict)
    episode_tasks: dict[str, int] = field(default_factory=dict)
    dataset_fingerprint_sha256: str | None = None
    lerobot_version: str | None = None
    lerobot_revision: str | None = None
    recording_patch_sha256: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.1",
            "dataset": self.dataset,
            "revision": self.revision,
            "passed": self.passed,
            "frames_checked": self.frames_checked,
            "camera_keys": self.camera_keys,
            "action_std": self.action_std,
            "episode_lengths": self.episode_lengths,
            "episode_tasks": self.episode_tasks,
            "dataset_fingerprint_sha256": self.dataset_fingerprint_sha256,
            "lerobot_version": self.lerobot_version,
            "lerobot_revision": self.lerobot_revision,
            "recording_patch_sha256": self.recording_patch_sha256,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _array(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def _scalar_int(value: Any) -> int:
    array = _array(value)
    if array.size != 1:
        raise ValueError(f"expected scalar, got shape {array.shape}")
    return int(array.reshape(-1)[0])


def dataset_fingerprint(path: str | Path) -> str:
    root = Path(path)
    if not root.is_dir():
        raise ValueError(f"dataset root is not a directory: {root}")
    files = sorted(
        file for file in root.rglob("*") if file.is_file() and file.name != ".DS_Store"
    )
    if not files:
        raise ValueError("dataset root contains no files to fingerprint")
    digest = hashlib.sha256()
    for file in files:
        relative = file.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(file.stat().st_size.to_bytes(8, "big"))
        with file.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def pinned_lerobot_provenance(patch_path: str | Path) -> dict[str, str]:
    import lerobot

    version = importlib.metadata.version("lerobot")
    if version != EXPECTED_LEROBOT_VERSION:
        raise RuntimeError(
            f"LeRobot version is {version}; require exactly {EXPECTED_LEROBOT_VERSION}"
        )
    source = Path(inspect.getfile(lerobot)).resolve()
    repo = next((parent for parent in source.parents if (parent / ".git").exists()), None)
    if repo is None:
        raise RuntimeError("LeRobot must be an editable checkout with readable Git provenance")
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    revision = completed.stdout.strip()
    if revision != EXPECTED_LEROBOT_REVISION:
        raise RuntimeError(
            f"LeRobot revision is {revision}; require exactly {EXPECTED_LEROBOT_REVISION}"
        )
    patch = Path(patch_path)
    patch_digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    if patch_digest != EXPECTED_RECORDING_PATCH_SHA256:
        raise RuntimeError("recording patch hash differs from the repository-approved patch")
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "apply",
                "--reverse",
                "--check",
                "--unidiff-zero",
                str(patch.resolve()),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("repository-approved recording patch is not applied") from exc
    return {
        "lerobot_version": version,
        "lerobot_revision": revision,
        "recording_patch_sha256": patch_digest,
    }


def camera_feature_keys(features: Mapping[str, Any]) -> list[str]:
    return [key for key in features if key.startswith("observation.images.")]


def validate_frame(
    item: Mapping[str, Any],
    *,
    expected_cameras: Iterable[str] = EXPECTED_CAMERAS,
    action_dim: int = 6,
    min_gradient_energy: float = 1e-5,
) -> list[str]:
    errors: list[str] = []
    for key in expected_cameras:
        if key not in item:
            errors.append(f"missing camera frame {key}")
            continue
        frame = _array(item[key])
        if frame.size == 0:
            errors.append(f"empty camera frame {key}")
        elif not np.isfinite(frame).all():
            errors.append(f"non-finite values in camera frame {key}")
        elif frame.ndim != 3 or 3 not in frame.shape:
            errors.append(f"camera frame {key} has malformed shape {frame.shape}")
        else:
            image = frame.astype(float)
            image_range = float(np.ptp(image))
            if image_range == 0:
                errors.append(f"constant camera frame {key}")
            else:
                normalized = (image - image.min()) / image_range
                channel_axis = next(index for index, size in enumerate(frame.shape) if size == 3)
                luminance = normalized.mean(axis=channel_axis)
                dx = np.diff(luminance, axis=1)
                dy = np.diff(luminance, axis=0)
                gradient_energy = float(np.mean(dx**2) + np.mean(dy**2))
                if gradient_energy < min_gradient_energy:
                    errors.append(
                        f"camera frame {key} is likely blurred/dead "
                        f"(gradient_energy={gradient_energy:.3g})"
                    )

    if "action" not in item:
        errors.append("missing action")
    else:
        action = _array(item["action"]).reshape(-1)
        if action.shape != (action_dim,):
            errors.append(f"action has shape {action.shape}; expected ({action_dim},)")
        elif not np.isfinite(action).all():
            errors.append("action contains NaN or Inf")

    for key in ("episode_index", "frame_index"):
        if key not in item:
            errors.append(f"missing {key}")
    return errors


def validate_dataset(
    dataset: Any,
    *,
    dataset_name: str,
    expected_cameras: tuple[str, ...] = EXPECTED_CAMERAS,
    action_dim: int = 6,
    dead_joint_std: float = 1e-6,
    min_frame_gradient: float = 1e-5,
    max_frames: int | None = None,
    dataset_revision: str | None = None,
) -> ValidationReport:
    report = ValidationReport(dataset=dataset_name, revision=dataset_revision)
    features = getattr(dataset, "features", {})
    report.camera_keys = camera_feature_keys(features)
    if report.camera_keys != list(expected_cameras):
        report.errors.append(
            f"camera order is {report.camera_keys}; expected {list(expected_cameras)}"
        )

    total = len(dataset)
    if total == 0:
        report.errors.append("dataset contains no frames")
        return report
    if max_frames is None or max_frames >= total:
        indexes = list(range(total))
    else:
        indexes = sorted(set(np.linspace(0, total - 1, max_frames, dtype=int).tolist()))

    actions: list[np.ndarray] = []
    episode_frames: dict[int, list[int]] = defaultdict(list)
    episode_tasks: dict[int, set[int]] = defaultdict(set)
    for index in indexes:
        try:
            item = dataset[index]
        except Exception as exc:  # decoding errors include missing video frames
            report.errors.append(f"frame {index} could not be read: {exc}")
            continue
        errors = validate_frame(
            item,
            expected_cameras=expected_cameras,
            action_dim=action_dim,
            min_gradient_energy=min_frame_gradient,
        )
        report.errors.extend(f"frame {index}: {error}" for error in errors)
        if "action" in item:
            action = _array(item["action"]).reshape(-1)
            if action.shape == (action_dim,) and np.isfinite(action).all():
                actions.append(action.astype(float))
        try:
            episode = _scalar_int(item["episode_index"])
            episode_frames[episode].append(_scalar_int(item["frame_index"]))
            if "task_index" in item:
                episode_tasks[episode].add(_scalar_int(item["task_index"]))
        except (KeyError, ValueError) as exc:
            report.errors.append(f"frame {index}: malformed episode metadata: {exc}")
        report.frames_checked += 1

    if actions:
        report.action_std = np.std(np.stack(actions), axis=0).tolist()
        dead = [index for index, value in enumerate(report.action_std) if value <= dead_joint_std]
        if dead:
            report.errors.append(f"dead or constant action dimensions: {dead}")
    else:
        report.errors.append("no valid actions were available for statistical QA")

    for episode, frame_indexes in sorted(episode_frames.items()):
        report.episode_lengths[str(episode)] = len(frame_indexes)
        ordered = sorted(frame_indexes)
        if max_frames is None and ordered != list(range(len(ordered))):
            report.errors.append(
                f"episode {episode} frame_index is not contiguous from zero: "
                f"first={ordered[0]}, last={ordered[-1]}, count={len(ordered)}"
            )
        tasks = episode_tasks.get(episode, set())
        if len(tasks) > 1:
            report.errors.append(f"episode {episode} crosses task indexes: {sorted(tasks)}")
        elif tasks:
            report.episode_tasks[str(episode)] = next(iter(tasks))
    if max_frames is not None and max_frames < total:
        report.warnings.append(
            f"sampled {len(indexes)} of {total} frames; run without --max-frames before training"
        )
    if any(not math.isfinite(value) for value in report.action_std):
        report.errors.append("action statistics contain NaN or Inf")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gate a LeRobot dataset before cloud training.")
    parser.add_argument(
        "repo_id", help="Hugging Face dataset repo_id, or the identifier stored at --root"
    )
    parser.add_argument("--root", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--action-dim", type=int, default=6)
    parser.add_argument("--dead-joint-std", type=float, default=1e-6)
    parser.add_argument("--min-frame-gradient", type=float, default=1e-5)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--output", type=Path, default=Path("results/dataset_qa.json"))
    parser.add_argument(
        "--recording-patch",
        type=Path,
        default=DEFAULT_RECORDING_PATCH,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.revision:
        if not IMMUTABLE_REVISION.fullmatch(args.revision):
            parser.error("--revision must be a 40-character immutable commit hash")
        if args.root is None:
            parser.error("pinned Hub QA requires a fresh, explicit --root snapshot path")
        if args.root.exists() and any(args.root.iterdir()):
            parser.error("pinned Hub QA --root must be new or empty; refusing cached local bytes")
    provenance = pinned_lerobot_provenance(args.recording_patch)
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as exc:
        raise RuntimeError("Run dataset QA from the pinned LeRobot v0.6.0 environment") from exc
    dataset = LeRobotDataset(repo_id=args.repo_id, root=args.root, revision=args.revision)
    report = validate_dataset(
        dataset,
        dataset_name=args.repo_id,
        action_dim=args.action_dim,
        dead_joint_std=args.dead_joint_std,
        min_frame_gradient=args.min_frame_gradient,
        max_frames=args.max_frames,
        dataset_revision=args.revision,
    )
    resolved_root_value = getattr(dataset, "root", None) or args.root
    if resolved_root_value is None:
        raise RuntimeError("LeRobot dataset did not expose a root for content fingerprinting")
    resolved_root = Path(resolved_root_value)
    report.dataset_fingerprint_sha256 = dataset_fingerprint(resolved_root)
    report.lerobot_version = provenance["lerobot_version"]
    report.lerobot_revision = provenance["lerobot_revision"]
    report.recording_patch_sha256 = provenance["recording_patch_sha256"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
