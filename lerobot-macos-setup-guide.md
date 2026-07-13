# LeRobot macOS Setup Guide — Pre-Arrival Prep (M1 Pro)

Everything here can be done BEFORE the arm arrives. Goal: by the time the kit lands (~Jul 19–24), your entire software pipeline — record → dataset → Hub → cloud training → checkpoint → local inference — is already proven in simulation. Work through this top to bottom; it maps to Days 1–7 of the plan.

**Note:** LeRobot moves fast. Command names and flags below match the recent (v0.5.x-era) CLI; if anything errors, check `lerobot --help` and the official docs at huggingface.co/docs/lerobot — and pin whatever version you install (Step 2) for the whole project.

---

## Step 0 — Prerequisites (~20 min)

```bash
# Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Core tools
brew install git ffmpeg

# uv — fast Python package/env manager (LeRobot's recommended path)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installing uv, then verify:

```bash
uv --version
ffmpeg -version   # needed for video encoding of camera streams
```

## Step 1 — Accounts (~15 min)

1. **Hugging Face**: create account → Settings → Access Tokens → create a token with **write** access. You'll push datasets and model checkpoints here.
2. **Weights & Biases** (wandb.ai): create account, grab your API key from settings.
3. **vast.ai**: create account, add ~$30 credit (credit card or crypto). Don't rent anything yet.

## Step 2 — Install LeRobot (~20 min)

```bash
mkdir -p ~/robotics && cd ~/robotics

# Clone (editable install so you can read/patch source — you'll want to)
git clone https://github.com/huggingface/lerobot.git
cd lerobot

# Record the exact commit for reproducibility — put this in DECISIONS.md
git rev-parse HEAD

# Python 3.12 env
uv venv --python 3.12
source .venv/bin/activate

# Install with the extras you need:
# feetech = SO-101 servo drivers, smolvla = VLA fine-tuning deps
uv pip install -e ".[feetech,smolvla]"
```

Verify:

```bash
python -c "import lerobot; print(lerobot.__version__)"
lerobot-train --help
```

Log in to services:

```bash
huggingface-cli login    # paste your write token
wandb login              # paste your API key
```

**Gotcha:** if `uv pip install` fails on a dependency compile, make sure Xcode command line tools are installed: `xcode-select --install`.

## Step 3 — Test your cameras as soon as they arrive from Shopee (~15 min)

```bash
lerobot-find-cameras opencv
```

This lists every camera macOS can see with its index. Plug in both webcams (through your powered hub) and confirm:
- Both show up with distinct indices
- Note which index = which physical camera (tape a label on each)

macOS will ask for **camera permission** for your terminal app the first time — grant it in System Settings → Privacy & Security → Camera.

Quick capture test (adjust index):

```bash
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print('Camera 0 OK:', ret, frame.shape if ret else None)
cap.release()
"
```

Do this for both cameras. If frames are black, it's almost always the permission setting.

## Step 4 — Simulation: gym-hil (Days 3–4 of the plan)

This is your hardware-free practice loop. It's a MuJoCo environment where you control a simulated arm and record LeRobot-format datasets — the exact same dataset format and training commands you'll use on the real arm.

```bash
uv pip install gym_hil mujoco
```

Test render (macOS: MuJoCo viewer needs `mjpython` on Apple Silicon):

```bash
python -c "
import gymnasium as gym
import gym_hil
env = gym.make('gym_hil/PandaPickCubeKeyboard-v0')
obs, info = env.reset()
print('Sim OK. Obs keys:', list(obs.keys()) if hasattr(obs, 'keys') else type(obs))
"
```

Then collect ~10 practice episodes with keyboard control and push them to the Hub as `YOUR_HF_USERNAME/sim_practice_dataset`. The exact record command for sim is in the LeRobot `il_sim` docs page — follow it verbatim, since flags change between versions. What matters is that you exit this step having:
1. Recorded episodes in LeRobot dataset format
2. Pushed to HF Hub
3. Viewed them in the dataset visualizer: https://huggingface.co/spaces/lerobot/visualize_dataset

## Step 5 — Study a real community dataset (Day 4)

Pick a community SO-101 pick-and-place dataset from the Hub (search "so101" in datasets, filter by LeRobot format). Load and inspect it:

```bash
python -c "
from lerobot.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset('lerobot/svla_so101_pickplace')  # or another community repo_id
print('Episodes:', ds.num_episodes)
print('Frames:', ds.num_frames)
print('Features:', list(ds.features.keys()))
print('FPS:', ds.fps)
"
```

Look at: how many episodes they used, camera views, episode length, action space. This calibrates your own data collection next week.

## Step 6 — vast.ai training dry run (Day 5, ~$2–3)

The point: prove the cloud pipeline BEFORE your own data exists, so Week 3 training is a solved problem.

1. On vast.ai, filter: RTX 5090 (or 4090), ≥32GB RAM, ≥100GB disk, high reliability score, price ≤$0.70/hr.
2. Use a LeRobot docker image (e.g. `ioaitech/lerobot-gpu`) or a plain PyTorch CUDA image + `pip install 'lerobot[smolvla]'`.
3. SSH in, then:

```bash
huggingface-cli login
wandb login

