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
| 2026-07-16 | 2× 26 cm USB ring light + 2.1 m stand ("Đèn 26cm + Chân Đèn") | Phụ Kiện Vu Phat (Shopee) | 390,000 (2×195,000 − 10,000 bundle) — ORDERED | ~$15 | Workspace lighting rig (docs/03 §3.2/§3.4). On arrival: same model/batch check, white mode, tape dials. |
| 2026-07-16 | 6-roll colored electrical tape multipack (đủ màu) | QĐPFree (Shopee) | 29,760 — ORDERED | ~$1 | PSU safety labels (red=12V FOLLOWER, blue/white=5V LEADER), PET-bottle bands (yellow), camera-port flags. |
| 2026-07-16 | 100× zip ties 100 mm, black | Diệp Tấn Phát (Shopee) | 16,000 — ORDERED | ~$0.60 | Cable routing along follower arm. |
| 2026-07-16 | 115-in-1 precision screwdriver bit set | Shopee (bought earlier, logged now) | 109,000 — OWNED | ~$4 | Covers PH0–PH2 for M2×6/M3×6 kit screws; low-torque handle, drive M3 patiently. |
| 2026-07-16 | A1 self-healing cutting mat, 90×60 cm, 3 mm PVC, **green** (Xanh) | Ướt DIY (Shopee) | 315,000 — ORDERED, ETA Jul 19–20 | ~$12 | Workspace background (docs/03 §3.4). Green over black: black drags webcam auto-exposure. Anti-slip PVC, still tape the corners. Lie flat overnight — ships rolled. Green wooden blocks = low contrast on this mat; use red/yellow/blue first. |
| — | **Peripherals subtotal** | — | **4,294,911** | **~$165** | Prices as listed before platform vouchers/discounts. Still open: **spare gripper servos + spare Waveshare driver board (AliExpress, ~$40–50 — 7–20 day lead, order FIRST)**; power strip 4–6 sockets + 2–3 USB ports (~150–250k, see note below); masking tape + permanent marker (~20k); side cutters (~30–60k); kitchen scale (~60–120k); 2× USB-A→C adapters (~60–160k); muffin cups + white tray + bowl/reject cups (~70k); mì ly cups + PET bottles + caps (BHX, ~100k); M3×10/12 spare screws (~20k); high-CRI lamp (deferred to coffee phase). |

**Desk power budget (identified 2026-07-16):** the bench needs **4 AC sockets** (Mac charger, Orico hub adapter, 5V leader PSU, 12V follower PSU) **+ 2 USB-A ports** for the ring lights. The lights must NOT draw from the Mac — those ports are reserved for the cameras. One ổ cắm điện (Điện Quang/Lioa) with 4–6 sockets and 2–3 USB ports covers both.
