# AGENTS.md — BeanSight VN / SO-101

Instructions for any coding agent working in this repository. Read this file completely before
making plan-level suggestions or touching hardware-facing code. Then read, in order:

1. [docs/HANDOFF.md](docs/HANDOFF.md) — current status, full roadmap, gates, and open design gaps
2. `AGENTS.local.md` (gitignored, repo root) — private owner context; read it if present
3. [docs/runbook.md](docs/runbook.md) — the single operational path for any hardware/training step
4. [skills/README.md](skills/README.md) — task-specific playbooks; load the matching skill before
   executing a matching task

## What this project is

**BeanSight VN**: a small, supervised robotic workcell built on the Hugging Face LeRobot **SO-101**
(SO-ARM101) 6-DOF leader-follower arm. A fixed Logitech C920 inspects one Vietnamese Robusta
green-coffee bean at a time in a fixed nest; a two-class classifier labels it `acceptable` or
`visible_reject` (clearly black, clearly broken, or agreed foreign matter). Only on a confident
reject — and only when the operator has explicitly armed the controller — does an ACT-learned
pick-and-place skill (wrist C270 + joint state) move the bean to a reject cup. Acceptable or
uncertain always routes to `no_motion`.

**Scope boundary (do not widen it):** no food-safety claim, no cup-quality claim, no
industrial-sorter comparison, no worker-replacement claim. Ambiguous mold, moisture, taste, and
internal insect damage are outside the v1 label set. The one-month goal is an honest, quantified
answer to "how far can a low-cost arm assist this inspection step," published with datasets,
checkpoints, trial logs, and failure analysis.

The owner is a solo student builder, in Ho Chi Minh City until mid-August 2026 and then in Boston.
This is a portfolio-grade public project: everything published must survive expert scrutiny.

## Non-negotiable safety rules

Restate the relevant rule whenever you give an instruction involving power, wiring, or motor
configuration.

1. **Leader arm = 5 V supply. Follower arm = 12 V supply. Never swap.** A wrong supply can burn
   motors. Both arms, supplies, barrels, and cables get permanent distinct color labels.
2. **Inventory before power.** No supply is connected until servo labels, controller boards,
   voltage, current, barrel polarity, and the invoice have been photographed and cross-checked
   (docs/hardware_and_safety.md). Connector fit never implies identity.
3. **Motor IDs are assigned one motor at a time.** Never flash a daisy chain. This is the #1
   documented assembly failure. Joint map: pan 1, lift 2, elbow 3, wrist flex 4, wrist roll 5,
   gripper 6.
4. **The controller starts unarmed.** `BeanSightController` cannot cause motion until an explicit
   reject callback is installed and the operator arms it. Never write code that bypasses this.
5. **Supervised operation only.** Switched power strip within reach; never run unattended; a safety
   stop ends the trial with the `safety_stop` failure code. Cut power on unexpected direction,
   grinding, repeated comm errors, rising servo temperature, or a taut camera cable.
6. Beans touched by the gripper are permanently removed from food use.

## Hardware and environment

- **Arm:** WitMotion SO-ARM101 **Pro DIY kit** (12 servos, 2 controller boards, printed parts,
  5 V 3 A + 12 V 3 A supplies). The leader set has **mixed gear ratios** (three 1/147, two 1/191,
  one 1/345) — servos are not interchangeable across joints or arms. Expected arrival ~Jul 19–25, 2026.
- **Cameras:** Logitech **C920 (top/inspection)** + **C270 (wrist)** — two different models on
  purpose, because macOS swaps identical-model USB indexes. Both run 640×480/30 MJPG. Camera
  identity is resolved semantically at every launch via `beansight-camera-preflight`; never reuse a
  numeric index from an earlier session.
- **Local machine:** MacBook M1 Pro. Used for teleoperation, recording, calibration, and inference
  (`--policy.device=mps` or cpu). **Never for training.**
- **Training compute:** rented vast.ai GPUs (RTX 4090 class proved sufficient for ACT at $0.22/run).
  Budget discipline: justify every run, prefer a 5k-step validation run first, destroy (not pause)
  instances, log every dollar in COSTS.md.
- **LeRobot is pinned** to v0.6.0, commit `30da8e687a6dfc617fcd94afc367ac7071c376ce`, as a separate
  editable checkout at `~/robotics/lerobot` with the macOS serial-encoding patch from `patches/`
  applied. Do not assume behavior from newer LeRobot `main`; when docs and source disagree, the
  pinned source is the spec.

## Known gotchas (flag these proactively)

1. Motor ID conflicts — one motor at a time (see safety rules).
2. "Incorrect status packet" on macOS usually means a charge-only USB cable or wrong adapter
   jumpers, not broken motors. Use data-capable cables; don't change supplies by guesswork.
