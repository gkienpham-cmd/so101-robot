# BeanSight setup and experiment runbook

This is the single operational path from a clean Mac and sealed boxes to a scored workcell. Complete
the physical gate in [hardware_and_safety.md](hardware_and_safety.md) before connecting power. Replace
every placeholder and preserve terminal output with the experiment manifest.

## 1. Install the pinned environment

```bash
brew install git ffmpeg

mkdir -p ~/robotics
cd ~/robotics
git clone https://github.com/huggingface/lerobot.git
cd lerobot
git checkout 30da8e687a6dfc617fcd94afc367ac7071c376ce

uv venv --python 3.12
source .venv/bin/activate
uv pip install -e '.[feetech,smolvla,dataset,training,viz,core_scripts]'
```

Xcode command-line tools are required for native dependencies. If a new `uv` installation is not on
`PATH`, restart the shell or use the path printed by its installer.

Verify and save the output:

```bash
python --version
python -c 'import lerobot; print(lerobot.__version__)'
git rev-parse HEAD
lerobot-train --help
lerobot-record --help
ffmpeg -version
```

The Git revision must be `30da8e687a6dfc617fcd94afc367ac7071c376ce`. This project does not
assume behavior from a newer LeRobot `main`.

Use write-scoped credentials and keep new Hub artifacts private:

```bash
hf auth login
wandb login
```

Never commit tokens, seller messages, receipts, addresses, or private roaster information.

## 2. Record the macOS encoding workaround

The pinned local checkout needs serial episode encoding in the gym-manipulator path because the
cv2/av duplicate-`libavdevice` collision caused `BrokenProcessPool`. The exact change is versioned at
`patches/lerobot-v0.6.0-macos-serial-encoding.patch`.

On a clean checkout:

```bash
cd ~/robotics/lerobot
git apply --check --unidiff-zero /ABSOLUTE/PATH/TO/patches/lerobot-v0.6.0-macos-serial-encoding.patch
git apply --unidiff-zero /ABSOLUTE/PATH/TO/patches/lerobot-v0.6.0-macos-serial-encoding.patch
git diff --check
```

Record the patch filename and LeRobot revision in every manifest. This fixes the confirmed HIL path;
it does not prove that every video failure has the same cause.

## 3. Inventory before power

Complete every purchase, electrical, labeling, layout, and stop-condition item in
[hardware_and_safety.md](hardware_and_safety.md). Do not connect a supply until the actual motor,
controller, voltage, current, barrel, and polarity records agree.

## 4. Resolve cameras and serial ports

Grant the terminal Camera, Accessibility, and Input Monitoring permissions in macOS System Settings.
Keep the C920 and C270 on separate physical Mac ports where possible.

Run the semantic camera soak from the BeanSight environment:

```bash
beansight-camera-preflight \
  --top-match C920 \
  --wrist-match C270 \
  --duration 1800 \
  --output results/camera_preflight
```

Inspect both saved frames and the JSON report. Confirm that `top` is the C920 and `wrist` is the C270.
Re-run after a replug or reboot; never copy a numeric camera index from an older session.

Identify each controller before and after plugging it in:

```bash
lerobot-find-port
```

Use the observed `/dev/tty.*` paths for the current launch.

## 5. Assign motor IDs and calibrate

Assign IDs with one motor connected at a time:

```bash
lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/REPLACE_FOLLOWER
lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/REPLACE_LEADER
```

Calibrate with stable IDs:

```bash
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/REPLACE_FOLLOWER \
  --robot.id=beansight_follower

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/REPLACE_LEADER \
  --teleop.id=beansight_leader
```

Back up both files from `~/.cache/huggingface/lerobot/calibration/`. Teleoperate first without
cameras, then with both. Start with wooden blocks.

## 6. Generate the recording config

```bash
beansight-build-record-config results/camera_preflight/camera_preflight.json \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/beansight-vn-coffee-v1

cd ~/robotics/lerobot
lerobot-record --config_path=/ABSOLUTE/PATH/TO/configs/generated/record_coffee.json
```

