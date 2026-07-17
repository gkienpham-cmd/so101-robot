from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .camera_attestation import preflight_sha256

RECORD_PROFILES: dict[str, dict[str, Any]] = {
    "blocks": {
        "single_task": (
            "Pick the wooden block from the marked position and place it in the target cup."
        ),
        "episodes": 50,
        "episode_time_s": 12,
        "tags": ["so101", "blocks", "bringup", "beansight-vn"],
    },
    "coffee": {
        "single_task": "Pick the bean from the inspection nest and place it in the reject cup.",
        "episodes": 60,
        "episode_time_s": 12,
        "tags": ["so101", "coffee", "beansight-vn"],
    },
    "caps": {
        "single_task": (
            "Pick the upright plastic screw cap and lift it to the safe handoff pose."
        ),
        "episodes": 75,
        "episode_time_s": 10,
        "tags": ["so101", "plastic-caps", "transfer", "beansight-vn"],
    },
    "bottles": {
        "single_task": (
            "Pick the empty dry bottle by the neck from the V-cradle and lift it to the "
            "safe handoff pose."
        ),
        "episodes": 75,
        "episode_time_s": 12,
        "tags": ["so101", "plastic-bottles", "transfer", "beansight-vn"],
    },
}
SHA256 = re.compile(r"[0-9a-f]{64}")


def _require_gate(
    evidence: Mapping[str, Any] | None,
    gate: str,
    *,
    pass_field: str,
    path_field: str,
    hash_field: str,
) -> None:
    payload = evidence.get(gate) if evidence else None
    if not isinstance(payload, Mapping) or payload.get(pass_field) is not True:
        raise ValueError(f"recording profile requires passing gate evidence: {gate}")
    expected_digest = str(payload.get(hash_field, ""))
    if not SHA256.fullmatch(expected_digest):
        raise ValueError(f"recording gate {gate} requires {hash_field} sha256 evidence")
    evidence_path = Path(str(payload.get(path_field, "")))
    if not evidence_path.is_file():
        raise ValueError(f"recording gate {gate} evidence file does not exist: {evidence_path}")
    actual_digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    if actual_digest != expected_digest:
        raise ValueError(f"recording gate {gate} evidence hash does not match {evidence_path}")


def _read_gate_json(
    evidence: Mapping[str, Any] | None, gate: str, *, path_field: str
) -> Mapping[str, Any]:
    payload = evidence.get(gate) if evidence else None
    if not isinstance(payload, Mapping):
        raise ValueError(f"recording gate evidence is missing: {gate}")
    path = Path(str(payload.get(path_field, "")))
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"recording gate {gate} is not readable JSON: {path}") from exc
    if not isinstance(report, Mapping):
        raise ValueError(f"recording gate {gate} report must be a JSON object")
    return report


def validate_recording_profile_gates(
    task_profile: str, evidence: Mapping[str, Any] | None
) -> None:
    if task_profile == "blocks":
        return
    if task_profile == "coffee":
        _require_gate(
            evidence,
            "bean_mechanical_gate",
            pass_field="passed",
            path_field="summary_path",
            hash_field="summary_sha256",
        )
        return
    _require_gate(
        evidence,
        "beansight_frozen_evaluation",
        pass_field="completed",
        path_field="summary_path",
        hash_field="summary_sha256",
    )
    if task_profile == "bottles":
        _require_gate(
            evidence,
            "material_sensor_gate",
            pass_field="passed",
            path_field="metrics_path",
            hash_field="metrics_sha256",
        )
        sensor_metrics = _read_gate_json(
            evidence, "material_sensor_gate", path_field="metrics_path"
        )
        rbf_metrics = sensor_metrics.get("rbf_svm")
        artifact_metrics = sensor_metrics.get("artifact")
        if not (
            isinstance(rbf_metrics, Mapping)
            and isinstance(rbf_metrics.get("gate"), Mapping)
            and rbf_metrics["gate"].get("passed") is True
            and isinstance(artifact_metrics, Mapping)
            and artifact_metrics.get("deployable") is True
        ):
            raise ValueError("bottle recording requires qualified material-sensor metrics")
        _require_gate(
            evidence,
            "bottle_waypoint_gate",
            pass_field="pose_variation_is_largest_failure",
            path_field="summary_path",
            hash_field="summary_sha256",
        )
        waypoint_summary = _read_gate_json(
            evidence, "bottle_waypoint_gate", path_field="summary_path"
        )
        overall = waypoint_summary.get("scripted_waypoint_overall_gate")
        geometry_count = (
            overall.get("representative_geometry_count")
            if isinstance(overall, Mapping)
            else None
        )
        if not (
            isinstance(overall, Mapping)
            and isinstance(geometry_count, int)
            and not isinstance(geometry_count, bool)
            and geometry_count >= 3
            and overall.get("all_geometries_have_exactly_20_trials") is True
            and overall.get("passed") is False
            and waypoint_summary.get("bottle_failure_branch")
            == "collect_act_for_pose_variation"
        ):
            raise ValueError(
                "bottle ACT recording requires a complete failed waypoint gate with pose "
                "variation as the computed largest failure group"
            )


