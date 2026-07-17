import json
from pathlib import Path

from beansight_vn.material_sorting import RouteProfile

ROOT = Path(__file__).parents[1]


def load(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_material_sensor_config_freezes_v1_counts_and_fail_policy():
    config = load("configs/material_sensor.json")
    assert config["dataset"]["items_per_class"] == 30
    assert config["dataset"]["exact_items_per_class"] is True
    assert config["dataset"]["scans_per_item"] == 10
    assert config["dataset"]["exact_scans_per_item"] is True
    assert config["dataset"]["sessions_per_item"] == 3
    assert config["dataset"]["parent_sku_groups_per_class_min"] >= 7
    assert config["preprocessing"]["repeats_per_decision"] == 5
    assert config["evaluation"]["outer_folds"] == 5
    assert config["evaluation"]["gates"]["min_accepted_correctness"] == 0.95
    assert config["evaluation"]["threshold_min_target_coverage"] == 2 / 3
    assert config["failure_policy"]["rgb_substitution_allowed"] is False


def test_transfer_order_and_isaac_defaults_are_gated():
    tasks = load("configs/transfer_tasks.json")
    assert tasks["sequence"][0] == "beansight_v1_frozen_complete"
    assert tasks["cap_transfer"]["policy_horizon"].endswith("safe_handoff")
    assert tasks["bottle_sort"]["scripted_baseline_trials_per_geometry"] == 20
    assert tasks["bottle_sort"]["scripted_pass_count"] == 16
    assert tasks["bottle_sort"]["representative_geometry_count_min"] == 3

    isaac = load("configs/isaac_vastai_spike.json")
    assert isaac["enabled"] is False
    assert isaac["infrastructure_gate"]["paid_gpu_hours_max"] == 2
    assert isaac["budget"]["total_gpu_cost_usd_max"] == 10
    assert isaac["vast_host"]["verified_host_required"] is True
    assert isaac["custom_task_gate"]["training_path"].endswith("groot_n1_6_cotraining")
    assert isaac["safety"]["physical_teleoperation_over_public_internet"] is False


def test_committed_route_profile_examples_cannot_allow_motion():
    for name in ("hcmc", "boston"):
        payload = load(f"configs/route_profiles/{name}_material_demo.example.json")
        profile = RouteProfile.from_dict(payload)
        assert profile.enabled is False