The generator refuses a failed camera report and preserves semantic `top`/`wrist` keys. Record 50
block episodes over the five-position grid, then pass the 20-grasp bean gate in
[evaluation_protocol.md](evaluation_protocol.md). Collect 50–75 real-bean demonstrations with the
exact task string from the generated config.

## 7. Gate and publish the dataset

Run full QA before any upload or GPU rental:

```bash
beansight-dataset-qa YOUR_HF_USER/beansight-vn-coffee-v1 \
  --root /ABSOLUTE/LOCAL/DATASET/ROOT \
  --output results/dataset_qa.json
```

Watch sample episodes end to end. Confirm camera order, sharpness, duration, task string, and all six
action dimensions. Push privately only after QA passes, then record the immutable Hub commit.

## 8. Train ACT

Replace the dataset and policy IDs, immutable dataset revision, output directory, and step count in
`configs/train_act.json`. For approximately five data epochs:

```text
steps = ceil(training_frames / batch_size) × 5
```

Run from the pinned environment:

```bash
lerobot-train --config_path=/ABSOLUTE/PATH/TO/configs/train_act.json
```

Stop immediately on NaN/Inf. If loss is flat after roughly 1,000 steps, inspect the dataset before
paying for a longer run. Evaluate a short checkpoint before extending toward ten epochs.

## 9. Integrate and score

The rollout loop passes its existing `observation.images.top` frame to `BeanSightController`; no
second process opens the C920. The controller remains unarmed until the explicit ACT callback is
installed, the workspace is clear, and the operator is ready. One trigger permits one reject rollout,
followed by verification and a `TrialRecord` append.

Run the complete frozen protocol before reading the aggregate:

```bash
beansight-trial-summary results/trials-v1.jsonl --output results/summary-v1.json
```

Keep the first result, including poor trials. After the one allowed targeted iteration, compare
matching physical strata:

```bash
beansight-compare results/trials-v1-before.jsonl results/trials-v1-after.jsonl \
  --output results/before-after-v1.json
```

The comparison refuses different ground-truth, position, or lighting counts by default.

## 10. Optional SmolVLA

Continue only if ACT exceeds 40% over 20 frozen trials and evaluation tooling is complete. Replace the
placeholders in `configs/train_smolvla.json`:

```bash
lerobot-train \
  --config_path=/ABSOLUTE/PATH/TO/configs/train_smolvla.json \
  --policy.path=lerobot/smolvla_base \
  --policy.repo_id=YOUR_HF_USER/beansight-vn-smolvla-v1 \
  --policy.private=true
```

Use one RTX 4090, batch 4, and about 20,000 steps. Keep additional GPU spend near $10 unless a
specific measured result justifies more. Destroy Vast.ai instances after use and record actual spend.

## Troubleshooting

- No camera: check the data cable and terminal Camera permission.
- Black frame: check lens, privacy shutter, exposure, and permission before changing code.
- Recording hotkeys fail: grant Accessibility and Input Monitoring, then fully restart the terminal.
- Incorrect status packet or missing motor model: inspect the USB cable, adapter jumpers, power, and
  current port. Do not try a different supply by guesswork.
- cv2/av Objective-C collision warning: retain the versioned patch and watch the real recording path
  for the same confirmed parallel-encoding failure.

## Completion checklist

- [ ] Python 3.12 and exact LeRobot revision recorded
- [ ] encoding patch recorded and diff checked
- [ ] ffmpeg, LeRobot CLI, Hugging Face, and W&B verified
- [ ] electrical and polarity inventory signed off
- [ ] both semantic cameras pass the concurrent 30-minute soak
- [ ] leader/follower ports and calibration IDs recorded; calibration backed up
- [ ] 20-grasp physical gate passed
- [ ] full dataset QA passed before GPU rental
- [ ] immutable dataset and policy revisions copied into the manifest
