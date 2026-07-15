# Camera & Applications Research — Scoping Document (Fable 5 Plan agent, 2026-07-14)

> Produced by the Fable 5 Plan agent before the completed deep-research workflow. This is the
> decision framework behind `CAMERA-RESEARCH-REPORT.md`.

## A. Camera Requirements Spec

### A1. How many cameras — decision: 2 now, 3 by semester 2

- **Month 1 (imitation learning): exactly 2.** The reference dataset format is 2 views (overhead/front + wrist) at 640×480@30fps; ACT/SmolVLA community results (e.g., ggand0's vla-so101: wrist + overhead C920) confirm 2 views is the practiced standard. A 3rd camera adds USB load, dataset size, and training cost for marginal gain — no.
- **Coffee-bean phase (semester 2): add 1 dedicated inspection camera → 3 total.** The wrist cam moves and the teleop overhead cam is framed for the whole workspace; defect classification wants a *fixed, close, color-stable* view of the tray. Don't buy it now — but the research report must name 2–3 candidate models with VN availability so the purchase is a 1-day decision later. Candidates: ELP/HBV 1080p USB module with manual-focus M12 lens (hshop.vn stocks these), or repurpose the C920 overhead + buy a cheap module for teleop.

### A2. Hard constraints (any candidate must pass ALL)

1. **UVC class-compliant, zero-driver on macOS.** Must appear in `lerobot-find-cameras` / AVFoundation without vendor software. Disqualify anything requiring a Windows app for basic streaming.
2. **Resolution/fps: 640×480@30 is what's consumed.** Anything ≥720p@30 suffices for month 1; >1080p is wasted (ACT has no built-in resize — high res risks OOM). 1080p is only useful headroom for the inspection cam.
3. **Focus: fixed-focus (or lockable AF) on the wrist cam.** AF hunting during arm motion injects blur/inconsistency into policy inputs. C270 is fixed-focus (verify exact focus distance); C920 AF can be locked via Logi Tune on macOS (verify).
4. **FOV:** overhead ~60–78° covers a 10cm workspace from 30–50cm easily; wrist wants wider (~78–90°) to keep gripper + object in frame at 10–20cm. C270=60°, C920=78° — workable either way.
5. **USB bandwidth:** MJPEG at 640×480@30 is ~2–4 MB/s per cam — trivial. Uncompressed YUY2 is ~17.6 MB/s per cam; two on one USB2 hub is marginal. Rule: force MJPEG in LeRobot camera config, put the 2 serial adapters and 2 cams on a *powered* hub or split across the M1 Pro's ports. The binding constraint is isochronous reservation, not raw bandwidth — flag any camera that only offers uncompressed modes.
6. **Mounting:** overhead needs a 1/4-20 tripod thread or sturdy clip (gooseneck/scissor mount). Wrist cam weight matters: a full C920 (~160g) on the wrist eats into the 100–300g payload and needs a printable mount. Research must find which SO-101 wrist-mount STLs exist and for which camera bodies — this may flip the pair to *C920 overhead + C270 (or module) wrist*. Treat wrist assignment as open; the pair itself is settled.
7. **Rolling shutter is fine.** Tabletop speeds at 30fps do not need global shutter; do not pay for it.
8. **Low light / color:** the lamp, not the sensor, is the binding constraint. Require only: no aggressive auto-exposure oscillation, and UVC-exposed manual WB/exposure controls for the inspection cam.

### A3. Coffee-bean specifics (px/mm math)

- Tray 20cm imaged at 640px → 3.2 px/mm → an 8mm bean is ~26px: enough to *localize*, not enough to classify subtle sour/insect defects (~0.5–1mm features need ≥3–5px).
- Target **≥8 px/mm**: 1920px across a ~20cm tray = 9.6 px/mm → beans render at 77–115px. **Conclusion: 1080p over a 15–20cm FOV is sufficient; 4K is only needed for trays >30cm — don't buy 4K.**
- **White-balance and exposure LOCK are mandatory** for the inspection cam (auto-WB drift shifts bean color between frames → classifier drift). Strongest argument for an ELP/Arducam module with manual controls over a consumer webcam.
- **Close focus:** at 20–30cm working distance, fixed-focus consumer cams optimized for ~50cm may be soft — verify C270's actual minimum sharp distance. Manual-focus M12 lens modules win here.
- **Lighting is the binding constraint:** a diffuse high-CRI clip lamp (~150–400k VND) improves defect separability more than any camera upgrade.

### A4. Tiers (VND, per camera) — recommend as PAIRS (A5)

| Tier | Band | Representative models to hunt for in VN |
|---|---|---|
| Budget | <300k | No-name 1080p webcams, Rapoo C200, **Logitech C270** (235–299k), HBV bare modules |
| **Medium (recommended)** | 300k–1.2M | **Logitech C920/C920e** (700k–1M), C922, ELP/HBV 1080p USB modules w/ manual focus (hshop.vn ~200–500k) |
| Expensive | 1.2M–3M | Logitech C930e, Brio 500, Razer Kiyo, OBSBOT Meet |
| High-end | 3M+ | Brio 4K, OBSBOT Tiny 2, Arducam AF/global-shutter modules, **Intel RealSense D405/D435** (~7–10M; depth NOT needed for ACT/SmolVLA; only justify for a future grasp-pose pipeline) |

### A5. Recommend PAIRS (2-different-models rule)

- **Budget pair:** C270 + no-name/HBV 1080p module (~450–550k total)
- **Recommended pair:** C270 + C920 (~950k–1.3M total) — confirm price/stock and pick specific Shopee sellers
- **Stretch pair:** C920 + C930e or ELP manual-focus module (adds inspection-cam reuse value)
- Plus a standalone **inspection-cam candidate list** (tier-medium modules) for semester 2.

## B. Research decomposition — 6 parallel angles

1. LeRobot/SO-101 community camera practice (mounts/STLs, index-swap, MJPEG, RealSense support)
2. Shopee VN pricing/stock
3. Lazada + HCMC brick-and-mortar (hshop.vn, proe.vn, Phong Vũ, GearVN, CellphoneS, Tiki)
4. Machine vision for coffee defect detection
5. 1-month-doable HCMC applications + prior art
6. Accessories in VN (hub, lamp, mounts, trays, cubes, bean samples)

## C. Verification criteria

**Must adversarially verify:** every price (VND + date + seller); decision-driving spec claims (C270 fixed-focus + min sharp distance; C920 AF-lock on macOS; FOV; MJPEG availability; UVC compliance of no-name modules); existence of printable SO-101 wrist mounts per camera model; LeRobot RealSense/depth support status.
**Acceptable with caveat:** Shopee/Lazada deep links are session-dependent — report *seller name + exact search string + price band + date* instead.
**Reject outright:** specs sourced only from a marketplace listing description.

## D. Application brainstorm scope

**Cap: 8 ideas.** Build on existing ranking (coffee/cashew defect-sort flagship, e-commerce kitting, pharmacy box handling, STEM education, bird's-nest impurity picking). New angles to assess honestly: laundry (fold/sort — expect NO-GO), sock-pairing by color (maybe), wiping (likely no-go, force control), small-item desk organization (likely GO). Constraints: payload ≤300g, 2–5mm repeatability, ~10cm workspace, fixed camera, single object class, human-supervised, 75–100 demos. Per idea: description, why-HCMC, difficulty (demo count + success band), accessory list with VND, go/no-go with the binding constraint named.

## E. Report structure

1. Executive summary (buy list + total VND + how-many-cameras answer)
2. Camera requirements spec (constraints table, px/mm math)
3. Tiered recommendations as pairs, with VN sellers/prices/dates
4. Semester-2 inspection camera shortlist
5. Accessories with VND
6. 8 application ideas with go/no-go verdicts
7. Verification log + link-stability caveats
8. Open questions / what to re-check on purchase day