3. macOS serial ports appear as `/dev/tty.usbmodem*`; identify via unplug/replug with
   `lerobot-find-port`, per launch.
4. Keyboard control during recording silently does nothing until the terminal app has BOTH
   Accessibility AND Input Monitoring permissions and has been fully restarted (⌘Q). This already
   cost 4 junk episodes once.
5. Parallel per-camera video encoding crashes on macOS (`BrokenProcessPool`, cv2/av duplicate
   ffmpeg dylibs). The fix is serial encoding — versioned at
   `patches/lerobot-v0.6.0-macos-serial-encoding.patch`. Watch for the same crash in the real-arm
   record path.
6. Don't overtighten screws into 3D-printed parts — threads strip.
7. ACT has no built-in image resize; watch for OOM at high resolution/batch.
8. Use consistent `--robot.id`/`--teleop.id` names everywhere; calibration JSONs live in
   `~/.cache/huggingface/lerobot/calibration/` and must be backed up after calibration.
9. Task design: narrow beats wide. 75 demos in a ~10 cm workspace beat 50 in a large one; use fixed
   positions with small controlled offsets.
10. Lighting must be identical between data collection and inference — fixed diffused lamp, marked
    positions; if any fixture mark moves, start a new session ID rather than silently mixing data.

## Evidence standard (applies to every number you produce)

- Every evaluation reports **trial count, numerator/denominator, and a Wilson 95% confidence
  interval** (`beansight_vn.metrics.wilson_interval`). Never a bare percentage.
- Every failed trial gets exactly one primary failure code from the fixed taxonomy in
  [docs/evaluation_protocol.md](docs/evaluation_protocol.md). Never delete a trial.
- Latency and cycle time report sample count, median, and p95.
- Failures are reported alongside successes in all writeups and videos. Do failure triage before
  celebrating any number.
- `results/` holds only real hardware-generated outputs. **Never invent or placeholder results.**
- The repo claims no physical success rate until the frozen `beansight-v1-frozen` protocol has run.
- **ACT is the required policy. SmolVLA is optional** and only attempted after ACT exceeds 40% on
  20 frozen trials with evaluation tooling complete. Exactly **one targeted iteration** (10–25
  demos at the largest failure category, one retrain) is allowed after the first frozen run.
- Honest expectations: the first trained policy may fail completely ("pecking at the table" is a
  documented first-run outcome); a realistic final result is 50–70% on narrow pick-and-place. Do
  not let optimism inflate claims.

## Working style expected from the agent

- **Teach, don't just answer.** Explain the systems tradeoff behind each choice so the owner could
  re-derive it.
- **Roofline framing:** identify the binding constraint (control-loop Hz, camera fps, USB
  bandwidth, VRAM, $/GPU-hour) before optimizing anything else.
- **Honest failure logging:** for every design choice, state the failure mode it does NOT fix.
- **Cost discipline:** cheapest compute that answers the question; log spend in
  [COSTS.md](COSTS.md).
- **Decision log:** one line per significant choice with rationale in [DECISIONS.md](DECISIONS.md);
  weekly retros in [RETRO.md](RETRO.md).
- Never commit tokens, receipts, addresses, seller chats, or roaster contact details. `private/`,
  `logs/`, `videos/`, and `CLAUDE.md`/`AGENTS.local.md` are gitignored on purpose.

## Repo map and commands

```
src/beansight_vn/   typed records, routing, controller, perception, dataset QA, metrics, trial log
src/inference_smoke_test.py   standalone HF-Hub→MPS inference check
configs/            pinned JSON contracts (camera, perception, ACT, SmolVLA, rollout, evaluation)
patches/            LeRobot v0.6.0 macOS serial-encoding patch
docs/               runbook, hardware/safety, data/labeling, evaluation protocol, execution plan,
                    Vietnam idea bank, HANDOFF
skills/             portable task playbooks (see skills/README.md)
tests/              11 deterministic pytest modules — no arm or camera needed
results/            real hardware-generated summaries only
```

Setup and checks (run tests before and after any code change):

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,camera]'        # add [perception] for ResNet-18 training
pytest
ruff check .
```

CLI entry points installed by this package: `beansight-camera-preflight`, `beansight-dataset-qa`,
`beansight-capture-perception`, `beansight-build-perception-manifest`,
`beansight-build-record-config`, `beansight-compare`, `beansight-gripper-summary`,
`beansight-train-perception`, `beansight-trial-summary`.

Arm recording and policy training run inside the **pinned LeRobot environment**
(`~/robotics/lerobot`, see runbook §1–2), not this venv. Key LeRobot CLIs: `lerobot-find-port`,
`lerobot-setup-motors`, `lerobot-calibrate`, `lerobot-teleoperate`, `lerobot-record`,
`lerobot-train`, `lerobot-find-cameras`.
