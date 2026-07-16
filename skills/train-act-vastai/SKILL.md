---
name: train-act-vastai
description: Cost-disciplined cloud training on vast.ai for BeanSight VN — justify the run, validate at 5k steps, train ACT on the pinned LeRobot v0.6.0, log every dollar in COSTS.md, destroy the instance. Use for any paid GPU run (ACT bring-up, coffee ACT, the one retrain, optional SmolVLA).
---

# ACT training on vast.ai (cost-disciplined)

Full authority: `docs/runbook.md` §8, §10; spend rules in `COSTS.md`. Training NEVER runs on the
M1 Pro — the Mac is for teleop, recording, calibration, and inference only.

## The spending ritual (every run, no exceptions)

1. **Justify the run in one sentence before launching.** What question does it answer that a
   cheaper run cannot?
2. **Gate first:** `beansight-dataset-qa` must have passed on the immutable HF revision being
   trained on (see the dataset-qa-and-publish skill).
3. **Validate small before training big:** a 5k-step run answers "does loss move" for ~$0.22
   (measured: RTX 4090 @ ~$0.31/hr, ~40 min incl. setup).
4. **Log actual cost in `COSTS.md`** (date, GPU, GPU-hrs, $, cumulative, justification) as soon as
   the run ends.
5. **DESTROY (not pause) the vast.ai instance** when done.

Budget state at handoff: $0.22 spent, balance $8.78, projected total $9–14. Top up ~$10 before the
coffee-ACT week.

## Proven environment recipe (from the successful dry run)

Plain CUDA base image + pinned install — NOT an unverified prebuilt LeRobot image:

```bash
uv pip install 'lerobot[dataset,training]==0.6.0'
hf auth login      # write-scoped token
wandb login        # project: so101
```

This guarantees train-side compatibility with the local pinned checkout
(commit `30da8e687a6dfc617fcd94afc367ac7071c376ce`) and the dataset v3.0 `codebase_version`.

## ACT run

Edit `configs/train_act.json`: dataset repo ID + **immutable revision**, policy repo ID, output
dir, and steps. Sizing for ~5 data epochs at batch 8:

```text
steps = ceil(training_frames / batch_size) × 5
```

```bash
lerobot-train --config_path=/ABSOLUTE/PATH/TO/configs/train_act.json
```

Watch W&B. **Abort criteria:** NaN/Inf at any point; loss flat after ~1,000 steps → stop paying
and inspect the dataset/config instead. Evaluate a short checkpoint before extending toward ten
epochs. Reference telemetry from the dry run: `updt_s:0.077` vs `data_s:0.003` (compute-bound at
batch 8), 3.7/24 GB VRAM, ~100 samples/s, constant lr 1e-5 (ACT default has no schedule).

After training: push the checkpoint (private) to the HF Hub, record the immutable policy revision
in the manifest, verify it loads on the M1 (`src/inference_smoke_test.py`, `--policy.device=mps`).

## Retrain and SmolVLA constraints

- **One targeted retrain only** after the first frozen eval: add 10–25 demos at the largest
  failure category, retrain once, re-run the identical protocol.
- **SmolVLA is conditional:** only if ACT >40% on the 20 frozen trials AND eval tooling is
  complete. `configs/train_smolvla.json`, `--policy.path=lerobot/smolvla_base`, one RTX 4090,
  batch 4, ~20k steps, keep additional spend near $10 unless a measured result justifies more.
  Another model does not repair calibration, presentation, grasping, or weak demonstrations.
