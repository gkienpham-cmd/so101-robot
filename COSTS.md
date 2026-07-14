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
