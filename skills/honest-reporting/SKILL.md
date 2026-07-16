---
name: honest-reporting
description: The evidence standard for any public artifact from this project — numbers with n and Wilson CIs, failure histograms, failures shown in videos, no claims ahead of hardware, and the DECISIONS/COSTS/RETRO logging discipline. Use before publishing or drafting ANY number, figure, video, README claim, or writeup.
---

# Honest reporting

This project's credibility IS the deliverable. A modest, well-measured result with visible
failures beats an inflated one every time. These rules apply to every public artifact: README,
release notes, dataset/model cards, videos, portfolio pages.

## Numbers

- Every rate ships with numerator, denominator, and a **Wilson 95% CI**
  (`beansight_vn.metrics.wilson_interval` / `rate_summary`). Never a bare percentage. Put the
  numerator and denominator beside every percentage in videos too.
- Latency and cycle time: sample count, median, p95.
- Every failed trial keeps exactly one failure code; publish the failure histogram next to the
  success rate. **Do failure triage before celebrating any number.**
- No result exists until real hardware produced it: `results/` never contains invented or
  placeholder data, and the repo claims no physical success rate until the frozen protocol runs.

## Claims

- The claim stays narrow: visible defects (`acceptable` vs `visible_reject`) on Vietnamese Robusta
  green coffee, in a fixed supervised workcell. No food-safety, cup-quality, throughput, or
  worker-replacement claims — ever.
- Honest expectations calibration: a first policy may fail completely ("pecking at the table" is a
  documented first-run outcome); realistic final success is 50–70% on narrow pick-and-place;
  community best-case ≈78%, independent VLA benchmarks 30–56% on SO-101. Flag any draft that
  implies better without evidence.
- If performance is poor, **publish the negative result**: where low-cost manipulation failed,
  what the nest/fingertips changed, which measurements drive the next design.

## Videos

- Hero (60–90 s) and technical (3–5 min) videos both include at least one failure clip and the
  measured failure breakdown. Label sped-up footage. English captions, Vietnamese subtitles.
- Lead with the HCMC coffee problem and the chain of choices — not the model name.

## Artifact chain

Portfolio page → tagged GitHub release → exact immutable HF dataset + policy revisions, W&B run,
experiment manifest, aggregate JSON, videos. Dataset and model releases carry cards with
limitations and license.

## Logging discipline (keeps the writeup reconstructible)

- `DECISIONS.md`: one line per significant choice, with rationale, same day.
- `COSTS.md`: every GPU dollar, logged when the run ends.
- `RETRO.md`: weekly — what broke, what fixed it, what worked first try, carry-over risks.

## Privacy line

Public: code, configs, protocols, results, honest analysis. Private (gitignored, never publish):
`private/`, `logs/`, `videos/` raw footage, admissions strategy, seller chats, receipts,
addresses, roaster contact details, tokens. When in doubt, keep it private and ask the owner.
