# Perception collection runbook

This is the operational path for the fixed-C920 image dataset. It covers visible green-Robusta
defects only: `acceptable` versus `visible_reject`, with the eight-type visible-defect vocabulary
defined in [data_and_labeling.md](data_and_labeling.md) (`black`, `broken`, `insect_damage`,
`dried_cherry`, `shell_husk`, `immature_faded`, `moldy`, `foreign_matter`). It does not establish
food safety, moisture, taste, internal insect damage, or cup quality. A `moldy` label records
visible surface mold in one photograph; it is never a food-safety determination.

The binding constraint is data validity, not GPU speed. A larger model cannot repair a moved lamp,
a class-correlated bag, a label written after seeing a prediction, or the same bean leaking into two
splits.

## 1. Prepare material and identities

1. Obtain clean green Robusta and clean sorting rejects or unsorted material. Never manufacture a
   defect. Reject whole lots that are damp, odorous, floor-swept, trash-mixed, roasted, or
   deliberately damaged. An individual surface-mold bean found in an otherwise sound, dry lot may be
   captured and labeled `moldy`; store it separately and handle it minimally.
2. Give each physical bean one durable ASCII `bean_id`. Keep it in one numbered cell or envelope.
   A recapture never becomes a new sample.
3. Record the blind label before any model output is visible. Allowed scored labels and defect types
   are defined in [data_and_labeling.md](data_and_labeling.md).
4. Keep supplier chats, addresses, permission records, blind-label working files, and pilot IDs in
   `private/`. Supplying beans does not grant publication permission.

### Current lot roster (decided 2026-07-21)

| Lot | Supplier | Material | Split role |
|---|---|---|---|
| `LOT_A` | 96B Cafe & Roastery | 200 g "good" bag + 200 g "defect" bag, green Robusta Gia Lai sàng 16 | train / val |
| `LOT_B` | SOUL Coffee | 1 kg "good" + 1 kg "defect", green Robusta | held-out test |

Both suppliers deliver roaster-pre-sorted bags. The bag is provenance, never the label: a
roaster's "defect" bag may differ from its "good" bag in batch, age, and moisture, so treating bag
membership as ground truth would teach the model the bag, not the bean. Defects found inside a
"good" bag are especially valuable because they break that correlation. Phone photos of received
material (see `docs/lots/`) document provenance only; they never enter the dataset.

### Sealed draw procedure (solo bag-blind grading)

1. At draw time, take beans from both bags of the lot and place each bean in a numbered cup in one
   randomized, interleaved sequence. Append one row per bean to `private/sourcing/draw_mapping.csv`
   (`bean_id,lot_id,source_bag,drawn_at`) as the bean is drawn. Close the file.
2. Grade later, in a shuffled cup order, against the written taxonomy only. Do not reopen the
   mapping while grading or capturing. Perfect solo blinding is impossible — you drew the beans —
   but the time separation plus shuffle is the honest mitigation, and this limitation is disclosed
   in the dataset card.
