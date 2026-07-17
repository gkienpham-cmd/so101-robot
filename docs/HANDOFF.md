# HANDOFF.md — Project status and roadmap of record

Written 2026-07-16 and updated 2026-07-18. This is the single
"where are we and what happens next" document. If it conflicts with an older doc, this one wins;
if it conflicts with [AGENTS.md](../AGENTS.md) on safety or evidence rules, AGENTS.md wins.

## 1. Status by workstream

| Workstream | Status |
|---|---|
| **A. BeanSight VN flagship** | **Active.** Software layer complete: typed records, confidence-gated routing, unarmed-by-default controller, camera preflight/attestation, pinned dataset QA, gated ACT config generation, frozen eval protocol, Wilson-CI metrics, trial logging/comparison, 19 deterministic test modules, green CI. The 30-minute C920+C270 direct-port soak passed on Jul 16. **The physical arm has not arrived** (expected ~Jul 19–25, 2026). No physical success rate is claimed anywhere, deliberately. |
| **B. Camera & accessory sourcing** | **Complete.** C920 + C270 pair bought (~$88, in transit at handoff), Ulanzi LS08 boom arm, Orico PW7U powered hub, 25 wooden blocks. Peripherals ≈ 3,435,151₫ (~$132). Full research in [CAMERA-RESEARCH-REPORT.md](../CAMERA-RESEARCH-REPORT.md). Still open to buy: white tray + reject cups, spare M3 screws, high-CRI lamp (deferred to coffee phase). |
| **C. Post-flagship caps and bottles** | **Software groundwork complete; physical work gated.** Named recording profiles, fail-still material routing/controller records, a grouped spectral-classifier evaluator, disabled local route profiles, ACT config gating, and a capped Isaac/Vast experiment contract are implemented. Execution starts only after the BeanSight frozen result. See [transfer_training_roadmap.md](transfer_training_roadmap.md). |
| **D. Vietnam applications idea bank** | **Parked backlog.** 12 adversarially-scored concepts remain in [vietnam_applications.md](vietnam_applications.md). They do not alter the flagship schedule. |

## 2. What is proven vs. what is untested

**Proven end-to-end (Week 1, $0.22 spent):**

```
sim teleop (gym-hil, mjpython) → LeRobot v3.0 dataset → HF Hub (gkienpham/sim_practice_dataset)
→ vast.ai RTX 4090 → lerobot-train ACT 5k steps (loss 6.4 → ~0.7, W&B project so101)
→ checkpoint → HF Hub (gkienpham/act_dryrun) → M1 Pro MPS → forward pass ✓
```

Four failures were hit and fixed on the way (details in [RETRO.md](../RETRO.md)): LeRobot extras
breakage, record-config schema drift (source is the spec), the macOS Accessibility silent-keyboard
trap, and the parallel-encoding `BrokenProcessPool` crash (fix versioned in `patches/`).
This was a Franka/Panda `gym-hil` plumbing dry run, not an SO-101 dynamics or sim-to-real result.

**Proven physical camera gate:** C920=`top` and C270=`wrist` ran concurrently on separate direct Mac
ports for 30 minutes at 640×480/30 with zero failed reads. Effective rates were 29.91 and 29.98 fps;
the canonical report is `results/camera_preflight/camera_preflight.json`. This qualifies the
direct-port camera topology only.

**Untested by design — sim cannot reach these (Week-2 carry-over risks):**

- Real-arm calibration and one-at-a-time motor ID assignment.
- macOS USB serial behavior with the real controller boards.
- Two physical cameras plus both controller boards through one powered hub (four-device USB load).
- The parallel-encoding crash may resurface in the real-arm record path (workaround known).
- Teleop latency/feel — no sim proxy for leader-follower mechanics.

## 3. Roadmap with hard gates

Follow [runbook.md](runbook.md) step numbers for every operational item. Each phase's gate must
pass before the next phase spends money or motion.

