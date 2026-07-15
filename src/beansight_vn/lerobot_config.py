from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_record_config(
    preflight: dict[str, Any],
    *,
    follower_port: str,
    leader_port: str,
    repo_id: str,
    root: str | None = None,
    episodes: int = 60,
    episode_time_s: int = 12,
) -> dict[str, Any]:
    if not preflight.get("passed"):
        raise ValueError("camera preflight did not pass; refusing to build a recording config")
    cameras = preflight.get("cameras", {})
    if list(sorted(cameras)) != ["top", "wrist"]:
        raise ValueError("preflight must contain exactly the semantic top and wrist cameras")

    camera_config: dict[str, Any] = {}
    for name in ("top", "wrist"):
        report = cameras[name]
        if not report.get("passed"):
            raise ValueError(f"{name} camera did not pass preflight")
        requested = report["requested"]
        camera_config[name] = {
            "type": "opencv",
            "index_or_path": int(report["index"]),
            "fps": int(requested["fps"]),
            "width": int(requested["width"]),
            "height": int(requested["height"]),
            "fourcc": requested["fourcc"],
        }

    return {
        "robot": {
            "type": "so101_follower",
            "port": follower_port,
            "id": "beansight_follower",
            "max_relative_target": 10.0,
            "cameras": camera_config,
            "use_degrees": True,
        },
        "teleop": {
            "type": "so101_leader",
            "port": leader_port,
            "id": "beansight_leader",
            "use_degrees": True,
        },
        "dataset": {
            "repo_id": repo_id,
            "single_task": "Pick the bean from the inspection nest and place it in the reject cup.",
            "root": root,
            "fps": 30,
            "episode_time_s": episode_time_s,
            "reset_time_s": 8,
            "num_episodes": episodes,
            "video": True,
            "push_to_hub": False,
            "private": True,
            "tags": ["so101", "coffee", "beansight-vn"],
            "num_image_writer_processes": 0,
            "num_image_writer_threads_per_camera": 4,
            "video_encoding_batch_size": 1,
            "streaming_encoding": False,
        },
        "display_data": True,
        "display_mode": "rerun",
        "play_sounds": True,
        "resume": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a LeRobot v0.6 recording config from a passing semantic camera report."
    )
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--follower-port", required=True)
    parser.add_argument("--leader-port", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--root")
    parser.add_argument("--episodes", type=int, default=60)
    parser.add_argument("--episode-time", type=int, default=12)
    parser.add_argument("--output", type=Path, default=Path("configs/generated/record_coffee.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    config = build_record_config(
        preflight,
        follower_port=args.follower_port,
        leader_port=args.leader_port,
        repo_id=args.repo_id,
        root=args.root,
        episodes=args.episodes,
        episode_time_s=args.episode_time,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
