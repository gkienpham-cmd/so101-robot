import json

import pytest

from beansight_vn.models import Decision, Label, TrialRecord
from beansight_vn.trial_log import append_trial, load_trials, write_summary


def trial():
    return TrialRecord(
        trial_id="T1",
        experiment_id="E1",
        session_id="S1",
        bean_id="B1",
        bean_lot="L1",
        ground_truth_label=Label.ACCEPTABLE,
        predicted_label=Label.ACCEPTABLE,
        confidence=0.98,
        decision=Decision.NO_MOTION,
        end_to_end_success=True,
    )


def test_jsonl_append_load_and_summary(tmp_path):
    path = tmp_path / "trials.jsonl"
    original = trial()
    append_trial(path, original)
    restored = load_trials(path)
    assert restored == [original]
    summary_path = tmp_path / "summary.json"
    summary = write_summary(summary_path, restored)
    assert summary["acceptable_no_motion"]["rate"] == 1.0
    assert json.loads(summary_path.read_text())["trial_count"] == 1


def test_invalid_jsonl_reports_line_number(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{}\nnot-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        load_trials(path)
