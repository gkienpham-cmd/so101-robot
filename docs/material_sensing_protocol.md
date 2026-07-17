# Plastic material sensing protocol: `plastic-material-sensor-v1`

This protocol asks one narrow question: can the fixed, sub-$300 sensor distinguish PET, HDPE, and PP
from an explicit unknown class well enough to justify connecting its output to a supervised sorter?
It does not claim universal polymer identification or universal recyclability.

Ordinary RGB can localize an item or read a visible marking, but it does not establish the chemistry
of an unlabeled polymer. Industrial facilities commonly use near-infrared sensing for this boundary
([NIST overview](https://www.nist.gov/how-do-you-measure-it/how-do-recycling-facilities-sort-different-kinds-plastic)).

## Hardware gate

Use an enclosed fixture derived from the Plastic Scanner DB2.3 design, with measurements at 855,
940, 1050, 1200, 1300, 1450, 1550, and 1650 nm. The open project calls DB2.3 an early development
prototype, so do not treat the build as guaranteed:

- Total sensor, PCB, enclosure, reference, and fixture spend must remain at or below $300.
- Procurement and bring-up stop after seven days.
- Every emitter is enclosed. Invisible light is still light; never look into an active emitter.
- Record the exact board, detector, emitter, enclosure, spacing, and reference revision.
- If the fixture is unstable or irreproducible, stop. Preserve the negative result.

References: [Plastic Scanner operating principle](https://docs.plasticscanner.com/how_it_works) and
[DB2.x hardware warning](https://github.com/Plastic-Scanner/DB2.x-Hardware).

## Samples and ground truth

Collect 30 unique physical items in each class:

- PET
- HDPE
- PP
- `unknown`: black, multilayer, PVC, PS, LDPE, non-target, or genuinely uncertain material

Target-resin labels require a traceable reference sample, molded RIC, or manufacturer record.
`unverified` is allowed only for the unknown class. An RIC supports resin identity; it does not prove
that a municipality accepts the object for recycling.

Capture ten scans per item across at least three sessions. Each row carries the physical `item_id`,
`parent_sku`, `session_id`, evidence method, reference ID, raw readings, and paired dark/white
readings. Every row also names the same fixed `sensor_revision`; the trainer rejects mixed or
config-mismatched fixtures. Start from `configs/material_manifest.example.csv`.

Do not count repeated scans as independent items. The cross-validation group is `parent_sku`, so a
SKU cannot appear on both sides of a fold. Plan at least seven parent-SKU groups per class for the
configured five-by-five nested evaluation. The tool refuses any outer or inner split that cannot
retain five groups per class instead of silently reducing the fold count.

## Preprocessing and models

For every scan, the implementation performs:

1. `(raw - dark) / (white - dark)` per wavelength.
2. Standard normal variate normalization across the eight bands.
3. Median aggregation across the physical item's repeated scans.

The item-level held-out study uses all ten recorded scans to count each physical item once. A
runtime `MaterialDecision` is stricter: `classify_repeated_scans` requires exactly five fresh scans
with the same `item_id`, qualified wavelengths, and the same dark/white/SNV preprocessing, then
classifies their median. A single scan cannot authorize routing.

The declared baseline is nearest centroid. The primary model is a class-balanced RBF-SVM. Model and
threshold selection use only grouped inner folds. Five grouped outer folds provide the held-out
predictions. Confidence comes from temperature-scaled decision scores; low-confidence target
predictions become `unknown`.

Run:

```bash
beansight-train-material-sensor data/materials/manifest.csv \
  --config configs/material_sensor.json \
  --output-dir outputs/material_sensor/db23_r1
```

Before running, replace `sensor.revision` in a copied config with the actual fixture revision. The
tool refuses the placeholder. It writes `metrics.json` under `outputs/`, never `results/`. A passing
pipeline writes `material_model.joblib`; a failure writes
`candidate_material_model.UNQUALIFIED.joblib`. Every artifact carries its frozen-gate status and
qualification-payload hash, and inference refuses an unqualified model. Joblib artifacts are
executable Python objects; load only artifacts produced by this project.

## Frozen integration gate

Using pooled outer-fold predictions:

- Each target class must accept at least 20 of its 30 physical items.
- Correctness among accepted decisions must be at least 95% for PET, HDPE, and PP.
- At most 1 of 30 unknown items may be falsely accepted as a target resin.

Report the complete confusion matrix, abstention count/reasons, accepted correctness, target
coverage, unknown false acceptance, exact fold/SKU assignments, and per-item inference latency.
Every rate carries its numerator, denominator, and Wilson 95% interval.

Failure stops the material-to-arm integration. Keep the sensing result as a standalone study; do not
tune against outer-fold predictions, remove difficult items, relabel after seeing predictions, or
replace spectroscopy with RGB while keeping the same claim.

Failure is credible: one published low-cost six-resin system reported 72.5% mean accuracy and 66%
for PET. Those figures do not predict this fixture, but they are a warning not to relax the gate
after seeing a disappointing result
([study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11086069/)).

## Arm boundary

After the gate passes, the sensor produces a `MaterialDecision`. A separate dated `RouteProfile`
turns that into a `RouteDecision`. Only a confident PET, HDPE, or PP route from an enabled profile can
create a `ManipulationRequest`. Unknown, low confidence, expired/disabled profiles, and manual review
all mean no motion.

The controller must still have an explicit callback and a fresh operator arm action. Every handled
sensor decision consumes that one-shot authorization, including a no-motion decision. The sensor
never owns a robot, policy, or camera handle. Integration records preserve the dated profile and
location, classifier latency, safety state, all manipulation stages, and exactly one primary code
for every failed trial.
