# COSTS.md — Cloud & Hardware Spend Tracker

Budget target (cloud): **$8–40 total**. vast.ai balance at project start: **$9.00**.
Rule: justify every GPU run before launching; prefer 5k-step validation runs before full runs; DESTROY (not pause) vast.ai instances when done.

## Cloud spend log

| Date | Item | GPU | GPU-hrs | Cost ($) | Cumulative ($) | Justification |
|------|------|-----|---------|----------|----------------|---------------|
| 2026-07-14 | ACT dry run, 5k steps on `lerobot/svla_so101_pickplace` → `gkienpham/act_dryrun` | RTX 4090 | ~0.7 | 0.22 | 0.22 | Prove Hub→GPU→wandb→checkpoint→MPS loop before own data exists. Result: loss 6.4→~0.7, checkpoint verified on Hub + loaded on M1 MPS. Instance destroyed. |

## Planned spend (estimates from SO-101 Plan.md)

| Week | Item | Est. cost |
|------|------|-----------|
| 1 | ~~ACT dry run~~ DONE: $0.22 actual (4090, ~40 min incl. setup) — estimates below likely similarly padded | $2–3 est |
| 3 | ACT full training on own dataset (~3 hrs, 5090) | $2–3 |
| 3 | Retrain after targeted data iteration | $2–3 |
| 4 | SmolVLA fine-tune (~4 hrs, A100 or 5090) | $3–5 |
| — | **Total projected** | **$9–14** |

⚠️ $9 balance covers Week 1 + roughly one more run. Top up ~$10 before Week 3 training.

## Hardware spend (reference — already committed)

See SO-101 Plan.md Part 1F for the full BOM. Log actual landed costs (incl. VN customs) here when the kit arrives.

| Date | Item | Seller | Cost (VND) | Cost (~$) | Notes |
|------|------|--------|-----------|-----------|-------|
| 2026-07-15 | Logitech C920 Pro (overhead cam) + C270 (wrist cam), one Shopee checkout | LOGITECH OFFICIAL STORE (Mall) / Trọng Ân Audio Tp.HCM | 2,288,736 (C920 1,830,360 + C270 458,376, after vouchers) — PAID, in transit | ~$88 | Recommended-tier pair from CAMERA-RESEARCH-REPORT.md. C270 needs lens refocus mod before wrist mounting; lock C920 AF in Logi Tune. |
| 2026-07-15 | ULANZI LS08 clamp boom arm (overhead cam mount, 1/4-20) | Ulanzi_Việt Nam (Shopee) | 742,000 — PAID, ETA Jul 16–17 | ~$29 | Rigid lockable arm; set-once framing for the overhead C920. |
| 2026-07-15 | Orico PW7U 7-port USB 3.0 powered hub (USB-C 100cm host cable) | Orico Official Mall.VN (Shopee Mall) | 296,415 — PAID, ETA ≤Jul 20 | ~$11 | Hosts 2 cams + 2 servo adapters. ON ARRIVAL: confirm AC adapter in box + no dropouts with all 4 devices live. |
| 2026-07-15 | 25× wooden color blocks, 3 cm | Đồ Chơi Gỗ Việt Nam KEN (Shopee) | 108,000 — PAID, ETA Jul 16–17 | ~$4 | Month-1 task objects (25–40 mm target ✓). |
| — | **Peripherals subtotal** | — | **3,435,151** | **~$132** | Within report estimate (3.2–3.6M). Still open: white tray + bowl/reject cups (~50k), M3×10/12 spare screws (~20k), high-CRI lamp (deferred to coffee phase), spare follower servos (optional, ProE 790k ea). |
