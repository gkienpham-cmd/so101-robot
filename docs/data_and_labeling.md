# Coffee data, roaster review, and perception training

This is the complete path from a roaster conversation to a leak-free two-class image dataset.

## Roaster interview

The interview defines a defensible experiment; it is not a request for an endorsement. Keep it to
20–30 minutes and bring the actual lamp, nest, sample bags, and a printed label sheet.

Ask:

1. At this stage of green-bean handling, which visible defects do you remove by eye?
2. Which are unmistakable in one top-down image?
3. Can v1 include only clearly black, clearly broken beans, and specified foreign matter?
4. Which examples should be marked ambiguous and excluded?
5. Does the importance or appearance change between the two lots?
6. Would presenting uncertain beans to a person be more useful than forcing an automatic decision?
7. What would make a low-cost prototype useful or useless in a small HCMC roasting workflow?

Do not ask for medical, chemical, food-safety, moisture, taste, or cup-quality conclusions from a
photograph. Record the roaster's wording instead of translating it into a stronger claim.

## Blind labels and permission

Randomize bag order and hide classifier output. Record:

```csv
bean_id,lot_id,grader_label,visible_defect_type,ambiguous,grader_notes,reviewed_at
B001,LOT_A,acceptable,,false,,2026-07-18
B002,LOT_A,visible_reject,black,false,,2026-07-18
```

Allowed labels are `acceptable` and `visible_reject`. Initial defect types are `black`, `broken`, and
`foreign_matter`. Preserve disagreements. Ambiguous samples remain outside the scored v1 set.

Ask separately for permission to publish anonymized labels, bean photographs, the business name, and
interview quotations. A yes to one is not a yes to the others. Contact details and signed permission
remain outside the public repository.

## Image capture

Use the final C920 mount, fixed lamp, matte surface, and inspection nest. Lock focus, exposure, and
white balance before the first session. Capture the top-camera stream already used by the robot; do
not open a second C920 process.

Give every physical bean a durable `bean_id`. Record its `lot_id`, `session_id`, blind label,
visible-defect category, and any disagreement. A burst may help select one sharp image, but it does
not create several independent beans.

The training manifest is CSV:

```csv
path,label,bean_id,lot_id,session_id,split
images/B001.jpg,acceptable,B001,LOT_A,S01,train
images/B302.jpg,visible_reject,B302,LOT_B,S04,test
```

`beansight-train-perception` rejects a manifest if a bean or capture session crosses splits, or if a
test lot appears in training. Validation may use a different session from the training lot; the test
lot stays held out. Adjacent frames are not independent examples.

## Baseline and transfer model

Calibrate the dark-pixel/shape baseline using training and validation data only. Values in
`configs/perception.json` remain placeholders until the fixed lighting exists. Then train one compact
transfer model:

```bash
pip install -e '.[perception]'
beansight-train-perception data/coffee/manifest.csv \
  --architecture resnet18 \
  --epochs 10 \
  --output outputs/perception/resnet18
```

The trainer saves a state dictionary, CPU/M1-compatible TorchScript model, epoch history, confusion
matrix, macro-F1, false-accept and false-reject rates, and a validation threshold curve from 0.05 to
0.95. Freeze the operating threshold from validation data before physical evaluation. Training aborts
on NaN/Inf.

USK-Coffee and CBD may exercise the code, but they do not replace the final Vietnamese Robusta test
set captured in this workcell. Publish the real dataset only with permission and a card describing
label scope, lot/session splits, lighting, bias, license, and non-food-safety limitations.
