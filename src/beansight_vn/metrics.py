from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Sequence
from statistics import median

from .models import FailureCode, Label, TrialRecord


def wilson_interval(
    successes: int, trials: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials")
    if trials == 0:
        return (0.0, 0.0)
    proportion = successes / trials
    denominator = 1.0 + z**2 / trials
    center = (proportion + z**2 / (2.0 * trials)) / denominator
    margin = (
        z
        * math.sqrt((proportion * (1.0 - proportion) + z**2 / (4.0 * trials)) / trials)
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def rate_summary(values: Iterable[bool]) -> dict[str, float | int | list[float]]:
    observations = list(values)
    successes = sum(observations)
    trials = len(observations)
    low, high = wilson_interval(successes, trials)
    return {
        "successes": successes,
        "trials": trials,
        "rate": successes / trials if trials else 0.0,
        "wilson_95": [low, high],
    }


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _classification_metrics(records: Sequence[TrialRecord]) -> dict[str, object]:
    confusion = {actual.value: {predicted.value: 0 for predicted in Label} for actual in Label}
    for record in records:
        confusion[record.ground_truth_label.value][record.predicted_label.value] += 1

    per_class: dict[str, dict[str, float | int]] = {}
    f1_scores: list[float] = []
    for label in Label:
        tp = confusion[label.value][label.value]
        fp = sum(confusion[actual.value][label.value] for actual in Label if actual is not label)
        fn = sum(
            confusion[label.value][predicted.value] for predicted in Label if predicted is not label
        )
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_scores.append(f1)
        per_class[label.value] = {
            "support": sum(confusion[label.value].values()),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    acceptable = Label.ACCEPTABLE.value
    reject = Label.VISIBLE_REJECT.value
    reject_support = sum(confusion[reject].values())
    acceptable_support = sum(confusion[acceptable].values())
    return {
        "confusion_matrix": confusion,
        "per_class": per_class,
        "macro_f1": sum(f1_scores) / len(f1_scores),
        "false_accept_rate": confusion[reject][acceptable] / reject_support
        if reject_support
        else 0.0,
        "false_reject_rate": confusion[acceptable][reject] / acceptable_support
        if acceptable_support
        else 0.0,
        "accuracy": sum(r.ground_truth_label is r.predicted_label for r in records) / len(records)
        if records
        else 0.0,
    }


def summarize_trials(records: Sequence[TrialRecord]) -> dict[str, object]:
    latency_fields = {
        "perception_ms": [r.perception_ms for r in records if r.perception_ms is not None],
        "policy_ms": [r.policy_ms for r in records if r.policy_ms is not None],
        "cycle_ms": [r.cycle_ms for r in records if r.cycle_ms is not None],
    }
    latencies = {
        name: {
            "n": len(values),
            "median": median(values) if values else None,
            "p95": percentile(values, 0.95),
        }
        for name, values in latency_fields.items()
    }
    failure_counts = Counter(
        r.failure_code.value for r in records if r.failure_code is not FailureCode.NONE
    )
    reject_trials = [r for r in records if r.pick_success is not None]
    place_trials = [r for r in records if r.place_success is not None]
    acceptable_trials = [r for r in records if r.ground_truth_label is Label.ACCEPTABLE]
    reject_ground_truth = [r for r in records if r.ground_truth_label is Label.VISIBLE_REJECT]

    return {
        "trial_count": len(records),
        "classification": _classification_metrics(records),
        "pick_success": rate_summary(bool(r.pick_success) for r in reject_trials),
        "place_success": rate_summary(bool(r.place_success) for r in place_trials),
        "end_to_end": rate_summary(r.end_to_end_success for r in records),
        "acceptable_no_motion": rate_summary(r.end_to_end_success for r in acceptable_trials),
        "reject_end_to_end": rate_summary(r.end_to_end_success for r in reject_ground_truth),
        "intervention": rate_summary(r.intervention for r in records),
        "latency": latencies,
        "failures": {
            code.value: failure_counts.get(code.value, 0)
            for code in FailureCode
            if code is not FailureCode.NONE
        },
    }
