import pytest

from beansight_vn.metrics import percentile, summarize_trials, wilson_interval
from beansight_vn.models import Decision, FailureCode, Label, TrialRecord


def trial(index, truth, prediction, success, failure=FailureCode.NONE):
    reject = truth is Label.VISIBLE_REJECT
    return TrialRecord(
        trial_id=f"T{index}",
        experiment_id="E1",
        session_id="S1",
        bean_id=f"B{index}",
        bean_lot="LOT_A",
        ground_truth_label=truth,
        predicted_label=prediction,
        confidence=0.9,
        decision=Decision.REJECT if prediction is Label.VISIBLE_REJECT else Decision.NO_MOTION,
        end_to_end_success=success,
        failure_code=failure,
        pick_success=success if reject and prediction is Label.VISIBLE_REJECT else None,
        place_success=success if reject and prediction is Label.VISIBLE_REJECT else None,
        perception_ms=10 + index,
        cycle_ms=100 + index,
    )


def test_wilson_interval_known_value():
    low, high = wilson_interval(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-4)
    assert high == pytest.approx(0.7634, abs=1e-4)


def test_wilson_rejects_invalid_counts():
    with pytest.raises(ValueError):
        wilson_interval(3, 2)


def test_percentile_interpolates():
    assert percentile([0.0, 10.0], 0.95) == pytest.approx(9.5)
    assert percentile([], 0.5) is None


def test_summary_separates_classification_and_robot_outcomes():
    records = [
        trial(1, Label.ACCEPTABLE, Label.ACCEPTABLE, True),
        trial(
            2,
            Label.VISIBLE_REJECT,
            Label.ACCEPTABLE,
            False,
            FailureCode.PERCEPTION_FALSE_ACCEPT,
        ),
        trial(3, Label.VISIBLE_REJECT, Label.VISIBLE_REJECT, True),
    ]
    summary = summarize_trials(records)
    assert summary["trial_count"] == 3
    assert summary["classification"]["accuracy"] == pytest.approx(2 / 3)
    assert summary["classification"]["macro_f1"] == pytest.approx(2 / 3)
    assert summary["classification"]["false_accept_rate"] == pytest.approx(0.5)
    assert summary["classification"]["false_reject_rate"] == 0.0
    assert summary["reject_end_to_end"]["rate"] == pytest.approx(0.5)
    assert summary["failures"] == {"perception_false_accept": 1}
    assert summary["latency"]["cycle_ms"]["p95"] == pytest.approx(102.9)
