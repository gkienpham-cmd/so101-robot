import pytest

from beansight_vn.lerobot_config import build_record_config


def report(passed=True):
    camera = {
        "passed": True,
        "requested": {"width": 640, "height": 480, "fps": 30, "fourcc": "MJPG"},
    }
    return {
        "passed": passed,
        "cameras": {
            "top": {**camera, "index": 3, "device_name": "C920"},
            "wrist": {**camera, "index": 7, "device_name": "C270"},
        },
    }


def test_record_config_preserves_semantic_keys_and_safety_limit():
    config = build_record_config(
        report(), follower_port="/dev/follower", leader_port="/dev/leader", repo_id="user/data"
    )
    assert list(config["robot"]["cameras"]) == ["top", "wrist"]
    assert config["robot"]["cameras"]["top"]["index_or_path"] == 3
    assert config["robot"]["max_relative_target"] == 10.0
    assert config["dataset"]["push_to_hub"] is False
    assert config["dataset"]["private"] is True


def test_failed_camera_report_cannot_create_recording_config():
    with pytest.raises(ValueError, match="did not pass"):
        build_record_config(
            report(False), follower_port="/dev/f", leader_port="/dev/l", repo_id="user/data"
        )
