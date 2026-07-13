# Dataset study: `lerobot/svla_so101_pickplace` (2026-07-14)

Reference dataset for Week-2 collection design. Inspected via `LeRobotDatasetMetadata` (metadata only, no full video download).

## Facts

| Property | Value |
|---|---|
| codebase_version | v3.0 (native to our pinned LeRobot v0.6.0 — no conversion needed) |
| Episodes | 50 |
| Total frames | 11,939 |
| FPS | 30 |
| Avg episode length | **~8.0 s** |
| Robot type | so100_follower (SO-100 software = SO-101 compatible) |
| Cameras | 2 × 640×480 video: `up` (overhead) + `side` |
| Action / state | 6-dim float32 (5 joints + gripper), joint-space |
| Task string | "pink lego brick into the transparent box" |

## Sanity checks

- Action std per joint: [44.6, 36.5, 29.0, 13.2, 17.8, 9.0] — **no zero-std joints** (the known dead-joint recording bug is absent).
- `observation.state` mean/std ≈ `action` mean/std → follower tracks leader commands tightly; a big gap here would mean lag or a broken joint.
- Gripper (dim 6) range 0–33: normalized, mostly-closed distribution — makes sense for a small brick.

## Implications for our Week-2 collection

1. **8-second episodes** at 30 fps ≈ 240 frames/episode — matches the plan's 10-sec target; keep episodes short and end right after placement.
2. **Camera naming discipline:** they used semantic names (`up`, `side`). We'll do the same (`up`, `wrist`) — feature keys become part of the policy contract.
3. **640×480 @ 30 fps** is the community-proven resolution; no reason to go higher (ACT has no built-in resize — higher res = OOM risk at training).
4. **One precise task string** reused across all episodes — needed for SmolVLA language conditioning later; decide ours before recording episode 1.
5. 50 episodes was enough for their SmolVLA demo; our plan (75–100, 5 fixed positions × 15) sits comfortably above.
