from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

IMMUTABLE_REVISION = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
EXPECTED_LEROBOT_VERSION = "0.6.0"
EXPECTED_LEROBOT_REVISION = "30da8e687a6dfc617fcd94afc367ac7071c376ce"
EXPECTED_RECORDING_PATCH_SHA256 = (
    "8480712f0b3485968557e0a648f47a7cd54f0edebba8fd9981c5f88301bdb01f"
)


def five_epoch_steps(training_frames: int, *, batch_size: int = 8, epochs: int = 5) -> int:
    if training_frames < 1 or batch_size < 1 or epochs < 1:
        raise ValueError("training_frames, batch_size, and epochs must be positive")
    return math.ceil(training_frames / batch_size) * epochs


def validate_paid_run_gate(
    qa_report: dict[str, Any],
    dataset_revision: str,
    *,
    dataset_repo_id: str | None = None,
) -> int:
    if not qa_report.get("passed"):
        raise ValueError("dataset QA did not pass; refusing to build a paid-run config")
    if qa_report.get("errors"):
        raise ValueError("dataset QA report contains errors")
    warnings = qa_report.get("warnings", [])
    if any("sampled" in str(warning).lower() for warning in warnings):
        raise ValueError("sampled dataset QA cannot authorize a paid run")
    if not IMMUTABLE_REVISION.fullmatch(dataset_revision):
        raise ValueError("dataset revision must be a 40-character immutable commit hash")
    if qa_report.get("revision") != dataset_revision:
        raise ValueError("dataset QA revision does not match the immutable training revision")
    if dataset_repo_id is not None and qa_report.get("dataset") != dataset_repo_id:
        raise ValueError("dataset QA repo_id does not match the training dataset repo_id")
    if not SHA256.fullmatch(str(qa_report.get("dataset_fingerprint_sha256", ""))):
        raise ValueError("dataset QA report lacks a complete content fingerprint")
    if qa_report.get("lerobot_version") != EXPECTED_LEROBOT_VERSION:
        raise ValueError("dataset QA did not run with the pinned LeRobot version")
    if qa_report.get("lerobot_revision") != EXPECTED_LEROBOT_REVISION:
        raise ValueError("dataset QA did not run at the pinned LeRobot revision")
    if qa_report.get("recording_patch_sha256") != EXPECTED_RECORDING_PATCH_SHA256:
        raise ValueError("dataset QA report has the wrong recording-patch provenance")
    frames = int(qa_report.get("frames_checked", 0))
    if frames < 1:
        raise ValueError("dataset QA report contains no checked frames")
    episode_lengths = qa_report.get("episode_lengths", {})
    if episode_lengths and sum(int(value) for value in episode_lengths.values()) != frames:
        raise ValueError("QA frame count does not match the complete episode lengths")
    return frames


def training_frames_from_episode_split(
    qa_report: dict[str, Any], *, eval_split: float
) -> tuple[int, list[int], list[int]]:
    episode_lengths = qa_report.get("episode_lengths", {})
    episode_tasks = qa_report.get("episode_tasks", {})
    if not episode_lengths or set(episode_lengths) != set(episode_tasks):
        raise ValueError("QA must record one task index for every complete episode")
    try:
        lengths = {int(key): int(value) for key, value in episode_lengths.items()}
        tasks = {int(key): int(value) for key, value in episode_tasks.items()}
    except (TypeError, ValueError) as exc:
        raise ValueError("QA episode lengths/tasks must use integer identifiers") from exc
    by_task: dict[int, list[int]] = {}
    for episode, task in tasks.items():
        by_task.setdefault(task, []).append(episode)
    train_episodes: list[int] = []
    eval_episodes: list[int] = []
    for episodes in by_task.values():
        ordered = sorted(episodes)
        eval_count = math.ceil(len(ordered) * eval_split) if eval_split else 0
        if eval_count >= len(ordered):
            raise ValueError("eval_split leaves no training episodes for a task")
        if eval_count:
            train_episodes.extend(ordered[:-eval_count])
            eval_episodes.extend(ordered[-eval_count:])
        else:
            train_episodes.extend(ordered)
    train_episodes.sort()
    eval_episodes.sort()
    return sum(lengths[episode] for episode in train_episodes), train_episodes, eval_episodes


