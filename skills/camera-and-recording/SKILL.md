---
name: camera-and-recording
description: Camera preflight soak, serial-port resolution, record-config generation, and episode recording for BeanSight VN on macOS — including the Accessibility/Input-Monitoring trap and the parallel-encoding crash patch. Use for any task involving cameras, lerobot-record, or teleoperated data collection.
---

# Cameras and recording (macOS)

Full authority: `docs/runbook.md` §2, §4, §6. Environment: recording runs inside the pinned
LeRobot checkout (`~/robotics/lerobot`, v0.6.0 commit `30da8e687a6dfc617fcd94afc367ac7071c376ce`)
with `patches/lerobot-v0.6.0-macos-serial-encoding.patch` applied; the `beansight-*` CLIs run from
this repo's venv.

## Ground rules

- Two DIFFERENT camera models on purpose: **C920 = top/inspection, C270 = wrist**. macOS swaps
  numeric indexes of identical models after replug/reboot — **never reuse a numeric camera index
  from an earlier session**; resolve identity semantically every launch.
- Both cameras: 640×480 / 30 fps MJPG, ideally on separate physical Mac ports.
- Grant the terminal Camera permission (System Settings) before anything opens a camera.

## 1. Camera preflight soak (gate)

```bash
beansight-camera-preflight \
  --top-match C920 --wrist-match C270 \
  --duration 1800 \
  --output results/camera_preflight
```

Inspect both saved frames + JSON; confirm `top` is really the C920 and `wrist` the C270. Re-run
after any replug or reboot. A failed report **cannot** generate a recording config — that's by design.
The 30-minute run qualifies throughput once. Before every recording launch, run a 10-second probe
under `results/camera_launch/current`, inspect the new frames, and record the view attestation:

```bash
beansight-camera-preflight \
  --top-match C920 --wrist-match C270 --duration 10 \
  --output results/camera_launch/current
beansight-attest-cameras results/camera_launch/current/camera_preflight.json \
  --reviewer YOUR_NAME \
  --confirm-sample-images-reviewed --confirm-top-is-c920 --confirm-wrist-is-c270 \
  --output results/camera_launch/current/attestation.json
```

## 2. Serial ports

```bash
lerobot-find-port   # run before and after plugging each controller in
```

Ports appear as `/dev/tty.usbmodem*` and can change between launches; use the currently observed
paths only.

## C920 perception stills before arm recording

The 30-minute soak qualifies USB throughput. Before each still-image session, run a fresh 10-second
semantic probe, inspect its samples, and use that report immediately with
`beansight-capture-perception`. The still-image tool opens only the semantic C920 `top`, saves one
full 640×480 lossless PNG per physical bean, and requires beginning/ending neutral references plus
an operator-recorded settings snapshot. It never displays a prediction. The C270 must never enter
the perception image manifest.

Follow [docs/perception_collection.md](../../docs/perception_collection.md) for the exact capture and
manifest commands. A settings SHA records what the operator entered; it does not prove the camera
accepted the setting.

## 3. Generate the record config

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile blocks \
  --camera-attestation results/camera_launch/current/attestation.json \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port  /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/beansight-blocks-v1
```

Produces `configs/generated/record_blocks.json` with semantic `top`/`wrist` keys and streaming
video encoding (two encoder threads) to bypass the crash-prone post-episode process pool.

## 4. Record

```bash
cd ~/robotics/lerobot
lerobot-record --config_path=/ABSOLUTE/PATH/TO/configs/generated/record_blocks.json
```

- Record **5 smoke episodes first** and inspect the first completed save before committing to a
  session.
- Then: 50 wooden-block episodes over the five-position grid (bring-up), later 50–75 real-bean
  demos with the exact task string from the generated config and small controlled offsets.
- LeRobot v0.6 stamps non-resume datasets `_YYYYMMDD_HHMMSS` — copy the actual stamped ID from the
  log and use that immutable name for QA/replay/upload/training. To resume an interrupted local
  dataset: `--resume=true` + stamped repo ID + explicit local root.
- Lighting and fixture positions must match between collection and inference; if any mark moves,
  start a new session ID — never silently mix sessions.

## macOS traps (both have already bitten this project)

1. **Silent keyboard**: pynput prints "This process is not trusted!" and hotkeys do nothing while
   the recorder happily saves motionless episodes. Fix: add the terminal app under BOTH Privacy &
   Security → Accessibility AND → Input Monitoring, then fully quit (⌘Q) and reopen. The v0.6
   terminal fallback (`n`/`r`/`q`) only needs the launching terminal focused.
2. **`BrokenProcessPool` on first episode save**: cv2 and av bundle duplicate ffmpeg dylibs;
   parallel per-camera encoding aborts. Fix is serial encoding —
   `patches/lerobot-v0.6.0-macos-serial-encoding.patch` (i.e. `save_episode(parallel_encoding=False)`).
   On a clean checkout, verify applicability with `git apply --check --unidiff-zero <patch>`.
   On an already-patched checkout, verify presence with
   `git apply --reverse --check --unidiff-zero <patch>`. Finish with `git diff --check`. Watch for
   the same crash in the real-arm record path.

Other quick checks: no camera → data cable + Camera permission; black frame → lens/privacy
shutter/exposure/permission before touching code.
