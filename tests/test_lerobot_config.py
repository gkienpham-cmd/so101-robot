import hashlib
import json
from datetime import UTC, datetime

import pytest

from beansight_vn.camera_attestation import build_camera_attestation
from beansight_vn.lerobot_config import build_record_config


def report(passed=True):
    camera = {
        "passed": True,
        "requested": {"width": 640, "height": 480, "fps": 30, "fourcc": "MJPG"},
    }
    return {
        "passed": passed,
        "session_id": "camera-session-1",
        "completed_at": datetime.now(UTC).isoformat(),
        "cameras": {
            "top": {**camera, "index": 3, "device_name": "C920"},
            "wrist": {**camera, "index": 7, "device_name": "C270"},
        },
    }


def camera_evidence():
    preflight = report()
    return preflight, build_camera_attestation(preflight, reviewer="test-reviewer")


def test_record_config_preserves_semantic_keys_and_safety_limit():
    preflight, attestation = camera_evidence()
    config = build_record_config(
        preflight,
        follower_port="/dev/follower",
        leader_port="/dev/leader",
        repo_id="user/data",
        camera_attestation=attestation,
    )
    assert list(config["robot"]["cameras"]) == ["top", "wrist"]
    assert config["robot"]["cameras"]["top"]["index_or_path"] == 3
    assert config["robot"]["max_relative_target"] == 10.0
    assert config["dataset"]["push_to_hub"] is False
    assert config["dataset"]["private"] is True
    assert config["dataset"]["streaming_encoding"] is True
    assert config["dataset"]["encoder_threads"] == 2


def test_failed_camera_report_cannot_create_recording_config():
    with pytest.raises(ValueError, match="did not pass"):
        build_record_config(
            report(False), follower_port="/dev/f", leader_port="/dev/l", repo_id="user/data"
        )


def test_cap_profile_records_only_short_horizon_grasp_to_handoff(tmp_path):
    summary = tmp_path / "beansight-summary.json"
    summary.write_text("{}", encoding="utf-8")
    preflight, attestation = camera_evidence()
    config = build_record_config(
        preflight,
        follower_port="/dev/follower",
        leader_port="/dev/leader",
        repo_id="user/caps",
        task_profile="caps",
        gate_evidence={
            "beansight_frozen_evaluation": {
                "completed": True,
                "summary_path": str(summary),
                "summary_sha256": hashlib.sha256(summary.read_bytes()).hexdigest(),
            }
        },
        camera_attestation=attestation,
    )
    assert config["dataset"]["num_episodes"] == 75
    assert config["dataset"]["episode_time_s"] == 10
    assert "handoff pose" in config["dataset"]["single_task"]
    assert "plastic-caps" in config["dataset"]["tags"]


def test_unknown_recording_profile_is_rejected():
    preflight, attestation = camera_evidence()
    with pytest.raises(ValueError, match="unknown recording profile"):
        build_record_config(
            preflight,
            follower_port="/dev/follower",
            leader_port="/dev/leader",
            repo_id="user/data",
            task_profile="unbounded-pile",
            camera_attestation=attestation,
        )


def test_transfer_profiles_require_hashed_sequence_gates():
    preflight, attestation = camera_evidence()
    with pytest.raises(ValueError, match="beansight_frozen_evaluation"):
        build_record_config(
            preflight,
            follower_port="/dev/follower",
            leader_port="/dev/leader",
            repo_id="user/caps",
            task_profile="caps",
            camera_attestation=attestation,
        )


def test_bottle_act_profile_requires_sensor_and_waypoint_failure_evidence(tmp_path):
    beansight_summary = tmp_path / "beansight-summary.json"
    waypoint_summary = tmp_path / "waypoint-summary.json"
    metrics = tmp_path / "metrics.json"
    beansight_summary.write_text("{}", encoding="utf-8")
    waypoint_summary.write_text(
        json.dumps(
            {
                "scripted_waypoint_overall_gate": {
                    "representative_geometry_count": 3,
                    "all_geometries_have_exactly_20_trials": True,
                    "passed": False,
                },
                "bottle_failure_branch": "collect_act_for_pose_variation",
            }
        ),
        encoding="utf-8",
    )
    metrics.write_text(
        json.dumps(
            {
                "rbf_svm": {"gate": {"passed": True}},
                "artifact": {"deployable": True},
            }
        ),
        encoding="utf-8",
    )
    evidence = {
        "beansight_frozen_evaluation": {
            "completed": True,
            "summary_path": str(beansight_summary),
            "summary_sha256": hashlib.sha256(beansight_summary.read_bytes()).hexdigest(),
        },
        "material_sensor_gate": {
            "passed": True,
            "metrics_path": str(metrics),
            "metrics_sha256": hashlib.sha256(metrics.read_bytes()).hexdigest(),
        },
        "bottle_waypoint_gate": {
            "pose_variation_is_largest_failure": True,
            "summary_path": str(waypoint_summary),
            "summary_sha256": hashlib.sha256(waypoint_summary.read_bytes()).hexdigest(),
        },
    }
    preflight, attestation = camera_evidence()
    config = build_record_config(
        preflight,
        follower_port="/dev/follower",
        leader_port="/dev/leader",
        repo_id="user/bottles",
        task_profile="bottles",
        gate_evidence=evidence,
        camera_attestation=attestation,
    )
    assert config["dataset"]["num_episodes"] == 75


def test_bottle_profile_rejects_self_attested_but_unqualified_metrics(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    digest = hashlib.sha256(empty.read_bytes()).hexdigest()
    evidence = {
        "beansight_frozen_evaluation": {
            "completed": True,
            "summary_path": str(empty),
            "summary_sha256": digest,
        },
        "material_sensor_gate": {
            "passed": True,
            "metrics_path": str(empty),
            "metrics_sha256": digest,
        },
        "bottle_waypoint_gate": {
            "pose_variation_is_largest_failure": True,
            "summary_path": str(empty),
            "summary_sha256": digest,
        },
    }
    preflight, attestation = camera_evidence()
    with pytest.raises(ValueError, match="qualified material-sensor metrics"):
        build_record_config(
            preflight,
            follower_port="/dev/follower",
            leader_port="/dev/leader",
            repo_id="user/bottles",
            task_profile="bottles",
            gate_evidence=evidence,
            camera_attestation=attestation,
        )
