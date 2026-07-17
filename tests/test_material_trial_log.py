import json
from datetime import date

import pytest

from beansight_vn.material_metrics import summarize_material_trials
from beansight_vn.material_sorting import (
    BinTarget,
    ManipulationMethod,
    MaterialDecision,
    MaterialTrialRecord,
    Resin,
    RouteProfile,
    SortFailureCode,
    SupervisionState,
    route_material,
)
from beansight_vn.material_trial_log import (
    append_material_trial,
    load_material_trials,
    write_material_summary,
)


def record(**overrides):
    material = MaterialDecision("item-1", Resin.PET, 0.98, "sensor-r1")
    route = route_material(
        material,
        RouteProfile(
            "profile-r1",
            "lab",
            "2026-01-01",
            {Resin.PET: BinTarget.PET, Resin.HDPE: BinTarget.HDPE, Resin.PP: BinTarget.PP},
            enabled=True,
        ),
        min_confidence=0.95,
        as_of=date(2026, 7, 18),
    )
    values = {
        "trial_id": "trial-1",
        "experiment_id": "experiment-1",
        "session_id": "session-1",
        "item_id": "item-1",
        "ground_truth_resin": Resin.PET,
        "material": material,
        "route": route,
        "end_to_end_success": True,
        "motion_executed": True,
        "supervision_state": SupervisionState.SUPERVISED_ARMED,
        "approach_success": True,
        "grasp_success": True,
        "lift_success": True,
        "transport_success": True,
        "place_success": True,
        "sensor_ms": 4.0,
        "classifier_ms": 0.4,
        "object_geometry": "bottle-neck-v1",
        "manipulation_method": ManipulationMethod.SCRIPTED_WAYPOINTS,
        "policy_revision": "waypoints-r1",
        "observed_bin": BinTarget.PET,
    }
    values.update(overrides)
    return MaterialTrialRecord(**values)


def test_material_trial_round_trip_and_summary(tmp_path):
    path = tmp_path / "material-trials.jsonl"
    original = record()
    append_material_trial(path, original)
    restored = load_material_trials(path)
    assert restored == [original]
    output = tmp_path / "summary.json"
    summary = write_material_summary(output, restored)
    assert summary["accepted_correctness"]["successes"] == 1
    assert summary["accepted_correctness"]["wilson_95"][1] <= 1.0
    assert summary["stages"]["grasp_success"]["successes"] == 1
    assert summary["latency"]["classifier_ms"]["n"] == 1
    assert summary["abstention"]["trials"] == 1
    assert not summary["scripted_waypoint_overall_gate"]["passed"]
    assert set(summary["failures"]) == {
        "sensor_invalid",
        "material_wrong_class",
        "material_false_accept",
        "routing_invalid",
        "approach_error",
        "grasp_miss",
        "jaw_opening_limit",
        "payload_limit",
        "friction_slip",
        "bottle_deformation",
        "drop",
        "placement_miss",
        "human_intervention",
        "safety_stop",
        "other",
    }
    assert json.loads(output.read_text())["trial_count"] == 1


def test_success_cannot_include_failure_code():
    with pytest.raises(ValueError, match="successful"):
        record(failure_code=SortFailureCode.DROP)


def test_failure_requires_a_primary_failure_code():
    with pytest.raises(ValueError, match="primary failure_code"):
        record(end_to_end_success=False, place_success=False)


def test_no_motion_cannot_include_manipulation_stage_outcomes():
    material = MaterialDecision(
        "item-1",
        Resin.UNKNOWN,
        0.4,
        "sensor-r1",
        abstain_reason="out_of_distribution",
    )
    route = route_material(
        material,
        RouteProfile(
            "profile-r1",
            "lab",
            "2026-01-01",
            {Resin.PET: BinTarget.PET, Resin.HDPE: BinTarget.HDPE, Resin.PP: BinTarget.PP},
            enabled=True,
        ),
        min_confidence=0.95,
        as_of=date(2026, 7, 18),
    )
    with pytest.raises(ValueError, match="no-motion"):
        record(
            material=material,
            route=route,
            end_to_end_success=False,
            motion_executed=False,
            supervision_state=SupervisionState.SUPERVISED_UNARMED,
            failure_code=SortFailureCode.MATERIAL_WRONG_CLASS,
            approach_success=None,
            grasp_success=False,
            lift_success=None,
            transport_success=None,
            place_success=None,
            object_geometry=None,
            manipulation_method=ManipulationMethod.NONE,
            policy_revision=None,
            observed_bin=None,
        )


def test_material_trial_ids_cannot_be_appended_twice(tmp_path):
    path = tmp_path / "trials.jsonl"
    append_material_trial(path, record())
    with pytest.raises(ValueError, match="duplicate material trial_id"):
        append_material_trial(path, record())


def waypoint_trials(failure_code):
    trials = []
    for geometry_index in range(3):
        geometry = f"bottle-neck-{geometry_index}"
        for trial_index in range(20):
            overrides = {
                "trial_id": f"{geometry}-{trial_index}",
                "object_geometry": geometry,
            }
            if trial_index >= 15:
                overrides.update(
                    {
                        "end_to_end_success": False,
                        "failure_code": failure_code,
                        "observed_bin": None,
                        "grasp_success": None,
                        "lift_success": None,
                        "transport_success": None,
                        "place_success": None,
                    }
                )
                if failure_code is SortFailureCode.APPROACH_ERROR:
                    overrides["approach_success"] = False
                elif failure_code is SortFailureCode.JAW_OPENING_LIMIT:
                    overrides["grasp_success"] = False
            trials.append(record(**overrides))
    return trials


def test_waypoint_summary_computes_pose_and_mechanical_branches():
    pose_summary = summarize_material_trials(
        waypoint_trials(SortFailureCode.APPROACH_ERROR)
    )
    assert pose_summary["scripted_waypoint_failure_groups"]["pose_variation"] == 15
    assert pose_summary["bottle_failure_branch"] == "collect_act_for_pose_variation"

    mechanical_summary = summarize_material_trials(
        waypoint_trials(SortFailureCode.JAW_OPENING_LIMIT)
    )
    assert mechanical_summary["scripted_waypoint_failure_groups"][
        "mechanical_feasibility"
    ] == 15
    assert (
        mechanical_summary["bottle_failure_branch"]
        == "fix_fixture_fingertip_or_grasp"
    )
