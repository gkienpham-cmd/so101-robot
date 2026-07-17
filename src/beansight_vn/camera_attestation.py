from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def preflight_sha256(preflight: dict[str, Any]) -> str:
    canonical = json.dumps(preflight, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def build_camera_attestation(preflight: dict[str, Any], *, reviewer: str) -> dict[str, Any]:
    if not preflight.get("passed"):
        raise ValueError("cannot attest a failed camera preflight")
    if not reviewer.strip():
        raise ValueError("reviewer must be non-empty")
    return {
        "schema_version": "1.0",
        "preflight_session_id": preflight.get("session_id"),
        "preflight_sha256": preflight_sha256(preflight),
        "reviewer": reviewer,
        "sample_images_reviewed": True,
        "top_view_confirmed_c920": True,
        "wrist_view_confirmed_c270": True,
        "attested_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record human review of the current C920 top and C270 wrist sample images."
    )
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--confirm-sample-images-reviewed", action="store_true")
    parser.add_argument("--confirm-top-is-c920", action="store_true")
    parser.add_argument("--confirm-wrist-is-c270", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not all(
        (
            args.confirm_sample_images_reviewed,
            args.confirm_top_is_c920,
            args.confirm_wrist_is_c270,
        )
    ):
        parser.error("all three visual confirmation flags are required")
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    attestation = build_camera_attestation(preflight, reviewer=args.reviewer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
