import pytest

from beansight_vn.models import Decision, FailureCode, Label, PerceptionResult, TrialRecord


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


def test_no_motion_cannot_report_grasp_results():
    with pytest.raises(ValueError, match="no-motion"):
        make_trial(decision=Decision.NO_MOTION)
