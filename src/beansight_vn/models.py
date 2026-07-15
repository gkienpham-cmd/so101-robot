from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class Label(StrEnum):
    ACCEPTABLE = "acceptable"
    VISIBLE_REJECT = "visible_reject"


class Decision(StrEnum):
    NO_MOTION = "no_motion"
    REJECT = "reject"


class FailureCode(StrEnum):
    NONE = "none"
    PERCEPTION_FALSE_ACCEPT = "perception_false_accept"
    PERCEPTION_FALSE_REJECT = "perception_false_reject"
    LOCALIZATION_TRIGGER_ERROR = "localization_trigger_error"
    APPROACH_ERROR = "approach_error"
    GRASP_MISS = "grasp_miss"
    DROP = "drop"
    PLACEMENT_MISS = "placement_miss"
    HUMAN_INTERVENTION = "human_intervention"
    SAFETY_STOP = "safety_stop"
    OTHER = "other"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class PerceptionResult:
    label: Label
    confidence: float
    defect_type: str | None = None
    roi: tuple[int, int, int, int] | None = None
    frame_id: str | None = None
    session_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", Label(self.label))
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if self.roi is not None:
            if len(self.roi) != 4 or any(value < 0 for value in self.roi):
                raise ValueError("roi must be a non-negative (x, y, width, height) tuple")
            if self.roi[2] == 0 or self.roi[3] == 0:
                raise ValueError("roi width and height must be non-zero")


@dataclass(slots=True)
class TrialRecord:
    trial_id: str
    experiment_id: str
    session_id: str
    bean_id: str
    bean_lot: str
    ground_truth_label: Label
    predicted_label: Label
    confidence: float
    decision: Decision
    end_to_end_success: bool
    failure_code: FailureCode = FailureCode.NONE
    ground_truth_defect_type: str | None = None
    predicted_defect_type: str | None = None
    roi: tuple[int, int, int, int] | None = None
    frame_id: str | None = None
    pick_success: bool | None = None
    place_success: bool | None = None
    intervention: bool = False
    perception_ms: float | None = None
    policy_ms: float | None = None
    cycle_ms: float | None = None
    position: str | None = None
    lighting_condition: str = "nominal"
    video_path: str | None = None
    notes: str | None = None
    git_sha: str | None = None
    lerobot_revision: str | None = None
    dataset_revision: str | None = None
    policy_revision: str | None = None
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.ground_truth_label = Label(self.ground_truth_label)
        self.predicted_label = Label(self.predicted_label)
        self.decision = Decision(self.decision)
        self.failure_code = FailureCode(self.failure_code)
        if self.roi is not None:
            self.roi = tuple(self.roi)
            if len(self.roi) != 4 or any(value < 0 for value in self.roi):
                raise ValueError("roi must be a non-negative (x, y, width, height) tuple")
            if self.roi[2] == 0 or self.roi[3] == 0:
                raise ValueError("roi width and height must be non-zero")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        for name in ("perception_ms", "policy_ms", "cycle_ms"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.end_to_end_success and self.failure_code is not FailureCode.NONE:
            raise ValueError("a successful trial cannot have a failure_code")
        if self.predicted_label is Label.ACCEPTABLE and self.decision is Decision.REJECT:
            raise ValueError("an acceptable prediction cannot request reject motion")
        if self.decision is Decision.NO_MOTION and (
            self.pick_success is not None or self.place_success is not None
        ):
            raise ValueError("no-motion trials cannot report pick/place outcomes")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TrialRecord:
        return cls(**payload)


@dataclass(slots=True)
class ExperimentManifest:
    experiment_id: str
    git_sha: str
    lerobot_revision: str
    protocol_id: str = "beansight-v1-frozen"
    dataset_revision: str | None = None
    policy_revision: str | None = None
    config_paths: dict[str, str] = field(default_factory=dict)
    calibration_ids: dict[str, str] = field(default_factory=dict)
    cameras: dict[str, dict[str, Any]] = field(default_factory=dict)
    seed: int = 1000
    hardware: dict[str, str] = field(default_factory=dict)
    gpu: str | None = None
    wandb_run: str | None = None
    hf_artifacts: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
