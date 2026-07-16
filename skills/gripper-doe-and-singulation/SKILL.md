---
name: gripper-doe-and-singulation
description: Evaluate BeanSight bean-scale mechanics — the 20-grasp gate, config-defined stock/tape/compliant fingertip DOE, Wilson-scored gripper summaries, and measured one-bean singulation-fixture design. Use when testing 8–12 mm bean grasping, choosing fingertips, diagnosing grasp failures, or publishing fixture dimensions.
---

# Gripper DOE and singulation

Full authority: `docs/evaluation_protocol.md` (20-grasp gate), `docs/hardware_and_safety.md`
(mechanical safety), `configs/gripper_doe.json` and `src/beansight_vn/gripper_doe.py` (DOE
contract), and `CAMERA-RESEARCH-REPORT.md` §9 (end-effector and singulation gaps).

## Non-negotiable safety and evidence

- **Leader arm = 5 V. Follower arm = 12 V. Never swap.** Complete inventory and polarity checks
  before power.
- Assign motor IDs one motor at a time; never flash a daisy chain.
- Keep autonomous control unarmed until an explicit callback is installed and the operator arms it.
- Run supervised with the switched power strip within reach; stop on unexpected motion, grinding,
  communication errors, rising temperature, taut cable, shifted base, or off-path contact.
- Record a safety cutoff as `safety_stop`. Remove every gripper-touched bean from food use.
- Report each rate with numerator, denominator, and Wilson 95% interval; report cycle time with
  sample count, median, and p95.

**TODO(owner): decide how the fixed failure-code taxonomy is represented in gripper DOE JSONL.**
The current `GripperTrial` schema has `notes` but no `failure_code`; do not add a field the loader
rejects. Preserve the stopped attempt and note `safety_stop`; if it is also a frozen `TrialRecord`,
set that record's primary failure code.

## 1. Run the physical grasp gate first

Use the fixed nest and teleoperated real-bean grasp procedure for 20 attempts:

- At least 16/20: proceed to coffee data as planned.
- 12–15/20: add the indexed nest plus compliant/high-friction fingertips and repeat once.
- Below 12/20 after one redesign: pivot manipulation to coffee sample cups or sachets and keep bean
  vision as a separate evaluated contribution.

Do not silently continue after a failed gate or substitute model changes for a mechanics failure.

## 2. Execute the fingertip DOE as configured

Treat `configs/gripper_doe.json` as the protocol contract:

- Variants: `stock`, `high_friction_tape`, and `compliant_tapered`.
- Orientations: `longitudinal`, `transverse`, and `diagonal`.
- Run 10 trials per variant/orientation cell, randomize order, reuse the same bean set per variant,
  and hold the nest and trajectory fixed.
- Keep v1 to the stock/tape/compliant choices. `docs/hardware_and_safety.md` explicitly defers a
  suction system during this month.

Write one real hardware `GripperTrial` JSON object per line with trial, variant, orientation, bean,
grasp, transfer, drop, cycle, optional servo temperature/load, and notes fields. Never put simulated
or placeholder trials in `results/`.

## 3. Summarize without hiding cells

```bash
beansight-gripper-summary /ABSOLUTE/PATH/TO/TRIALS.jsonl \
  --output results/gripper_doe_summary.json
```

The summary reports grasp, transfer, and drop rates with Wilson intervals plus cycle-time n,
median, and p95 for every populated variant/orientation cell. Raw temperature and load fields are
preserved in trials but are not currently aggregated by the CLI; do not claim otherwise.

Choose a fingertip from the measured cell results and failure observations, not one pooled rate.
State which failure the choice does not fix, such as approach error or unstable presentation.

## 4. Design the singulation fixture from measurements

V1 presents one 8–12 mm bean manually in the fixed inspection nest. The next documented concept is
an inclined chute with a single-bean pocket; do not claim an automatic feeder exists.

**TODO(owner): measure the real bean distribution and choose the chute, pocket, clearance, slope,
material, and mounting dimensions.** Do not infer dimensions from the nominal bean range alone.

Publish a ruler photo and millimetre drawing covering the pocket, chute, nest interface, mounting
references, materials, and the exact workcell/session identity used for evaluation. If a fixture
mark moves, start a new session ID and do not mix data.

The DOE distinguishes fingertip/orientation effects. It does not solve perception, calibration,
approach policy errors, cup placement, or repeatable upstream bean feeding.
