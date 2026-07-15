from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from statistics import median
from typing import Any

from .metrics import percentile, rate_summary


class GripperVariant(StrEnum):
    STOCK = "stock"
    HIGH_FRICTION_TAPE = "high_friction_tape"
    COMPLIANT_TAPERED = "compliant_tapered"


class BeanOrientation(StrEnum):
    LONGITUDINAL = "longitudinal"
    TRANSVERSE = "transverse"
    DIAGONAL = "diagonal"


@dataclass(slots=True)
class GripperTrial:
    trial_id: str
    variant: GripperVariant
    orientation: BeanOrientation
    bean_id: str
    grasp_success: bool
    transfer_success: bool
    dropped: bool
    cycle_ms: float
    servo_peak_temperature_c: float | None = None
    servo_peak_load: float | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        self.variant = GripperVariant(self.variant)
        self.orientation = BeanOrientation(self.orientation)
        if self.cycle_ms < 0:
            raise ValueError("cycle_ms must be non-negative")
        if self.transfer_success and (not self.grasp_success or self.dropped):
            raise ValueError("transfer success requires a grasp with no drop")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_gripper_trials(path: str | Path) -> list[GripperTrial]:
    records: list[GripperTrial] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(GripperTrial(**json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid gripper trial at line {line_number}: {exc}") from exc
    return records


def summarize_gripper_trials(records: list[GripperTrial]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[GripperTrial]] = defaultdict(list)
    for record in records:
        grouped[(record.variant.value, record.orientation.value)].append(record)

    cells: dict[str, Any] = {}
    for (variant, orientation), trials in sorted(grouped.items()):
        cycle_values = [trial.cycle_ms for trial in trials]
        cells[f"{variant}/{orientation}"] = {
            "grasp": rate_summary(trial.grasp_success for trial in trials),
            "transfer": rate_summary(trial.transfer_success for trial in trials),
            "drop": rate_summary(trial.dropped for trial in trials),
            "cycle_ms": {
                "n": len(cycle_values),
                "median": median(cycle_values),
                "p95": percentile(cycle_values, 0.95),
            },
        }
    return {"schema_version": "1.0", "trial_count": len(records), "cells": cells}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize the BeanSight gripper mechanics DOE.")
    parser.add_argument("trials", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/gripper_doe_summary.json"))
    args = parser.parse_args(argv)
    summary = summarize_gripper_trials(load_gripper_trials(args.trials))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
