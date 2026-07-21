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
uv pip install --no-deps -e /ABSOLUTE/PATH/TO/so101-robot
```

The last line exposes the lightweight `beansight-*` commands inside the pinned LeRobot interpreter
without resolving or replacing any LeRobot dependencies. It is required for dataset QA, which must
inspect the exact editable LeRobot checkout. Keep the normal project `.venv` for tests, camera work,
material sensing, and analysis; do not install LeRobot into that environment.

Xcode command-line tools are required for native dependencies. If a new `uv` installation is not on
`PATH`, restart the shell or use the path printed by its installer.

Verify and save the output:

```bash
python --version
python -c 'import lerobot; print(lerobot.__version__)'
git rev-parse HEAD
lerobot-train --help
lerobot-record --help
beansight-dataset-qa --help
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
[hardware_and_safety.md](hardware_and_safety.md), using the printable
[arrival-day bring-up checklist](arrival_day_checklist.md) for evidence references and sign-offs.
Do not connect a supply until the actual motor, controller, voltage, current, barrel, and polarity
records agree.

## 4. Resolve cameras and serial ports

Grant the terminal Camera permission in macOS System Settings. Accessibility and Input Monitoring may
also be needed for pynput-based simulation controls; the v0.6 terminal fallback only needs the
launching terminal to stay focused. Keep the C920 and C270 on separate physical Mac ports where
possible.

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

### Pre-arm C920 perception collection

The completed 30-minute soak qualifies throughput, not the current camera index, lamp, nest, or bean
presentation. Before each perception session, run a fresh 10-second semantic probe and inspect its
samples. Lock and record manual C920 focus and white balance with 50 Hz anti-flicker (exposure is
hardware-auto on macOS and declared as such — see docs/perception_collection.md §2), then use
`beansight-capture-perception` for beginning/ending neutral references and exactly one full-frame PNG
per physical bean. Join the blind labels and explicit split assignments with
`beansight-build-perception-manifest` before any model run.

The decision-complete commands and the three-session/two-lot 24-bean pilot layout are in
[perception_collection.md](perception_collection.md). The C270 never enters the perception manifest,
and pre-arm C270 images cannot train ACT.

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

## 6. Record blocks first, then coffee

Re-run a short semantic camera probe for the current launch, inspect both saved images, and create
the human attestation. The earlier 30-minute soak qualifies throughput; this probe prevents reuse of
stale numeric indexes:

```bash
beansight-camera-preflight --top-match C920 --wrist-match C270 --duration 10 \
  --output results/camera_launch/current
beansight-attest-cameras results/camera_launch/current/camera_preflight.json \
  --reviewer YOUR_NAME \
  --confirm-sample-images-reviewed --confirm-top-is-c920 --confirm-wrist-is-c270 \
  --output results/camera_launch/current/attestation.json
```

Generate a separate five-episode block smoke config:

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile blocks \
  --camera-attestation results/camera_launch/current/attestation.json \
  --episodes 5 \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/beansight-blocks-smoke-v1 \
  --output configs/generated/record_blocks_smoke.json

cd ~/robotics/lerobot
lerobot-record --config_path=/ABSOLUTE/PATH/TO/configs/generated/record_blocks_smoke.json
```

The generator refuses a failed camera report, preserves semantic `top`/`wrist` keys, and enables
streaming video encoding with two encoder threads to bypass the crash-prone post-episode process pool.
Inspect the first completed episode end to end. If all five are sound, generate the full block
profile separately and record 50 episodes over the five-position grid:

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile blocks \
  --camera-attestation results/camera_launch/current/attestation.json \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/beansight-blocks-v1 \
  --output configs/generated/record_blocks.json
```

Train and physically evaluate that bring-up baseline before the 20-grasp bean gate in
[evaluation_protocol.md](evaluation_protocol.md). Only after the mechanical gate passes, generate
`--profile coffee` with a copied, filled `configs/transfer_gate_evidence.example.json` passed via
`--gate-evidence`, and collect 50–75 real-bean demonstrations with its exact task string. The cap
profile later requires the frozen BeanSight summary hash. The bottle profile additionally requires
the passed sensor metrics and the failed waypoint/pose-variation summary hashes.

LeRobot v0.6 stamps a new non-resume dataset ID with `_YYYYMMDD_HHMMSS`. Copy the actual ID from the
recording log and use that immutable name for QA, replay, upload, and training. To continue an
interrupted local dataset, pass `--resume=true`, the stamped repo ID, and its explicit local root.

## 7. Gate and publish the dataset

Activate `~/robotics/lerobot/.venv` and run full QA through the no-dependency BeanSight CLI bridge
before any upload or GPU rental:

```bash
beansight-dataset-qa YOUR_HF_USER/beansight-vn-coffee-v1 \
  --root /ABSOLUTE/LOCAL/DATASET/ROOT \
  --output results/dataset_qa.json
```

