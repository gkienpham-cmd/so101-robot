---
name: dataset-qa-and-publish
description: Gate a recorded LeRobot dataset with beansight-dataset-qa and publish it privately to the Hugging Face Hub with an immutable revision — required before ANY paid GPU training run. Use when a dataset has been recorded and needs validation, upload, or revision pinning.
---

# Dataset QA and publish

Full authority: `docs/runbook.md` §7 and `docs/evaluation_protocol.md` (splits). Rule: **no upload
and no GPU rental until QA passes.** This gate exists because a bad dataset discovered after a
paid run wastes both money and the one allowed iteration.

Run these commands from the pinned LeRobot venv after installing this project there with
`uv pip install --no-deps -e /ABSOLUTE/PATH/TO/so101-robot`. The normal project venv intentionally
does not contain LeRobot and cannot attest its checkout or load a LeRobot dataset.

## 1. Run QA on the local dataset

```bash
beansight-dataset-qa YOUR_HF_USER/beansight-vn-coffee-v1 \
  --root /ABSOLUTE/LOCAL/DATASET/ROOT \
  --output results/dataset_qa.json
```

Use the actual timestamped repo ID from the recording log (LeRobot v0.6 stamps
`_YYYYMMDD_HHMMSS`). QA rejects, among others:

- swapped `top`/`wrist` cameras
- missing or unreadable frames
- malformed episode metadata
- action shape errors, NaN/Inf values
- **constant action dimensions** — all six action dims must have nonzero variance

## 2. Human review (QA is necessary, not sufficient)

Watch sample episodes end-to-end. Confirm camera order, sharpness, duration, the exact task
string, and visible motion in all six joints. Delete-and-rerecord beats patching a bad episode.

## 3. Split discipline (for the coffee dataset)

- One `bean_id` per physical bean; 300–500 beans, ≥50 visible rejects, ≥2 Robusta lots.
- Splits never share a `bean_id` or a capture session; the test lot never appears in training.
- Adjacent video frames are never treated as independent examples.
- Ground-truth labels are blind roaster labels recorded BEFORE any model prediction.

## 4. Publish and pin

1. Push **privately** to the HF Hub only after QA passes (`hf auth login` with a write-scoped
   token; never commit tokens).
2. Record the **immutable Hub commit hash** and put it in the experiment manifest
   (`configs/experiment_manifest.example.json` shows the shape). Pass it to
   `beansight-build-act-config`; do not hand-edit the template. Training must reference the
   immutable revision, never a branch.
3. Re-run QA against the uploaded revision as a final check:

```bash
beansight-dataset-qa YOUR_HF_USER/beansight-vn-coffee-v1 \
  --revision IMMUTABLE_HF_COMMIT \
  --root /ABSOLUTE/FRESH/QA_SNAPSHOTS/IMMUTABLE_HF_COMMIT \
  --output results/dataset_qa_pinned.json
```

The pinned check refuses a populated root, records a content fingerprint, and verifies the exact
editable LeRobot v0.6.0 commit plus the repository-approved recording-patch hash. Use this pinned
report—not the pre-upload local report—to build a paid-run config.

A dataset that fails any of this is not "mostly fine" — it is not trainable yet.
