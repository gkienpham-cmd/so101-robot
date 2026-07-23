# PILOT_TRAIN session notes — 2026-07-22 (night session, ~00:35–01:45 +07)

## Pre-session gate results

- Marks check, glare check, nest wipe: PASS (operator, ~00:40).
- Rigidity press-test: PASS (live OpenCV preview, framing returns exactly, no oscillation).
- No camera replug since preflight (results/camera_launch/PILOT_TRAIN/camera_preflight.json,
  PASSED 2026-07-21 23:46 +07; no reboot since — boot 2026-06-26).
- Settings JSON sha256 0f52f966f2420ffa939b4c3ab39a738b1c9506a825e20e8cbaead299cc741d72 (matches frozen).

## Throwaway/health gate: FAILED first, then PASSED after triage

Throwaway captures (all RIGTEST_02, discarded by construction, in
data/perception/rigtest/canonical/):

| frame | mean | corner lapvar TL/BR | black floor | note |
|---|---|---|---|---|
| B011 (reference) | 127.3 | 91 / 340 | 55 | frozen-config reference |
| C001 | 170.9 | 18 / 92 | ~93 | FAIL — washed out, soft |
| C002 | 171.4 | 18 / 95 | — | identical → stable broken state |
| C003 | 210.0 | 4 / 9 | — | post-CameraController transient, 5th reproduction |
| C004 | 171.0 | 18 / 94 | 93 | after 1st profile-apply attempt: unchanged |
| C005 | 149.4 | 41 / 155 | 75 | post-Photo-Booth settling frame |
| C006 | 170.9 | 19 / 97 | 93 | control: nothing changed → identical |
| C007 | 126.4 | 81 / 171 | 54 | PASS — after 2nd (effective) profile apply |

Grid pitch 110 px and phase constant throughout → no physical camera movement, no zoom change.
BR lapvar 171 vs 340: crops visually identical; Laplacian variance difference attributed to
AE gain/noise texture, not optical blur.

## Root cause (confirmed by controlled state change)

Operator manual-exposure experimentation in CameraController earlier in the evening left
persistent camera-side settings (brightness offset et al.) off the frozen "coffee bean 1"
profile. First profile-apply attempt did not take effect (C004 unchanged). Second apply
(operator, ~01:20, announced after the fact) restored the frozen state; the immediately
following stream converged to mean 126.8 and C007 passed all criteria.

Wrong hypotheses eliminated en route (Claude): lens smudge from press-test handling; extra
room light. Both fit the histogram signature (lifted shadows, pinned highlights) but were
refuted by recovery without wipe/lighting change. Operator's "camera-side exposure state"
instinct was directionally correct; the specific mechanism is the AE-immune persistent
brightness offset, not AE itself (exposure remains hardware-auto per frozen state).

## Session paused ~01:50 +07 (operator sleep) — clean stopping point

All pre-capture gates passed; sealed draw NOT started (draw_mapping.csv does not exist);
zero pilot captures, zero neutral frames. No interrupted state.

Prepared and durable:
- `private/sourcing/draw_plan_20260722.csv` (seed 1978128820), `capture_order_PILOT_TRAIN.txt`,
  `capture_order_PILOT_VAL.txt` — sealed, do not reopen except to execute the draw.
- Runner scripts copied to `src/pilot_draw_runner.py`, `src/pilot_capture_runner.py`,
  `src/press_test_preview.py` (uncommitted).

Resume checklist for the next session (all session-start gates apply fresh):
1. If the Mac rebooted or any camera was replugged/deep-slept: rerun beansight-camera-preflight
   and visually confirm the top sample frame.
2. Marks check vs photos, press-test (handle head by its sides), glare check, nest wipe.
3. If capturing in DAYTIME: window must be fully blocked; rings remain the only light source.
   Night capture avoids this entirely.
4. One throwaway RIGTEST_02 capture; mean must be 110–170 near reference 127.3.
5. Then: sealed draw (src/pilot_draw_runner.py) → PILOT_TRAIN capture
   (src/pilot_capture_runner.py). CameraController/Photo Booth stay closed; any touch is
   announced and followed by a discarded throwaway.

## Lighting re-freeze — 2026-07-23 ~00:45 +07 (PILOT_GEOM_02)

Operator moved both ring stands closer at max brightness (ergonomics/stability) and elected to
re-freeze the capture configuration around the new lighting rather than restore the old marks.
Camera profile untouched. Old references (RIGTEST_B011 bean-scene, RIGTEST_C007 empty-scene)
are SUPERSEDED for operating-point comparison. All pilot sessions use geometry_id
PILOT_GEOM_02 and the new ring-feet tape marks (photographed).

New canonical references (data/perception/rigtest/canonical/, session RIGTEST_02):