def build_act_training_config(
    template: dict[str, Any],
    qa_report: dict[str, Any],
    *,
    dataset_repo_id: str,
    dataset_revision: str,
    policy_repo_id: str,
    job_name: str,
    output_dir: str,
    mode: str,
    epochs: int = 5,
) -> dict[str, Any]:
    for name, value in (
        ("dataset_repo_id", dataset_repo_id),
        ("policy_repo_id", policy_repo_id),
        ("job_name", job_name),
        ("output_dir", output_dir),
    ):
        if not value.strip():
            raise ValueError(f"{name} must be non-empty")
    if epochs < 1:
        raise ValueError("epochs must be positive")
    frames = validate_paid_run_gate(
        qa_report, dataset_revision, dataset_repo_id=dataset_repo_id
    )
    if mode not in {"smoke", "full"}:
        raise ValueError("mode must be smoke or full")
    config = copy.deepcopy(template)
    batch_size = int(config["batch_size"])
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    eval_split = float(config["dataset"].get("eval_split", 0.0))
    if not 0.0 <= eval_split < 1.0:
        raise ValueError("dataset eval_split must be in [0, 1)")
    training_frames, train_episodes, eval_episodes = training_frames_from_episode_split(
        qa_report, eval_split=eval_split
    )
    config["dataset"]["repo_id"] = dataset_repo_id
    config["dataset"]["revision"] = dataset_revision
    config["policy"]["repo_id"] = policy_repo_id
    config["output_dir"] = output_dir
    config["job_name"] = job_name
    config["steps"] = (
        5000
        if mode == "smoke"
        else five_epoch_steps(training_frames, batch_size=batch_size, epochs=epochs)
    )
    qa_digest = hashlib.sha256(
        json.dumps(qa_report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    config["wandb"]["notes"] = (
        f"{mode} run; {frames} QA-passed frames, {training_frames} exact training frames "
        f"from episodes {train_episodes}; eval episodes {eval_episodes}; immutable dataset "
        f"{dataset_revision}; QA sha256 {qa_digest}."
    )
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an ACT config only after complete dataset QA and revision pinning."
    )
    parser.add_argument("qa_report", type=Path)
    parser.add_argument("--template", type=Path, default=Path("configs/train_act.json"))
    parser.add_argument("--dataset-repo-id", required=True)
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("--policy-repo-id", required=True)
    parser.add_argument("--job-name", required=True)
    parser.add_argument("--train-output-dir", required=True)
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    qa_report = json.loads(args.qa_report.read_text(encoding="utf-8"))
    template = json.loads(args.template.read_text(encoding="utf-8"))
    config = build_act_training_config(
        template,
        qa_report,
        dataset_repo_id=args.dataset_repo_id,
        dataset_revision=args.dataset_revision,
        policy_repo_id=args.policy_repo_id,
        job_name=args.job_name,
        output_dir=args.train_output_dir,
        mode=args.mode,
        epochs=args.epochs,
    )
    output = args.output or Path(f"configs/generated/{args.job_name}_{args.mode}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    config_text = json.dumps(config, indent=2, sort_keys=True) + "\n"
    output.write_text(config_text, encoding="utf-8")
    provenance = {
        "schema_version": "1.0",
        "dataset_repo_id": args.dataset_repo_id,
        "dataset_revision": args.dataset_revision,
        "dataset_fingerprint_sha256": qa_report["dataset_fingerprint_sha256"],
        "qa_report_sha256": hashlib.sha256(
            json.dumps(qa_report, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "generated_config_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
        "lerobot_version": qa_report["lerobot_version"],
        "lerobot_revision": qa_report["lerobot_revision"],
        "recording_patch_sha256": qa_report["recording_patch_sha256"],
    }
    provenance_path = output.with_suffix(".provenance.json")
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(output)
    print(provenance_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
