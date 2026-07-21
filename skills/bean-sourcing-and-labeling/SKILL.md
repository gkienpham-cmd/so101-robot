---
name: bean-sourcing-and-labeling
description: Source Vietnamese Robusta samples and create defensible blind labels — roaster interview, Vietnamese phone script, purchase branches, two-class scope, ambiguity handling, label records, and separate publication permissions. Use before buying beans, interviewing a roaster, grading samples, or preparing perception ground truth.
---

# Bean sourcing and labeling

Full authority: `docs/data_and_labeling.md` (interview, sourcing, labels, permissions, and capture)
and `docs/evaluation_protocol.md` (frozen scope and split rules).

## 1. Keep the ask narrow

Frame this as a 20–30 minute research interview, not a request for an endorsement. Bring the actual
lamp, nest, sample bags, and a printed label sheet.

Ask which defects are removed by eye, which are unmistakable in one top-down image, whether v1 can
stay limited to the eight clearly visible defect types (black, broken, insect-damaged, dried
cherry, shell/husk, immature/faded, moldy, foreign matter), which examples are ambiguous, how the
two lots differ, whether uncertain beans should be shown to a person, and what would make a
low-cost prototype useful or useless.

Do not ask a photograph to establish food safety, chemistry, moisture, taste, cup quality, or
internal insect damage. Preserve the roaster's wording instead of strengthening it.

## 2. Use the Vietnamese phone opener

> Chào anh/chị, em là Kiên, sinh viên ngành kỹ thuật. Em đang làm một đồ án robot và thị giác máy
> tính: camera nhận diện hạt cà phê nhân bị lỗi rõ ràng như hạt đen hoặc hạt vỡ, rồi một cánh tay
> robot nhỏ gắp hạt lỗi ra. Đây là dự án học tập, quy mô để bàn. Em muốn mua một lượng nhỏ cà phê
> nhân xanh robusta và đặc biệt là hạt được loại ra trong khâu lựa tay. Bên mình có thể hỗ trợ em
> không ạ?

Also ask for origin, screen size, minimum quantity, and whether an experienced sorter can review
approximately 100 beans for a fee.

## 3. Buy according to actual availability

- Separated defect lot: buy 1 kg good Robusta plus 0.5–1 kg rejects for balanced capture.
- Unsorted or low-grade Robusta: buy about 2 kg and require blind hand labeling.
- Sorted clean beans only: buy 1 kg clean plus request a supplier referral; do not manufacture
  black-defect labels.
- If no reject lot exists, ask for `nhân xanh chưa phân loại / chưa bắn màu`.

Useful terms: `cà phê nhân xanh`, `cà phê vối`, `hạt lỗi / hàng loại`, `hạt đen`, `hạt vỡ`,
`lựa tay`, `chưa phân loại`, `sàng`, and `độ ẩm`.

## 4. Label blind and preserve disagreement

Randomize bag order and hide all classifier output. Record:

```csv
bean_id,lot_id,grader_label,visible_defect_type,ambiguous,grader_notes,reviewed_at
B001,LOT_A,acceptable,,false,,2026-07-18
```

- Allow only `acceptable` and `visible_reject` for v1 scored labels.
- Use the eight-type vocabulary from `docs/data_and_labeling.md`: `black`, `broken`,
  `insect_damage`, `dried_cherry`, `shell_husk`, `immature_faded`, `moldy`, `foreign_matter`.
- Give each physical bean one durable `bean_id`; record its lot and review date.
- Preserve disagreements. Keep ambiguous samples outside the scored v1 set.
- Record ground truth before any prediction; never relabel after viewing model output.

The collection target is 300–500 physical beans from at least two Vietnamese Robusta lots,
including at least 50 visible rejects. Treat these as targets until real counts exist; never report
them as achieved prematurely.

## 5. Ask permissions separately

Request distinct yes/no permission for anonymized labels, bean photographs, the business name, and
interview quotations. A yes to one is not consent to the others. Keep contact details and signed
permission outside the public repository.

Hand labeled beans to the capture workflow only after IDs and permissions are recorded. Once a bean
is touched by the gripper, permanently remove it from food use.

## 6. Keep counts and performance claims separate

- Publish actual label/lot/session counts, not collection targets presented as completed work.
- If sourcing or dataset material cites a model or robot rate, include numerator, denominator, and
  Wilson 95% interval; latency requires sample count, median, and p95.
- Every failed physical trial retains exactly one primary frozen failure code.

Blind review controls prediction leakage. It does not make ambiguous defects visible, guarantee
cross-lot generalization, or authorize a food-safety claim.