Watch sample episodes end to end. Confirm camera order, sharpness, duration, task string, and all six
action dimensions. Push privately only after QA passes, then record the immutable Hub commit.
Re-run QA against that exact uploaded commit and use this second report for training:

```bash
beansight-dataset-qa YOUR_HF_USER/beansight-vn-coffee-v1_TIMESTAMP \
  --revision 40_CHARACTER_HF_COMMIT \
  --root /ABSOLUTE/FRESH/QA_SNAPSHOTS/40_CHARACTER_HF_COMMIT \
  --output results/dataset_qa_pinned.json
```

The pinned run requires a new or empty snapshot root so an older local copy cannot shadow the Hub
revision. Its report includes a content fingerprint plus the exact LeRobot and recording-patch
provenance. The ACT config builder rejects a report whose dataset ID, revision, fingerprint, or
pinned runtime differs from the requested training dataset.

## 8. Train ACT

Use `beansight-build-act-config` with the pinned-revision QA report to create the 5,000-step smoke
config and, only after the smoke run is healthy, the full config. For approximately five data
epochs:

```text
steps = ceil(training_frames / batch_size) × 5
```

The builder derives `training_frames` from the complete train episode IDs selected by LeRobot's
episode-level evaluation split; it does not multiply the total frame count by 0.9.

```bash
beansight-build-act-config results/dataset_qa_pinned.json \
  --dataset-repo-id YOUR_HF_USER/beansight-vn-coffee-v1_TIMESTAMP \
  --dataset-revision 40_CHARACTER_HF_COMMIT \
  --policy-repo-id YOUR_HF_USER/beansight-vn-act-v1 \
  --job-name beansight-act-v1 \
  --train-output-dir outputs/train/beansight-act-v1 \
  --mode smoke

beansight-build-act-config results/dataset_qa_pinned.json \
  --dataset-repo-id YOUR_HF_USER/beansight-vn-coffee-v1_TIMESTAMP \
  --dataset-revision 40_CHARACTER_HF_COMMIT \
  --policy-repo-id YOUR_HF_USER/beansight-vn-act-v1 \
  --job-name beansight-act-v1 \
  --train-output-dir outputs/train/beansight-act-v1 \
  --mode full
```

Each generated config has a `.provenance.json` sidecar containing the QA, dataset-content, config,
LeRobot, and patch hashes. Preserve both files.

On Vast, use a plain CUDA image and an editable checkout at the same exact commit—
`30da8e687a6dfc617fcd94afc367ac7071c376ce`—rather than a mutable `main` checkout or an unverified
prebuilt LeRobot image. Save `git rev-parse HEAD` with the run evidence before launching
`lerobot-train`.

Run from the pinned environment:

```bash
lerobot-train --config_path=/ABSOLUTE/PATH/TO/configs/generated/beansight-act-v1_smoke.json
```

Stop immediately on NaN/Inf. If loss is flat after roughly 1,000 steps, inspect the dataset before
paying for a longer run. Evaluate the smoke checkpoint before starting the generated five-epoch
full config.

The generated policy config pushes privately to the Hub. After training, copy the immutable policy
revision into the experiment manifest and verify the exact checkpoint on the M1 from the project
root, using the pinned LeRobot environment:

```bash
python src/inference_smoke_test.py YOUR_HF_USER/beansight-vn-act-v1 \
  --revision 40_CHARACTER_POLICY_COMMIT --device mps
```

Preserve the W&B run and checkpoint revision, record the actual GPU-hours and dollars in
`COSTS.md`, then destroy—not pause—the Vast instance. Do not leave paid compute running while doing
local physical evaluation.

## 9. Integrate and score

The rollout loop passes its existing `observation.images.top` frame to `BeanSightController`; no
second process opens the C920. The controller remains unarmed until the explicit ACT callback is
installed, the workspace is clear, and the operator is ready. One trigger permits one reject rollout,
followed by verification and a `TrialRecord` append.

Load the classifier operating threshold from the training run's `operating_threshold.json` and pass
it explicitly to `TorchScriptClassifier`. That validation-selected classifier threshold is distinct
from the controller's more conservative reject-confidence motion gate. Never derive either value
from test predictions or physical trial outcomes.

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

## 11. Post-flagship cap transfer

Do not start this section until the first BeanSight frozen result is preserved. Before any physical
instruction: **leader = 5 V, follower = 12 V, never swap; inventory before power; motor IDs one at a
time; supervised operation only.**

Use one upright plastic screw cap in the fixed 15 x 15 cm zone. Exclude crown caps, piles, touching
caps, side poses, and cap removal. Re-resolve the semantic cameras, then generate the short-horizon
recording config:

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile caps \
  --camera-attestation results/camera_launch/current/attestation.json \
  --gate-evidence /ABSOLUTE/PATH/TO/filled_transfer_gate_evidence.json \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/cap-grasp-v1
