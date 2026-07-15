# Thirty-day execution and portfolio plan

Each day ends with an artifact: a signed inventory, soak report, drawing, manifest, QA report,
immutable revision, trial log, figure, or video. “Worked on training” is not a deliverable.

## What pre-arrival training can prove

No manipulation checkpoint trained before arrival will drive this particular arm: calibration,
camera geometry, gripper mechanics, and the real workcell are missing. Public SO-101 datasets may
smoke-test loaders and configs, but they are not deployment data. Before arrival, spend model time on
the coffee perception baseline and use the already-proven simulation→Hub→4090→W&B→M1 pipeline in
`RETRO.md` as the infrastructure check.

## Before arrival: days −5 to −1

- **−5:** repository and LeRobot patch frozen; electrical inventory ready; seller asked to confirm
  the follower adapter specification.
- **−4:** C920 and C270 tested separately, then together for 30 minutes at 640×480/30.
- **−3:** nest, light, cup, bins, five-position block grid, schema, and failure codes frozen.
- **−2:** roaster interview; two lots and blind labels obtained; first workcell images captured.
- **−1:** color baseline and ResNet-18 trained. A 200–500-step SmolVLA installation smoke test is
  optional; do not repeat a full ACT run on somebody else's workcell.

## Hardware week

- Photograph and verify everything before power.
- Assign servo IDs one at a time, assemble, calibrate, and back up calibration.
- Teleoperate without cameras, then with both.
- Record 50 wooden-block episodes across five positions and train the bring-up ACT baseline.
- Run the 20-grasp bean gate and follow its 16/20, 12–15/20, or below-12/20 branch exactly.

## Coffee data and model week

- Capture and label 300–500 physical beans, at least 50 visible rejects, from two or more lots.
- Validate every manipulation episode and all six action dimensions.
- Record 50–75 fixed-nest demonstrations with small controlled offsets.
- Train ACT at batch 8 for about five data epochs; check a short checkpoint before extending.

## Integration and evaluation week

- Connect the thresholded classifier to the unarmed rollout controller.
- Run at least 30 reject and 20 acceptable no-motion trials.
- Report perception, grasp, placement, end-to-end success, latency, cycle time, and every failure.
- Add 10–25 demonstrations for the largest failure category, retrain once, and repeat unchanged.

## Portfolio week

- Run the gripper fingertip experiment and publish the singulation-fixture dimensions.
- Attempt the clean bottle-cap transfer only after the flagship evaluation is frozen.
- Fine-tune SmolVLA only if the ACT and evaluation gates pass.
- Publish versioned GitHub, Hugging Face, and W&B artifacts with limitations.
- Edit a 60–90 second overview and a 3–5 minute technical video that includes failures.

Lead with the HCMC coffee problem and experiment, not the model name or a university application. The
story is the chain of choices: a narrow visible-defect claim, low-cost arm, fail-still routing,
physical grasp bottleneck, and honest measurement.

## Hero video: 60–90 seconds

1. Mixed green Robusta and roaster-labeled examples.
2. A wide shot showing the complete workcell.
3. One sentence of architecture: inspect, stay still or reject, verify.
4. One acceptable no-motion trial and one successful reject trial with confidence and timing.
5. A short failure clip followed by the measured failure breakdown.
6. A final card with sample size, Wilson interval, GitHub, artifact revisions, and scope limit.

Use English captions and Vietnamese subtitles. Keep the robot's natural sound. Label any sped-up
footage clearly.

## Technical video: 3–5 minutes

Show the power labels and calibration IDs, semantic camera preflight, fixed geometry, label protocol,
dataset split, ACT demonstrations, frozen evaluation, largest failure mode, and targeted iteration.
Put the numerator and denominator beside every percentage.

## Required visuals

- architecture diagram and annotated workcell drawing with millimetre dimensions
- sample grid for both labels and lots
- confusion matrix and threshold curve
- grasp, placement, and end-to-end chart with Wilson intervals
- failure chart with representative frames or clip links
- median and p95 latency/cycle-time chart
- before/after result under the identical frozen protocol
- gripper fingertip and singulation-fixture dimensions

## Public artifact chain

The portfolio page links to a tagged GitHub release. The release links to exact Hugging Face dataset
and policy revisions, W&B run, experiment manifest, aggregate JSON, and videos. Personal notes,
admissions strategy, seller chats, addresses, receipts, and roaster contacts remain private.

If performance is poor, publish the negative result: where low-cost manipulation failed, what the
nest or fingertips changed, and which measurements support the next design. That is more credible
than selecting only successful clips.