### Phase 1 — Pre-arrival (NOW, days until the kit lands)

1. **Complete Jul 16:** the 30-minute dual-camera direct-port soak passed
   (`beansight-camera-preflight`, runbook §4). Re-resolve semantic identity after a replug/reboot and
   validate the final mounted views before recording; do not repeat the pre-arrival soak now.
2. Freeze workcell geometry: nest, lamp, cup, bins, five-position block grid, millimetre drawing.
3. Roaster interview + obtain two Robusta lots with **blind labels** (≥50 visible rejects). Phone
   and in-store scripts are in [data_and_labeling.md](data_and_labeling.md).
4. Train the color baseline and ResNet-18 perception model on captured bean images
   (`beansight-train-perception`). Pre-arrival manipulation training is explicitly ruled out — no
   checkpoint trained before arrival can drive this arm (calibration/geometry/gripper missing).

### Phase 2 — Hardware week (~Jul 19–25)

1. Film the unboxing; photograph and cross-check everything **before any power** (hardware_and_safety.md).
2. Servo IDs one at a time → assemble → calibrate → **back up calibration files**.
3. Teleoperate without cameras, then with both. Record 5 smoke episodes, inspect the first save.
4. Record 50 wooden-block episodes over the five-position grid; train the bring-up ACT baseline.
5. **GATE — 20-grasp bean test** with explicit branch logic:
   - **≥16/20:** proceed to Phase 3 as planned.
   - **12–15/20:** add the indexed nest + compliant/high-friction fingertips, repeat once.
   - **<12/20 after one redesign:** pivot manipulation to coffee sample cups/sachets and keep bean
     vision as a separately evaluated contribution. Do not silently continue.

### Phase 3 — Coffee data and model week

1. Capture 300–500 physical beans (≥50 visible rejects, ≥2 lots), one `bean_id` per bean; splits
   never share a bean or capture session; test lot never appears in training.
2. Record 50–75 fixed-nest demonstrations with small controlled offsets.
3. **GATE — `beansight-dataset-qa` passes** (all six action dims nonzero variance, no swapped
   cameras/NaN/Inf) before any upload or GPU rental. Record the immutable HF revision.
4. Train ACT: batch 8, ~5 data epochs (`steps = ceil(frames/batch) × 5`), stop on NaN/Inf or flat
   loss at ~1k steps. Top up ~$10 vast.ai credit before this week (balance $8.78).

### Phase 4 — Integration and evaluation week

1. Connect the thresholded classifier to the **unarmed** `BeanSightController`; threshold chosen on
   validation data, never on the frozen trial set.
2. Run the frozen protocol ([evaluation_protocol.md](evaluation_protocol.md)): ≥30 reject trials +
   ≥20 acceptable no-motion trials; report perception/approach/grasp/transfer/placement/end-to-end
   with Wilson 95% CIs, latency median/p95, and one failure code per failed trial.
3. **One allowed iteration:** add 10–25 demos targeting the largest failure category, retrain once,
   repeat the identical protocol, present before/after via `beansight-compare`.
4. If ACT <30%: fix calibration/geometry/demos/scope, not the model. If still <40% after the
   iteration: narrow the task and publish the negative result honestly.

### Phase 5 — Portfolio, then gated transfer work

1. Gripper fingertip DOE (`beansight-gripper-summary`) + publish singulation-fixture dimensions.
2. Optional upright-cap transfer test — **only after** the flagship eval is frozen. ACT learns
   grasp-to-handoff; routing and bin transport remain separate.
3. Standalone PET/HDPE/PP/unknown sensor gate — **before** any bottle motion is driven by a material
   prediction. Failure remains a publishable sensing result and stops integration.
4. Clean single-bottle transfer — waypoint baseline first; ACT only if measured pose variation is
   the binding failure.
