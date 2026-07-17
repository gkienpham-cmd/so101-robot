from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from .models import utc_now


class Resin(StrEnum):
    PET = "PET"
    HDPE = "HDPE"
    PP = "PP"
    UNKNOWN = "unknown"


class BinTarget(StrEnum):
    PET = "pet_bin"
    HDPE = "hdpe_bin"
    PP = "pp_bin"
    MANUAL_REVIEW = "manual_review"


class EvidenceMethod(StrEnum):
    REFERENCE_SAMPLE = "reference_sample"
    MOLDED_RIC = "molded_ric"
    MANUFACTURER_RECORD = "manufacturer_record"
    DISCRETE_NIR = "discrete_nir"
    UNVERIFIED = "unverified"


class SupervisionState(StrEnum):
    SUPERVISED_UNARMED = "supervised_unarmed"
    SUPERVISED_ARMED = "supervised_armed"


class SafetyState(StrEnum):
    NOMINAL = "nominal"
    SAFETY_STOPPED = "safety_stopped"


class ManipulationMethod(StrEnum):
    NONE = "none"
    SCRIPTED_WAYPOINTS = "scripted_waypoints"
    ACT = "act"


class SortFailureCode(StrEnum):
    NONE = "none"
    SENSOR_INVALID = "sensor_invalid"
    MATERIAL_WRONG_CLASS = "material_wrong_class"
    MATERIAL_FALSE_ACCEPT = "material_false_accept"
    ROUTING_INVALID = "routing_invalid"
    APPROACH_ERROR = "approach_error"
    GRASP_MISS = "grasp_miss"
    JAW_OPENING_LIMIT = "jaw_opening_limit"
    PAYLOAD_LIMIT = "payload_limit"
    FRICTION_SLIP = "friction_slip"
    BOTTLE_DEFORMATION = "bottle_deformation"
    DROP = "drop"
    PLACEMENT_MISS = "placement_miss"
    HUMAN_INTERVENTION = "human_intervention"
    SAFETY_STOP = "safety_stop"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class MaterialDecision:
    item_id: str
    resin: Resin
    confidence: float
    sensor_revision: str
    evidence_method: EvidenceMethod = EvidenceMethod.DISCRETE_NIR
    abstain_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "resin", Resin(self.resin))
        object.__setattr__(self, "evidence_method", EvidenceMethod(self.evidence_method))
        if not self.item_id.strip():
            raise ValueError("item_id must be non-empty")
        if not self.sensor_revision.strip():
            raise ValueError("sensor_revision must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.resin is Resin.UNKNOWN and not self.abstain_reason:
            raise ValueError("unknown resin requires an abstain_reason")
        if self.resin is not Resin.UNKNOWN and self.abstain_reason is not None:
            raise ValueError("a target-resin decision cannot include an abstain_reason")


@dataclass(frozen=True, slots=True)
class RouteProfile:
    profile_id: str
    location: str
    effective_from: str
    bins: Mapping[Resin | str, BinTarget | str]
    effective_until: str | None = None
    enabled: bool = False

    def __post_init__(self) -> None:
        if not self.profile_id.strip() or not self.location.strip():
            raise ValueError("route profile id and location must be non-empty")
        start = date.fromisoformat(self.effective_from)
        end = date.fromisoformat(self.effective_until) if self.effective_until else None
        if end is not None and end < start:
            raise ValueError("effective_until cannot precede effective_from")
        normalized = {Resin(key): BinTarget(value) for key, value in self.bins.items()}
        missing = {Resin.PET, Resin.HDPE, Resin.PP} - set(normalized)
        if missing:
            raise ValueError(f"route profile is missing target resins: {sorted(missing)}")
        expected_bins = {
            Resin.PET: BinTarget.PET,
            Resin.HDPE: BinTarget.HDPE,
            Resin.PP: BinTarget.PP,
        }
        mismatched = {
            resin.value: normalized[resin].value
            for resin, expected in expected_bins.items()
            if normalized[resin] is not expected
        }
        if mismatched:
            raise ValueError(f"route profile has mismatched target bins: {mismatched}")
        if Resin.UNKNOWN in normalized and normalized[Resin.UNKNOWN] is not BinTarget.MANUAL_REVIEW:
            raise ValueError("unknown resin can only route to manual_review")
        object.__setattr__(self, "bins", normalized)

    def is_active(self, as_of: date) -> bool:
        if not self.enabled:
            return False
        start = date.fromisoformat(self.effective_from)
        end = date.fromisoformat(self.effective_until) if self.effective_until else None
        return as_of >= start and (end is None or as_of <= end)

    @property
    def sha256(self) -> str:
        payload = {
            "profile_id": self.profile_id,
            "location": self.location,
            "effective_from": self.effective_from,
            "effective_until": self.effective_until,
            "enabled": self.enabled,
            "bins": {resin.value: target.value for resin, target in self.bins.items()},
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RouteProfile:
        return cls(
            profile_id=str(payload["profile_id"]),
            location=str(payload["location"]),
            effective_from=str(payload["effective_from"]),
            effective_until=(
                str(payload["effective_until"]) if payload.get("effective_until") else None
            ),
            enabled=bool(payload.get("enabled", False)),
            bins=payload["bins"],
        )


@dataclass(frozen=True, slots=True)
class RouteDecision:
    profile_id: str
    profile_sha256: str
    location: str
    route_as_of: str
    resin: Resin
    bin_target: BinTarget
    motion_allowed: bool
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "resin", Resin(self.resin))
        object.__setattr__(self, "bin_target", BinTarget(self.bin_target))
        if not self.profile_id.strip() or not self.location.strip():
            raise ValueError("route profile id and location must be non-empty")
        if len(self.profile_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.profile_sha256
        ):
            raise ValueError("route profile sha256 must be 64 lowercase hex characters")
        date.fromisoformat(self.route_as_of)
        if self.motion_allowed and self.bin_target is BinTarget.MANUAL_REVIEW:
            raise ValueError("manual_review can never allow motion")
        if not self.motion_allowed and self.bin_target is not BinTarget.MANUAL_REVIEW:
            raise ValueError("a blocked route must target manual_review")


@dataclass(frozen=True, slots=True)
class ManipulationRequest:
    item_id: str
    target_bin: BinTarget
    object_geometry: str
    policy_revision: str
    supervision_state: SupervisionState

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_bin", BinTarget(self.target_bin))
        object.__setattr__(self, "supervision_state", SupervisionState(self.supervision_state))
        if self.target_bin is BinTarget.MANUAL_REVIEW:
            raise ValueError("manual_review cannot create a manipulation request")
        for name in ("item_id", "object_geometry", "policy_revision"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class MaterialControllerOutcome:
    material: MaterialDecision
    route: RouteDecision
    request: ManipulationRequest | None
    motion_executed: bool
    callback_result: Any = None
    callback_error: str | None = None


def route_material(
    decision: MaterialDecision,
    profile: RouteProfile,
    *,
    min_confidence: float,
    as_of: date | None = None,
) -> RouteDecision:
    """Convert a material result into a dated, fail-still routing decision."""

    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be in [0, 1]")
    route_date = as_of or date.today()
    blocked_reason: str | None = None
    if not profile.is_active(route_date):
        blocked_reason = "route_profile_inactive"
    elif decision.resin is Resin.UNKNOWN:
        blocked_reason = decision.abstain_reason or "unknown_resin"
    elif decision.confidence < min_confidence:
        blocked_reason = "below_confidence_threshold"
    elif decision.resin not in profile.bins:
        blocked_reason = "resin_not_routable"

    if blocked_reason is not None:
        return RouteDecision(
            profile_id=profile.profile_id,
            profile_sha256=profile.sha256,
            location=profile.location,
            route_as_of=route_date.isoformat(),
            resin=decision.resin,
            bin_target=BinTarget.MANUAL_REVIEW,
            motion_allowed=False,
            reason=blocked_reason,
        )
    return RouteDecision(
        profile_id=profile.profile_id,
        profile_sha256=profile.sha256,
        location=profile.location,
        route_as_of=route_date.isoformat(),
        resin=decision.resin,
        bin_target=profile.bins[decision.resin],
        motion_allowed=True,
        reason="confident_material_route",
    )


class MaterialSortController:
    """Route a material decision to at most one explicitly armed callback.

    This controller does not own a camera, sensor, robot, or policy. Every
    handled decision consumes an existing authorization, including a decision
    that correctly fails still. It disarms before invoking the callback, so
    every physical rollout requires a fresh explicit call to :meth:`arm`.
    """

    def __init__(
        self,
        profile: RouteProfile,
        *,
        min_confidence: float,
        execute_manipulation: Callable[[ManipulationRequest, Mapping[str, Any]], Any] | None = None,
        armed: bool = False,
    ) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        if armed and execute_manipulation is None:
            raise ValueError("armed controller requires an explicit manipulation callback")
        self.profile = profile
        self.min_confidence = min_confidence
        self.execute_manipulation = execute_manipulation
        self.armed = armed

    def arm(self) -> None:
        if self.execute_manipulation is None:
            raise RuntimeError("cannot arm without an explicit manipulation callback")
        self.armed = True

    def disarm(self) -> None:
        self.armed = False

    def handle_decision(
        self,
        material: MaterialDecision,
        observation: Mapping[str, Any],
        *,
        object_geometry: str,
        policy_revision: str,
        as_of: date | None = None,
    ) -> MaterialControllerOutcome:
        route = route_material(
            material, self.profile, min_confidence=self.min_confidence, as_of=as_of
        )
        authorized = self.armed
        if authorized:
            # A single sensor decision consumes a single operator authorization,
            # including decisions that correctly fail still.
            self.armed = False
        if not route.motion_allowed:
            return MaterialControllerOutcome(material, route, None, motion_executed=False)

        state = (
            SupervisionState.SUPERVISED_ARMED
            if authorized
            else SupervisionState.SUPERVISED_UNARMED
        )
        request = ManipulationRequest(
            item_id=material.item_id,
            target_bin=route.bin_target,
            object_geometry=object_geometry,
            policy_revision=policy_revision,
            supervision_state=state,
        )
        if not authorized:
            return MaterialControllerOutcome(material, route, request, motion_executed=False)

        callback = self.execute_manipulation
        if callback is None:  # Defensive; __init__/arm make this unreachable.
            raise RuntimeError("armed controller has no manipulation callback")
        try:
            result = callback(request, observation)
        except Exception as exc:
            return MaterialControllerOutcome(
                material,
                route,
                request,
                motion_executed=True,
                callback_error=f"{type(exc).__name__}: {exc}",
            )
        return MaterialControllerOutcome(
            material, route, request, motion_executed=True, callback_result=result
        )


@dataclass(slots=True)
class MaterialTrialRecord:
    trial_id: str
    experiment_id: str
    session_id: str
    item_id: str
    ground_truth_resin: Resin
    material: MaterialDecision
    route: RouteDecision
    end_to_end_success: bool
    motion_executed: bool
    supervision_state: SupervisionState
    failure_code: SortFailureCode = SortFailureCode.NONE
    safety_state: SafetyState = SafetyState.NOMINAL
    approach_success: bool | None = None
    grasp_success: bool | None = None
    lift_success: bool | None = None
    transport_success: bool | None = None
    place_success: bool | None = None
    intervention: bool = False
    sensor_ms: float | None = None
    classifier_ms: float | None = None
    policy_ms: float | None = None
    cycle_ms: float | None = None
    object_geometry: str | None = None
    manipulation_method: ManipulationMethod = ManipulationMethod.NONE
    policy_revision: str | None = None
    observed_bin: BinTarget | None = None
    notes: str | None = None
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("trial_id", "experiment_id", "session_id", "item_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        self.ground_truth_resin = Resin(self.ground_truth_resin)
        if isinstance(self.material, dict):
            self.material = MaterialDecision(**self.material)
        if isinstance(self.route, dict):
            self.route = RouteDecision(**self.route)
        self.failure_code = SortFailureCode(self.failure_code)
        self.safety_state = SafetyState(self.safety_state)
        self.supervision_state = SupervisionState(self.supervision_state)
        self.manipulation_method = ManipulationMethod(self.manipulation_method)
        if self.observed_bin is not None:
            self.observed_bin = BinTarget(self.observed_bin)
        if self.material.item_id != self.item_id:
            raise ValueError("material decision item_id does not match trial item_id")
        if self.material.resin is not self.route.resin:
            raise ValueError("material and route resin values do not match")
        if self.end_to_end_success and self.failure_code is not SortFailureCode.NONE:
            raise ValueError("a successful trial cannot have a failure_code")
        if not self.end_to_end_success and self.failure_code is SortFailureCode.NONE:
            raise ValueError("a failed trial requires exactly one primary failure_code")
        if self.end_to_end_success and self.intervention:
            raise ValueError("a successful trial cannot include an intervention")
        if self.motion_executed and not self.route.motion_allowed:
            raise ValueError("a blocked route cannot report motion_executed")
        if self.motion_executed and self.supervision_state is not SupervisionState.SUPERVISED_ARMED:
            raise ValueError("motion_executed requires supervised_armed state")
        if self.end_to_end_success and self.route.motion_allowed and not self.motion_executed:
            raise ValueError("a successful routed trial requires motion_executed")
        if self.safety_state is SafetyState.SAFETY_STOPPED:
            if self.end_to_end_success or self.failure_code is not SortFailureCode.SAFETY_STOP:
                raise ValueError("safety_stopped requires a failed trial with safety_stop")
        elif self.failure_code is SortFailureCode.SAFETY_STOP:
            raise ValueError("safety_stop requires safety_state=safety_stopped")
        stages = (
            self.approach_success,
            self.grasp_success,
            self.lift_success,
            self.transport_success,
            self.place_success,
        )
        if not self.route.motion_allowed and any(value is not None for value in stages):
            raise ValueError("no-motion trials cannot report manipulation-stage outcomes")
        if self.end_to_end_success and self.route.motion_allowed and not all(stages):
            raise ValueError("a successful motion trial requires all manipulation stages to pass")
        if self.motion_executed:
            if self.manipulation_method is ManipulationMethod.NONE:
                raise ValueError("motion_executed requires a manipulation_method")
            if not self.object_geometry or not self.policy_revision:
                raise ValueError("motion_executed requires object_geometry and policy_revision")
        elif self.manipulation_method is not ManipulationMethod.NONE:
            raise ValueError("a no-motion trial must use manipulation_method=none")
        if (
            self.end_to_end_success
            and self.route.motion_allowed
            and self.observed_bin is not self.route.bin_target
        ):
            raise ValueError("successful placement must match the routed target bin")
        if (
            self.failure_code is SortFailureCode.APPROACH_ERROR
            and self.approach_success is not False
        ):
            raise ValueError("approach_error requires approach_success=false")
        if self.failure_code is SortFailureCode.GRASP_MISS and self.grasp_success is not False:
            raise ValueError("grasp_miss requires grasp_success=false")
        if self.failure_code is SortFailureCode.DROP and not any(
            value is False
            for value in (self.lift_success, self.transport_success, self.place_success)
        ):
            raise ValueError("drop requires a failed lift, transport, or place stage")
        if self.failure_code is SortFailureCode.PLACEMENT_MISS and self.place_success is not False:
            raise ValueError("placement_miss requires place_success=false")
        if self.failure_code is SortFailureCode.HUMAN_INTERVENTION and not self.intervention:
            raise ValueError("human_intervention requires intervention=true")
        if self.failure_code is SortFailureCode.MATERIAL_FALSE_ACCEPT and not (
            self.ground_truth_resin is Resin.UNKNOWN
            and self.material.resin is not Resin.UNKNOWN
        ):
            raise ValueError("material_false_accept requires unknown truth accepted as a target")
        if self.failure_code is SortFailureCode.MATERIAL_WRONG_CLASS and (
            self.material.resin is self.ground_truth_resin
            or self.ground_truth_resin is Resin.UNKNOWN
        ):
            raise ValueError("material_wrong_class requires an incorrect non-unknown truth label")
        if self.failure_code is SortFailureCode.SENSOR_INVALID and not (
            self.material.resin is Resin.UNKNOWN
            and not self.route.motion_allowed
            and not self.motion_executed
        ):
            raise ValueError("sensor_invalid requires an unknown, blocked, no-motion decision")
        if self.failure_code is SortFailureCode.ROUTING_INVALID and (
            self.route.motion_allowed or self.motion_executed
        ):
            raise ValueError("routing_invalid requires a blocked, no-motion route")
        if (
            self.failure_code is SortFailureCode.JAW_OPENING_LIMIT
            and self.grasp_success is not False
        ):
            raise ValueError("jaw_opening_limit requires grasp_success=false")
        if self.failure_code is SortFailureCode.PAYLOAD_LIMIT and self.lift_success is not False:
            raise ValueError("payload_limit requires lift_success=false")
        if self.failure_code is SortFailureCode.FRICTION_SLIP and not any(
            value is False
            for value in (self.grasp_success, self.lift_success, self.transport_success)
        ):
            raise ValueError("friction_slip requires a failed grasp, lift, or transport stage")
        if self.failure_code is SortFailureCode.BOTTLE_DEFORMATION and (
            not any(value is False for value in stages) or not self.notes
        ):
            raise ValueError("bottle_deformation requires a failed stage and a note")
        if self.failure_code is SortFailureCode.OTHER and not self.notes:
            raise ValueError("other failure requires a note")
        for name in ("sensor_ms", "classifier_ms", "policy_ms", "cycle_ms"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> MaterialTrialRecord:
        return cls(**payload)
