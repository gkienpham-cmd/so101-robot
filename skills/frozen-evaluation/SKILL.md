---
name: frozen-evaluation
description: Run and score the beansight-v1-frozen evaluation protocol — gates, trial counts, Wilson 95% CIs, the fixed failure-code taxonomy, the one-allowed-iteration rule, and before/after comparison. Use for any task that produces, scores, or compares physical trial results.
---

# Frozen evaluation (`beansight-v1-frozen`)

Full authority: `docs/evaluation_protocol.md` (frozen — a change creates a NEW protocol ID, never
an edit) and `docs/runbook.md` §9. Unit of evaluation: one physical bean in the fixed nest, with a
blind roaster label recorded BEFORE the robot prediction.

## Gates before any scored trial

1. Electrical inventory/polarity signed off.
2. Dual-camera 30-min soak passed.
3. Calibration backed up under unique leader/follower IDs.
4. Dataset QA passed; all six action dims nonzero variance.
5. Teleoperated real-bean grasping reached 16/20
   (12–15/20 → indexed nest + fingertips, repeat once; <12/20 after one redesign → pivot to
   sample cups/sachets and keep bean vision as a separate contribution).

## Perception eval

Compare the calibrated color/shape baseline vs. the ResNet-18 transfer model on the same held-out
test split. Report per-class precision/recall/F1, macro-F1, confusion matrix, false-accept rate
(rejects predicted acceptable), false-reject rate, agreement with the blind human label, and
median + p95 M1 inference latency. **Choose the operating threshold on validation data — never on
the frozen physical trial set.**

## Manipulation eval

- **≥30 ground-truth reject trials**, balanced across nest positions and bean orientations.
  Record separately: approach reached the bean, grasp succeeded, held during transfer, placement
  in cup, end-to-end success without intervention, cycle time + policy latency.
- **≥20 acceptable-bean trials**: success = correct classification AND no robot motion.
- The controller stays unarmed until the explicit ACT callback is installed and the operator is
  ready; one trigger permits one rollout; the rollout consumes the existing
  `observation.images.top` frame (never a second C920 handle). Every trial appends a `TrialRecord`.

## Reporting rules

- Every rate: numerator, denominator, and **Wilson 95% interval** (`beansight_vn.metrics.wilson_interval`).
- Latency/cycle time: sample count, median, p95 (`beansight_vn.latency.LatencyRecorder`).
- Exactly one primary failure code per failed trial: `perception_false_accept`,
  `perception_false_reject`, `localization_trigger_error`, `approach_error`, `grasp_miss`, `drop`,
  `placement_miss`, `human_intervention`, `safety_stop`, `other` (with note).
- **Never delete a trial.** Operator mistakes stay in the log with a note.
- Keep representative successful AND failed videos.

```bash
beansight-trial-summary results/trials-v1.jsonl --output results/summary-v1.json
```

Keep the first result, including poor trials.

## One allowed iteration

Identify the largest failure category → add only 10–25 demos addressing it → retrain once →
repeat the SAME protocol, positions, label balance, lighting, and threshold → present before and
after together:

```bash
beansight-compare results/trials-v1-before.jsonl results/trials-v1-after.jsonl \
  --output results/before-after-v1.json
```

The comparison refuses mismatched ground-truth/position/lighting counts by default — that refusal
is a feature, not a bug to work around.

If ACT <30%: inspect calibration, camera geometry, demonstrations, and task scope before anything
else. If still <40% after the iteration: narrow the workspace/object and publish the failure
analysis — do not model-hop until something works.
