# PILOT_TRAIN session guide — resume after 2026-07-22 pause

All commands run from the repo root (`~/Documents/so101-robot`). Physical order:
**gates → draw (all 20 cups, no camera) → capture (cup → nest → photo → same cup)**.

## Phase A — physical setup (no terminal)

1. Lighting domain: capture at night, or block the window COMPLETELY. Both ring lights on
   at their taped marks; every other light off. Rings are the only light sources.
2. Marks check: mat corners, nest, stool feet, boom clamp, joint flags, ring-stand feet —
   all against their photos. Anything moved → realign to photos; tell Claude.
3. Wipe the nest region (dry cloth).
4. CameraController and Photo Booth: fully quit (Cmd-Q). They stay closed all session.
   If either touches the camera at ANY point: say so immediately — one discarded throwaway
   is required before data.

## Phase B — terminal gates

1. ONLY IF the Mac rebooted or a camera was replugged overnight, rerun preflight and
   confirm the printed report passes, then eyeball `top.jpg` = bean-scene view:

   .venv/bin/beansight-camera-preflight --top-match C920 --wrist-match C270 --duration 10 --output results/camera_launch/PILOT_TRAIN
   open results/camera_launch/PILOT_TRAIN/top.jpg

2. Press-test (live preview opens; press the camera head lightly BY ITS SIDES — never touch
   the lens face — framing must return exactly, wobble < 1 s; q to quit):

   .venv/bin/python3 src/press_test_preview.py

   While it is open, also do the glare check: empty nest, zero hotspots, no shadows crossing.

3. Throwaway health frame (discarded by construction; increment the ID if C008 exists):

   .venv/bin/beansight-capture-perception results/camera_launch/PILOT_TRAIN/camera_preflight.json --settings private/perception_capture_settings.json --output data/perception/rigtest --session-id RIGTEST_02 --lot-id LOT_A --geometry-id PILOT_GEOM_01 --bean-id RIGTEST_C008

   Check it (must print a mean between 110 and 170; reference is 127.3):

   .venv/bin/python3 -c "import cv2; print('mean %.1f' % cv2.imread('data/perception/rigtest/canonical/RIGTEST_C008.png').mean())"

   Outside the window → STOP, tell Claude, failure triage. Do not proceed to beans.

## Phase C — sealed draw (~8 min, camera idle, away from the rig)

Materials: both 96B bags, 20 numbered containers = the 5cm x 7cm LDPE zip bags
(pre-label ALL of them before the draw, permanent marker, let ink dry; 4x6 pack stays as
reserve). LABEL CONVENTION (fixed 2026-07-22): bag label "P<n>" means bean_id PILOT_B<nnn>
zero-padded — P1 = PILOT_B001 ... P20 = PILOT_B020; PILOT_TEST beans will continue P21-P24.
The "P" prefix is reserved for pilot beans; no future container set may use bare P<number>
labels. Verify after labeling: P1..P20 present, no gaps, no repeats. "Cup N" in the runner
prompts means zip bag P<N>. Storage after: dry spot away from sun/heat; if condensation ever appears
inside a bag, crack all the zips and report it.

   .venv/bin/python3 src/pilot_draw_runner.py

- Each prompt names the bag (GOOD or DEFECT) and the cup. Take the FIRST bean your fingers
  land on — no looking, no choosing. Into the cup, press Enter.
- Suspected surface mold on a bean → stop, tell Claude before it goes in a cup.
- Ctrl-C is safe; rerunning resumes at the next unrecorded cup.
- When it prints "Draw complete": the mapping is SEALED. Never reopen
  `draw_mapping.csv` or `draw_plan_20260722.csv` until analysis, weeks away.

## Phase D — PILOT_TRAIN capture (≤60 min from neutral begin to neutral end)

   .venv/bin/python3 src/pilot_capture_runner.py

The script drives the whole session in the predeclared order:

1. Neutral BEGIN — nest empty, hands clear, Enter.
2. 16 beans, one at a time: it names the cup ("place the bean from CUP 15") — bean to the
   nest center, hands fully clear, Enter, wait for "[OK]", then bean BACK TO ITS SAME CUP.
   Any "OUT OF WINDOW" abort → stop, tell Claude, triage.
3. Neutral END — last bean removed, nest empty, Enter.

Rules during the loop: operator seated in one spot, nobody walks in the room, no bag or cup
ever near the mat, don't touch camera/lights/fixtures. Any bump → stop, tell Claude
(new session_id event).

## Phase E — after capture

- Cups filed by number, bags closed and away.
- Tell Claude: sidecar verification (16 canonical + 2 neutrals, hashes, means, IDs) runs
  from the filesystem.
- Blind grading is a SEPARATE later step (time-separated, shuffled cup order that Claude
  generates fresh; eight-type vocabulary; ambiguous allowed). Not right after capture.
- No git commits, no HF uploads.
