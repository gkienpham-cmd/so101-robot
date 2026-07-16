---
name: perception-controller-integration
description: Integrate the thresholded BeanSight classifier with the fail-still rollout controller — shared top-camera observations, explicit ACT callback installation, unarmed-by-default behavior, one-trigger/one-rollout supervision, latency capture, and TrialRecord logging. Use when connecting perception to physical motion or implementing the real rollout loop.
---

# Perception-controller integration

Full authority: `docs/runbook.md` §9 and `docs/evaluation_protocol.md`; safety authority:
`AGENTS.md`; code contract: `src/beansight_vn/controller.py`, `src/beansight_vn/routing.py`,
`src/beansight_vn/models.py`, and `src/beansight_vn/trial_log.py`.

## Non-negotiable safety boundary

- **Leader arm = 5 V. Follower arm = 12 V. Never swap.** Inventory and polarity must be signed
  off before power.
- If motor IDs are configured, connect one motor at a time; never flash a daisy chain.
- `BeanSightController` starts unarmed. Never bypass `armed=False` or create motion without an
  explicit reject callback.
- Operate supervised with the switched power strip within reach. One trigger permits one rollout.
- Cut power on unexpected direction, grinding, repeated communication errors, rising temperature,
  a taut camera cable, shifted base, or off-path contact; record `safety_stop`.

## 1. Satisfy every physical gate

Do not integrate scored motion until electrical inventory, the 30-minute dual-camera soak,
calibration backup, dataset QA, and the 16/20 teleoperated real-bean grasp gate have passed.
Use the immutable dataset and policy revisions recorded in the experiment manifest.

Freeze the reject threshold from validation data before physical evaluation. Never tune it from
the frozen trial set.

## 2. Respect the existing interfaces

- Pass the rollout loop's existing `observation.images.top` frame to the controller. Never open a
  second C920 process or capture a newer frame for the same decision.
- Provide a classifier implementing `classify(frame, frame_id=None, session_id=None)` and returning
  `PerceptionResult`.
- Keep `image_key="observation.images.top"` unless the recorded config changes the contract.
- Route only a confident `visible_reject` at or above the frozen threshold to `reject`; acceptable
  and uncertain results must remain `no_motion`.
- Provide the reject callback with the current observation mapping; do not pass detector
  coordinates into ACT. V1 is the fixed one-bean nest-to-cup skill.

## 3. Install motion in the safe order

1. Construct and exercise the controller unarmed; confirm all decisions log without motion.
2. Verify acceptable and below-threshold reject cases never invoke the callback.
3. Install the explicit ACT reject callback while the controller remains unarmed.
4. **TODO(owner): define the real-arm callback/rollout entry point that loads the immutable ACT
   policy and executes exactly one reject rollout.** Do not invent a CLI or bypass this gap.
5. Clear the workspace, place the switched cutoff within reach, and have the operator arm the
   controller explicitly.
6. Let the outer rollout loop admit one trigger, execute at most one callback, then verify and log
   before another trigger is accepted. The controller class does not auto-disarm for the outer loop.

Run `pytest tests/test_routing_controller.py` after any controller or routing change.

## 4. Log every outcome

Append one `TrialRecord` for every attempt using `append_trial`; never delete an operator mistake.
Record the experiment/session/bean/lot IDs, blind ground truth, prediction, confidence, decision,
pick/place/end-to-end outcomes, intervention, position, lighting, immutable revisions, and available
perception/policy/cycle latency.

Assign exactly one primary failure code to every failed physical trial from the frozen taxonomy.
Use `other` only with a note. A safety cutoff always uses `safety_stop`.

## 5. Report decomposed evidence

- Every rate needs numerator, denominator, and Wilson 95% interval.
- Every latency or cycle-time statistic needs sample count, median, and p95.
- Keep perception, pick, placement, acceptable no-motion, and end-to-end rates separate.
- Keep successful and failed videos and the first frozen result, including poor trials.

This integration enforces fail-still routing. It does not fix classification errors, camera drift,
calibration, weak ACT demonstrations, missed grasps, or placement geometry.
