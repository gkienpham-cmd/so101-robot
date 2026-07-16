# Bottle & Cap Plastic-Type Sorting — workflow recovery notes

**Goal:** adversarially-verified research + build plan for picking recyclable water
bottles/caps and sorting them by plastic type (PET / HDPE / PP …) with the SO-101,
via computer vision + other suitable techniques. Extends the rescoped cap-sorter idea
in `docs/vietnam_applications.md` §3.1 and the 3-stream sorter §3.3.

## Orchestration plan (3 phases)

1. **Phase 1 — Deep research (RUNNING):** built-in `deep-research` workflow.
   5 parallel search angles → fetch top sources → extract falsifiable claims →
   3-vote adversarial verification per claim → cited synthesis.
2. **Phase 2 — Plan-agent panel (after phase 1):** parallel planner agents draft
   competing build plans (perception-first vs ACT-end-to-end vs hybrid), judged and
   merged.
3. **Phase 3 — Adversary pass on the winning plan:** skeptic agents attack grasp
   physics, 640×480 perception limits, horizon math, and VND economics (same method
   as the existing doc), then final synthesis into `research/bottle_cap_sorting/REPORT.md`.

## How to resume if the session dies mid-run (usage limits etc.)

Phase 1 run:

- **Run ID:** `wf_24bbc770-1fc`
- **Script file:** `/Users/kienpham/.claude/projects/-Users-kienpham-Documents-so101-robot--claude-worktrees-bottle-cap-sorting-vision-eebb2c/b1c24470-259a-4008-a8d9-a0a4cb85420d/workflows/scripts/deep-research-wf_24bbc770-1fc.js`
- **Journal (per-agent results, survives crashes):** `/Users/kienpham/.claude/projects/-Users-kienpham-Documents-so101-robot--claude-worktrees-bottle-cap-sorting-vision-eebb2c/b1c24470-259a-4008-a8d9-a0a4cb85420d/subagents/workflows/wf_24bbc770-1fc/journal.jsonl`

Recovery steps:

1. Reopen this session (`claude --resume`, pick the "bottle-cap-sorting-vision" session).
2. Tell Claude: *"Resume the deep-research workflow per research/bottle_cap_sorting/RESUME.md"*.
   Claude runs `Workflow({scriptPath: <script file above>, resumeFromRunId: "wf_24bbc770-1fc"})`
   — every already-completed agent returns its cached result instantly; only
   unfinished agents re-run.
3. If the original session is unrecoverable: the journal.jsonl above still holds every
   completed agent's output. In a fresh session, ask Claude to read that journal and
   hand-author a continuation from the cached results — no research is repeated.
4. Phase 2/3 run IDs will be appended below as they launch, same recovery procedure.

## Phase log

- [x] Phase 1 launched — `wf_24bbc770-1fc` (2026-07-16)
- [x] Phase 1 hit usage limit mid-verify (76/106 agents done, 30 verify votes + synthesis failed)
- [x] Phase 1 resumed from cache with same run ID + identical args — only failed agents re-run
- [x] Resume also killed by usage limit mid-verify (135/171 agents journaled)
- [x] All progress salvaged to this directory (2026-07-16 17:35): 223 claims, 17 confirmed /
      10 refuted / 2 mid-vote, raw journal + script copied to `raw/`
- [x] **Handoff written for external completion (ChatGPT Codex): see `HANDOFF.md` — it supersedes
      this file's resume path and lists all remaining tasks (finish verify → synthesize → plan
      panel → adversary pass → REPORT.md)**
- [ ] Phase 1 report saved to `research/bottle_cap_sorting/phase1_research.md`
- [ ] Phase 2 launched — run ID: _pending_
- [ ] Phase 3 launched — run ID: _pending_
- [ ] Final report at `research/bottle_cap_sorting/REPORT.md`
