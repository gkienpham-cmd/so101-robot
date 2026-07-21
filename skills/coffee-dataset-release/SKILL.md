---
name: coffee-dataset-release
description: Prepare the Vietnamese Robusta image dataset as a public, permission-safe artifact — release eligibility, card content, label and split provenance, lighting and bias documentation, license decision, immutable revisions, limitations, and evidence-safe claims. Use after image-manifest validation when drafting or publishing the dataset card or public release.
---

# Coffee dataset release

Full authority: `docs/data_and_labeling.md` (labels, permissions, splits, and card requirements),
`docs/execution_and_portfolio.md` (public artifact chain), and
`skills/honest-reporting/SKILL.md` (claims/evidence). The separate
`skills/dataset-qa-and-publish/SKILL.md` validates LeRobot manipulation data, not this image manifest.

## 1. Establish release eligibility

Do not make the dataset public until all of these are true:

- The final image manifest has passed `read_manifest`/`validate_manifest` in
  `src/beansight_vn/train_perception.py`, including file, label, split, bean, session, and lot checks.
- Every image maps to a durable `bean_id`, `lot_id`, `session_id`, split, and blind label.
- No bean or capture session crosses splits; the test lot does not appear in training.
- Ambiguous examples are excluded from the scored v1 set or clearly separated as unscored data.
- Permission for anonymized labels and bean photographs is recorded outside the repository.
- Any business name or interview quotation has its own separate permission.
- **TODO(owner): choose and record the dataset license.** Do not infer it from the code license or
  publish until it is compatible with the recorded permissions.
- **TODO(owner): choose the final image-dataset Hugging Face repository ID.** The private staging,
  immutable upload, and fresh-revision QA procedure is in `docs/perception_collection.md`; do not
  reuse its pilot repository as the public release without the remaining permission/license gates.

Keep roaster contacts, signed permissions, seller messages, receipts, addresses, and tokens in
gitignored private storage. Never copy them into a card, commit, model artifact, or video.

## 2. Freeze the dataset identity

- Once published, preserve the actual immutable Hugging Face commit hash; never cite a mutable
  branch as the experiment input.
- Record that image-dataset revision in the dataset card and tagged release without overwriting the
  separately pinned LeRobot manipulation-dataset revision.
- State actual image, bean, label, lot, and session counts. Do not present the collection targets
  of 300–500 beans, at least 50 rejects, and at least two lots as achieved until the data proves it.
- Keep the label record created before model predictions; do not repair disagreements after seeing
  results.

## 3. Write the dataset card

Document:

1. Purpose: supervised research on visible Vietnamese Robusta defects in a fixed workcell.
2. Labels: `acceptable` and `visible_reject`; visible defect types follow the eight-type
   TCVN-4193-aligned vocabulary in `docs/data_and_labeling.md` (`black`, `broken`, `insect_damage`,
   `dried_cherry`, `shell_husk`, `immature_faded`, `moldy`, `foreign_matter`).
3. Exclusions: ambiguous mold, moisture, taste, internal insect damage, and cup-quality judgments.
4. Acquisition: C920, final mount, fixed lamp, locked focus/exposure/white balance, inspection
   nest, and capture-session boundaries. State explicitly that the background is a **printed A1
   cutting mat (back side, uniform grid)** — a documented deviation from a neutral surface — with
   its known risks (green color spill, semi-gloss sheen, grid-as-scale-cue) per the amended
   `docs/perception_collection.md` §2.
5. Ground truth: blind roaster review, ambiguity handling, preserved disagreements, and separate
   publication permissions.
6. Splits: bean/session isolation, held-out test lot, and no adjacent-frame independence claim.
7. Biases: controlled lighting, limited lots, visible-only scope, class/defect distribution, and
   dependence on the fixed capture geometry.
8. Intended and out-of-scope uses, license, file/manifest structure, and immutable revision.

Do not claim food safety, cup quality, industrial throughput, worker replacement, or defect classes
the labels do not support.

## 4. Attach evidence without leakage

- Include an anonymized sample grid spanning both labels and lots only where photo permission exists.
- Publish split counts and confusion/threshold figures without exposing private identities.
- For every reported model or system rate, include numerator, denominator, and Wilson 95% interval.
- Include the background-dependence probe outcome (`beansight-background-probe` report: probe vs
  in-domain accuracy with both Wilson intervals, plus the saliency summary) whenever any classifier
  rate is published. Probe numbers are diagnostics — never headline metrics.
- For latency or cycle time, include sample count, median, and p95.
- Give every failed physical trial exactly one frozen failure code and show failures beside successes.
- Never write invented, simulated, or placeholder performance to `results/`.

Dataset counts describe the artifact; they are not evidence of classifier or robot performance.

## 5. Link the public artifact chain

Link the tagged GitHub release to the exact dataset and policy revisions, W&B run, experiment
manifest, aggregate JSON, and videos that permissions allow. Keep the private training upload and
public release identities explicit if they differ.

Release the dataset only after the card, license, permissions, immutable revision, limitations, and
split provenance agree. A careful card does not eliminate sampling bias, label disagreement,
lighting dependence, or the need for a separately frozen physical evaluation.
