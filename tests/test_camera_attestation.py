from datetime import UTC, datetime, timedelta

import pytest

from beansight_vn.camera_attestation import build_camera_attestation
from beansight_vn.lerobot_config import validate_current_camera_evidence


def preflight(*, completed_at=None):
    return {
        "passed": True,
        "session_id": "camera-session-1",
        "completed_at": completed_at or datetime.now(UTC).isoformat(),
        "cameras": {},
    }


def test_current_camera_attestation_binds_review_to_preflight():
    report = preflight()
    attestation = build_camera_attestation(report, reviewer="operator")
    validate_current_camera_evidence(report, attestation, max_age_minutes=120)

    changed = {**report, "session_id": "different-session"}
    with pytest.raises(ValueError, match="session"):
        validate_current_camera_evidence(changed, attestation, max_age_minutes=120)


def test_stale_camera_indexes_cannot_generate_a_recording_config():
    report = preflight(completed_at=(datetime.now(UTC) - timedelta(hours=3)).isoformat())
    attestation = build_camera_attestation(report, reviewer="operator")
    with pytest.raises(ValueError, match="stale"):
        validate_current_camera_evidence(report, attestation, max_age_minutes=120)
