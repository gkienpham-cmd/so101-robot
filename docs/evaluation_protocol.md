# Frozen evaluation protocol: `beansight-v1-frozen`

Freeze this document before the first scored run. A later change creates a new protocol ID; it does
not overwrite v1.

## Scope and labels

The unit of evaluation is one physical bean in the fixed inspection nest. Ground truth is a blind
roaster label recorded before the robot prediction:

- `acceptable`
- `visible_reject`: clearly black, clearly broken, or agreed foreign matter

Exclude ambiguous mold, moisture, taste, internal insect damage, and cup-quality judgments. Record
disagreements rather than forcing consensus after seeing the model output.

Collect 300–500 beans from at least two Vietnamese Robusta lots, including at least 50 visible
rejects. Each physical bean has one `bean_id`. Splits cannot share a bean ID or capture session, and
the test lot cannot appear in training. Validation may use a separate session from the training lot so
this is possible with two lots. Adjacent video frames are never treated as independent examples.

## Gates before scoring

1. Electrical inventory and polarity check is signed off.
2. The dual-camera 30-minute soak passes.
3. Calibration files are backed up under unique leader/follower IDs.
4. All six action dimensions have nonzero variance and dataset QA passes.
5. Teleoperated real-bean grasping reaches 16/20.

At 12–15/20, add the indexed nest and compliant/high-friction fingertips, then repeat. Below 12/20
after one redesign, manipulate larger coffee sample cups or sachets and keep bean vision as a separate
evaluated contribution.

## Perception evaluation

Compare a calibrated color/shape baseline with one transfer model, initially ResNet-18. Use the same
held-out test split and report:

- per-class precision, recall, and F1
- macro-F1 and confusion matrix
- false-accept rate: visible rejects predicted acceptable
- false-reject rate: acceptable beans predicted reject
- agreement and disagreements with the blind human label
- median and p95 inference latency on the M1

Choose the operating threshold on validation data. Do not tune it on the frozen physical trial set.

## Manipulation evaluation

Run at least 30 ground-truth reject trials, balanced across planned nest positions and bean
orientations. Record separately:

- approach reached the intended bean
- grasp succeeded
- bean remained held during transfer
- placement landed in the reject cup
- end-to-end success without intervention
- complete cycle time, policy latency, and intervention

Run at least 20 acceptable-bean trials. Success means correct classification and no robot motion.

For every rate, report numerator, denominator, and Wilson 95% interval. For latency and cycle time,
report sample count, median, and p95. Keep representative successful and failed videos.

## Failure codes

Use exactly one primary code per failed trial:

- `perception_false_accept`
- `perception_false_reject`
- `localization_trigger_error`
- `approach_error`
- `grasp_miss`
- `drop`
- `placement_miss`
- `human_intervention`
- `safety_stop`
- `other` with a note

Never delete a trial. Operator mistakes remain in the log with a note; a separate, predeclared
exclusion flag can be added in a later schema version if needed.

## One allowed iteration

After the first frozen run, identify the largest failure category. Add only 10–25 demonstrations that
address it, retrain once, and repeat the same protocol, positions, label balance, lighting, and
threshold. Present before and after together.

If ACT is below 30%, first inspect calibration, camera geometry, demonstrations, and task scope. If it
remains below 40% after the targeted iteration, narrow the workspace/object and publish the failure
analysis instead of switching models until something works.