```

The policy learns approach, grasp, and lift to a safe handoff pose. A dated external classifier or
sensor chooses the bin; supervised waypoints perform bin transport and release. Run dataset QA and
use `beansight-build-act-config` for the 5k smoke and five-epoch full configs. Do not hand-edit around
the immutable-revision gate.

## 12. Plastic material sensing

This is a standalone test. It is not an arm trial and cannot create motion.

```bash
python -m pip install -e '.[dev,materials]'
beansight-train-material-sensor data/materials/manifest.csv \
  --config configs/material_sensor.json \
  --output-dir outputs/material_sensor/db23_r1
```

Follow [material_sensing_protocol.md](material_sensing_protocol.md). Replace the sensor revision in a
copied config, collect 30 unique items per class and ten scans per item across three sessions, and
keep physical item/SKU groups intact. A nonzero exit status means the gate failed. Preserve the
metrics and stop before arm integration; do not weaken the claim or use RGB as a hidden substitute.

## 13. Bottle sorting

Start with one empty, dry, uncrushed bottle in the V-cradle. **Leader = 5 V and follower = 12 V;
never swap. Keep the controller unarmed, the switched cutoff within reach, and the run supervised.**

Run 20 waypoint grasp/lift/drop trials for each representative geometry. At 16/20 or better, retain
the waypoint solution. If pose variation is the largest failure category, generate the `bottles`
recording profile and collect 75 approach/grasp/handoff demonstrations. Payload, jaw, friction, or
deformation failures require a mechanical change rather than another training run.

Generate the waypoint summary with `beansight-material-trial-summary`. The bottle recording builder
does not trust the evidence Boolean by itself: it verifies the hashed summary has at least three
geometries with exactly 20 trials, a failed waypoint gate, and the computed
`collect_act_for_pose_variation` branch. It also verifies that the hashed material metrics contain a
passing RBF-SVM gate and a deployable artifact. If the summary instead selects the mechanical or
manual-triage branch, do not collect ACT data.

Load a copied, dated route profile with `RouteProfile.from_dict`. The committed HCMC and Boston
examples are disabled. Enable one only after current local-route review and the frozen material
sensor gate. Unknown, low confidence, inactive profiles, and manual review remain no-motion paths.

```bash
beansight-material-trial-summary results/material-trials-v1.jsonl \
  --output results/material-summary-v1.json
```

Only real hardware trials go in `results/`.

## 14. Optional Isaac/Vast spike

The spike remains disabled until a real cap ACT baseline, pinned QA, modified asset, measured
follower/workcell, and local Linux RTX inference host exist. Fill a copy of
`configs/isaac_vastai_spike.json`, then run `beansight-validate-isaac-spike` on it before any rental.
Keep the NVIDIA workshop environment separate from LeRobot v0.6.0 and exchange only converted,
QA-passed datasets.

Use a Vast VM or prebuilt flattened image on an RTX 4090 with at least 64 GB RAM and 100 GB disk.
Limit infrastructure bring-up to two paid GPU-hours. Verify `nvidia-smi`, run the compatibility
checker, boot headlessly, render RGB/depth, sustain a ten-minute rollout, terminate and relaunch the
Isaac application in the same instance, save evidence under `outputs/`, and destroy the instance.
Never teleoperate or infer on the physical arm over the public internet.

Preserve every file required by the config validator: the live offer, host specification,
`nvidia-smi`, compatibility report, immutable version/digest manifest, RGB/depth render, rollout
log, first/second clean-boot logs, GPU-hours/cost, and destruction confirmation.

The custom cap comparison is capped at one engineering week and a $10 total inclusive of
infrastructure. GR00T physical trials require the validated local Linux RTX host; the M1 Pro cannot
run them. **For every physical trial, leader = 5 V, follower = 12 V, never swap; inventory first;
motor IDs one at a time; controller unarmed by default; explicit one-shot arming and supervised
operation with the cutoff in reach.** Follow every fixed count and retention condition, log every
dollar in `COSTS.md`, and preserve simulated evidence outside `results/`.

## Troubleshooting

- No camera: check the data cable and terminal Camera permission.
- Black frame: check lens, privacy shutter, exposure, and permission before changing code.
- Recording hotkeys fail: focus the launching terminal and use `n`, `r`, or `q`; grant Accessibility
  and Input Monitoring only if the active input backend still requires them.
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
- [ ] C920 perception manifest passes automated QA and full-size manual review
- [ ] leader/follower ports and calibration IDs recorded; calibration backed up
- [ ] 20-grasp physical gate passed
- [ ] full dataset QA passed before GPU rental
- [ ] immutable dataset and policy revisions copied into the manifest
- [ ] BeanSight frozen result preserved before cap transfer work
- [ ] material sensor gate passed before any material-driven motion
- [ ] copied, dated local route profile reviewed and explicitly enabled
- [ ] optional Isaac environment isolated from the pinned real-robot checkout