def validate_current_camera_evidence(
    preflight: Mapping[str, Any],
    attestation: Mapping[str, Any] | None,
    *,
    max_age_minutes: float,
) -> None:
    if max_age_minutes <= 0:
        raise ValueError("max camera-evidence age must be positive")
    completed_text = str(preflight.get("completed_at", ""))
    try:
        completed = datetime.fromisoformat(completed_text)
    except ValueError as exc:
        raise ValueError("camera preflight lacks a valid completed_at timestamp") from exc
    if completed.tzinfo is None:
        raise ValueError("camera preflight completed_at must include a timezone")
    age_seconds = (datetime.now(UTC) - completed.astimezone(UTC)).total_seconds()
    if age_seconds < -60 or age_seconds > max_age_minutes * 60:
        raise ValueError("camera preflight is stale; resolve semantic cameras for this launch")
    if not preflight.get("session_id"):
        raise ValueError("camera preflight lacks a launch session_id")
    if not isinstance(attestation, Mapping):
        raise ValueError("current camera visual attestation is required")
    if attestation.get("preflight_session_id") != preflight["session_id"]:
        raise ValueError("camera attestation session does not match the current preflight")
    if attestation.get("preflight_sha256") != preflight_sha256(dict(preflight)):
        raise ValueError("camera attestation hash does not match the current preflight")
    if not all(
        attestation.get(key)
        for key in (
            "sample_images_reviewed",
            "top_view_confirmed_c920",
            "wrist_view_confirmed_c270",
        )
    ):
        raise ValueError("camera attestation must confirm both named views and sample review")
    if not str(attestation.get("reviewer", "")).strip():
        raise ValueError("camera attestation requires a reviewer")


def build_record_config(
    preflight: dict[str, Any],
    *,
    follower_port: str,
    leader_port: str,
    repo_id: str,
    root: str | None = None,
    task_profile: str = "blocks",
    episodes: int | None = None,
    episode_time_s: int | None = None,
    gate_evidence: Mapping[str, Any] | None = None,
    camera_attestation: Mapping[str, Any] | None = None,
    max_camera_evidence_age_minutes: float = 120.0,
) -> dict[str, Any]:
    if not preflight.get("passed"):
        raise ValueError("camera preflight did not pass; refusing to build a recording config")
    validate_current_camera_evidence(
        preflight,
        camera_attestation,
        max_age_minutes=max_camera_evidence_age_minutes,
    )
    cameras = preflight.get("cameras", {})
    if list(sorted(cameras)) != ["top", "wrist"]:
        raise ValueError("preflight must contain exactly the semantic top and wrist cameras")
    if task_profile not in RECORD_PROFILES:
        raise ValueError(f"unknown recording profile: {task_profile}")
    validate_recording_profile_gates(task_profile, gate_evidence)
    profile = RECORD_PROFILES[task_profile]
    episode_count = int(episodes if episodes is not None else profile["episodes"])
    duration = int(
        episode_time_s if episode_time_s is not None else profile["episode_time_s"]
    )
    if episode_count < 1 or duration < 1:
        raise ValueError("episodes and episode_time_s must be positive")

    camera_config: dict[str, Any] = {}
    for name in ("top", "wrist"):
        report = cameras[name]
        if not report.get("passed"):
            raise ValueError(f"{name} camera did not pass preflight")
        requested = report["requested"]
        camera_config[name] = {
            "type": "opencv",
            "index_or_path": int(report["index"]),
            "fps": int(requested["fps"]),
            "width": int(requested["width"]),
            "height": int(requested["height"]),
            "fourcc": requested["fourcc"],
        }

    return {
        "robot": {
            "type": "so101_follower",
            "port": follower_port,
            "id": "beansight_follower",
            "max_relative_target": 10.0,
            "cameras": camera_config,
            "use_degrees": True,
        },
        "teleop": {
            "type": "so101_leader",
            "port": leader_port,
            "id": "beansight_leader",
            "use_degrees": True,
        },
        "dataset": {
            "repo_id": repo_id,
            "single_task": profile["single_task"],
            "root": root,
            "fps": 30,
            "episode_time_s": duration,
            "reset_time_s": 8,
            "num_episodes": episode_count,
            "video": True,
            "push_to_hub": False,
            "private": True,
            "tags": profile["tags"],
            "num_image_writer_processes": 0,
            "num_image_writer_threads_per_camera": 4,
            "video_encoding_batch_size": 1,
            # Avoid the post-episode multi-camera process pool that collides
            # with duplicate cv2/av libavdevice builds on this macOS setup.
            "streaming_encoding": True,
            "encoder_threads": 2,
        },
        "display_data": True,
        "display_mode": "rerun",
        "play_sounds": True,
        "resume": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a LeRobot v0.6 recording config from a passing semantic camera report."
    )
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--follower-port", required=True)
    parser.add_argument("--leader-port", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--root")
    parser.add_argument("--profile", choices=sorted(RECORD_PROFILES), default="blocks")
    parser.add_argument("--gate-evidence", type=Path)
    parser.add_argument("--camera-attestation", type=Path, required=True)
    parser.add_argument("--max-camera-evidence-age-minutes", type=float, default=120.0)
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--episode-time", type=int)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    gate_evidence = (
        json.loads(args.gate_evidence.read_text(encoding="utf-8"))
        if args.gate_evidence
        else None
    )
    camera_attestation = json.loads(
        args.camera_attestation.read_text(encoding="utf-8")
    )
    config = build_record_config(
        preflight,
        follower_port=args.follower_port,
        leader_port=args.leader_port,
        repo_id=args.repo_id,
        root=args.root,
        task_profile=args.profile,
        episodes=args.episodes,
        episode_time_s=args.episode_time,
        gate_evidence=gate_evidence,
        camera_attestation=camera_attestation,
        max_camera_evidence_age_minutes=args.max_camera_evidence_age_minutes,
    )
    output = args.output or Path(f"configs/generated/record_{args.profile}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if gate_evidence is not None:
        evidence_text = json.dumps(gate_evidence, sort_keys=True, separators=(",", ":"))
        sidecar = output.with_suffix(".gate.json")
        sidecar.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "profile": args.profile,
                    "gate_evidence_sha256": hashlib.sha256(evidence_text.encode()).hexdigest(),
                    "gate_evidence": gate_evidence,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
