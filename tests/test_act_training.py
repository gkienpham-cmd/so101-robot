import json

import pytest

from beansight_vn.act_training import (
    EXPECTED_LEROBOT_REVISION,
    EXPECTED_LEROBOT_VERSION,
    EXPECTED_RECORDING_PATCH_SHA256,
    build_act_training_config,
    five_epoch_steps,
    main,
    training_frames_from_episode_split,
    validate_paid_run_gate,
)


def template():
    return {
        "dataset": {"repo_id": "placeholder", "revision": "placeholder", "eval_split": 0.1},
        "policy": {"repo_id": "placeholder"},
        "batch_size": 8,
        "steps": 1,
        "output_dir": "placeholder",
        "job_name": "placeholder",
        "wandb": {"notes": "placeholder"},
    }


def qa_report(**overrides):
    values = {
        "dataset": "user/caps",
        "revision": "a" * 40,
        "passed": True,
        "frames_checked": 100,
        "episode_lengths": {"0": 50, "1": 50},
        "episode_tasks": {"0": 0, "1": 0},
        "dataset_fingerprint_sha256": "f" * 64,
        "lerobot_version": EXPECTED_LEROBOT_VERSION,
        "lerobot_revision": EXPECTED_LEROBOT_REVISION,
        "recording_patch_sha256": EXPECTED_RECORDING_PATCH_SHA256,
        "errors": [],
        "warnings": [],
    }
    values.update(overrides)
    return values


def test_step_count_and_full_config_use_qa_frame_total():
    assert five_epoch_steps(90, batch_size=8, epochs=5) == 60
    revision = "a" * 40
    config = build_act_training_config(
        template(),
        qa_report(),
        dataset_repo_id="user/caps",
        dataset_revision=revision,
        policy_repo_id="user/caps-act",
        job_name="caps-act-v1",
        output_dir="outputs/train/caps-act-v1",
        mode="full",
    )
    assert config["steps"] == 35
    assert config["dataset"]["revision"] == revision
    assert "50 exact training frames" in config["wandb"]["notes"]


def test_smoke_mode_is_fixed_at_five_thousand_steps():
    config = build_act_training_config(
        template(),
        qa_report(revision="b" * 40),
        dataset_repo_id="user/caps",
        dataset_revision="b" * 40,
        policy_repo_id="user/caps-act",
        job_name="caps-act-v1",
        output_dir="outputs/train/caps-act-v1",
        mode="smoke",
    )
    assert config["steps"] == 5000


@pytest.mark.parametrize(
    ("report", "revision", "message"),
    [
        (qa_report(passed=False), "a" * 40, "did not pass"),
        (qa_report(warnings=["sampled 20 of 100 frames"]), "a" * 40, "sampled"),
        (qa_report(), "main", "immutable"),
        (qa_report(frames_checked=99), "a" * 40, "frame count"),
        (qa_report(revision="b" * 40), "a" * 40, "QA revision"),
    ],
)
def test_paid_run_gate_rejects_incomplete_or_mutable_inputs(report, revision, message):
    with pytest.raises(ValueError, match=message):
        validate_paid_run_gate(report, revision)


def test_paid_run_gate_rejects_a_different_dataset_repo():
    with pytest.raises(ValueError, match="repo_id"):
        build_act_training_config(
            template(),
            qa_report(),
            dataset_repo_id="user/not-caps",
            dataset_revision="a" * 40,
            policy_repo_id="user/caps-act",
            job_name="caps-act-v1",
            output_dir="outputs/train/caps-act-v1",
            mode="smoke",
        )


def test_training_split_uses_complete_episodes_not_a_frame_fraction():
    report = qa_report(
        frames_checked=100,
        episode_lengths={"0": 10, "1": 20, "2": 70},
        episode_tasks={"0": 0, "1": 0, "2": 0},
    )
    frames, train_episodes, eval_episodes = training_frames_from_episode_split(
        report, eval_split=0.1
    )
    assert frames == 30
    assert train_episodes == [0, 1]
    assert eval_episodes == [2]


def test_cli_writes_hashed_provenance_sidecar(tmp_path):
    qa_path = tmp_path / "qa.json"
    template_path = tmp_path / "template.json"
    output = tmp_path / "act.json"
    qa_path.write_text(json.dumps(qa_report()), encoding="utf-8")
    template_path.write_text(json.dumps(template()), encoding="utf-8")
    assert (
        main(
            [
                str(qa_path),
                "--template",
                str(template_path),
                "--dataset-repo-id",
                "user/caps",
                "--dataset-revision",
                "a" * 40,
                "--policy-repo-id",
                "user/caps-act",
                "--job-name",
                "caps-act-v1",
                "--train-output-dir",
                "outputs/train/caps-act-v1",
                "--mode",
                "smoke",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    provenance = json.loads(output.with_suffix(".provenance.json").read_text())
    assert len(provenance["generated_config_sha256"]) == 64
