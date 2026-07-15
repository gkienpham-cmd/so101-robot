from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .metrics import summarize_trials
from .models import TrialRecord
from .trial_log import load_trials


def _strata(records: list[TrialRecord]) -> Counter[tuple[str, str | None, str]]:
    return Counter(
        (record.ground_truth_label.value, record.position, record.lighting_condition)
        for record in records
    )


def compare_trial_sets(
    before: list[TrialRecord], after: list[TrialRecord], *, require_matching_strata: bool = True
) -> dict[str, Any]:
    before_strata = _strata(before)
    after_strata = _strata(after)
    if require_matching_strata and before_strata != after_strata:
        raise ValueError(
            "before/after ground-truth, position, and lighting strata differ; "
            "this is not the frozen comparison"
        )

    summaries = {"before": summarize_trials(before), "after": summarize_trials(after)}
    paths = {
        "macro_f1": ("classification", "macro_f1"),
        "false_accept_rate": ("classification", "false_accept_rate"),
        "false_reject_rate": ("classification", "false_reject_rate"),
        "pick_success_rate": ("pick_success", "rate"),
        "place_success_rate": ("place_success", "rate"),
        "end_to_end_rate": ("end_to_end", "rate"),
        "reject_end_to_end_rate": ("reject_end_to_end", "rate"),
        "acceptable_no_motion_rate": ("acceptable_no_motion", "rate"),
    }
    deltas: dict[str, float] = {}
    for name, path in paths.items():
        before_value: Any = summaries["before"]
        after_value: Any = summaries["after"]
        for key in path:
            before_value = before_value[key]
            after_value = after_value[key]
        deltas[name] = float(after_value) - float(before_value)

    return {
        "schema_version": "1.0",
        "matching_strata": before_strata == after_strata,
        "strata": [
            {
                "ground_truth": ground_truth,
                "position": position,
                "lighting": lighting,
                "count": count,
            }
            for (ground_truth, position, lighting), count in sorted(
                before_strata.items(), key=lambda item: str(item[0])
            )
        ],
        "before": summaries["before"],
        "after": summaries["after"],
        "delta_after_minus_before": deltas,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare two BeanSight frozen-protocol trial logs."
    )
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/before_after.json"))
    parser.add_argument("--allow-strata-mismatch", action="store_true")
    args = parser.parse_args(argv)
    comparison = compare_trial_sets(
        load_trials(args.before),
        load_trials(args.after),
        require_matching_strata=not args.allow_strata_mismatch,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
