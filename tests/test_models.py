import pytest

from beansight_vn.models import (
    Decision,
    ExperimentManifest,
    FailureCode,
    Label,
    PerceptionResult,
    TrialRecord,
)


def make_trial(**overrides):
    values = {
        "trial_id": "T001",
        "experiment_id": "E001",
        "session_id": "S001",
        "bean_id": "B001",
        "bean_lot": "LOT_A",
        "ground_truth_label": Label.VISIBLE_REJECT,
        "predicted_label": Label.VISIBLE_REJECT,
        "confidence": 0.91,
        "decision": Decision.REJECT,
        "end_to_end_success": True,
        "pick_success": True,
        "place_success": True,
    }
    values.update(overrides)
    return TrialRecord(**values)


def test_perception_contract_validates_confidence_and_roi():
    with pytest.raises(ValueError, match="confidence"):
        PerceptionResult(Label.ACCEPTABLE, 1.1)
    with pytest.raises(ValueError, match="non-zero"):
        PerceptionResult(Label.ACCEPTABLE, 0.5, roi=(0, 0, 0, 20))


def test_trial_contract_round_trips():
    trial = make_trial(roi=(1, 2, 3, 4))
    restored = TrialRecord.from_dict(trial.to_dict())
    assert restored == trial
    assert restored.roi == (1, 2, 3, 4)
    assert restored.failure_code is FailureCode.NONE


def test_success_cannot_have_failure_code():
    with pytest.raises(ValueError, match="successful"):
        make_trial(failure_code=FailureCode.DROP)


def test_failure_requires_a_primary_failure_code():
    with pytest.raises(ValueError, match="primary failure_code"):
        make_trial(end_to_end_success=False, pick_success=False, place_success=False)


def test_no_motion_cannot_report_grasp_results():
    with pytest.raises(ValueError, match="no-motion"):
        make_trial(decision=Decision.NO_MOTION)


def test_experiment_manifest_rejects_placeholder_provenance_hashes():
    required = {
        "experiment_id": "experiment-1",
        "git_sha": "a" * 40,
        "lerobot_revision": "30da8e687a6dfc617fcd94afc367ac7071c376ce",
    }
    with pytest.raises(ValueError, match="qa_report_sha256"):
        ExperimentManifest(**required, qa_report_sha256="REPLACE_WITH_SHA256")
    with pytest.raises(ValueError, match="policy_revision"):
        ExperimentManifest(**required, policy_revision="main")
    manifest = ExperimentManifest(**required, qa_report_sha256="b" * 64)
    assert manifest.qa_report_sha256 == "b" * 64
