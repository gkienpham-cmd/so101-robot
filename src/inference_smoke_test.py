"""Checkpoint -> local-inference smoke test (Week 1, Phase F).

Proves the cloud-trained checkpoint loads on the M1 Pro and runs one forward
pass on MPS. This is a plumbing test, NOT the latency profile — proper
roofline-style timing with warmup and repeated trials is the Week-4 task.

Usage (from the lerobot venv):
    python src/inference_smoke_test.py gkienpham/act_dryrun --revision 40_HEX_COMMIT
"""

import argparse
import re
import sys

import torch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", help="HF Hub repo of the trained policy, e.g. user/act_dryrun")
    parser.add_argument(
        "--revision",
        required=True,
        help="Immutable 40-character Hugging Face policy commit",
    )
    parser.add_argument("--device", default=None, help="mps | cpu (default: mps if available)")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("--revision must be a 40-character lowercase hexadecimal commit")

    from lerobot.policies.act.modeling_act import ACTPolicy

    device = args.device or ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading {args.repo_id}@{args.revision} on {device}...")
    policy = ACTPolicy.from_pretrained(args.repo_id, revision=args.revision)
    policy.to(device)
    policy.eval()

    n_params = sum(p.numel() for p in policy.parameters())
    print(f"Loaded. Params: {n_params / 1e6:.1f}M")

    # One dummy forward pass shaped like the training data
    # (svla_so101_pickplace: 6-dim state, two 480x640 cameras).
    cfg = policy.config
    batch = {}
    for key, feat in cfg.input_features.items():
        shape = tuple(feat.shape)
        if "image" in key:
            batch[key] = torch.rand(1, *shape, device=device)
        else:
            batch[key] = torch.zeros(1, *shape, device=device)
    with torch.no_grad():
        action = policy.select_action(batch)
    print(f"Forward pass OK. Action shape: {tuple(action.shape)}, device: {action.device}")
    print("Checkpoint -> local-inference path proven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
