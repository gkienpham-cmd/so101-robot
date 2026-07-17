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

## Pinned environment recipe

The historical $0.22 dry run used the released `lerobot==0.6.0` package. For every new paid run,
remove the remaining package-to-source ambiguity: use a plain CUDA image, clone the repository, and
check out the exact project commit rather than using an unverified prebuilt LeRobot image:

```bash
git clone https://github.com/huggingface/lerobot.git /workspace/lerobot
git -C /workspace/lerobot checkout 30da8e687a6dfc617fcd94afc367ac7071c376ce
uv pip install -e '/workspace/lerobot[dataset,training]'
git -C /workspace/lerobot rev-parse HEAD
hf auth login      # write-scoped token
wandb login        # project: so101
```

Save the `rev-parse` output with the generated config and provenance sidecar. It must be
`30da8e687a6dfc617fcd94afc367ac7071c376ce`, matching local QA and the dataset v3.0
`codebase_version`.

## ACT run

Build the smoke and full configs from the pinned-revision QA report; do not hand-edit around the
gate:

```bash
beansight-build-act-config results/dataset_qa_pinned.json \
  --dataset-repo-id YOUR_HF_USER/TIMESTAMPED_DATASET \
  --dataset-revision IMMUTABLE_HF_COMMIT \
  --policy-repo-id YOUR_HF_USER/POLICY \
  --job-name ACT_JOB \
  --train-output-dir outputs/train/ACT_JOB \
  --mode smoke
```

Repeat with `--mode full` only after the smoke loss is healthy. The builder uses the exact complete
training episodes selected by pinned LeRobot's evaluation split. Sizing remains:

```text
steps = ceil(training_frames / batch_size) × 5
```

```bash
lerobot-train --config_path=/ABSOLUTE/PATH/TO/configs/generated/ACT_JOB_smoke.json
```

Preserve the generated `.provenance.json` sidecar and verify its config hash before training.

Watch W&B. **Abort criteria:** NaN/Inf at any point; loss flat after ~1,000 steps → stop paying
and inspect the dataset/config instead. Evaluate the smoke checkpoint before starting the generated
five-epoch full config. Reference telemetry from the dry run: `updt_s:0.077` vs `data_s:0.003` (compute-bound at
batch 8), 3.7/24 GB VRAM, ~100 samples/s, constant lr 1e-5 (ACT default has no schedule).

After training: push the checkpoint (private) to the HF Hub, record the immutable policy revision
in the manifest, and verify it loads on the M1 with
`python src/inference_smoke_test.py USER/POLICY --revision IMMUTABLE_POLICY_COMMIT --device mps`.

## Retrain and SmolVLA constraints

- **One targeted retrain only** after the first frozen eval: add 10–25 demos at the largest
  failure category, retrain once, re-run the identical protocol.
- **SmolVLA is conditional:** only if ACT >40% on the 20 frozen trials AND eval tooling is
  complete. `configs/train_smolvla.json`, `--policy.path=lerobot/smolvla_base`, one RTX 4090,
  batch 4, ~20k steps, keep additional spend near $10 unless a measured result justifies more.
  Another model does not repair calibration, presentation, grasping, or weak demonstrations.