| role | frames | mean | pitch | black floor | sharpness | notes |
|---|---|---|---|---|---|---|
| empty scene | C022/C023 | 147.3 | 112px | 131 | lapvar 92, edge amp 95 | stable ±0.2, no luminance hotspots, clip 0% (gray) |
| bean scene | C026/C027 | 150.1 | 112px | 112 | ROI lapvar 245 | normal bean, sharpest of night |
| dark-defect probe | C028/C029 | 143.2 | 112px | 115 | ROI lapvar 270 | PASSED — see below |

Dark-defect probe finding: bean/mat separation is ~2 gray levels in LUMINANCE but 135.9 in
RGB euclidean distance (mat teal B186/G173/R10 vs bean neutral ~128; red channel alone
differs by ~116). The pre-declared black-defect-vs-dark-mat risk is REDUCED under the new
brighter mat rendering, but the separation is almost entirely chromatic.

**STANDING TRAINING RULE (from probe):** no grayscale conversion and no aggressive
hue/saturation augmentation anywhere in the perception training path — chromatic separation
is what makes dark defects visible on this background. Check configs/perception.json
transforms before any training run.

Session-start gate additions learned tonight (add to rig guide at next doc pass):
- Operator Mac screen: dimmed and angled away from the mat during capture (variable fill
  light; caused capture-to-capture instability).
- Ring lights: brightness step is part of the frozen config; verify step, not just dial tape,
  after any power cycle.
- ffmpeg vs OpenCV camera-index divergence (discovered tonight): preflight sample frames MUST
  be visually/fingerprint verified every run; press_test_preview.py and pilot_capture_runner.py
  now resolve/verify the camera by grid-pitch scene fingerprint, never by name or stored index
  alone.
- Oversized/atypical beans (jumbo white husk) destabilize AE metering — aiming/tests use
  normal-sized spares.

## PILOT_TRAIN capture — COMPLETE & VERIFIED (2026-07-23, window 17:37:51Z → 18:01:01Z = 23.2 min)

16/16 beans captured in the predeclared randomized order, zero gate failures:
- All sidecars: session PILOT_TRAIN, lot LOT_A, geometry PILOT_GEOM_02, frozen settings sha
  0f52f966…, correct per-image sha256.
- Health: means 139.8–154.0 (window 110–170), grid pitch 110–112 px every frame, ROI Laplacian
  140–400 (bean-dependent).
- Neutral begin/end drift: 2.6 mean gray levels; pitch 112→110 (quantization-level).
- P5/P7/P12/P16 correctly absent — they are the predeclared PILOT_VAL set.

Next in pipeline: (1) blind grade at a later sitting, shuffled order over all 20 LOT_A beans,
eight-type vocabulary, mapping stays sealed; (2) §6 manual image gate (contact sheet);
(3) PILOT_VAL session with full session-start gates; (4) on SOUL arrival: PILOT_TEST →
manifest → private HF (on request) → Colab smoke.

## Paused 2026-07-23 ~01:25 +07 — resume point: BLIND GRADE

Capture night fully closed: draw sealed, PILOT_TRAIN 16/16 verified, re-freeze documented.
Blind grade NOT started (blind_labels.csv still header-only — zero rows). Prepared and waiting:
- `src/pilot_grading_runner.py` (validated) + sealed order in
  `private/sourcing/grading_order_20260723.txt`
- `results/camera_launch/PILOT_TRAIN/contact_sheet_PILOT_TRAIN.png` for the §6 gate after

Resume checklist (next sitting — any time of day, no camera involved):
1. Grade: `.venv/bin/python3 src/pilot_grading_runner.py` — bean in hand, sealed order,
   taxonomy only, `?` when unsure, mapping stays closed.
2. Claude verifies labels (20 rows, vocabulary, counts, defect histogram).
3. §6 manual image gate (contact sheet + full-size, reject-visibility per image).
4. PILOT_VAL session (P5/P7/P12/P16): full session-start gates first (marks, press-test by
   head sides, glare, screen dimmed/away, throwaway vs new canonicals C022/23), runner
   switched to VAL.
5. SOUL/LOT_B on arrival → PILOT_TEST → manifest → HF (on request) → Colab smoke.

## Rules reaffirmed for the rest of the pilot

1. CameraController/Photo Booth do not open on capture days; ANY touch is announced
   immediately and is followed by one discarded throwaway capture before data.
2. Two silent app touches occurred mid-triage tonight; they confounded diagnosis for ~30 min.
   No data was affected (throwaway session only; zero beans drawn at the time).
3. Press-test addendum for rig guide: handle the camera head by its sides, never the lens
   face; torch-check the lens after handling. (Smudge was not tonight's cause but the
   contamination path is real and un-gated.)
