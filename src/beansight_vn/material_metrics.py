from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from statistics import median

from .material_sorting import (
    ManipulationMethod,
    MaterialTrialRecord,
    Resin,
    SafetyState,
    SortFailureCode,
)
from .metrics import percentile, rate_summary

POSE_VARIATION_FAILURES = {
    SortFailureCode.APPROACH_ERROR,
    SortFailureCode.GRASP_MISS,
}
MECHANICAL_FEASIBILITY_FAILURES = {
    SortFailureCode.JAW_OPENING_LIMIT,
    SortFailureCode.PAYLOAD_LIMIT,
    SortFailureCode.FRICTION_SLIP,
    SortFailureCode.BOTTLE_DEFORMATION,
}
TRANSPORT_FAILURES = {
    SortFailureCode.DROP,
    SortFailureCode.PLACEMENT_MISS,
}
SAFETY_OR_INTERVENTION_FAILURES = {
    SortFailureCode.HUMAN_INTERVENTION,
    SortFailureCode.SAFETY_STOP,
}
MATERIAL_OR_ROUTE_FAILURES = {
    SortFailureCode.SENSOR_INVALID,
    SortFailureCode.MATERIAL_WRONG_CLASS,
    SortFailureCode.MATERIAL_FALSE_ACCEPT,
    SortFailureCode.ROUTING_INVALID,
}


