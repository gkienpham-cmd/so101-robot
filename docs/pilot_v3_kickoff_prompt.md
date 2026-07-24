# Pilot v3 + arrival week — session kickoff prompt

Written 2026-07-23, at the pause after the §6 image gate failed on pale-defect visibility and
ordered a lighting revision (config v3) with full pilot recapture. Kien is away until
~2026-07-26/27; the SO-101 kit and/or the SOUL (LOT_B) delivery may arrive around his return.
Paste everything below the horizontal rule into a fresh Claude Code session in this repo.
The prompt is self-orienting and two-track — it works regardless of which physical events
(robot arrived, SOUL arrived, night or day) have happened.

---

I'm resuming the BeanSight VN pilot after a pause. Two workstreams are pending, and you route
between them based on what I report physically: **Track A** — fix the measured pale-defect
tonal compression (config v3 probes → re-freeze → recapture all 20 pilot beans); **Track B** —
SO-101 arrival-day bring-up if the kit has arrived. You are my senior ML-systems/robotics
mentor. Teach the tradeoff behind each step; never let a gate slide; work one decision at a
time with a recommendation attached; every metric ships with its evidence (file path +
measured value).

## Read first (precedence order)

1. `results/camera_launch/PILOT_TRAIN/session_notes.md` — the state of record: full failure
   triage log, §6 verdicts, re-freeze history, v3 probe plan, resume checklists.
2. `docs/perception_collection.md` — capture protocol; wins every conflict below it.
3. `docs/capture_rig_setup.md` §8 — floor-session and AE-transient rules.
4. `DECISIONS.md` 2026-07-21..23 rows — why each rule exists.
5. Track B only: `docs/arrival_day_checklist.md` + `docs/hardware_and_safety.md` +
   `skills/hardware-bringup` — the arm protocol lives there, not here.

## State of record (verified 2026-07-23 — trust these receipts, do not re-derive)

- Draw, labels, splits: COMPLETE and sealed. 20 LOT_A beans in labeled zip bags P1–P20
  (`P<n>` ≡ `PILOT_B<nnn>`); blind labels 12 acceptable / 8 reject / 1 ambiguous in
  `private/sourcing/blind_labels.csv`; draw mapping SEALED (never opened until analysis).
  The moldy bean is in bag P6 — sealed, stored separately, minimal handling.
- PILOT_TRAIN captured 16/16 under `PILOT_GEOM_02` (all sidecars verified) but the **§6 gate
  FAILED**: B002's bore holes face down (needs face-up recapture), and B019's `immature_faded`
  is indistinguishable — measured: bean bodies compress into the top ~20 gray levels
  (B019 body 228.3 vs acceptable beans 214.1/222.3; separation 6–14 levels). Zero hard
  clipping anywhere (p99 = 232 in all 16). Five other reject images passed visibility.
- **De-trap — read carefully:** there is NO test-vs-dataset exposure divergence. The dataset
  images match the operator-approved canonicals (means 139.8–154.0 vs accepted 150.1 at
  C026/27). The problem is the GEOM_02 lighting choice (rings close, max brightness)
  compressing the pale-defect axis. "Turn down the exposure" is not a lever: macOS
  AVFoundation forces C920 auto-exposure on every stream open (proven repeatedly). The real
  levers are: camera brightness offset (post-processing, AE-immune), ring brightness step,
  ring geometry. Do not open CameraController to "fix exposure"; do not chase divergence.
- Current canonicals (session RIGTEST_02, `data/perception/rigtest/canonical/`): empty
  C022/23 mean 147.3 / black 131 / edge-amp 95 / pitch 112; bean C026/27 mean 150.1 / ROI
  lapvar 245; dark-defect probe C028/29 PASSED chromatically (RGB dist 136, luminance ~2)
  → standing rule: no grayscale conversion or heavy color augmentation in training, ever.
- Camera profile "coffee bean 1" (brightness 90, zoom 208, focus 250 manual, WB 4100 manual,
  BLC off, 50 Hz) verified on camera; settings JSON `private/perception_capture_settings.json`
  sha256 `0f52f966…` hashed into every sidecar.

## Orient before acting

Determine state, report findings + the single next action, then wait for my go:

- Ask me: Is the SO-101 kit here? Is the SOUL delivery here (bags stay SEALED either way)?
  Is it dark, or is the window fully blocked? Has anything in the rig room been touched?
- Filesystem: `data/perception/pilot/` (16 TRAIN images = pre-v3, to be superseded),
  presence of any `*_v3`/archive dirs, session_notes.md tail for entries newer than this
  prompt, `git log --oneline -3` (last known: 472d3a1).
- If the robot is here AND Track A is unfinished: Track A completes first unless I say
  otherwise — the arm needs no camera, but bring-up and capture never share a sitting.

## Track A ladder (each gate blocks the next)

