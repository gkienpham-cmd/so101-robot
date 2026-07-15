import pytest

from beansight_vn.comparison import compare_trial_sets
from beansight_vn.models import Decision, FailureCode, Label, TrialRecord


def trial(trial_id, experiment, truth, success, position="center"):
    prediction = truth if success else Label.ACCEPTABLE
    decision = Decision.REJECT if prediction is Label.VISIBLE_REJECT else Decision.NO_MOTION
    reject_motion = decision is Decision.REJECT
    return TrialRecord(
        trial_id=trial_id,
        experiment_id=experiment,
        session_id=experiment,
        bean_id=trial_id,
        bean_lot="L1",
        ground_truth_label=truth,
        predicted_label=prediction,
        confidence=0.9,
        decision=decision,
        end_to_end_success=success,
        failure_code=FailureCode.NONE if success else FailureCode.PERCEPTION_FALSE_ACCEPT,
        pick_success=success if reject_motion else None,
        place_success=success if reject_motion else None,
        position=position,
    )


def test_comparison_reports_after_minus_before_delta():
    before = [
        trial("B1", "before", Label.ACCEPTABLE, True),
        trial("B2", "before", Label.VISIBLE_REJECT, False),
    ]
    after = [
        trial("A1", "after", Label.ACCEPTABLE, True),
        trial("A2", "after", Label.VISIBLE_REJECT, True),
    ]
    comparison = compare_trial_sets(before, after)
    assert comparison["matching_strata"]
    assert comparison["delta_after_minus_before"]["end_to_end_rate"] == 0.5


def test_comparison_rejects_changed_physical_strata():
    before = [trial("B1", "before", Label.ACCEPTABLE, True, "center")]
    after = [trial("A1", "after", Label.ACCEPTABLE, True, "left")]
    with pytest.raises(ValueError, match="strata differ"):
        compare_trial_sets(before, after)