lerobot-train \
  --policy.type=act \
  --dataset.repo_id=lerobot/svla_so101_pickplace \
  --policy.device=cuda \
  --wandb.enable=true \
  --steps=5000 \
  --batch_size=8 \
  --output_dir=outputs/dryrun_act
```

4. Watch the wandb dashboard: loss should decrease within the first few hundred steps.
5. Confirm you can push the checkpoint to the Hub (`--policy.repo_id=YOUR_USERNAME/act_dryrun` or push manually).
6. **DESTROY the instance** when done — billing stops only when destroyed, not paused.

Log the cost in `COSTS.md`. Expect ~$2–3 total.

## Step 7 — Local inference smoke test (Day 6)

Pull your dry-run checkpoint back to the Mac and verify it loads and runs a forward pass on MPS:

```bash
python -c "
import torch, time
from lerobot.policies.act.modeling_act import ACTPolicy
policy = ACTPolicy.from_pretrained('YOUR_USERNAME/act_dryrun')
device = 'mps' if torch.backends.mps.is_available() else 'cpu'
policy.to(device)
print(f'Policy loaded on {device}. Params: {sum(p.numel() for p in policy.parameters())/1e6:.1f}M')
"
```

This proves the checkpoint→local-inference path. (Timing it properly with dummy observations is your Week 4 latency-profiling task — don't rabbit-hole now.)

## Step 8 — Repo scaffolding (Day 6–7)

```bash
cd ~/robotics
mkdir -p so101-project/{src,configs,logs,videos}
cd so101-project
git init
touch CLAUDE.md COSTS.md DECISIONS.md RETRO.md README.md
```

Drop the `CLAUDE.md` project prompt and the research markdown into this folder, open it with Claude Code, and it will have full context.

---

## When the arm arrives — macOS-specific gotchas cheat sheet

Keep this handy for assembly week:

1. **Find serial ports:** `lerobot-find-port` — unplug/replug the servo adapter to identify it. Ports look like `/dev/tty.usbmodem58760431091`.
2. **"Incorrect status packet" / model number None:** 90% of the time it's a charge-only USB cable. Use the Type-C data cables from the kit; if errors persist, check the Waveshare adapter jumpers (should be on the USB/B-channel setting per the docs).
3. **Motor IDs:** connect ONE servo at a time to the driver board when running `lerobot-setup-motors`. Label each motor (L1–L6, F1–F6) with tape before assembly.
4. **Power:** 5V adapter → leader arm. 12V adapter → follower arm. Never swap. Check twice before plugging in.
5. **Keyboard controls during recording:** grant your terminal Accessibility + Input Monitoring permissions (System Settings → Privacy & Security), or the record script's arrow-key/exit controls silently won't work.
6. **Calibration files** live in `~/.cache/huggingface/lerobot/calibration/` — back them up after a good calibration, and use the same `--robot.id` string in every command.

## End-of-week-1 checklist

- [ ] LeRobot installed, version pinned in DECISIONS.md
- [ ] Both cameras detected and labeled
- [ ] 10 sim episodes recorded and visible on HF Hub
- [ ] Community dataset inspected in visualizer
- [ ] ACT dry-run trained on vast.ai, loss curve on wandb
- [ ] Checkpoint pulled and loaded on M1 Pro (MPS)
- [ ] Repo scaffolded with CLAUDE.md + research doc inside
- [ ] COSTS.md shows total spend (target: <$5 so far)

If all boxes are checked, Week 2 becomes purely a hardware week — every software unknown is already retired.