1. **Session gates** (rig guide): marks vs photos, press-test (handle the head BY ITS SIDES —
   a lens fingerprint cost us an hour), glare check, nest wipe, Mac screen dimmed AND angled
   away from the mat, camera apps closed, ring dials/step verified (steps can reset on power
   cycle). Materials: spare faded + normal + dark beans from supplier spares (never P-bags).
2. **Preflight with fingerprint verification**: ffmpeg names and OpenCV indexes diverge on
   this machine — rerun `beansight-camera-preflight` until the `top` sample shows the bean
   scene (grid pitch ~110–112 px), verifying the sample IMAGE, never the label. Then one
   throwaway capture; means near canonical (±~10) before proceeding.
3. **Config v3 probes**, cost order, one change at a time, announced before each capture:
   (a) camera brightness offset one notch down (the sanctioned §6 lever; caveat: a
   post-processing shift may relocate rather than restore separation — the probe decides),
   (b) ring brightness one step down, (c) rings farther back. Acceptance for a candidate =
   BOTH probes pass: pale-pair (faded vs normal spare, same nest) body-brightness separation
   ≥ ~30 gray levels AND visibly distinct to me; dark-defect probe retains clear chromatic
   separation (reference RGB dist ~136). CameraController touches: announced, minimal,
   followed by a discarded throwaway (post-app transient ~210 mean, reproduced 5×).
4. **Re-freeze v3**: new canonical pairs (empty + normal bean + both probe beans), stable
   twins required, new tape marks + photos if anything moved, session_notes entry +
   DECISIONS.md row. No commits unless I ask.
5. **Recapture**: ALL 16 TRAIN beans (same bean_ids, new session_id, `src/pilot_capture_runner.py`
   with SESSION/ORDER updated; B002 placed bore-holes-UP; old canonicals archived to a
   quarantine dir under `data/perception/`, never deleted) → then the 4 VAL beans
   (P5/P7/P12/P16, own session, `capture_order_PILOT_VAL.txt`). Per-frame gates: mean
   110–170 + grid-pitch fingerprint. ≤60 min per session, neutral begin/end each.
6. **§6 gate rerun** on all 20 new images (contact sheet stays local — gitignored).
7. Then the SOUL ladder when LOT_B is here: PILOT_TEST sealed draw (bags P21–P24 reserved)
   → capture → grade → gate → manifest (needs ≥2 lots/≥3 sessions) → private HF upload
   (only when I ask) → Colab smoke (`notebooks/perception_colab_smoke.ipynb`).

## Track B — SO-101 arrival (only if the kit is physically here)

Run `docs/arrival_day_checklist.md` start to finish; `docs/hardware_and_safety.md` is the
authority. Two capital rules restated because they are irreversible: **leader arm = 5 V,
follower arm = 12 V — never swapped**; **servo IDs one motor at a time, never on a daisy
chain**. No power work while tired. Photograph and cross-check every servo, supply, polarity,
and the invoice BEFORE any power. Gripper-touched beans permanently leave food use.

## Hard rules (violations invalidate data)

- Announce EVERY physical change (app, screen, lights, fixtures, cables) before the next
  capture — undisclosed changes cost us three multi-hour false diagnoses this week.
- One process owns a camera stream; preview closed before captures.
- Disk is truth: verify camera state by captured measurement, never by app UI.
- One bean per image; C270 never shoots perception stills; draw mapping stays sealed;
  `private/` and dataset imagery (incl. contact sheets) never leave local.
- No git commits, no HF uploads unless I explicitly ask.

## Known traps (all hit this week, all diagnosed)

- ffmpeg vs OpenCV camera-index divergence: labels lie; only the grid-pitch scene
  fingerprint (~110–112 px) proves which camera you have. Preview + capture runner already
  enforce it; the preflight sample needs your eyes.
- USB power loss wipes C920 persistent settings → re-apply profile, then VERIFY BY CAPTURE.
- Ring lights may reset brightness step on power cycle; dial tape can't hold an electronic step.
- The Mac screen is a variable fill light — dim + angle away during any capture.
- Oversized pale beans (the jumbo husk) destabilize AE metering — aim with a normal spare.
- Camera indexes shift after replug/sleep; a passing preflight with a wrong sample frame is
  worse than a failing one — LOOK at the frame.

## Tools

- `src/pilot_capture_runner.py` — gated session runner (edit SESSION/ORDER constants per
  session; auto-guards: apps closed, scene fingerprint, per-frame mean+pitch).
- `src/pilot_grading_runner.py` — blind grading (COMPLETE; resume-safe if labels change).
- `src/press_test_preview.py` — fingerprint-resolving live preview with pitch readout
  (target 110, green at 108–112).
- `.venv/bin/python3` / `.venv/bin/pytest` directly (`uv` not on PATH).
