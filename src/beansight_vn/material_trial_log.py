from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from pathlib import Path

from .material_metrics import summarize_material_trials
from .material_sorting import MaterialTrialRecord


def append_material_trial(path: str | Path, record: MaterialTrialRecord) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and any(
        existing.trial_id == record.trial_id for existing in load_material_trials(target)
    ):
        raise ValueError(f"duplicate material trial_id: {record.trial_id}")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_material_trials(path: str | Path) -> list[MaterialTrialRecord]:
    records: list[MaterialTrialRecord] = []
    trial_ids: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = MaterialTrialRecord.from_dict(json.loads(line))
                if record.trial_id in trial_ids:
                    raise ValueError(f"duplicate material trial_id: {record.trial_id}")
                trial_ids.add(record.trial_id)
                records.append(record)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid material trial at line {line_number}: {exc}") from exc
    return records


def write_material_summary(
    path: str | Path, records: Iterable[MaterialTrialRecord]
) -> dict[str, object]:
    summary = summarize_material_trials(list(records))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize material-sort trial JSONL.")
    parser.add_argument("trials", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/material-summary.json"))
    args = parser.parse_args(argv)
    summary = write_material_summary(args.output, load_material_trials(args.trials))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
