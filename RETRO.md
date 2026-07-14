# RETRO.md — Weekly retrospectives

## Week 1 (Jul 14–20) — Software, sim, pipeline dry run

**Status: Days 1–6 of the plan compressed into Day 1 (Jul 14). Every pre-hardware item retired except the camera test (Shopee delivery pending).**

### What broke (and what fixed it)

1. **LeRobot v0.6.0 modularized its extras** — the v0.5.x-era setup guide's `[feetech,smolvla]` install left `lerobot-train` broken (`ImportError: 'datasets'`). Fix: add `[dataset,training,core_scripts,viz]`. Lesson: with a fast-moving library, the error message is more current than the docs.
2. **Docs-vs-code drift in the sim record config** — the official docs show `"type": "gym_manipulator"` inside `env`, but the v0.6.0 parser rejects it (`env` is typed concretely, not via choice registry). Found by reading `GymManipulatorConfig` in the source; validated the fixed config through the actual draccus decoder before re-running. Lesson: when config schemas drift, the source is the spec.
3. **macOS Accessibility/Input Monitoring trap** — pynput printed "This process is not trusted!" and keyboard control silently did nothing; the recorder happily saved episodes of a motionless robot. Permissions must be granted to the terminal app AND the app fully restarted (⌘Q). Cost: ~4 junk episodes, deleted.
4. **Parallel video encoding crashed on macOS** (`BrokenProcessPool` on first episode save) — the per-camera encoder worker processes abort under a duplicate-libavdevice objc collision (`cv2` and `av` both bundle ffmpeg 61.3.100). Fix: one-line patch to our pinned editable install, `save_episode(parallel_encoding=False)`; serial encoding of 2×128×128 videos costs ~1 s/episode. **Carry-over risk: the real-arm record path with 2 cameras may hit the same crash — workaround is known in advance.**

### What worked first try

- gym-hil headless smoke test (offscreen MuJoCo rendering, front+wrist 128×128 views, 7-dim action space).
- The vast.ai dry run end-to-end: base image + `uv pip install lerobot[dataset,training]==0.6.0`, HF/wandb logins, 5k-step ACT launch — no debugging needed on the cloud side.
- MPS inference smoke test: checkpoint pulled from Hub, 51.6M-param ACT loaded on M1 Pro, forward pass → (1,6) action tensor.

### Pipeline status (proven end-to-end)

```
sim teleop (mjpython, keyboard) → LeRobot v3.0 dataset → HF Hub (gkienpham/sim_practice_dataset)
→ vast.ai RTX 4090 → lerobot-train ACT 5k steps (loss 6.4 → ~0.7, wandb project so101)
→ checkpoint → HF Hub (gkienpham/act_dryrun) → M1 Pro MPS → forward pass ✓
```

Training telemetry worth remembering: `updt_s:0.077` vs `data_s:0.003` — compute-bound at batch 8, dataloader nowhere near the roof; 3.7/24 GB VRAM; ~100 samples/s; constant lr 1e-5 (ACT default has no schedule).

### Spend

$0.22 of the $8–40 cloud budget (RTX 4090 @ ~$0.31/hr, ~40 min including setup). The runbook estimate of $2–3 was ~10× padded — good news for Week 3–4 iteration headroom. Balance: $8.78.

### Carry-over risks for Week 2 (untested by design — sim can't reach them)

- Real-arm calibration, motor ID assignment (one at a time!), USB serial behavior on macOS.
- Two physical cameras at 640×480/30 fps through one hub (USB bandwidth), camera permission for the terminal.
- The parallel-encoding crash may resurface in the real record path (fix known).
- Teleop latency/feel — no sim proxy for leader-follower mechanics.
- **Standing safety rules: 5V = leader, 12V = follower; never swap. IDs one servo at a time.**

## Week 2 — (pending hardware arrival ~Jul 19)
