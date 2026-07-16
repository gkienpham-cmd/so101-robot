# Pre-Arrival Preparation and Model Training Plan (Jul 15–20)

**Status:** hardware (WitMotion "SO-ARM101 Kit (Pro)", AliExpress, 1,443,860 VND + 459,436 VND shipping) arrives **Jul 20–25**. Today is **Jul 15**. This document covers: what to train NOW on public SO-101 data (and the honest transfer verdict), the remaining sim work worth doing, physical prep in HCMC, a day-by-day schedule, and a pre-staged copy-paste command sequence for hardware day 1.

**Budget position:** $0.22 spent of the $8–40 cloud budget. This plan spends **~$5–9 more** (prioritized ladder below), preserving ≥$4 of the first tranche for week-2 own-data training.

---

## 1. The transfer verdict: what pretraining now buys you (and what it doesn't)

### 1.1 Hard conclusion — no checkpoint trained before Jul 20 will drive your arm

- LeRobot action/observation spaces are **raw per-servo joint positions normalized by that specific arm's calibration file** (min/max recorded during `lerobot-calibrate`). Your arm's offsets don't exist yet, so any policy trained now is trained in *someone else's* action space. Source: https://trelis.substack.com/p/train-an-act-policy-for-an-so-101
- Documented proof that convention mismatches break deployment: the official MolmoAct2-SO100_101 checkpoint requires explicit `joint_signs: [1,-1,1,1,1,1]` and `joint_offsets: [0,90,90,0,0,0]` corrections because it was trained under the pre-v0.5.0 calibration convention — "the arm may move in the wrong direction" otherwise (https://huggingface.co/docs/lerobot/main/en/molmoact2). Note: the `lerobot/svla_*` datasets are mid-2025, i.e. **may carry the old joint convention** relative to your v0.6.0-calibrated arm.
- No community report exists of a hobbyist SO-101 checkpoint working zero-shot on a different SO-101. Issue #1607 (run a pretrained ACT without your own episodes) was closed stale with no supported path (https://github.com/huggingface/lerobot/issues/1607). HF docs treat own-arm fine-tuning as mandatory: "SmolVLA is a base model, so fine-tuning on your own data is required" (https://huggingface.co/docs/lerobot/en/smolvla).

### 1.2 Where pretraining DOES pay

The transfer benefit is already baked into **`lerobot/smolvla_base`** (pretrained on 487 community SO-100 datasets, ~10M frames, ~23k episodes): fine-tuning from it hits **78.3% vs 51.7% from scratch (+26.6 pp)** on SO-100 tasks (https://huggingface.co/blog/smolvla). SmolVLA had **zero** SO-101 pretraining data yet fine-tunes well on SO-101 (https://arxiv.org/html/2506.01844v1) — the winning recipe is "pretrain broadly (already done for you), fine-tune ~50 episodes on your own arm."

There is **no published evidence** that an intermediate fine-tune on someone else's SO-101 dataset (e.g. `svla_so101_pickplace`) before your own-arm fine-tune beats going straight from `smolvla_base`. Given the action-space mismatch, it plausibly teaches the model another arm's offsets — neutral-to-harmful. **Week 2 warm-starts from `lerobot/smolvla_base` directly, never from a rehearsal checkpoint.**

Context for expectations: on a 4-task SO-101 benchmark with 100 own-arm demos, π0.5 hit 56.3% and Wall-X 51.3% vs from-scratch ACT 33.75%, SmolVLA 32.5% (https://arxiv.org/html/2606.08881v1); on ggando's simple cube task, fine-tuned SmolVLA 60–100% and from-scratch ACT 80% (https://ggando.com/blog/smolvla-so101/). On easy single tasks, ACT-from-scratch is competitive — plan to run both in week 2.

### 1.3 Public SO-100/SO-101 datasets worth touching

| repo_id | Size | Cameras | Verdict |
|---|---|---|---|
| `lerobot/svla_so101_pickplace` | 50 ep / 11,939 frames, 30 fps | `observation.images.up`, `observation.images.side`, 480×640 | **Use this one.** SmolVLA-paper SO-101 reference set (5 cube positions × 10 ep). Format **v2.1** — must convert to v3.0 first. |
| `lerobot/svla_so100_pickplace` | 50 ep / 19,631 frames | `top` + `wrist`, 480×640 | Backup. Docs note 25 ep was NOT enough, 50 was. |
| `lerobot/svla_so100_stacking` / `_sorting` | 56 ep / 9 ep | top + wrist | **Skip** — known v2.1 parquet loading errors on current LeRobot, unresolved (https://github.com/huggingface/lerobot/issues/2035); sorting set is a partial upload. |
| `gtgando/so101_pick_place_10cm_*` | 75 clean ep, already v3 | wrist (D405) + overhead (C920) | Best-documented community set; no conversion needed if the primary set fights you (https://ggando.com/blog/smolvla-so101/). |
| `UniDataPro/lerobot-so-101-manipulations` | 20 ep | front/wrist/top | Reference only — small, 3-camera layout doesn't match your rig. |

**Format gotcha (do on the Mac BEFORE renting a GPU):** the `svla_*` sets are LeRobotDataset **v2.1**; LeRobot v0.6.0 trains on **v3.0**. Convert with the v2.1→v3.0 script shipped with the datasets-v3 release (https://huggingface.co/blog/lerobot-datasets-v3), push as `gkienpham/svla_so101_pickplace_v3`, and confirm it loads locally. Expect `Parquet magic bytes not found` / `KeyError`-class failures otherwise. Budget 30–60 min of debugging.

> **UNCERTAIN — verify before running:** the research did not pin down the exact conversion invocation. It is likely a module under `lerobot.datasets` (something like `python -m lerobot.datasets.v30.convert_dataset_v21_to_v30 --repo-id=lerobot/svla_so101_pickplace`), but **check `python -m lerobot... --help` / the datasets-v3 blog post for the real name** before use.

### 1.4 The run ladder (prioritized; stop when budget or time runs out)

vast.ai RTX 4090 rates: ~$0.29–0.45/hr, typical ~$0.39/hr (https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing). Your own anchor: 5k ACT steps = $0.22 all-in.

| Priority | Run | Data | Cost | Why |
|---|---|---|---|---|
| **1** | **SmolVLA fine-tune, 20k steps, batch 64** | converted `gkienpham/svla_so101_pickplace_v3` | ~$2.50–3.50 (~6–8 h on 4090; ggando measured 10.4 h on a 3090) | Full-scale rehearsal of the exact week-2 command, a wandb loss-curve baseline, and a smoke-tested v2.1→v3 workflow. **Will not drive your arm — that's fine.** |
| **2** | **ACT 50k steps on your own cleaned sim dataset** (`gkienpham/sim_clean_v1`, §2.4) | own sim data | ~$1.50–2.20 (extrapolated from $0.22/5k) | Rehearses full-length training profile (checkpoint cadence, convergence shape) + closes the loop with an MPS eval comparing data quality vs `act_dryrun`. |
| 3 (optional) | SmolVLA 5k-step path rehearsal on `sim_clean_v1` | own sim data | ~$1–2 | Verifies `smolvla_base` download, 4090 VRAM fit, and the `--policy.path` (vs `--policy.type`) flag pattern. Expect a weak policy; the goal is pipeline. |
| 4 (optional) | ACT from scratch, 100k steps on the converted public set | public data | ~$0.60–1.35 (~1.5–3 h) | Real-data ACT convergence baseline at 20× the dry run. Skip if time is short. |

**Priority-1 command (after conversion + push):**

```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=gkienpham/svla_so101_pickplace_v3 \
  --batch_size=64 --steps=20000 \
  --output_dir=outputs/train/smolvla_so101_rehearsal \
  --job_name=smolvla_so101_rehearsal \
  --policy.device=cuda --wandb.enable=true \
  --policy.push_to_hub=true --policy.repo_id=gkienpham/smolvla_so101_rehearsal
```

**Do NOT buy:**
- Multi-dataset ACT "pretraining" across public sets — ACT has no cross-embodiment story; each arm's calibrated action space is unique.
- π0/π0.5/GR00T/Wall-X fine-tunes — better benchmark numbers but A100-class VRAM/time blows the budget, and they still need 100 own-arm demos you can't record yet.
- Any run whose goal is a zero-shot-deployable checkpoint. Evidence says it won't work.

**Budget after ladder:** $0.22 + ~$3 + ~$2 (+ optional ~$1–3) ≈ **$5.22–8.22**, leaving room in the $40 cap for week-2 real-data ACT (~$1) and SmolVLA (~$3).

---

## 2. Remaining sim work (the human is the thing being trained)

As of mid-2026, gym-hil still has only three env IDs, all Franka Panda cube-pick: `PandaPickCubeBase-v0`, `PandaPickCubeGamepad-v0`, `PandaPickCubeKeyboard-v0` (https://github.com/huggingface/gym-hil). No SO-101 env exists that gives a drop-in LeRobot recording loop. Since keyboard EE-teleop doesn't resemble leader-arm teleop anyway, sim time targets **operator habits and dataset craft**, not task transfer.

macOS specifics (both documented at https://huggingface.co/docs/lerobot/main/en/il_sim): launch with **`mjpython`**, not `python` — `mjpython -m lerobot.rl.gym_manipulator --config_path env_config.json` — and set `"device": "mps"` in the config. Keep your week-1 `save_episode(parallel_encoding=False)` patch applied (`patches/lerobot-v0.6.0-macos-serial-encoding.patch`) — it's a Python-API parameter, not a config field or CLI flag; the CLI equivalent for `lerobot-record` is `--dataset.streaming_encoding=true --dataset.encoder_threads=2` (§5.1, doc 04 §6.5).

### 2.1 Teleop drills (all rehearsable now)

1. **Slow, smooth, deliberate motion** — jerky demos inflate action variance, the #1 cited ACT failure. Constant-velocity approaches, single-attempt grasps (no hunting near the cube).
2. **Trajectory consistency** — same approach direction and grasp style every episode ("maintain consistent grasping behavior throughout the recordings" — https://huggingface.co/docs/lerobot/main/en/il_robots).
3. **Structured variation** — ~50 episodes, ~10 per object location; vary the *start state*, not the *strategy*.
4. **Episode-control reflexes** — drill until automatic: `→`/`n` = end episode early on success (no trailing idle frames), `←`/`r` = cancel & re-record a botched episode *immediately* (never "keep it, prune later"), `q`/ESC = stop + encode + upload. macOS: keys need Accessibility permission or a **focused terminal** (letter-key fallback works in-terminal).
5. **Reset discipline** — treat `reset_time_s` as part of the job: deliberate start pose every time. Inconsistent resets = inconsistent initial observations = ACT failure mode.
6. **Camera-only rule** — "You should be able to do the task yourself by only looking at the camera images" (HF il_robots). Practice driving from the rendered camera view only — exactly the skill for two 640×480 webcams.
7. **Consistent endpoints** — e.g. cube lifted + held 1 s → `n`, giving ACT a clean terminal distribution.

### 2.2 Dataset-quality rules

- 30 ep minimum for the sim cube task; **50 ep is the real-world pick-place sweet spot** (~80% success reported for simple tasks). Sources: https://huggingface.co/blog/lerobot-datasets, https://www.roboticscenter.ai/learn/record-lerobot-dataset
- Fixed cameras, ≥2 views, stable neutral lighting, 480×640 min; leader arm and your body **out of frame**.
- Descriptive task strings, 25–50 chars ("Pick the red cube and lift it"), never `task1`.
- Kill list: 1–2-frame episodes, failed attempts, episodes >3σ from mean duration, jerky trajectories, inconsistent starts.
- ACT sanity: loss should converge within ~50k steps on wandb; if not, suspect data before hyperparameters.

### 2.3 Inspection workflow (free, do before every paid run)

1. Online visualizer — paste repo_id into https://huggingface.co/spaces/lerobot/visualize_dataset; scrub every episode, watch action traces for spikes.
2. `--display_data=true` streams to rerun live — verify camera keys, framing, action ranges **during** recording.
3. **Prune with v0.6.0 dataset tools** (highest-value new skill to drill):
   ```bash
   lerobot-edit-dataset --repo_id gkienpham/sim_practice_dataset \
     --new_repo_id gkienpham/sim_practice_clean \
     --operation.type delete_episodes --operation.episode_indices "[0,2,5]"
   ```
   Deleting renumbers episodes and recomputes stats automatically (https://huggingface.co/docs/lerobot/using_dataset_tools). **Known bug:** delete fails when `root` is set — use the hub repo_id path (https://github.com/huggingface/lerobot/issues/2316).
4. Tensor check: load the dataset in Python, print `dataset.features`, one frame's image shape/dtype and the action vector — confirm what the model actually sees (lesson from https://www.tinystruggles.com/posts/robotics_gyms_and_experiments/).

### 2.4 Deliverable: `gkienpham/sim_clean_v1`

Record 30–50 clean keyboard episodes applying every rule above, prune to the best 30–40, push as `gkienpham/sim_clean_v1`. This feeds run ladder priority 2.

**Do NOT spend sim days on:** new envs (none exist for this stack), Isaac (needs Linux + RTX), phosphobot (parallel stack — workflow fragmentation), RL/HIL-SERL (different pipeline; revisit post-hardware).

### 2.5 Camera key names — decide once, use everywhere

ACT bakes exact feature names (`observation.images.up` vs `.top`) into the checkpoint; SmolVLA standardizes slot 1 = top-down, slot 2 = wrist (https://github.com/huggingface/lerobot/issues/1763). **Decision: use `top` and `wrist` as your camera keys in every future recording, config, and rollout**, with `top` listed first. Keep 480×640 @ 30 fps (matches all reference datasets and the Shopee cameras).

---

## 3. Physical prep in HCMC (order TODAY — Shopee lead times are 2–3 days)

### 3.1 What's in the box

The order is the **Pro DIY Kit** (buyer-confirmed): 12 servos, 2 driver boards, 5V + 12V PSUs, cables, 4 table clamps, and both arms' 3D printed parts — the complete BOM (reference: Seeed's equivalent kit is $260, https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html; DIY BOM ~$230, https://github.com/TheRobotStudio/SO-ARM100). Still treat the day-1 unboxing (§4, arrival day) as a verification gate: count servos, check leader gear ratios, and test the driver boards before confirming receipt on AliExpress.

### 3.2 Shopping list (order Jul 15)

| Item | Where / price (VND) | USD | Notes |
|---|---|---|---|
| 2× 26 cm USB ring lights with stands (đèn livestream) | ✅ **BOUGHT Jul 16** — 2× "Đèn 26cm + Chân Đèn 2m1" (Phụ Kiện Vu Phat, Shopee), 390,000 total after bundle discount | $15 total | USB, 3 color modes, dimmable, 2.1 m stands. On arrival: verify same model/batch, set both to white + same level, **tape the dials**. |
| A2/A1 self-healing cutting mat or matte desk pad | Shopee, ~100,000–250,000 | $4–10 | Solid mid-tone; not pure white (auto-exposure clipping), not the object colors. |
| Precision screwdriver set (PH0/PH1 for M2×6, PH1/PH2 for M3×6) | ✅ **COVERED** — 115-in-1 precision bit set already owned (109,000, Shopee) | $4 | Bit range covers PH0–PH2 + flathead (support scraper). Caveat: precision handle = low torque; drive the M3×6 screws patiently, don't cam out. |
| Masking tape (băng keo giấy) + colored electrical tape | Electrical: ✅ **BOUGHT Jul 16** — 6-color multipack (29,760, Shopee). Masking tape: ⬜ still to buy, ~10,000 | <$2 | Electrical: red=12V FOLLOWER, blue/white=5V LEADER, yellow=object bands, green/white=camera-port flags. Masking: start-zone markers + light-dial tape (see §3.5). |
| Zip ties 2.5×100 mm ×100 | ✅ **BOUGHT Jul 16** — 100× black (16,000, Shopee) | <$1 | Cable routing along the follower arm. |
| Side cutters (kìm cắt) | ~30,000–60,000 | $1–2.50 | |
| Digital kitchen scale | ~60,000–120,000 | $2.50–5 | Verify task objects stay under ~250 g payload. |
| 4× C-clamps (kẹp chữ C) — optional backup | ~25,000–60,000 each | $1–2.50 ea | The Pro DIY Kit includes 4 clamps; skip unless yours arrive missing/flimsy. |
| ~~Short USB cables for cameras~~ → 2× USB-A(F)→USB-C(M) adapters (Ugreen/Baseus) | ⬜ ~30,000–80,000 each | $2–6 | NOT NEEDED as cables: the bought C920/C270 have captive 1.5 m USB-A cables. Buy the 2 adapters instead as the direct-port fallback if the Orico hub fails the dual-cam bandwidth test (§3.3). Never add extension cables — a documented SO-101 dual-cam failure was a cheap extension (https://hackaday.io/project/204187/log/243773-debugging-dual-camera-vision-system-for-so-101-robotic-manipulation-platform). |

**Task objects (Bách hoá Xanh + Shopee):**

| Object | Price | Role |
|---|---|---|
| 4–6× Mì ly Modern lẩu Thái tôm 67g | ~10,000–12,000 VND each (https://www.bachhoaxanh.com/mi/mi-ly-modern-lau-thai-tom-65g) | **Primary task object** — ~65–70 g, ~9 cm tapered cup, rigid, high-contrast label. Buy identical ones (grasp wear + consistent appearance). |
| 2× Mì ly Omachi xốt bò hầm 113g | ~17,000–20,000 VND | Level-2 object (heavier/taller). |
| 500 ml PET bottles (Aquafina) | ~4,600–4,800 VND/bottle by the case | **Full = 500 g+ = over payload.** Fill to 150–200 ml; wrap a colored tape band (transparent PET is hard at 640×480). |
| Bottle caps | free / craft bags ~15,000–30,000 per 50 | Precision-grasp drills (cap-in-cup, cap sorting) — matches the small gripper jaw. |
| 3–5 cm foam cubes / khối gỗ + silicone muffin cups as drop targets (~20,000–40,000) | Blocks: ✅ **BOUGHT Jul 15** — 25× 3 cm wooden color blocks (108,000, Shopee). Muffin cups: ⬜ | Classic pick-place starter before the noodle cup. |

**Purchase status (as of Jul 16):** ✅ ring lights ×2 + stands, electrical tape, zip ties, wooden blocks, screwdriver set (prior), C920+C270 cameras, ULANZI boom arm, Orico powered hub. ⬜ Still open: masking tape, matte mat, side cutters, kitchen scale, 2× USB-A→C adapters, muffin cups, mì ly cups + PET bottles + caps (BHX run), spare gripper servos + spare driver board (AliExpress — longest lead, order first).

**Total: roughly 1.2–1.8M VND (~$46–70)** excluding the possible ~$260 servo kit.

**If you have 3D-printer access this week**, print a wrist-camera mount now: official STL for 32×32 mm UVC boards at https://github.com/TheRobotStudio/SO-ARM100/blob/main/Optional/SO101_Wrist_Cam_Hex-Nut_Mount_32x32_UVC_Module/stl/SO-ARM101_camera_wrist_mount.stl (+ the Overhead_Cam_Mount in the same `Optional/` tree); community options: https://www.printables.com/model/1531820-modular-camera-mount-for-so-101-arm, https://www.thingiverse.com/thing:7143999. If the Shopee cameras aren't 32×32 boards: zip ties + hot glue on the wrist holder is the standard crude fallback.

### 3.3 Camera rig plan

- **Geometry** (svla-style): fixed **top/front camera** 40–60 cm from workspace center, angled 30–45° down, seeing the whole reach envelope + gripper; **wrist camera** on the follower gripper.
- **Once recording starts, never move the cameras** — policies learn camera geometry implicitly; moving them invalidates the dataset (https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/05-building-workspace.html).
- **USB bandwidth (your known open risk):** 640×480 @ 30 fps MJPG; **one camera per physical port, never two on one hub** (https://www.waveshare.com/wiki/SO-ARM100/101_Record_Dataset). M1 Pro's two built-in ports are separate controllers — one camera per side; put the two servo boards on a hub (serial = tiny bandwidth).
- Enumerate with `lerobot-find-cameras opencv` (macOS backend AVFOUNDATION). Indices can shuffle on replug/reboot — **record which physical port = which index and always use the same ports.** macOS gotcha: an iPhone on the same Apple ID appears as Continuity Camera and can grab index 0 — disable it (iPhone: Settings → General → AirPlay & Continuity → Continuity Camera) or keep the phone away.
- **Test both cameras the day the Shopee package lands — before the arm arrives.** This retires the USB-bandwidth unknown early.

### 3.4 Workspace

- Stable desk, rigid edge ≥2 cm thick for clamps; ~120×60 cm is plenty (reach 35–40 cm). Leader and follower **60–80 cm apart** so your teleop hand never crosses camera view.
- Masking-tape outlines: object start zone, drop zone, follower base footprint. Optional: printed A4 task board (grid + target circles) under clear tape — consistent resets are the cheapest dataset-quality lever (https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/08-operating-so101.html).
- Lighting: close the curtains, run the two ring lights, identical settings every session. HCMC daylight + rainy-season clouds change exposure between episodes — never rely on the window.
- Cable management: zip-tie the servo daisy-chain and wrist-cam cable along the arm, slack at each joint; stray cables in frame are visual noise and snag hazards.

### 3.5 PSU rule (standing safety rule — enforce with tape)

Label both bricks and both DC barrel ends **the moment you unbox**: 5V → "LEADER", 12V → "FOLLOWER" (colored electrical tape). Leader servos are 7.4V variants — **plugging 12V into the leader bus can permanently burn them** (https://wiki.seeedstudio.com/lerobot_so100m_new/). Never swap.

---

## 4. Day-by-day schedule (Jul 15 → arrival)

| Day | Sim / cloud | Physical / admin |
|---|---|---|
| **Jul 15 (today)** | 30–45 min gym-hil teleop fluency, no recording: `mjpython -m lerobot.rl.gym_manipulator --config_path env_config.json` (`PandaPickCubeKeyboard-v0`, `fps: 10`, `device: mps`). Drill `n`/`r`/`q` until reflexive; camera-view-only driving. Then start the **v2.1→v3 conversion** of `lerobot/svla_so101_pickplace` on the Mac (30–60 min debugging budget); push `gkienpham/svla_so101_pickplace_v3`, verify it loads. | Place ALL Shopee/BHX orders (§3.2) — 2–3 day lead times. Print wrist mount if printer access. |
| **Jul 16** | Recording-discipline drill: 10 episodes to a scratch repo (5 start positions × 2), end each on success with `n`, use `r` twice on purpose. Inspect all 10 in the online visualizer + rerun; delete the worst 2 with `lerobot-edit-dataset`. Then **launch cloud Run 1** (SmolVLA 20k on the converted set, §1.4 — 6–8 h, ~$3) and let it run overnight; watch wandb project `so101`. | Clear + measure the desk; plan camera positions. |
| **Jul 17** | Production dataset: 30–50 clean episodes applying §2.1–2.2; prune to best 30–40; push **`gkienpham/sim_clean_v1`**. Review Run 1's loss curve; pull the rehearsal checkpoint. | Cameras likely arrive → **dual-camera USB test immediately** (`lerobot-find-cameras opencv`, note port↔index mapping). |
| **Jul 18** | **Cloud Run A**: ACT 50k steps on `sim_clean_v1` (~$1.50–2.20), wandb `so101`, confirm convergence <50k. Pull checkpoint, eval on MPS (`mjpython -m lerobot.rl.eval_policy --config_path eval_config.json`), log success-rate delta vs `act_dryrun`. | Set up mat, ring lights, tape markers; dry-fit camera positions with the real cameras. |
| **Jul 19** | Optional Run 3 (SmolVLA 5k path rehearsal on `sim_clean_v1`, ~$1–2) and/or Run 4 (ACT 100k on public set, ~$1). While training: load the SO-101 MJCF from https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/README.md in `mjpython -m mujoco.viewer` — internalize joint limits, reach envelope, and the **new (mid-range zero) vs old (horizontal zero) calibration conventions** before real calibration day. | Weigh task objects on the scale; build the A4 task board. |
| **Jul 20 → arrival** | Buffer: re-read `lerobot-record` real-robot flags (`--dataset.episode_time_s`, `--dataset.reset_time_s`; `--resume=true` semantics — see §5.7 flag). Optional: one more 20-episode session on whatever felt weakest. | Pre-stage §5 in a terminal-ready file. Charge nothing else into this window — arrival can be any day Jul 20–25. |

---

## 5. Hardware Day 1 — arrival runbook + copy-paste command sequence

All commands below were verified against the **LeRobot v0.6.0 tag source** except where flagged. Namespacing: follower = `--robot.*`, leader = `--teleop.*`, recording = `--dataset.*`. The old `control_robot.py --control.type=...` syntax is gone.

### 5.0 Unboxing (BEFORE any assembly — this gates a possible $260 order)

1. **Video the unboxing.** AliExpress gives **15 days after delivery confirmation** to dispute (https://news.astools.app/en/blog/aliexpress-buyer-protection-return-policy-2026). Decide within hours, not after assembly week.
2. Inventory against the full leader+follower BOM (https://github.com/TheRobotStudio/SO-ARM100, https://huggingface.co/docs/lerobot/en/so101):
   - **12× Feetech STS3215** — check the gear-ratio label on each body. Follower: 6× **1/345** (12V). Leader: 1× 1/345 (shoulder lift), 2× **1/191** (base pan + elbow), 3× **1/147** (wrist flex, wrist roll, gripper) — all 7.4V. Sort by ratio before assembly; a 1/147 in the follower ruins torque.
   - 2× bus-servo driver boards (Waveshare boards: both jumpers on **B** for USB).
   - 2× PSUs: 5V ~4A (leader), 12V ~2A (follower) + pigtails. **Label immediately (§3.5).**
   - 2× USB-C cables, ~12× 3-pin daisy-chain cables, motor horns, M2×6 + M3×6 screw bags, 4× table clamps.
   - Printed parts: base, base motor holder, shoulder, upper arm, forearm, wrist, motor holders, follower gripper + moving jaw, leader handle/trigger/wrist-roll. Check warping, cracks, and that motor pockets fit an STS3215.
3. **If anything is missing** (not expected — the Pro DIY Kit includes the full BOM — but cross-border QC slips happen): file "item not as described" with the unboxing video within the 15-day window. Worst-case replacement channel: Seeed Pro motor kit (~$260, https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html), VN lead time 1–3 weeks.
4. Authenticity: genuine STS3215 = Feetech branding, 3-pin JST connectors, gear ratio on the label.

### 5.1 v0.6.0 gotchas to hold in your head

1. **`lerobot-record` auto-appends a timestamp to `repo_id`** on every non-resume run: `gkienpham/so101_pickcube` → `gkienpham/so101_pickcube_20260725_141230`. Copy the stamped name from the log — training and resume must use it.
2. **`lerobot-record` no longer does policy eval** — it hard-rejects `eval_`-prefixed names. Use `lerobot-rollout` for deployment. Old tutorials showing `lerobot-record --policy.path=...` are stale.
3. macOS video-encoding crash: **the v0.6.0 defaults are NOT safe.** `parallel_encoding` is a Python-API parameter (`LeRobotDataset.save_episode(parallel_encoding=True)` is the default), not a CLI flag — and `lerobot-record` calls `save_episode()` bare, so the CLI always takes the crash-prone multi-camera process-pool path. This is exactly the `BrokenProcessPool` crash from week-1 sim (DECISIONS.md 2026-07-14; `patches/lerobot-v0.6.0-macos-serial-encoding.patch`). CLI mitigation, **your macOS default on every `lerobot-record` run**: `--dataset.streaming_encoding=true --dataset.encoder_threads=2` (real-time thread encoding, bypasses the post-episode process pool). Python-API paths (the patched sim scripts) keep `save_episode(parallel_encoding=False)`. Full ground truth: doc 04 §6.5.
4. Recording control keys fall back to reading from the **terminal** without macOS Accessibility permission — keep the Terminal window focused.

### 5.2 The command sequence (copy-paste, in order)

```bash
# ---- 0. Environment (do before arrival) ----
pip install -U "lerobot[feetech]"          # feetech extra required for STS3215 bus
hf auth login --token $HUGGINGFACE_TOKEN --add-to-git-credential
wandb login
HF_USER=gkienpham

# ---- 1. Find serial ports (run once per arm; unplug-diff identifies each) ----
lerobot-find-port
# macOS ports look like /dev/tty.usbmodem575E0032081. No driver needed.
# Waveshare boards: both jumpers on channel B. Ports shuffle after replug — recheck each session.
FOLLOWER_PORT=/dev/tty.usbmodemXXXX
LEADER_PORT=/dev/tty.usbmodemYYYY

# ---- 2. Motor IDs (ONCE, writes EEPROM, BEFORE assembly, one motor at a time) ----
# VOLTAGE CHECK FIRST: 12V PSU on follower board, 5V PSU on leader board. Never swap.
lerobot-setup-motors --robot.type=so101_follower --robot.port=$FOLLOWER_PORT
lerobot-setup-motors --teleop.type=so101_leader  --teleop.port=$LEADER_PORT
# Prompt order: gripper=ID6 -> wrist_roll=5 -> wrist_flex=4 -> elbow_flex=3
#   -> shoulder_lift=2 -> shoulder_pan=ID1. Each motor plugged in ALONE, not daisy-chained.
# Baudrate is set to 1,000,000. Errors = check power, USB, 3-pin cable seating.
# After the last motor: daisy-chain all six, connect motor 1 to the board, then assemble.

# ---- 3. Calibrate (after assembly) ----
lerobot-calibrate --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower_arm
lerobot-calibrate --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=leader_arm
# Procedure: move all joints to MID-RANGE, press Enter, then sweep EACH joint full range.
# JSONs land at ~/.cache/huggingface/lerobot/calibration/{robots/so101_follower/follower_arm.json,
#   teleoperators/so101_leader/leader_arm.json}
# Redo: re-run with the same id (overwrites). The id KEYS the calibration —
# use follower_arm / leader_arm in every later command or you silently trigger recalibration.

# ---- 4a. Teleop WITHOUT cameras (~2 min: validates calibration + latency) ----
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower_arm \
  --teleop.type=so101_leader  --teleop.port=$LEADER_PORT  --teleop.id=leader_arm

# ---- 4b. Camera indices (iPhone Continuity Camera OFF; note port<->index mapping) ----
lerobot-find-cameras opencv

# ---- 4c. Teleop WITH both cameras (fill real indices; keys are top/wrist forever) ----
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower_arm \
  --robot.cameras="{ top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader_arm \
  --display_data=true
# rerun window opens; watch for dropped frames = USB bandwidth problem (separate ports!).

# ---- 5. First real recording (5 shakedown episodes; NOT the production dataset) ----
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=follower_arm \
  --robot.cameras="{ top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=leader_arm \
  --display_data=true \
  --dataset.repo_id=gkienpham/so101_pickcube \
  --dataset.num_episodes=5 \
  --dataset.single_task="Pick up the cube and place it in the box" \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2
# streaming_encoding=true + encoder_threads=2 is the macOS default (§5.1 gotcha 3 / doc 04 §6.5):
# the bare CLI path uses the multi-camera process-pool encoder that crashed in week-1 sim.
# Watch the FIRST save_episode complete without crashing — that was the exact sim failure point.
# REMEMBER: the hub repo becomes gkienpham/so101_pickcube_<timestamp>. Copy the stamped
# name from the log. Inspect all 5 in https://huggingface.co/spaces/lerobot/visualize_dataset
# before recording anything at scale.
```

Day-1 success criteria: 12 motors ID'd, both arms calibrated, teleop latency acceptable, both cameras streaming at 30 fps in rerun, 5 episodes on the Hub and visually sane. Production 50-episode recording and week-2 training (ACT ~$1, SmolVLA from `lerobot/smolvla_base` ~$3) come after.

### 5.7 UNCERTAINTY FLAGS — verify these before relying on them

| Item | Status |
|---|---|
| v2.1→v3.0 dataset conversion command | **Unverified exact invocation** — confirm module name from https://huggingface.co/blog/lerobot-datasets-v3 before Day-1 (Jul 15) work. |
| `lerobot-rollout` syntax for deploying a policy on the real arm | **Not verified in this research** — the v0.6.0 entry point exists, but check `lerobot-rollout --help` before week-2 eval. |
| `--resume=true` semantics on `lerobot-record` | **RESOLVED — verified against v0.6.0 source** (`lerobot_record.py`, `LeRobotDataset.resume()`): `num_episodes` = *additional* episodes this session; resume **requires** `--dataset.root` (hard `ValueError` without it); resume does NOT re-stamp, so pass the timestamp-stamped repo_id. See doc 04 §7 step 7 for the exact invocation. |
| gym-hil record mode with a null/throwaway repo_id | "If supported" per research — use a scratch repo_id if null isn't accepted. |
| SmolVLA rehearsal (Run 1) camera-key mismatch | `svla_so101_pickplace` uses `up`/`side`, your rig will use `top`/`wrist`. Harmless for the rehearsal (SmolVLA is name-agnostic, and you won't deploy this checkpoint), but do NOT resume/eval an ACT checkpoint across differing keys without renaming features. |
| Whether the sim eval entry point is `lerobot.rl.eval_policy` vs `lerobot-eval` for the gym-hil task | Both appear in docs/research; you used the `mjpython -m lerobot.rl.eval_policy --config_path` form successfully in week 1 — stick with it, confirm before Run A eval. |

---

## Sources

Pretraining/transfer: https://huggingface.co/docs/lerobot/en/smolvla · https://huggingface.co/blog/smolvla · https://arxiv.org/html/2506.01844v1 · https://arxiv.org/html/2606.08881v1 · https://ggando.com/blog/smolvla-so101/ · https://trelis.substack.com/p/train-an-act-policy-for-an-so-101 · https://huggingface.co/docs/lerobot/main/en/molmoact2 · https://huggingface.co/datasets/lerobot/svla_so101_pickplace · https://huggingface.co/blog/lerobot-datasets-v3 · GitHub issues #1763, #1607, #2259, #2035, #1592 · https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing

Sim curriculum: https://github.com/huggingface/gym-hil · https://huggingface.co/docs/lerobot/main/en/il_sim · https://huggingface.co/docs/lerobot/main/en/il_robots · https://huggingface.co/blog/lerobot-datasets · https://huggingface.co/docs/lerobot/using_dataset_tools · issue #2316 · https://huggingface.co/spaces/lerobot/visualize_dataset · https://www.tinystruggles.com/posts/robotics_gyms_and_experiments/ · https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/README.md · https://www.roboticscenter.ai/learn/record-lerobot-dataset

Physical prep: https://github.com/TheRobotStudio/SO-ARM100 · https://huggingface.co/docs/lerobot/en/so101 · https://huggingface.co/docs/lerobot/cameras · https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html · https://www.waveshare.com/wiki/SO-ARM100/101 · https://www.waveshare.com/wiki/SO-ARM100/101_Record_Dataset · https://hackaday.io/project/204187/log/243773-debugging-dual-camera-vision-system-for-so-101-robotic-manipulation-platform · https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/05-building-workspace.html · https://news.astools.app/en/blog/aliexpress-buyer-protection-return-policy-2026 · https://www.bachhoaxanh.com/mi/mi-ly-modern-lau-thai-tom-65g · https://www.binai.vn/products/ring-light-26cm · https://www.printables.com/model/1531820-modular-camera-mount-for-so-101-arm
