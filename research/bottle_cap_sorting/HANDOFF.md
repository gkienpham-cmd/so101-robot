# HANDOFF — bottle & cap plastic-type sorting research (for any agent/tool to finish)

**Written:** 2026-07-16, after the deep-research workflow was killed twice by Claude usage limits.
This file is tool-agnostic: everything needed to finish lives in this directory. No Claude-specific
state is required (the resume instructions in `RESUME.md` are optional; this handoff supersedes them).

## Goal

An actionable, adversarially-verified build plan for: SO-101 arm ($55, LeRobot, ACT, 2× 640×480 RGB
cams, no force sensing, 0.2–0.3 kg payload, 35–40 cm reach) picking recyclable water bottles and caps
and sorting them **by plastic type** (PET vs HDPE vs PP …) in the Vietnam/HCMC ve chai context.
Constraints and prior skeptic findings: `docs/vietnam_applications.md` (§3.1 cap sorter, §3.3
3-stream sorter, §5 cross-cutting failure modes). BeanSight is the flagship; this is the transfer test.

## What is DONE (do not redo)

| Stage | Status | Where |
|---|---|---|
| Scope → 5 search angles | ✅ | `salvage_claims.json` → `scope` |
| 5 parallel web-search sweeps | ✅ | `salvage_claims.json` → `search_results` (URLs + titles) |
| Fetch top sources + extract falsifiable claims | ✅ 223 claims from ~47 fetches | `salvage_claims.json` → `claims` (claim, quote, source, quality) |
| Adversarial verification (3 votes/claim, ≥2/3 refutes kill) | ⚠️ 29/223 claims voted: **17 CONFIRMED, 10 REFUTED, 2 mid-vote** | `phase1_partial_findings.md` (readable) + `salvage_claims.json` → `verdicts` (full evidence per vote) |
| Synthesis | ❌ never ran | — |

Raw artifacts in `raw/`: `workflow_journal.jsonl` (every agent's return value),
`first_run_full_output.json` (first run's aggregate), `deep_research_workflow_script.js`
(the orchestration logic — useful as a spec for reimplementing the remaining stages).

## Key confirmed findings so far (steer the plan with these)

1. **Cheap NIR/spectroscopy add-ons are a dead end** for this task: ~$70 AS7265x sensor tops out at
   ~72.5% across 6 resins, worst on PET (66%), and confuses exactly HDPE↔PP and PET↔PVC. (3-0 confirmed;
   the claim that it's a "plausible cheap add-on" was 0-3 REFUTED.)
2. **RGB vision is the right modality**: AMP Robotics' commercial sorter classifies by camera-visible
   features (color, shape, texture, brand labels) — same modality as the SO-101's webcams. (3-0)
3. **End-to-end ACT fails at identify-then-sort**: published SO-101 benchmark — 75% on plain
   pick-and-place, **0% on selective color sorting among distractors** with 100 demos. (3-0)
   → Architecture must be **decoupled**: external classifier picks the bin; policy only grasps.
4. **Published plastic-classification accuracies (99%+) are inflated** by controlled conditions and
   probable object-level train/test leakage; discount them when scoping. (3-0, two separate claims)
5. **Black/dark plastics defeat NIR** even commercially (TOMRA needs add-ons). (3-0)
6. Full list of 17 confirmed + 10 refuted with per-vote evidence: `phase1_partial_findings.md`.

## REMAINING TASKS (in order)

### Task 1 — finish verification (~1–2h of agent work)
- Complete the 2 mid-vote claims (each needs 2 more skeptic votes; see `phase1_partial_findings.md` bottom).
- From the 194 unverified claims (`salvage_unverified_claims.json`), select the ~25–40 most
  load-bearing for the build plan (prioritize: grasp physics for caps/bottles, crushed-PET handling,
  YOLO fine-tuning dataset sizes, resin-code readability at 640×480, ve chai price validation,
  ZenRobotics/TOMRA transfer lessons, decoupled-perception architectures on LeRobot).
- Verification protocol (mirror what was done): per claim, 3 independent skeptic passes, each
  instructed "Be SKEPTICAL. Try to REFUTE this claim" with the source URL; a claim dies on ≥2/3
  refutations. Record evidence + counter-sources per vote.

### Task 2 — synthesize `phase1_research.md`
Merge semantic duplicates among confirmed claims, rank by confidence, group into the five question
areas (a)–(e), cite every claim to its source URL. Explicitly list refuted claims as "known false."

### Task 3 — plan panel (3 competing build plans, then judge)
Draft three independent plans, each grounded ONLY in confirmed findings + `docs/vietnam_applications.md`:
- **Plan A — decoupled perception:** fine-tuned YOLO/classifier (resin code, color, shape priors) picks
  the bin; scripted or short-horizon learned grasp; state machine chains stages.
- **Plan B — ACT end-to-end** (expected to lose given finding 3, but keep it honest — it may win for
  the grasp-only sub-policy).
- **Plan C — hybrid/outside-the-box:** e.g. classifier + ACT grasp policy; cap-vs-bottle pre-separation
  by geometry; weight check via gripper current draw; water float/sink pre-stage done by human;
  turntable presentation to fix pose; "hard-negative" curriculum from ve chai stream photos.
Judge on: feasibility inside the envelope, dataset cost (episodes + $ on vast.ai, ~$0.22/5k steps),
probability of ≥80% per-pick success in 4 weeks, and honest VND value per `docs/vietnam_applications.md` §5
(the $1/hr wall — value is learning/content/education, not labor).

### Task 4 — adversary pass on the winning plan
Attack: cap grasp physics (flat 6mm objects, specular), crushed/clear PET at 640×480, HDPE-vs-PP
visual ambiguity (they often look identical — what breaks the tie? resin code? cap knurling? brand
priors?), horizon math (pᴺ per-stage compounding), lighting drift, and economics. Rescope; iterate
once. Output final `REPORT.md`: verified findings → chosen architecture → bill of materials →
dataset spec (episodes, conditions, HF dataset name `gkienpham/bottlecap_sort_v1`) → 4-week
milestone plan → explicit "what this cannot do" section.

### Task 5 — bookkeeping
Update `RESUME.md` phase log; commit to main.

## File inventory (this directory)

- `phase1_partial_findings.md` — human-readable verdicts (17 confirmed / 10 refuted / 2 partial)
- `salvage_claims.json` — machine-readable: scope, search results, all 223 claims, verdicts w/ evidence
- `salvage_unverified_claims.json` — the 194 claims still needing verification
- `raw/workflow_journal.jsonl` — every completed agent's raw return value
- `raw/first_run_full_output.json` — first run's aggregate output (subset of the above)
- `raw/deep_research_workflow_script.js` — orchestration script (spec for the remaining stages)
- `RESUME.md` — Claude-workflow resume notes (optional path; superseded by this handoff)