def summarize_material_trials(records: Sequence[MaterialTrialRecord]) -> dict[str, object]:
    confusion = {actual.value: {predicted.value: 0 for predicted in Resin} for actual in Resin}
    for record in records:
        confusion[record.ground_truth_resin.value][record.material.resin.value] += 1

    target_resins = (Resin.PET, Resin.HDPE, Resin.PP)
    accepted = [record for record in records if record.material.resin is not Resin.UNKNOWN]
    per_class: dict[str, object] = {}
    for resin in Resin:
        actual = [record for record in records if record.ground_truth_resin is resin]
        accepted_actual = [
            record for record in actual if record.material.resin is not Resin.UNKNOWN
        ]
        per_class[resin.value] = {
            "support": len(actual),
            "accepted": rate_summary(
                record.material.resin is not Resin.UNKNOWN for record in actual
            ),
            "correct": rate_summary(record.material.resin is resin for record in actual),
            "accepted_correctness": rate_summary(
                record.material.resin is resin for record in accepted_actual
            ),
        }

    unknown = [record for record in records if record.ground_truth_resin is Resin.UNKNOWN]
    stage_names = (
        "approach_success",
        "grasp_success",
        "lift_success",
        "transport_success",
        "place_success",
    )
    stages = {
        name: rate_summary(
            bool(getattr(record, name))
            for record in records
            if getattr(record, name) is not None
        )
        for name in stage_names
    }
    latency_values = {
        "sensor_ms": [record.sensor_ms for record in records if record.sensor_ms is not None],
        "classifier_ms": [
            record.classifier_ms for record in records if record.classifier_ms is not None
        ],
        "policy_ms": [record.policy_ms for record in records if record.policy_ms is not None],
        "cycle_ms": [record.cycle_ms for record in records if record.cycle_ms is not None],
    }
    latencies = {
        name: {
            "n": len(values),
            "median": median(values) if values else None,
            "p95": percentile(values, 0.95),
        }
        for name, values in latency_values.items()
    }
    failure_counts = Counter(
        record.failure_code.value
        for record in records
        if record.failure_code is not SortFailureCode.NONE
    )
    abstention_reasons = Counter(
        record.material.abstain_reason or "unspecified"
        for record in records
        if record.material.resin is Resin.UNKNOWN
    )
    waypoint_groups: dict[str, list[MaterialTrialRecord]] = {}
    for record in records:
        if record.manipulation_method is not ManipulationMethod.SCRIPTED_WAYPOINTS:
            continue
        geometry = record.object_geometry or "missing_geometry"
        waypoint_groups.setdefault(geometry, []).append(record)
    waypoint_gate = {}
    for geometry, trials in sorted(waypoint_groups.items()):
        successes = sum(record.end_to_end_success for record in trials)
        waypoint_gate[geometry] = {
            "outcome": rate_summary(record.end_to_end_success for record in trials),
            "eligible": len(trials) == 20,
            "passed": successes >= 16 if len(trials) == 20 else None,
            "criterion": "at_least_16_of_exactly_20",
        }
    complete_waypoint_geometries = [
        result for result in waypoint_gate.values() if result["eligible"]
    ]
    waypoint_overall_gate = {
        "representative_geometry_count": len(waypoint_gate),
        "required_geometry_count": 3,
        "all_geometries_have_exactly_20_trials": len(complete_waypoint_geometries)
        == len(waypoint_gate),
        "passed": len(waypoint_gate) >= 3
        and len(complete_waypoint_geometries) == len(waypoint_gate)
        and all(bool(result["passed"]) for result in complete_waypoint_geometries),
    }
    waypoint_failures = [
        record.failure_code
        for trials in waypoint_groups.values()
        for record in trials
        if not record.end_to_end_success
    ]
    failure_groups = {
        "pose_variation": sum(code in POSE_VARIATION_FAILURES for code in waypoint_failures),
        "mechanical_feasibility": sum(
            code in MECHANICAL_FEASIBILITY_FAILURES for code in waypoint_failures
        ),
        "transport_or_place": sum(code in TRANSPORT_FAILURES for code in waypoint_failures),
        "safety_or_intervention": sum(
            code in SAFETY_OR_INTERVENTION_FAILURES for code in waypoint_failures
        ),
        "material_or_routing": sum(
            code in MATERIAL_OR_ROUTE_FAILURES for code in waypoint_failures
        ),
        "other": sum(code is SortFailureCode.OTHER for code in waypoint_failures),
    }
    if not (
        len(waypoint_gate) >= 3
        and len(complete_waypoint_geometries) == len(waypoint_gate)
    ):
        bottle_failure_branch = "insufficient_waypoint_evidence"
    elif waypoint_overall_gate["passed"]:
        bottle_failure_branch = "retain_scripted_waypoints"
    else:
        largest = max(failure_groups.values(), default=0)
        leaders = [name for name, count in failure_groups.items() if count == largest]
        if largest == 0 or len(leaders) != 1:
            bottle_failure_branch = "manual_triage_required"
        elif leaders[0] == "pose_variation":
            bottle_failure_branch = "collect_act_for_pose_variation"
        elif leaders[0] == "mechanical_feasibility":
            bottle_failure_branch = "fix_fixture_fingertip_or_grasp"
        else:
            bottle_failure_branch = "manual_triage_required"
    return {
        "schema_version": "1.1",
        "trial_count": len(records),
        "confusion_matrix": confusion,
        "per_class": per_class,
        "accepted_correctness": rate_summary(
            record.material.resin is record.ground_truth_resin for record in accepted
        ),
        "abstention": rate_summary(
            record.material.resin is Resin.UNKNOWN for record in records
        ),
        "unknown_false_accept": rate_summary(
            record.material.resin is not Resin.UNKNOWN for record in unknown
        ),
        "abstention_reasons": dict(sorted(abstention_reasons.items())),
        "target_coverage": rate_summary(
            record.material.resin is not Resin.UNKNOWN
            for record in records
            if record.ground_truth_resin in target_resins
        ),
        "end_to_end": rate_summary(record.end_to_end_success for record in records),
        "intervention": rate_summary(record.intervention for record in records),
        "safety_stop": rate_summary(
            record.safety_state is SafetyState.SAFETY_STOPPED for record in records
        ),
        "blocked_route_no_motion": rate_summary(
            not record.motion_executed for record in records if not record.route.motion_allowed
        ),
        "allowed_route_motion_executed": rate_summary(
            record.motion_executed for record in records if record.route.motion_allowed
        ),
        "stages": stages,
        "latency": latencies,
        "scripted_waypoint_gate_by_geometry": waypoint_gate,
        "scripted_waypoint_overall_gate": waypoint_overall_gate,
        "scripted_waypoint_failure_groups": failure_groups,
        "bottle_failure_branch": bottle_failure_branch,
        "failures": {
            code.value: failure_counts.get(code.value, 0)
            for code in SortFailureCode
            if code is not SortFailureCode.NONE
        },
    }
