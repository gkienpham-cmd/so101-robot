from datetime import date

import pytest

from beansight_vn.material_sorting import (
    BinTarget,
    ManipulationMethod,
    MaterialDecision,
    MaterialSortController,
    MaterialTrialRecord,
    Resin,
    RouteProfile,
    SafetyState,
    SortFailureCode,
    SupervisionState,
    route_material,
)


def profile(**overrides):
    values = {
        "profile_id": "hcmc-lab-2026-07",
        "location": "HCMC lab demonstration",
        "effective_from": "2026-07-01",
        "enabled": True,
        "bins": {
            Resin.PET: BinTarget.PET,
            Resin.HDPE: BinTarget.HDPE,
            Resin.PP: BinTarget.PP,
        },
    }
    values.update(overrides)
    return RouteProfile(**values)


def material(resin=Resin.PET, confidence=0.98, **overrides):
    values = {
        "item_id": "item-001",
        "resin": resin,
        "confidence": confidence,
        "sensor_revision": "db23-fixture-r1",
    }
    if resin is Resin.UNKNOWN:
        values["abstain_reason"] = "below_confidence_threshold"
    values.update(overrides)
    return MaterialDecision(**values)


def test_unknown_low_confidence_and_inactive_profiles_fail_still():
    as_of = date(2026, 7, 18)
    assert not route_material(
        material(Resin.UNKNOWN), profile(), min_confidence=0.95, as_of=as_of
    ).motion_allowed
    assert route_material(
        material(confidence=0.94), profile(), min_confidence=0.95, as_of=as_of
    ).reason == "below_confidence_threshold"
    inactive = profile(effective_until="2026-07-17")
    assert route_material(
        material(), inactive, min_confidence=0.95, as_of=as_of
    ).reason == "route_profile_inactive"


def test_unknown_requires_a_reason_and_never_routes_to_a_bin():
    with pytest.raises(ValueError, match="abstain_reason"):
        MaterialDecision("item", Resin.UNKNOWN, 0.2, "sensor-r1")
    with pytest.raises(ValueError, match="manual_review"):
        RouteProfile(
            "bad",
            "lab",
            "2026-01-01",
            {
                Resin.PET: BinTarget.PET,
                Resin.HDPE: BinTarget.HDPE,
                Resin.PP: BinTarget.PP,
                Resin.UNKNOWN: BinTarget.PET,
            },
        )


def test_route_profile_loader_defaults_to_disabled():
    loaded = RouteProfile.from_dict(
        {
            "profile_id": "example",
            "location": "lab",
            "effective_from": "2026-07-18",
            "bins": {"PET": "pet_bin", "HDPE": "hdpe_bin", "PP": "pp_bin"},
            "activation_note": "ignored documentation field",
        }
    )
    assert not loaded.enabled


def test_route_profile_rejects_a_resin_mapped_to_the_wrong_bin():
    with pytest.raises(ValueError, match="mismatched target bins"):
        profile(
            bins={
                Resin.PET: BinTarget.HDPE,
                Resin.HDPE: BinTarget.PET,
                Resin.PP: BinTarget.PP,
            }
        )


def test_sort_controller_requires_callback_and_fresh_arm_for_each_rollout():
    controller = MaterialSortController(profile(), min_confidence=0.95)
    with pytest.raises(RuntimeError, match="callback"):
        controller.arm()

    calls = []
    controller = MaterialSortController(
        profile(),
        min_confidence=0.95,
        execute_manipulation=lambda request, observation: calls.append((request, observation)),
    )
    observation = {"observation.images.top": object()}
    unarmed = controller.handle_decision(
        material(), observation, object_geometry="bottle-neck-v1", policy_revision="waypoints-r1"
    )
    assert not unarmed.motion_executed
    assert unarmed.request.supervision_state is SupervisionState.SUPERVISED_UNARMED

    controller.arm()
    armed = controller.handle_decision(
        material(), observation, object_geometry="bottle-neck-v1", policy_revision="waypoints-r1"
    )
    assert armed.motion_executed
    assert armed.request.target_bin is BinTarget.PET
    assert armed.request.supervision_state is SupervisionState.SUPERVISED_ARMED
    assert len(calls) == 1
    assert not controller.armed

    second = controller.handle_decision(
        material(), observation, object_geometry="bottle-neck-v1", policy_revision="waypoints-r1"
    )
    assert not second.motion_executed
    assert len(calls) == 1


def test_unknown_never_invokes_callback_even_if_controller_is_armed():
    calls = []
    controller = MaterialSortController(
        profile(),
        min_confidence=0.95,
        execute_manipulation=lambda request, observation: calls.append((request, observation)),
        armed=True,
    )
    outcome = controller.handle_decision(
        material(Resin.UNKNOWN),
        {},
        object_geometry="bottle-neck-v1",
        policy_revision="waypoints-r1",
    )
    assert not outcome.motion_executed
    assert outcome.request is None
    assert calls == []
    assert not controller.armed


def test_route_decision_preserves_dated_location_profile():
    routed = route_material(
        material(), profile(), min_confidence=0.95, as_of=date(2026, 7, 18)
    )
    assert routed.profile_id == "hcmc-lab-2026-07"
    assert len(routed.profile_sha256) == 64
    assert routed.location == "HCMC lab demonstration"
    assert routed.route_as_of == "2026-07-18"


def test_material_trial_safety_state_requires_matching_primary_failure():
    decision = material()
    routed = route_material(
        decision, profile(), min_confidence=0.95, as_of=date(2026, 7, 18)
    )
    common = {
        "trial_id": "trial-1",
        "experiment_id": "experiment-1",
        "session_id": "session-1",
        "item_id": decision.item_id,
        "ground_truth_resin": Resin.PET,
        "material": decision,
        "route": routed,
        "end_to_end_success": False,
        "motion_executed": True,
        "supervision_state": SupervisionState.SUPERVISED_ARMED,
        "object_geometry": "bottle-neck-v1",
        "manipulation_method": ManipulationMethod.ACT,
        "policy_revision": "act-r1",
    }
    with pytest.raises(ValueError, match="primary failure_code"):
        MaterialTrialRecord(**common)
    with pytest.raises(ValueError, match="safety_stop requires"):
        MaterialTrialRecord(**common, failure_code=SortFailureCode.SAFETY_STOP)
    stopped = MaterialTrialRecord(
        **common,
        failure_code=SortFailureCode.SAFETY_STOP,
        safety_state=SafetyState.SAFETY_STOPPED,
    )
    assert stopped.safety_state is SafetyState.SAFETY_STOPPED


def test_callback_error_is_returned_after_one_shot_disarm():
    def fail_after_start(request, observation):
        raise RuntimeError("servo communication lost")

    controller = MaterialSortController(
        profile(), min_confidence=0.95, execute_manipulation=fail_after_start
    )
    controller.arm()
    outcome = controller.handle_decision(
        material(), {}, object_geometry="bottle-neck-v1", policy_revision="act-r1"
    )
    assert outcome.motion_executed
    assert outcome.callback_error == "RuntimeError: servo communication lost"
    assert not controller.armed
