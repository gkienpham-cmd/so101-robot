# Perception capture rig — floor station setup guide

This document sets up the physical rig only. The capture *protocol* — sealed draw, blind labels,
session boundaries, neutral references, manifest rules — lives in
[perception_collection.md](perception_collection.md) and always wins on any conflict. Follow this
doc once per session to build and verify the rig, then run the quickstart checklist there.

Decided 2026-07-21: the station is on the **floor** because the A1 mat (90×60 cm) is wider than the
available table. The LS08 boom clamps to a **wooden stool / low table** beside the mat. One bean
per image, always — the manifest builder rejects anything else, and batching by class would
recreate the session–label confound.

## 1. Hardware

- A1 cutting mat, **back side up** (uniform cross-hatch grid; front's templates/ovals stay down)
- ULANZI LS08 clamp boom + Logitech C920 (top camera; the C270 never shoots perception stills)
- Wooden stool or low table (the boom's clamp edge)
- 2× 26 cm USB ring lights on their floor stands
- Masking tape, permanent marker, phone (for level/plumb check and mark photos)
- MacBook + powered hub; ring lights powered from the power strip, **never from the Mac** (its USB
  ports are reserved for cameras)

## 2. Station layout (top view)

```
   window side (BLOCK all daylight: curtains/cardboard — floor level catches it worst)
   ─────────────────────────────────────────────────────────
                                                low-traffic corner
        [ring stand L]                  [ring stand R]
              \  ~45°                     ~45°  /
               \                               /
        ┌───────────────────────────────────────┐
        │        A1 mat, BACK side up           │
        │                                       │
        │              (nest)  ← uniform-grid   │
        │                ▲       region only    │
        └────────────────│──────────────────────┘
                         │  C920 pointing straight down (nadir)
                   ══════╧══════  LS08 boom arm
                        ║
                   [wooden stool]      [operator sits here]
                        ║
                   [Mac + hub on stool or beside]
```

Placement rules:

1. Pick a corner with no foot traffic and no direct daylight. Block floor-level window light
   completely — it shifts with time of day and defeats the locked exposure.
2. Tape the mat flat at all four corners and along the nest-side edge. No curl, no rock.
3. The nest sits in a region where the camera ROI will contain **only uniform gridlines** — no
   numerals, no angle labels, no branding block, no template shapes (runbook §2 rule).

## 3. Boom and stool

1. Clamp the LS08 to the stool edge exactly as it would clamp to a desk; tighten fully.
2. Extend the boom over the nest with the fewest joints unlocked; lock every joint.
3. **Rigidity press-test (required):** open the camera preview, press down lightly on the camera
   head, release, and watch the preview. If the framing does not return to exactly the same place,
   or the image visibly oscillates for more than ~1 s, shorten the boom or add mass to the stool
   (books, a water bottle taped to the base). No bean is captured on a rig that fails this test.
4. Zip-tie the C920 cable to the boom with slack at the head so cable tugs never move the camera.

## 4. Camera: angle and height

**Angle: nadir (straight down).** Lay your phone flat on the C920's top shell and use its level to
get the lens plumb within ~1°. Nadir matches the eventual robot top-camera view, keeps the bean's
top surface (where blind grading happens) fully visible, and makes the specular geometry below
work.

**Height: set by two competing constraints** — this is the binding-constraint trade for this rig:

| Lens-to-mat distance | approx. mm per pixel (640 px width) | 10 mm bean spans |
|---|---|---|
| 10 cm | ~0.22 mm/px | ~45 px |
| 15 cm | ~0.33 mm/px | ~30 px |
| 20 cm | ~0.44 mm/px | ~23 px |
| 25 cm | ~0.55 mm/px | ~18 px |

Lower is more defect pixels; too low and the C920 cannot focus (its near limit is roughly 7–10 cm).
Procedure:

1. Start at ~10 cm lens-to-mat.
2. In CameraController, set **manual focus** and adjust until a bean placed in the nest is
   critically sharp; then lock focus and white balance (50 Hz anti-flicker; exposure stays
   hardware-auto — macOS re-enables C920 AE on every open, see the runbook) per the
   runbook.
3. Screenshot the preview and measure the bean: it should span **≥ ~50 px** (target; ≥40 px is the
   floor). A defect you can't resolve in pixels doesn't exist to the model.
4. If sharp focus is impossible at this height, raise in 2 cm steps and repeat from step 2. If the
   bean drops below the pixel floor before focus is achievable, stop and re-check what the ROI
   shows at the new framing before continuing (the only-uniform-grid rule still binds).
5. When focus, sharpness, and pixel budget all pass: mark the boom joint positions with tape+marker
   and record the height in the session notes. This height is frozen for the whole dataset.

## 5. Ring lights: geometry and settings

**Why not overhead:** the mat's back is semi-gloss. A light shining from where the camera is comes
straight back into the lens (angle of incidence = angle of reflection) — a ring light coaxial with
a nadir camera paints a donut-shaped glare right in the ROI. Off-axis light reflects *away* from
the lens instead.

1. These ring heads do not tilt, so do not try to aim them: collapse both stand columns to their
   **minimum height** (~60–70 cm) and place the stands close, ~30–50 cm horizontal from the nest,
   one on each side, opposed. The mat receives oblique light — that is expected and fine for a
   nadir camera (glancing specular reflects away from the lens, not into it). Two opposed lights
   cancel each other's shadows. Never wedge a stand base with blocks to tilt it — a tipped stand
   falls on the rig; if the mat is underlit, move the stands closer instead.
2. Both rings: **white mode**, the **same brightness step**, dials taped (they are the same model —
   verify same batch behavior by eye: no color difference on a sheet of white paper).
3. Power both from the power strip. Never from the Mac.
4. **Rings are the only light sources.** All room lights off, daylight fully blocked — the mains
   ceiling light flickers at 100 Hz against the rolling shutter, casts your moving shadow over the
   nest from above, and can be silently toggled by someone else. Lock focus/white balance under
   this final configuration (rings on, room dark); values locked under different lighting are
   meaningless. Exposure is hardware-auto (macOS AVFoundation constraint) — constant room lighting
   is what keeps its converged operating point repeatable.
5. **Glare check (required, every session):** with the scene lit and no bean in the nest, inspect
   the live ROI: zero specular hotspots, no donut reflection, no stand or boom shadow crossing the
   nest. The neutral `begin` frame is the recorded evidence of this check.
6. If a hotspot appears: widen the off-axis angle first; move a stand, never touch brightness.
   A brightness change mid-lot is a new `session_id`.

Capturing at night with the room dark satisfies the no-daylight rule automatically. Any session
that must happen in daytime needs the window fully blocked to match — night sessions and leaky
daytime sessions are different lighting domains. Inference and demo videos must later run under
this same rings-only lighting (project rule: collection and inference lighting identical).

## 6. Marks and photos (before the first bean, and checked every session)

Tape-and-marker outline, then photograph together as the session's fixture record:

- all four mat corners and the nest position on the mat
- stool feet positions and the boom clamp location on the stool edge
- both ring-stand feet positions (tripod leg tips)
- boom joint angles (tape flags at each locked joint)

Anything found off its mark, or bumped mid-session (someone walks through, a stand shifts):
re-align to the photos, start a **new `session_id`**, and capture fresh neutral references.

## 7. Where files go

| Path | Contents | Git status |
|---|---|---|
| `data/perception/pilot/` | 24-bean pilot captures (PNG + JSON sidecars via the capture CLI) | ignored |
| `data/perception/final/` | full-collection captures | ignored |
| `data/perception/probe/` | post-training plain-paper probe re-shoot — **never a manifest source** | ignored |
| `private/sourcing/` | `draw_mapping.csv`, `pilot_ids.csv` | ignored (private) |
| `private/` | filled capture-settings JSON, blind-labels CSVs, split CSVs | ignored (private) |
| `results/camera_launch/<SESSION>/` | preflight reports consumed by the capture CLI | tracked policy per runbook |

## 8. Session flow (floor-specific rules on top of the quickstart)

Run the runbook's capture-day quickstart for the protocol steps. Floor additions:

- **AE transient rule (measured 2026-07-22):** the first capture after CameraController touches
  the camera is systematically overexposed (~210 mean vs ~130–170 converged; reproduced four
  times), and the built-in warmup does not absorb it. If the app touched the camera for any
  reason, capture one throwaway frame (RIGTEST-style session, never a data session) and discard
  it before the neutral `begin`. Best policy: CameraController never opens on a capture day.

- Wipe the mat's nest region with a dry cloth at session start (floor = dust).
- Nobody walks in the room during capture; work in socks; the operator stays seated in one spot.
- Sessions **≤ 60 minutes**. Kneeling/floor posture drifts, and drifting posture nudges fixtures.
  300+ beans happen across many short sessions, not one long one.
- Recheck all marks (section 6) against the photos at every session start and end.

## 9. Do not

- Do not capture on a rig that fails the press-test or the glare check.
- Do not put more than one bean in the frame, ever.
- Do not batch by class — draw order comes from the sealed-draw procedure, interleaved.
- Do not let the ROI see numerals, labels, branding, template shapes, hands, bags, or cups.
- Do not power ring lights from the Mac, change light dials mid-lot, or shoot with daylight leaking
  or any room light on — the two rings are the only permitted sources.
- Do not move any marked fixture without starting a new `session_id`.
- Do not tilt a light stand by wedging its base — move it closer or lower instead.
