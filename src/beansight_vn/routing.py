from __future__ import annotations

from .models import Decision, Label, PerceptionResult


def route_perception(result: PerceptionResult, reject_threshold: float = 0.80) -> Decision:
    """Route a perception result using a fail-still safety policy.

    Only a confident visible-reject prediction requests motion. Low-confidence
    predictions and acceptable beans leave the arm still.
    """

    if not 0.0 <= reject_threshold <= 1.0:
        raise ValueError("reject_threshold must be in [0, 1]")
    if result.label is Label.VISIBLE_REJECT and result.confidence >= reject_threshold:
        return Decision.REJECT
    return Decision.NO_MOTION