5. Optional SmolVLA — **only if** ACT >40% on the 20 frozen trials (configs/train_smolvla.json).
6. Publish: tagged GitHub release → exact HF dataset/policy revisions, W&B run, experiment
   manifest, aggregate JSON, hero video (60–90 s) + technical video (3–5 min), both including
   failures. Scripts and required visuals: [execution_and_portfolio.md](execution_and_portfolio.md).

## 4. Open design gaps (think about these first)

From [CAMERA-RESEARCH-REPORT.md](../CAMERA-RESEARCH-REPORT.md) §9 — known-unsolved problems a new
agent can add the most value on:

1. **Detector→policy handoff.** How the C920 classification result translates into where/how ACT
   is triggered is still hand-waved; the current design sidesteps it with a fixed one-bean nest.
2. **End-effector for 8–12 mm beans.** The stock gripper is unproven at bean scale; fingertip
   material/geometry DOE is planned but undesigned.
3. **Singulation.** Getting one bean into the nest repeatably is unsolved (currently manual).
4. **Dataset as a first-class deliverable.** The labeled Vietnamese Robusta defect dataset may be
   the most reusable artifact; card, license, and split design deserve real effort.
5. **Metrics decomposition.** Keeping perception, grasp, placement, and end-to-end numbers cleanly
   separable in the published story.
6. **Sub-$300 material sensing.** The DB2.3-derived fixture is an early prototype. Its parts,
   stability, transparent/black-plastic behavior, and held-out PET/HDPE/PP performance remain
   physically untested. The software gate deliberately allows this path to fail.

## 5. Budget state (2026-07-16)

- Cloud: **$0.22 spent**, vast.ai balance **$8.78**; projected total $9–14; top up ~$10 before
  Phase 3. Rules: justify every run, 5k-step validation first, destroy instances, log in
  [COSTS.md](../COSTS.md).
- Hardware: arm paid (in transit); peripherals ~$132 paid. Small open buys listed in §1.

## 6. Where everything lives

- **This branch/main** — the flagship repo (you are here).
- `research/bottle_cap_sorting/` (on main) — the salvaged bottle-cap plastic-sorting deep research
  (223 claims, 27 verdicts, its own HANDOFF/RESUME docs). Optional post-flagship material; the
  original working branch was `bottle-cap-sorting-vision-eebb2c`.
- `src/beansight_vn/material_*.py`, `configs/material_sensor.json`, and
  `docs/material_sensing_protocol.md` — the post-flagship sensing and fail-still routing contracts.
- `configs/isaac_vastai_spike.json` — disabled, capped cloud-simulation experiment; never part of
  arrival-day bring-up.
- Git branch `so101-vietnam-applications-ad547b` — raw research state behind
  vietnam_applications.md (research-resume file, pre-arrival plan, arrival guide drafts).
- Git branch `robotic-arm-camera-research-15819e` — camera research working branch
  (vast.ai dry-run notes, camera_check.py prototype).
- **Gitignored local dirs** (parent repo only, private on purpose): `private/` (strategy,
  receipts, contacts), `logs/`, `videos/`, `CLAUDE.md` (superseded by AGENTS.md + AGENTS.local.md).

## 7. Tips for the incoming agent

- Read [AGENTS.md](../AGENTS.md) first, then `AGENTS.local.md` if present — safety rules and the
  evidence standard there are non-negotiable and repeated in every relevant instruction you give.
- Before executing a hardware, recording, training, or evaluation task, open the matching playbook
  in [skills/](../skills/README.md).
- Run `pytest` and `ruff check .` before and after any code change; CI enforces both.
- Never write anything into `results/` that a real run didn't produce.
- The runbook's numbered steps are the operational contract — don't improvise around a gate, and
  when LeRobot docs disagree with the pinned v0.6.0 source, trust the source.
- Keep DECISIONS.md (one line per choice), COSTS.md (every GPU dollar), and RETRO.md (weekly)
  current — the final writeup is reconstructed from them.
- The owner values being taught: explain the binding constraint and the failure mode a choice does
  NOT fix, not just the command to run.
