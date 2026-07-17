from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

IMMUTABLE_REVISION = re.compile(r"[0-9a-f]{40}")
IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
EXPECTED_CAMERAS = ["observation.images.top", "observation.images.wrist"]
EXPECTED_BEANSIGHT_LEROBOT_REVISION = "30da8e687a6dfc617fcd94afc367ac7071c376ce"
REQUIRED_INFRASTRUCTURE_CHECKS = {
    "nvidia_smi",
    "driver_ram_disk_vram",
    "isaac_compatibility_checker",
    "headless_boot",
    "render_one_rgb_depth_observation",
    "ten_minute_rollout",
    "terminate_and_relaunch_isaac_application",
    "second_clean_application_boot",
    "preserve_logs_and_screenshot",
    "destroy_instance",
}
REQUIRED_EVIDENCE_FILES = {
    "vast_offer_quote.json",
    "host_specification.json",
    "nvidia_smi.txt",
    "isaac_compatibility.txt",
    "version_and_digest_manifest.json",
    "rgb_depth_render.png",
    "ten_minute_rollout.log",
    "first_boot.log",
    "second_boot.log",
    "gpu_hours_and_cost.json",
    "destruction_confirmation.json",
}


def _nested_values(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        return [nested for child in value.values() for nested in _nested_values(child)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [nested for child in value for nested in _nested_values(child)]
    return [value]


def _require_revision(section: Mapping[str, Any], key: str) -> None:
    value = str(section.get(key, ""))
    if not IMMUTABLE_REVISION.fullmatch(value):
        raise ValueError(f"{key} must be a 40-character immutable revision")


def _resolve_evidence_paths(
    evidence: Mapping[str, Any], *, base_dir: Path
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key, value in evidence.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing prerequisite evidence: {key}")
        path = Path(value)
        path = path if path.is_absolute() else base_dir / path
        if not path.is_file():
            raise ValueError(f"prerequisite evidence does not exist: {key}={path}")
        resolved[key] = path
    return resolved


def validate_isaac_spike_config(
    config: Mapping[str, Any], *, base_dir: str | Path = "."
) -> dict[str, object]:
    """Validate the paid optional Isaac experiment before it can be enabled."""

    if not config.get("enabled", False):
        return {
            "experiment_id": config.get("experiment_id"),
            "enabled": False,
            "ready": False,
            "reason": "disabled_planning_template",
        }

    placeholder_values = [
        value
        for value in _nested_values(config)
        if value is None or (isinstance(value, str) and "REPLACE" in value)
    ]
    if placeholder_values:
        raise ValueError("enabled Isaac config contains null or REPLACE placeholders")

    root = Path(base_dir)
    evidence = _resolve_evidence_paths(config["prerequisite_evidence"], base_dir=root)
    comparison = config["comparison"]
    comparison_evidence = _resolve_evidence_paths(
        {
            "immutable_start_manifest_path": comparison["immutable_start_manifest_path"],
            "reset_procedure_path": comparison["reset_procedure_path"],
        },
        base_dir=root,
    )

    artifacts = config["artifact_revisions"]
    for key in (
        "real_cap_dataset_revision",
        "real_cap_policy_revision",
        "modified_so101_asset_revision",
    ):
        _require_revision(artifacts, key)
    if not str(artifacts.get("real_cap_dataset_repo_id", "")).strip():
        raise ValueError("real_cap_dataset_repo_id must be non-empty")

    isolation = config["isolation"]
    for key in (
        "workshop_repo_revision",
        "workshop_lerobot_revision",
        "groot_code_revision",
        "groot_model_revision",
        "beansight_lerobot_revision",
    ):
        _require_revision(isolation, key)
    if not IMAGE_DIGEST.fullmatch(str(isolation.get("container_image_digest", ""))):
        raise ValueError("container_image_digest must be an immutable sha256 digest")
    if (
        isolation.get("isaac_sim") != "5.1.0"
        or isolation.get("isaac_lab") != "2.3.2"
        or isolation.get("groot") != "N1.6"
        or isolation.get("beansight_lerobot_revision")
        != EXPECTED_BEANSIGHT_LEROBOT_REVISION
        or not isolation.get("separate_from_project_lerobot_environment")
    ):
        raise ValueError("Isaac and project LeRobot environments must remain isolated")

    bridge = config["dataset_bridge"]
    for key in ("converter_revision", "simulated_dataset_revision", "real_dataset_revision"):
        _require_revision(bridge, key)
    if bridge["real_dataset_revision"] != artifacts["real_cap_dataset_revision"]:
        raise ValueError("dataset bridge and real-cap dataset revisions differ")
    if (
        bridge.get("output_schema") != "lerobot_v3"
        or bridge.get("action_dim") != 6
        or bridge.get("camera_keys") != EXPECTED_CAMERAS
        or not bridge.get("qa_required")
        or not bridge.get("exchange_only_explicitly_converted_datasets")
    ):
        raise ValueError("dataset bridge does not preserve the six-action/two-camera QA contract")

    qa_report = json.loads(evidence["real_cap_dataset_qa_path"].read_text(encoding="utf-8"))
    if not qa_report.get("passed"):
        raise ValueError("real-cap dataset QA did not pass")
    if qa_report.get("dataset") != artifacts["real_cap_dataset_repo_id"]:
        raise ValueError("real-cap dataset QA repo_id differs from the configured artifact")
    if qa_report.get("revision") != artifacts["real_cap_dataset_revision"]:
        raise ValueError("real-cap dataset QA revision differs from the configured artifact")
    if not re.fullmatch(
        r"[0-9a-f]{64}", str(qa_report.get("dataset_fingerprint_sha256", ""))
    ):
        raise ValueError("real-cap dataset QA lacks a content fingerprint")

    for evidence_key, revision_key in (
        ("converted_sim_dataset_qa_path", "simulated_dataset_revision"),
        ("converted_real_dataset_qa_path", "real_dataset_revision"),
    ):
        converted_qa = json.loads(evidence[evidence_key].read_text(encoding="utf-8"))
        if not converted_qa.get("passed") or converted_qa.get("revision") != bridge[revision_key]:
            raise ValueError(f"{evidence_key} did not pass at the converted dataset revision")

    measurements = json.loads(evidence["hardware_measurements_path"].read_text(encoding="utf-8"))
    missing_measurements = set(config["required_hardware_measurements"]) - set(measurements)
    if missing_measurements:
        raise ValueError(
            f"hardware measurement evidence is incomplete: {sorted(missing_measurements)}"
        )

    local_host = json.loads(
        evidence["local_linux_rtx_inference_host_path"].read_text(encoding="utf-8")
    )
    if not all(
        local_host.get(key)
        for key in ("physically_local", "linux", "nvidia_rtx", "supervised_inference")
    ):
        raise ValueError("local Linux RTX physical-inference host is not qualified")

    offer = json.loads(evidence["vast_offer_quote_path"].read_text(encoding="utf-8"))
    try:
        quoted_at_raw = datetime.fromisoformat(str(offer["quoted_at"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("Vast offer quote requires a timezone-aware quoted_at") from exc
    if quoted_at_raw.tzinfo is None:
        raise ValueError("Vast offer quote requires a timezone-aware quoted_at")
    quoted_at = quoted_at_raw.astimezone(UTC)
    quote_age = (datetime.now(UTC) - quoted_at).total_seconds()
    if quote_age < -60 or quote_age > 1800:
        raise ValueError("Vast offer quote is stale; capture a live quote within 30 minutes")
    if (
        offer.get("gpu") != "RTX 4090"
        or offer.get("gpu_vram_gb", 0) < 24
        or offer.get("host_ram_gb", 0) < 64
        or offer.get("disk_gb", 0) < 100
        or offer.get("reliability", 0) < 0.99
        or not offer.get("verified_host")
        or offer.get("instance_type") != "on_demand"
        or offer.get("download_mbps", 0) < 500
        or offer.get("upload_mbps", 0) < 100
        or offer.get("price_usd_per_hour", 0) <= 0
    ):
        raise ValueError("live Vast offer does not meet the configured host contract")

    host = config["vast_host"]
    if (
        host.get("gpu") != "RTX 4090"
        or host.get("gpu_vram_gb_min", 0) < 24
        or host.get("host_ram_gb_min", 0) < 64
        or host.get("disk_gb_min", 0) < 100
        or host.get("reliability_min", 0) < 0.99
        or not host.get("verified_host_required")
        or host.get("instance_type") != "on_demand"
        or not host.get("rt_cores_required")
        or not {"A100", "H100"}.issubset(set(host.get("excluded_gpus", [])))
        or host.get("mode") != "headless"
        or not host.get("strong_network_bandwidth_required")
        or host.get("standard_docker_in_docker_allowed") is not False
    ):
        raise ValueError("Vast host does not meet the frozen RTX/headless resource contract")
    if host.get("execution_mode") not in {"vast_vm", "prebuilt_flattened_image"}:
        raise ValueError("execution_mode must be vast_vm or prebuilt_flattened_image")

    budget = config["budget"]
    infrastructure = config["infrastructure_gate"]
    custom = config["custom_task_gate"]
    total_budget = budget.get("total_gpu_cost_usd_max")
    infrastructure_hours = infrastructure.get("paid_gpu_hours_max")
    engineering_days = custom.get("engineering_days_max")
    if (
        isinstance(total_budget, bool)
        or not isinstance(total_budget, (int, float))
        or not 0 < total_budget <= 10
    ):
        raise ValueError("total Isaac GPU budget exceeds $10")
    if not budget.get("includes_infrastructure_and_custom_task"):
        raise ValueError("the $10 total must include infrastructure and custom-task work")
    if (
        isinstance(infrastructure_hours, bool)
        or not isinstance(infrastructure_hours, (int, float))
        or not 0 < infrastructure_hours <= 2
    ):
        raise ValueError("Isaac infrastructure gate exceeds two paid GPU-hours")
    if (
        isinstance(engineering_days, bool)
        or not isinstance(engineering_days, (int, float))
        or not 0 < engineering_days <= 7
    ):
        raise ValueError("Isaac custom-task gate exceeds one engineering week")
    if not REQUIRED_INFRASTRUCTURE_CHECKS.issubset(
        set(infrastructure.get("checks", []))
    ):
        raise ValueError("Isaac infrastructure checklist is incomplete")
    if not REQUIRED_EVIDENCE_FILES.issubset(
        set(infrastructure.get("required_evidence_files", []))
    ):
        raise ValueError("Isaac infrastructure evidence bundle is incomplete")
    if (
        custom.get("training_path") != "workshop_native_groot_n1_6_cotraining"
        or not custom.get("training_smoke_required_before_full_run")
        or custom.get("sim_demonstrations") != 75
        or custom.get("real_cotraining_episodes") != 5
        or custom.get("physical_trials_per_policy") != 20
    ):
        raise ValueError("Isaac custom-task counts or native GR00T path changed")
    if not all(
        budget.get(key)
        for key in (
            "live_hourly_quote_required_before_each_launch",
            "one_sentence_justification_required_before_each_launch",
            "costs_md_update_required_after_each_run",
            "destroy_instance_after_each_run",
        )
    ):
        raise ValueError("Isaac cost controls are incomplete")

    output_dir = Path(infrastructure["evidence_output_dir"])
    if output_dir.is_absolute() or not output_dir.parts or output_dir.parts[0] != "outputs":
        raise ValueError("Isaac evidence must use a repository-relative outputs/ directory")
    if infrastructure.get("results_directory_allowed"):
        raise ValueError("simulated Isaac evidence cannot be written to results/")

    if (
        comparison.get("policies")
        != [
            "five_real_only_groot_control",
            "seventy_five_sim_plus_five_real_groot",
            "sixty_to_seventy_five_real_act_baseline",
        ]
        or
        comparison.get("retention_logic") != "all"
        or comparison.get("min_success_delta_vs_five_real_control") != 4
        or comparison.get("max_success_deficit_vs_full_real_act") != 3
        or not comparison.get("counterbalanced_policy_order")
        or not comparison.get("report_wilson_95_ci")
        or comparison.get("failure_histogram_regression_allowed") is not False
    ):
        raise ValueError("Isaac physical comparison does not match the frozen retention gate")

    safety = config["safety"]
    required_true = (
        "physical_inference_local_only",
        "local_linux_rtx_host_required_for_groot_physical_evaluation",
        "controller_unarmed_by_default",
        "explicit_arm_for_each_rollout",
        "supervised_operation_only",
        "switched_cutoff_within_reach",
        "inventory_before_power",
        "motor_ids_one_at_a_time",
    )
    if (
        safety.get("physical_teleoperation_over_public_internet") is not False
        or safety.get("cloud_use") != "headless_simulation_and_training_only"
        or not all(safety.get(key) for key in required_true)
    ):
        raise ValueError("Isaac physical-evaluation safety contract is incomplete")
    if safety.get("leader_supply_v") != 5 or safety.get("follower_supply_v") != 12:
        raise ValueError("leader must be 5 V and follower must be 12 V")

    return {
        "experiment_id": config["experiment_id"],
        "enabled": True,
        "ready": True,
        "evidence_files": len(evidence) + len(comparison_evidence),
        "total_gpu_cost_usd_max": budget["total_gpu_cost_usd_max"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the disabled-by-default Isaac/Vast experiment contract."
    )
    parser.add_argument(
        "config", type=Path, nargs="?", default=Path("configs/isaac_vastai_spike.json")
    )
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    report = validate_isaac_spike_config(config, base_dir=Path.cwd())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
