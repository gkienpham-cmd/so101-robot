---
name: perception-training
description: Leakage-safe BeanSight coffee-perception training — manifest validation, fixed-lighting color-baseline calibration, ResNet-18 transfer learning, validation-only threshold selection, held-out metrics, and M1 latency. Use when capturing perception images, preparing splits, training or selecting the classifier, or reporting classifier performance.
---

# Perception training

Full authority: `docs/data_and_labeling.md` and `docs/evaluation_protocol.md` (label scope,
splits, metrics, and frozen-threshold rule); implementation contract:
`src/beansight_vn/train_perception.py`, `src/beansight_vn/latency.py`, and
`configs/perception.json`.

## 1. Freeze capture conditions first

- Use the final C920 mount, inspection nest, matte surface, and fixed lamp.
- Lock focus, exposure, and white balance before the first session.
- Start a new `session_id` if any fixture or lighting mark moves; never combine the sessions
  silently.
- Use the existing top-camera stream. Do not open a second C920 process.
- Keep the claim to `acceptable` versus `visible_reject`; exclude ambiguous mold, moisture,
  taste, internal insect damage, and cup-quality judgments.

## 2. Build the manifest without leakage

Use exactly these columns:

```csv
path,label,bean_id,lot_id,session_id,split
images/B001.jpg,acceptable,B001,LOT_A,S01,train
```

- Give every physical bean one durable `bean_id`; a burst does not create independent beans.
- Include `train`, `val`, and `test`, with both labels represented in every split.
- Never let a `bean_id` or `session_id` cross splits.
- Never let a test `lot_id` appear in training. Validation may use a separate session from the
  training lot.
- Record the blind human label before any model prediction; adjacent frames are not independent.

## 3. Calibrate the baseline honestly

`configs/perception.json` contains placeholder luminance and reject-fraction values until the
fixed lighting exists. Fit or choose them using training and validation data only.

**TODO(owner): define the repository-approved fitting procedure for the dark-pixel/shape baseline.**
Until then, do not invent a search command, promote the placeholders, or tune against test images.

## 4. Train the transfer model

```bash
pip install -e '.[perception]'
beansight-train-perception data/coffee/manifest.csv \
  --architecture resnet18 \
  --epochs 10 \
  --output outputs/perception/resnet18
```

The trainer validates files and split invariants, aborts on NaN/Inf, selects a checkpoint by
validation macro-F1, and writes `model_state.pt`, `model.ts`, and `metrics.json`.

## 5. Select the threshold and evaluate

- Choose the operating threshold from the validation threshold curve associated with the
  validation-selected checkpoint.
- Never use `test.best_macro_f1_threshold` to set the threshold; that would tune on test data.
- Freeze the chosen threshold before the frozen physical trial set and record it in the experiment
  manifest/configuration.
- Compare the calibrated baseline and ResNet-18 on the same held-out test split.
- Report confusion matrix, per-class precision/recall/F1 and support, macro-F1, false-accept rate,
  false-reject rate, and agreement/disagreements with the blind label.

## 6. Meet the evidence standard

- For every published rate, include numerator, denominator, and Wilson 95% interval via
  `beansight_vn.metrics.wilson_interval`; raw trainer percentages alone are not publication-ready.
- For M1 inference latency, report sample count, median, and p95.
- **TODO(owner): define the standalone M1 latency-measurement entry point.** The repository has
  `LatencyRecorder` and trial latency fields, but no dedicated perception-latency CLI.
- When the classifier is used in physical trials, retain every attempt and give each failed trial
  exactly one primary failure code from `docs/evaluation_protocol.md`.
- Keep failures and disagreements; never move a sample between splits after seeing its prediction.

This workflow reduces label leakage and threshold overfitting. It does not fix lighting drift,
ambiguous labels, poor physical presentation, or grasp failures.
