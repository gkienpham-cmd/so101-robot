# vast.ai ACT Dry-Run Runbook (Week 1, Day 5) — budget ~$2–3

**Purpose:** prove the cloud pipeline (Hub dataset → GPU training → wandb → checkpoint on Hub) BEFORE our own data exists. We are buying *information*, not a model — abort as soon as loss is clearly decreasing and the checkpoint push works.

**Version pin:** local install is LeRobot **v0.6.0**. The cloud side MUST run v0.6.0 too, or dataset/checkpoint formats can mismatch. Safest path: plain CUDA PyTorch image + `pip install 'lerobot[act]==0.6.0'`-style install (exact command below). Only use a prebuilt LeRobot image (e.g. `ioaitech/lerobot-gpu`) if its tag is v0.6.0.

## 1. Rent the instance (vast.ai web console)

Filter:
- GPU: **RTX 5090** (or 4090 — fine for a 5k-step ACT run and cheaper)
- Price: **≤ $0.70/hr** (5090 spot often ~$0.60; 4090 ~$0.31)
- RAM ≥ 32 GB, Disk ≥ 60 GB, Reliability ≥ 99%, good inet_down
- Image: `pytorch/pytorch:2.7.0-cuda12.8-cudnn9-devel` (or the console's default recent PyTorch CUDA template). RTX 5090 is Blackwell (sm_120) — needs CUDA ≥ 12.8 builds; if torch errors with "no kernel image", pick a newer image or fall back to a 4090.

Cost math: 5k steps ACT ≈ 20–40 min + setup ≈ 1–1.5 hr total ≈ **$0.50–1.00**. Buffer to $3 for mistakes.

## 2. On the instance (SSH)

```bash
# --- setup (~5 min) ---
pip install "lerobot[dataset,training]==0.6.0" wandb   # ACT is in the base package; no [act] extra exists
huggingface-cli login    # paste WRITE token
wandb login              # paste API key

# --- sanity: GPU visible ---
python -c "import torch; print(torch.cuda.get_device_name(0))"

# --- the dry run (~20–40 min) ---
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=lerobot/svla_so101_pickplace \
  --policy.device=cuda \
  --wandb.enable=true \
  --wandb.project=so101 \
  --steps=5000 \
  --batch_size=8 \
  --save_freq=5000 \
  --policy.repo_id=gkienpham/act_dryrun \
  --policy.push_to_hub=true \
  --job_name=act_dryrun \
  --output_dir=outputs/act_dryrun
```

(All flags verified against v0.6.0 `lerobot-train --help` on 2026-07-14.)

## 3. What "success" looks like

- wandb `train/loss` drops steeply in the first ~500 steps, then keeps declining. Exact final value doesn't matter — **slope** does.
- Checkpoint appears at `huggingface.co/gkienpham/act_dryrun` after step 5000.
- If loss is flat or NaN by step 1000: kill the run, save the log, we debug locally for free.

## 4. Shutdown discipline

1. Confirm the checkpoint is on the Hub (open the repo page).
2. **DESTROY the instance** (trash icon) — *pausing still bills storage; only destroy stops billing.*
3. Log actual $ + GPU-hrs in `COSTS.md` immediately, from the vast.ai billing page, not from memory.

## Known failure modes this run does NOT rule out

- Our own dataset having issues (camera sync, zero-std joints) — this uses a known-good community dataset.
- MPS inference correctness/latency on the Mac (that's Phase F).
- Anything hardware: calibration, teleop latency, USB bandwidth with 2 cameras.
