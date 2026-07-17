import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from beansight_vn.isaac_spike import validate_isaac_spike_config

ROOT = Path(__file__).parents[1]


def template():
    return json.loads((ROOT / "configs/isaac_vastai_spike.json").read_text(encoding="utf-8"))


def ready_config(tmp_path):
    config = copy.deepcopy(template())
    config["enabled"] = True
    revision = "a" * 40
    artifacts = config["artifact_revisions"]
    artifacts.update(
        {
            "real_cap_dataset_repo_id": "user/caps",
            "real_cap_dataset_revision": revision,
            "real_cap_policy_revision": revision,
            "modified_so101_asset_revision": revision,
        }
    )
    isolation = config["isolation"]
    for key in (
        "workshop_repo_revision",
        "workshop_lerobot_revision",
        "groot_code_revision",
        "groot_model_revision",
    ):
        isolation[key] = revision
    isolation["container_image_digest"] = "sha256:" + "b" * 64
    bridge = config["dataset_bridge"]
    bridge["converter_revision"] = revision
    bridge["simulated_dataset_revision"] = revision
    bridge["real_dataset_revision"] = revision
    config["vast_host"]["execution_mode"] = "vast_vm"

    for key in config["prerequisite_evidence"]:
        path = tmp_path / f"{key}.json"
        if key == "real_cap_dataset_qa_path":
            payload = {
                "passed": True,
                "dataset": "user/caps",
                "revision": revision,
                "dataset_fingerprint_sha256": "f" * 64,
            }
        elif key in {"converted_sim_dataset_qa_path", "converted_real_dataset_qa_path"}:
            payload = {"passed": True, "revision": revision}
        elif key == "hardware_measurements_path":
            payload = {name: {} for name in config["required_hardware_measurements"]}
        elif key == "local_linux_rtx_inference_host_path":
            payload = {
                "physically_local": True,
                "linux": True,
                "nvidia_rtx": True,
                "supervised_inference": True,
            }
        elif key == "vast_offer_quote_path":
            payload = {
                "quoted_at": datetime.now(UTC).isoformat(),
                "gpu": "RTX 4090",
                "gpu_vram_gb": 24,
                "host_ram_gb": 64,
                "disk_gb": 100,
                "reliability": 0.99,
                "verified_host": True,
                "instance_type": "on_demand",
                "download_mbps": 500,
                "upload_mbps": 100,
                "price_usd_per_hour": 0.5,
            }
        else:
            payload = {}
        path.write_text(json.dumps(payload), encoding="utf-8")
        config["prerequisite_evidence"][key] = str(path)
    for key in ("immutable_start_manifest_path", "reset_procedure_path"):
        path = tmp_path / f"{key}.json"
        path.write_text("{}", encoding="utf-8")
        config["comparison"][key] = str(path)
    return config


def test_committed_isaac_config_is_a_disabled_planning_template():
    report = validate_isaac_spike_config(template())
    assert not report["enabled"]
    assert not report["ready"]


def test_enabled_isaac_config_rejects_placeholders():
    config = template()
    config["enabled"] = True
    with pytest.raises(ValueError, match="placeholders"):
        validate_isaac_spike_config(config)


def test_complete_isaac_gate_requires_evidence_and_frozen_limits(tmp_path):
    config = ready_config(tmp_path)
    report = validate_isaac_spike_config(config)
    assert report["ready"]
    assert report["total_gpu_cost_usd_max"] == 10

    config["budget"]["total_gpu_cost_usd_max"] = 11
    with pytest.raises(ValueError, match="exceeds"):
        validate_isaac_spike_config(config)


def test_isaac_gate_rejects_remote_or_incomplete_physical_safety(tmp_path):
    config = ready_config(tmp_path)
    config["safety"]["physical_teleoperation_over_public_internet"] = True
    with pytest.raises(ValueError, match="safety"):
        validate_isaac_spike_config(config)


def test_isaac_gate_enforces_versions_checklist_and_evidence_bundle(tmp_path):
    wrong_version = ready_config(tmp_path)
    wrong_version["isolation"]["isaac_sim"] = "latest"
    with pytest.raises(ValueError, match="environments must remain isolated"):
        validate_isaac_spike_config(wrong_version)

    missing_check = ready_config(tmp_path)
    missing_check["infrastructure_gate"]["checks"].remove("ten_minute_rollout")
    with pytest.raises(ValueError, match="checklist is incomplete"):
        validate_isaac_spike_config(missing_check)

    missing_evidence = ready_config(tmp_path)
    missing_evidence["infrastructure_gate"]["required_evidence_files"].remove(
        "nvidia_smi.txt"
    )
    with pytest.raises(ValueError, match="evidence bundle is incomplete"):
        validate_isaac_spike_config(missing_evidence)
