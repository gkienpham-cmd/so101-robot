from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from pathlib import Path

from .metrics import summarize_trials
from .models import TrialRecord


def append_trial(path: str | Path, record: TrialRecord) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_trials(path: str | Path) -> list[TrialRecord]:
    records: list[TrialRecord] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(TrialRecord.from_dict(json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid trial at line {line_number}: {exc}") from exc
    return records


def write_summary(path: str | Path, records: Iterable[TrialRecord]) -> dict[str, object]:
    summary = summarize_trials(list(records))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize BeanSight trial JSONL.")
    parser.add_argument("trials", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/summary.json"))
    args = parser.parse_args()
    summary = write_summary(args.output, load_trials(args.trials))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
