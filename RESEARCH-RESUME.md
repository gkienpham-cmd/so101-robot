# Camera + Applications Deep-Research — Resume State

**Purpose:** If this session dies (usage limits), a new Claude Code session can resume from here.
Tell the new session: "Read RESEARCH-RESUME.md and continue the workflow from the last completed phase."

## Task (original request, condensed)
1. Fable 5 Plan agent scopes the whole project first. ✅/❌ see status below
2. Deep-research workflow (model-tiered: fable=critical synthesis, opus=verification, sonnet=search/fetch):
   - Camera options for SO-101 LeRobot rig: how many cameras, which specs; Shopee.vn / Lazada.vn / local HCMC shop options with product names + links; tiers = budget / medium (recommended for this project) / expensive / high-end. Must account for future coffee-bean defect-sorting CV task.
   - Real-world HCMC applications for the SO-101 (laundry, cleaning, organization, etc.) — small-scale but clearly useful, doable in 1 month, with accessory/tool shopping list per idea.
3. Final deliverable: cited report (markdown in repo + artifact).

## Project context (already scouted — do not re-read everything)
- Full plan: `/Users/kienpham/Documents/so101-robot/private/SO-101 Plan.md` (§1D cameras: C270 + C920, 2 DIFFERENT models mandatory)
- Use cases: `/Users/kienpham/Documents/so101-robot/private/SO-101 Use Case Research.md`
- CLAUDE.md: M1 Pro, LeRobot v0.6.0, 640×480@30fps reference dataset (svla_so101_pickplace), 2 cams overhead+wrist, budget discipline.

## Workflow status
- [x] Phase 0: Fable 5 Plan agent scoping — DONE. Full scoping doc saved at `notes/camera-research-scoping.md` (key decisions: 2 cams now + 3rd fixed inspection cam for coffee phase; recommend PAIRS of different models; >=8 px/mm => 1080p over 15-20cm tray sufficient; lighting is the binding constraint; MJPEG + powered hub; report seller+search-string not deep links).
- [~] Phase 1+: Workflow LAUNCHED, running in background.
  - **runId:** `wf_db037f43-d15`
  - **scriptPath:** `/Users/kienpham/.claude/projects/-Users-kienpham-Documents-so101-robot--claude-worktrees-robotic-arm-camera-research-15819e/e22a9df3-90de-424d-86b2-eaa68232c200/workflows/scripts/so101-camera-hcmc-research-wf_db037f43-d15.js`
  - **journal:** `/Users/kienpham/.claude/projects/-Users-kienpham-Documents-so101-robot--claude-worktrees-robotic-arm-camera-research-15819e/e22a9df3-90de-424d-86b2-eaa68232c200/subagents/workflows/wf_db037f43-d15/journal.jsonl`
  - Phases: Search (6 Sonnet angles) → Verify (Opus per-angle + 3-vote panel on 5 critical claims) → Brainstorm (Opus, 8 ideas) → Synthesize (Fable 5 report)
- [x] Final report written to `CAMERA-RESEARCH-REPORT.md` in this worktree + artifact published:
  https://claude.ai/code/artifact/13bf249d-ecb1-405a-9b3a-dad20592e85d

## DONE 2026-07-14 — all phases complete (29 agents, 0 errors, ~25 min)
Nothing left to resume. Key outcomes: buy C920 (overhead) + C270 (wrist, needs lens refocus mod
— its stock fixed focus is only sharp from ~40cm, panel-REFUTED the original assumption);
3rd inspection cam (OV5693 @ ProE ~950k VND) deferred to coffee phase; 8 app ideas assessed:
GO = coffee defect sort (flagship), pharmacy box handling, desk organization, STEM demo;
MAYBE = TikTok-Shop kitting; NO-GO = sock pairing, laundry folding, wiping.

## How to resume the workflow after a crash / usage limit
```
Workflow({ scriptPath: "<scriptPath above>", resumeFromRunId: "wf_db037f43-d15" })
```
Completed agent() calls return cached results instantly; only unfinished stages re-run.
If the workflow COMPLETED but the session died before the report was written: read the journal.jsonl above — the `synthesize:final-report` agent's return value IS the full markdown report; just save it to `CAMERA-RESEARCH-REPORT.md` and publish.