3. `source_bag` is joined to labels only during analysis (for example, measuring agreement between
   your blind grade and the roaster's sort). It never appears in the training manifest.

## 2. Qualify the physical scene

Use the C920 on the fixed mount, the fixed diffused lamp, the fixed capture background, and one
provisional one-bean nest. The pilot nest may be a removable center mark or an extremely shallow
pocket. It must hold one bean without hiding its top surface or adding a colored or textual cue.

### Capture background (amended 2026-07-21)

The background is the **back side of the A1 cutting mat** (uniform cross-hatch grid), taped flat
at the floor capture station described in [capture_rig_setup.md](capture_rig_setup.md). This deliberately relaxes the earlier no-printed-background rule for the surface only —
the no-colored-or-textual-cue rule still binds the nest itself. The deviation is accepted with its
risks named, not hidden:

- **Green color spill** onto bean edges under the lamp (white balance is locked, so it is constant,
  but it is real and disclosed in the dataset card).
- **Semi-gloss sheen**: the mat can produce a specular hotspot; the neutral reference frames must
  show none inside the ROI.
- **Grid-as-scale-cue**: gridlines occluded by the bean act as a size ruler the model can read. This
  cannot be prevented on this background; it is why the background-dependence probe below is
  mandatory before any success claim.

Placement rule: the nest sits in a region where the **ROI contains only uniform gridlines** — no
numerals, no angle labels, no branding block, no template shapes. Verify in the neutral `begin`
frame at every session start. If the mat region is later stained or damaged, move to an
identical-pattern region: that is a new `session_id` with fresh neutral references.

Assign the arrangement a `geometry_id`. Mark and photograph the C920 clamp, nest, lamp, diffuser,
and matte-surface positions. If any mark moves, stop and start a new `session_id`. The settings file
and geometry ID make a change auditable; they cannot prove that the physical fixtures stayed put.

Use [CameraController](https://github.com/itaybre/CameraController) or another UVC controller to set
manual focus and white balance, with 50 Hz anti-flicker. Exposure runs **hardware auto**: macOS
AVFoundation re-enables C920 auto-exposure on every stream open (verified empirically 2026-07-21;
saved manual values were ignored by pipeline captures), so it is declared `"mode": "auto"` with a
null value rather than misrecorded as locked. Mitigations: the fixed scene makes AE converge to a
near-constant operating point, the capture CLI warms up 90 frames (~3 s) before the kept frame, and
the background-dependence probe gate detects systematic exposure artifacts. The warmup does **not**
absorb the post-CameraController transient — the first capture after the app touches the camera is
systematically overexposed; see the AE transient rule in
[capture_rig_setup.md §8](capture_rig_setup.md). Block variable window light.
Copy the deliberately invalid example before filling it:

```bash
cp configs/perception_capture_settings.example.json \
  private/perception_capture_settings.json
```

Replace every `null` and placeholder with the values shown by the controller. The capture CLI stores
the file and its SHA-256 as operator-reported provenance. OpenCV cannot prove that the camera
accepted those settings, so recheck them visually and in the controller at each session boundary.

## 3. Design the 24-bean pilot correctly

Capture exactly 24 physical beans: 12 clear `acceptable` and 12 clear `visible_reject`. A valid
training-path pilot needs at least three capture sessions and two lots:

| Session | Lot | Split | Acceptable | Visible reject |
|---|---|---:|---:|---:|
| `PILOT_TRAIN` | `LOT_A` | train | 8 | 8 |
| `PILOT_VAL` | `LOT_A` | val | 2 | 2 |
| `PILOT_TEST` | `LOT_B` | test | 2 | 2 |

Randomize and interleave the two labels within each session. This layout is intentional: one session
cannot cross splits, and the test lot cannot appear in training. If a second lot or both labels in
each split are unavailable, capture can continue for debugging, but the Colab training smoke must
wait. Do not weaken the split gate.

Record all 24 IDs in `private/sourcing/pilot_ids.csv`. They may be used for the private pilot smoke,
but they are permanently excluded from final manifests and published counts.

Current phasing (2026-07-21): `PILOT_TRAIN` and `PILOT_VAL` run now from the two `LOT_A` (96B)
bags via the sealed draw procedure; `PILOT_TEST` runs when the `LOT_B` (SOUL) delivery arrives.
The manifest build and Colab smoke wait for all three sessions — that wait is structural, not
optional.

## 4. Resolve the current C920 and capture

After every reboot or camera replug, run a fresh semantic probe. The earlier 30-minute report proves
the direct-port throughput only; it is not the current camera index or final bean scene.

```bash
beansight-camera-preflight \
  --top-match C920 --wrist-match C270 --duration 10 \
  --output results/camera_launch/PILOT_TRAIN
```

Inspect both sample frames. Confirm that `top` is the C920 view before using its report. Keep the
C270 connected for semantic identity, but never put a C270 image in the perception manifest.

Start each session with a neutral reference, capture one PNG per bean, and finish with another
neutral reference:

```bash
beansight-capture-perception \
  results/camera_launch/PILOT_TRAIN/camera_preflight.json \
  --settings private/perception_capture_settings.json \
  --output data/perception/pilot \
  --session-id PILOT_TRAIN --lot-id LOT_A --geometry-id PILOT_GEOM_01 \
  --neutral begin

beansight-capture-perception \
  results/camera_launch/PILOT_TRAIN/camera_preflight.json \
  --settings private/perception_capture_settings.json \
  --output data/perception/pilot \
  --session-id PILOT_TRAIN --lot-id LOT_A --geometry-id PILOT_GEOM_01 \
  --bean-id PILOT_B001

beansight-capture-perception \
  results/camera_launch/PILOT_TRAIN/camera_preflight.json \
  --settings private/perception_capture_settings.json \
  --output data/perception/pilot \
  --session-id PILOT_TRAIN --lot-id LOT_A --geometry-id PILOT_GEOM_01 \
  --neutral end
```

Repeat the middle command with the predeclared randomized roster, then repeat the complete sequence
for `PILOT_VAL` and `PILOT_TEST`. The tool saves a lossless full-frame 640×480 PNG and JSON sidecar,
refuses overwrites, records image/settings/preflight hashes, and never displays a prediction.

## 5. Build and validate the manifest

Copy the example schemas into `private/`, then fill them from the blind records and predeclared split
plan:

```bash
cp configs/perception_blind_labels.example.csv private/perception_blind_labels.csv
cp configs/perception_split_assignments.example.csv private/perception_splits.csv
```

Build the six-column manifest only after all three sessions have beginning and ending references:

```bash
beansight-build-perception-manifest \
  data/perception/pilot \
  private/perception_blind_labels.csv \
  --split-assignments private/perception_splits.csv \
  --config configs/perception.json \
  --output data/perception/pilot_qa/manifest.csv \
  --qa-summary data/perception/pilot_qa/manifest_qa.json
```

The builder fails on missing or empty IDs and unsupported labels; it excludes ambiguous examples
from the scored set. It also fails on more or fewer than one canonical image per bean, changed
session provenance, missing reference frames, bad hashes, decode failures, non-RGB or non-640×480
images, C270 contamination, duplicate
paths/hashes, split leakage, train/test lot overlap, and unreviewed cross-split near duplicates.

If perceptual hashing reports a possible near duplicate, inspect the two ROI crops side by side. Fix
an accidental recapture or split mistake. Only a verified false positive may receive a non-empty
reason in a copied waiver file; never waive a pair simply to make the command pass.

For the final collection, provide the permanent pilot exclusion list:

```bash
beansight-build-perception-manifest \
  data/perception/final \
  private/perception_blind_labels_final.csv \
  --split-assignments private/perception_splits_final.csv \
  --exclude-pilot-ids-file private/sourcing/pilot_ids.csv \
  --config configs/perception.json \
  --output data/perception/final_qa/manifest.csv \
  --qa-summary data/perception/final_qa/manifest_qa.json
```

The final target is 300–500 unique beans, at least 50 visible rejects, and at least two Vietnamese
Robusta lots. Treat those as targets until the QA summary proves the actual counts.

## 6. Manual image gate

Automated checks cannot decide whether a defect is actually visible. Before any model run, inspect
every full-size PNG and a contact sheet:

- exactly one sharp, unobscured bean is inside the configured ROI;
- every reject's declared defect is visible in that photographed presentation;
- there is no hand, bag, business label, glare, label card, or class-correlated background cue;
- the ROI shows only uniform mat gridlines — no numerals, angle labels, branding, or template
  shapes (see the amended background rule in section 2);
- no specular hotspot from the mat's sheen appears inside the ROI in any frame;
- acceptable and reject beans are interleaved across the session rather than captured in two
  different lighting blocks;
- the beginning and ending neutral references show no visible lighting, color, or geometry drift.

Recapture warnings before training. Do not repair a blind label after viewing model output.

## 7. Private Hugging Face and Colab smoke

Keep raw collection local and gitignored until it passes both gates. Then create a private Hugging
Face dataset repository, leave its dataset license unset, and upload the validated snapshot together
with its capture sidecars, blind-label export, split assignments, manifest, and QA summary. Keep
business identities, contacts, permission evidence, and grader notes out of the upload.

Stage a self-contained snapshot first. Copy only the capture artifacts and an anonymized label export;
do not copy the rest of `private/`:

```bash
mkdir data/perception/pilot_hf
mkdir data/perception/pilot_hf/capture_metadata
cp -R data/perception/pilot/canonical data/perception/pilot_hf/capture_metadata/
cp -R data/perception/pilot/references data/perception/pilot_hf/capture_metadata/
cp private/perception_blind_labels.csv data/perception/pilot_hf/blind_labels.csv
cp private/perception_splits.csv data/perception/pilot_hf/split_assignments.csv
cp configs/perception.json data/perception/pilot_hf/perception.json

beansight-build-perception-manifest \
  data/perception/pilot_hf/capture_metadata \
  data/perception/pilot_hf/blind_labels.csv \
  --split-assignments data/perception/pilot_hf/split_assignments.csv \
  --config data/perception/pilot_hf/perception.json \
  --output data/perception/pilot_hf/manifest.csv \
  --qa-summary data/perception/pilot_hf/manifest_qa.json
```

Before upload, open `blind_labels.csv` and confirm that contact details, business identity, private
notes, and grader notes are absent. The example schema's `grader_notes` column may remain only if all
cells are blank; removing that extra column is safer.

Authenticate interactively, create the repository as private, and upload the whole staged folder:

```bash
hf auth login
hf repos create YOUR_HF_USER/beansight-vn-perception-pilot --repo-type dataset --private
hf upload YOUR_HF_USER/beansight-vn-perception-pilot \
  data/perception/pilot_hf . --repo-type dataset
```

Record the full 40-character Hub commit. Pull that exact revision into a fresh directory and rerun
the manifest builder. The prepared [Colab notebook](../notebooks/perception_colab_smoke.ipynb) does
this using a fine-grained read-only `HF_TOKEN` stored in Colab Secrets, then runs one epoch only to
exercise the loader and training path. It suppresses pilot metrics because the pilot is not an
evaluation.

Hugging Face is the canonical store because the experiment can pin one immutable dataset revision.
Kaggle would create a second source of truth; use it only as an optional public mirror after photo
permissions, license, card, and limitations are complete.

## 8. Final training on Vast.ai

Do not rent a GPU until the final QA summary passes on the exact private Hub revision. Before launch,
write one sentence explaining what the paid run answers that the free Colab smoke did not, set a
cost cap, and record the exact code commit, dataset commit, seed, image, GPU, and planned epochs.

Use a pinned plain CUDA/PyTorch image, clone the exact BeanSight code commit, download the exact
dataset commit into a fresh directory, and rerun QA. Then:

```bash
beansight-train-perception data_snapshot/manifest.csv \
  --config /workspace/so101-robot/configs/perception.json \
  --dataset-revision FULL_40_CHARACTER_HF_COMMIT \
  --epochs 10 \
  --output outputs/perception/resnet18
```

Abort on NaN or Inf. Preserve `model_state.pt`, `model.ts`, `metrics.json`,
`operating_threshold.json`, and `provenance.json`; log the actual GPU-hours and cost in `COSTS.md`;
then destroy, not pause, the Vast instance. The M1 is for capture and inference, never training.

The operating threshold comes only from the validation curve of the validation-selected checkpoint.
The test split is evaluated once at that frozen threshold. Runtime must pass the saved operating
threshold explicitly to `TorchScriptClassifier`; the controller's reject-confidence threshold is a
separate motion gate.

### Background-dependence probe (mandatory before any success claim)

Training and test share the printed-mat background, so background exploitation *inflates* test
metrics — no in-domain number can detect it. After the final training run, and before reporting any
result:

1. Re-photograph 20–30 already-labeled archived beans (mixed classes, same `bean_id`s) on **plain
   white paper** with the same C920, locked settings, and lamp, using the capture CLI with
   `--geometry-id PROBE_GEOM_01 --session-id PROBE_01` into `data/perception/probe/`. Skip and log
   any bean whose physical specimen was lost.
2. `data/perception/probe/` is never passed to `beansight-build-perception-manifest`, never
   uploaded, and never enters a split. Probe scores are diagnostics, not benchmarks; the operating
   threshold is never tuned against them.
3. Run the gate:

```bash
beansight-background-probe \
  data/perception/probe/canonical \
  private/perception_blind_labels_final.csv \
  --model outputs/perception/resnet18/model.ts \
  --config configs/perception.json \
  --threshold-artifact outputs/perception/resnet18/operating_threshold.json \
  --in-domain-successes TEST_CORRECT --in-domain-trials TEST_TOTAL \
  --saliency 10 \
  --output results/perception_probe/report.json
```

Pre-declared thresholds (fixed 2026-07-21, before any model existed; never retuned): probe accuracy
≥ 15 percentage points below in-domain test accuracy **with disjoint Wilson 95% intervals** flags
the dataset as background-dependent — the surface changes to a neutral matte card and affected
splits are recaptured (same `bean_id`s, new sessions). Independently, occlusion-saliency heatmaps
for 10 probe images go into the writeup; off-bean attribution dominating in more than 2 of 10 is
reported as a background-dependence signal even if the accuracy gap passes.

## 9. When the arm arrives

Pre-arm C270 frames cannot train ACT. Manipulation data begins only after arrival-day inventory,
assembly, calibration, and physical gates.

Before any power: photograph and cross-check every servo, controller, supply voltage/current,
barrel polarity, and invoice. Only after that check, leader arm uses 5 V and follower arm uses 12 V;
never swap them. Assign motor IDs one motor at a time, never on a daisy chain. Keep the controller
unarmed, operate only under supervision with the switched cutoff in reach, and permanently remove
every gripper-touched bean from food use.

After measuring real gripper clearance, freeze the final nest. If it differs from the pilot nest,
start a new `geometry_id` and `session_id` and recapture the final perception set instead of mixing
the two domains.

## Appendix: capture-day quickstart checklist

The long-form rules above win on any conflict. This is the one-page operational order for a session:

1. **Rig**: floor station assembled and verified per
   [capture_rig_setup.md](capture_rig_setup.md) — LS08 on the stool press-tested, C920 at nadir at
   the frozen height, ring lights at their marks, window light blocked, A1 mat **back side** taped
   flat with the marked one-bean nest in a uniform-grid region (ROI must show no
   numerals/branding/templates — see §2). Photograph the fixture marks. Anything moved since last
   session → new `session_id` (and new `geometry_id` if the arrangement changed).
2. **Preflight**: run `beansight-camera-preflight` fresh (after any reboot/replug); confirm the
   `top` sample frame is the C920 bean scene before using its report. C270 stays connected for
   identity, never for perception images.
3. **Settings**: verify against disk, not the app — the frozen values live in
   `private/perception_capture_settings.json` and the CameraController container plist ("disk is
   truth"; the UI has misreported values repeatedly). **CameraController does not open on capture
   days.** If it touched the camera for any reason, capture one throwaway RIGTEST-style frame and
   discard it before the neutral `begin` (AE transient rule,
   [capture_rig_setup.md §8](capture_rig_setup.md)). Exposure is hardware-auto (macOS constraint,
   declared `auto`/null in the settings JSON); the capture CLI rejects placeholders and fabricated
   exposure values.
4. **Draw + seal**: numbered cups from both bags, interleaved and randomized; append
   `private/sourcing/draw_mapping.csv` at draw time; close it (see the sealed draw procedure, §1).
5. **Capture**: neutral `begin` frame → one 640×480 PNG per `bean_id` via
   `beansight-capture-perception` in the predeclared randomized roster → neutral `end` frame. The
   tool refuses overwrites; a recapture keeps the same `bean_id`.
6. **Blind grade**: label every bean in the blind-labels CSV (eight-type vocabulary, `ambiguous`
   allowed) against the written taxonomy, in shuffled cup order, before any model output exists and
   without reopening the draw mapping.
7. **Close out**: recheck settings in the controller, spot-inspect the session's PNGs full-size,
   and file cups/envelopes by `bean_id`.
