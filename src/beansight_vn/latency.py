from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter_ns

from .metrics import percentile


@dataclass(slots=True)
class LatencyRecorder:
    samples_ms: dict[str, list[float]] = field(default_factory=dict)

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        start = perf_counter_ns()
        try:
            yield
        finally:
            elapsed_ms = (perf_counter_ns() - start) / 1_000_000
            self.samples_ms.setdefault(stage, []).append(elapsed_ms)

    def summary(self) -> dict[str, dict[str, float | int | None]]:
        return {
            stage: {
                "n": len(values),
                "median_ms": percentile(values, 0.5),
                "p95_ms": percentile(values, 0.95),
                "max_ms": max(values) if values else None,
            }
            for stage, values in sorted(self.samples_ms.items())
        }
