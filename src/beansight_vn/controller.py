from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .models import Decision, PerceptionResult
from .routing import route_perception


class Classifier(Protocol):
    def classify(
        self, frame: Any, *, frame_id: str | None = None, session_id: str | None = None
    ) -> PerceptionResult: ...


@dataclass(frozen=True, slots=True)
class ControllerOutcome:
    perception: PerceptionResult
    decision: Decision
    motion_executed: bool
    callback_result: Any = None


class BeanSightController:
    """Route a shared observation frame to an optional reject-motion callback.

    The controller never opens a camera. It consumes the same top-camera frame
    already present in the robot observation. Motion is disabled by default.
    """

    def __init__(
        self,
        classifier: Classifier,
        *,
        image_key: str = "observation.images.top",
        reject_threshold: float = 0.80,
        execute_reject: Callable[[Mapping[str, Any]], Any] | None = None,
        armed: bool = False,
    ) -> None:
        if armed and execute_reject is None:
            raise ValueError("armed controller requires an explicit execute_reject callback")
        self.classifier = classifier
        self.image_key = image_key
        self.reject_threshold = reject_threshold
        self.execute_reject = execute_reject
        self.armed = armed

    def handle_observation(
        self,
        observation: Mapping[str, Any],
        *,
        frame_id: str | None = None,
        session_id: str | None = None,
    ) -> ControllerOutcome:
        if self.image_key not in observation:
            raise KeyError(f"missing shared camera observation: {self.image_key}")
        perception = self.classifier.classify(
            observation[self.image_key], frame_id=frame_id, session_id=session_id
        )
        decision = route_perception(perception, self.reject_threshold)
        if decision is not Decision.REJECT or not self.armed:
            return ControllerOutcome(perception, decision, motion_executed=False)
        callback_result = self.execute_reject(observation)  # type: ignore[misc]
        return ControllerOutcome(
            perception, decision, motion_executed=True, callback_result=callback_result
        )
