# SO-101 Camera & Accessories Research Report — HCMC Sourcing, July 2026

**Prepared 2026-07-14.** All prices in VND with seller and date. Claims marked UNVERIFIED were not confirmed first-hand this session; nothing marked REFUTED is presented as fact anywhere below.

---

## 1. Executive summary — the buy list

**Buy two cameras this week: a Logitech C920 (overhead/scene) and a Logitech C270 (wrist).** The C920 is the community-standard SO-101 scene camera (used in the ggand0/vla-so101 SmolVLA build) and its autofocus can be locked on macOS via Logi Tune or a UVC tool (panel-verified); the C270 is the cheapest camera with dedicated, community-published SO-101 wrist-mount STLs (ProtoFlux, Thingiverse thing:7246089) — with one mandatory caveat: the C270's stock fixed focus is only sharp from ~40 cm out, so plan the well-documented lens un-glue/refocus mod for wrist duty (panel-verified; see §7). Buy the C270 from Phong Vũ at **399,000 VND** (verified live 2026-07-14, in stock) and the C920 from the Logitech Official Store on Shopee at **~1,529,000–1,900,000 VND** (UNVERIFIED — Shopee blocked scraping; CellphoneS had it at 1,890,000 VND but temporarily out of stock, 2026-07-14). Add a genuinely powered USB hub (Ugreen 7-port 20296 w/ 12V adapter, GearVN, ~400,000 VND, price UNVERIFIED), a clamp/gooseneck camera mount (~80,000–200,000), a high-CRI clamp lamp (~150,000–300,000), white trays and colored cubes (~100,000–200,000), and 1 kg of green coffee beans (~150,000–300,000, Saigon Coffee Roastery Q3). **Total: roughly 3,200,000–3,600,000 VND.**

**How many cameras? Two now** (overhead + wrist — matching LeRobot's SO-101 dataset conventions), **plus a third fixed inspection camera in semester 2** for the coffee-defect phase: a manual-focus, WB/exposure-lockable USB module (e.g. OV5693 at ProE, 950,000 VND) mounted rigidly over the inspection tray. Do **not** buy two identical camera models — LeRobot has an open bug (#2754) where a second identical UVC camera fails to enumerate.

---

## 2. Camera requirements spec

| Constraint | Requirement | Why |
|---|---|---|
| Interface | UVC over USB (plug-and-play with LeRobot `OpenCVCamera`) | Confirmed in official LeRobot camera docs |
| Recorded format | 640×480 @ 30 fps | Dominant format across ~66–72% of LeRobot SO-101 datasets (panel-verified); a convention, not a hard rule |
| Compression | MJPEG capable; set `fourcc="MJPG"` in `OpenCVCameraConfig` | Two uncompressed YUY2 640×480@30 streams (~147 Mbps each) risk saturating a shared USB2 hub's isochronous budget; MJPEG shrinks this 4–10× (panel-verified) |
| Focus | Lockable (manual focus, or autofocus that can be disabled via UVC/Logi Tune) | Focus hunting mid-episode corrupts demos |
| Resolution | 1080p sensor is sufficient; **4K is unnecessary** | Frames are stored at 640×480 and models downsample anyway (SmolVLA → 512×512; ACT's ResNet18 has no built-in resize, so oversized frames just cost compute). Panel-verified. |
| Count | 2 for training (overhead + wrist), same order at train and inference | Community report: reordering cameras at inference degrades SmolVLA performance (issue #1763) |
| macOS | Expect camera-index instability | AVFoundation enumeration order isn't stable; only mitigation is mapping names via `ffmpeg -f avfoundation -list_devices` (panel/source-verified) |

**px/mm math for coffee beans.** A 1080p camera (1920 px wide) imaging a 20 cm tray gives 1920/200 = **9.6 px/mm**; over 15 cm, **12.8 px/mm** — both clear the ≥8 px/mm target. An 8–12 mm green bean then spans ~77–123 px, far above the 220×220 to 256×256 px-per-bean resolutions at which published classifiers (MDPI 2019, CBD, USK-COFFEE — all verified) report high accuracy on black/sour/broken defects. **Caveat (marked inference, not published benchmark):** no paper directly tested 1080p-over-15–20cm-tray; and hyperspectral work (MDPI Remote Sensing 2020, verified) shows insect-damage spots are often sub-pixel at machine-vision resolutions — insect damage is the weakest defect class for pure RGB and may need closer working distance or be de-scoped. 4K buys nothing for the ACT/SmolVLA pipeline and little for inspection versus simply moving the camera closer.

---

## 3. Tiered camera pairs

> **Link-stability caveat:** Shopee/Lazada deep links rot and are session-dependent (both platforms blocked scraping this session; several checked URLs had already 404'd). **The durable pointer is seller name + exact in-app search string**, given for every item. All Shopee/Lazada prices below are from search snippets/aggregators, not live pages — re-verify in-app.

### Budget pair — ~900,000 VND
- **Wrist: Logitech C270** — **399,000 VND, Phong Vũ, in stock, verified live 2026-07-14** (`phongvu.vn`); Shopee band ~220,800–478,000 VND across sellers (websosanh floor verified; Shopee figures UNVERIFIED). Search: `webcam logitech c270 chính hãng`. Dedicated SO-101 wrist STL exists (ProtoFlux, Thingiverse thing:7246089 — verified). **Requires the lens refocus mod for <40 cm work** (see §7).
- **Overhead: HXSJ S4 1080p** — **499,000 VND, shop "HXSJ VIỆT NAM", Shopee** (direct listing indexed; price UNVERIFIED in-app, 2026-07-14). Search: `webcam hxsj s4`. Deliberately a *different model* from the wrist cam to dodge LeRobot issue #2754.
- Honest note: budget no-name webcams have unverified marketplace specs (e.g. Rapoo C200 is titled "FullHD 720p" — internally contradictory; it's 720p).

### Medium pair — **RECOMMENDED** — ~1,930,000–2,300,000 VND
- **Overhead: Logitech C920** — CellphoneS **1,890,000 VND** (list 2,890,000), *temporarily out of stock*, verified 2026-07-14; Shopee **~1,529,000 VND** via **LOGITECH OFFICIAL STORE (Shopee Mall)**, UNVERIFIED. Search: `logitech c920 hd pro webcam`. Wide Shopee spread (1.3–2.18M, verified via aggregator) — buy Mall-only; sub-1.2M listings deserve scrutiny (spread may also reflect C920/C920s/C920e variants). Proven in the ggand0/vla-so101 SmolVLA project (verified). Lock autofocus via **Logi Tune** (not Logi Options+ — panel correction) or scripted `uvcc`/`uvc-util`, and re-apply the lock on device connect since it may not survive replug.
- **Wrist: Logitech C270** — 399,000 VND, Phong Vũ (verified), + refocus mod. Same STL as above.
- Why this pair wins: both cameras have proven SO-101 track records, distinct models (no #2754 risk), total under 2.3M VND, and every failure mode has a documented workaround.

### Expensive pair — ~3,100,000–3,500,000 VND
- **Overhead: Logitech Brio 500** — Phong Vũ **2,990,000 VND** (verified live 2026-07-14, −25% from 3,990,000); Phúc Anh ~2,490,000 VND (plausible, page-level UNVERIFIED); GearVN 2,750,000 (snippet, UNVERIFIED — site 403s scrapers). Search: `Logitech Brio 500`.
- **Wrist: Logitech C270** (399,000, Phong Vũ) — or C922 (~2,100,000 VND MemoryZone, out of stock 2026-07-14; Phong Vũ 2,099,000 "Liên hệ") as a second full-shell cam if you'd rather clamp-mount than print. Honest note: above the C920 tier you're paying for conferencing features (HDR, mics) the policy never sees; this tier is mostly not worth it.

### High-end pair — ~13,000,000+ VND (depth option)
- **Wrist: Intel RealSense D405** — **11,148,000 VND, Tiki seller "BrandPC", verified live 2026-07-14** (`tiki.vn`, hàng chính hãng, app-only extra discount noted); ProE.vn ~11,500,000 VND (snippet, UNVERIFIED). Search: `Intel RealSense Depth Camera D405`. First-party wrist STL ships in the official SO-ARM100 repo (verified). Select by `serial_number_or_name` — the one real fix for macOS index instability.
- **Overhead: Logitech C920** as above.
- **Honest note: depth is not needed for ACT/SmolVLA.** LeRobot can record depth (v0.6.0), but no source found in this research shows depth measurably improving ACT or SmolVLA success on SO-101 — the flagship community build uses the D405 as an *RGB-only* wrist cam (verified). Also: RealSense on macOS is officially documented as unstable (sudo workaround), and the D405 silently throttles on USB-2 ports — check `lsusb -t` (both verified). Buy this tier only if you want depth data for later research, not for this semester's tasks.
- D435/D435i price check: ProE (Q11, HCMC) D435 **13,600,000** / D435i **14,150,000 VND** (verified live 2026-07-14) vs Tiki/BrandPC D435i **19,328,800 VND** (verified) — a 5.2M gap; SKU/bundle equivalence unverified, so ProE is the better starting point if you go D435-class.

---

## 4. Semester-2 coffee inspection camera shortlist

The inspection camera must hold **manual focus, locked white balance, and locked exposure** — the lighting-consistency literature makes locked WB/exposure a prerequisite for color-based defect classification (note: inferred from lighting guidance; no paper directly benchmarked auto vs. manual WB — marked as inference).

| Option | Price (seller, date) | Notes |
|---|---|---|
| **OV5693 5MP USB module** | 950,000 VND (ProE.vn, verified live 2026-07-14, but "Liên hệ" button — call 0938946849 to confirm stock) | 2592×1944, USB2 UVC, compact board. Search: `OV5693 USB camera ProE` |
| **Arducam 1080p Low-Light USB module (B0468)** | 2,300,000 VND (ProE.vn, verified live 2026-07-14, add-to-cart active) | Low-distortion lens, best documented local option |
| **InnoMaker U20CAM-1080P** | Not sold on VN marketplaces (Amazon ASIN B0CNCSFQC1) | The camera the *official* SO-101 32×32 mounts are designed around (verified); manual-focus M12 lens. Import if you also want it as a future wrist cam — but never as a *pair* of them (#2754) |
| **ELP/HBV OV2710-class bare modules** | No Shopee VN presence found (verified negative, this session) | AliExpress import only; ~$39–40 USD reference |
| Raspberry Pi Camera Module 3 (864,000–1,323,000 VND, hshop.vn, verified 2026-07-14) | **Not recommended** — CSI ribbon interface, needs a Pi host, not UVC |

Pick: **OV5693 from ProE** if stock confirms by phone; Arducam as the premium fallback.

---

## 5. Accessories list (VND)

| Item | Price (seller, date) | Status | Search string |
|---|---|---|---|
| **Powered USB hub — Ugreen 7-port 20296, 12V/48W adapter** | est. 300,000–500,000 (GearVN, 2026-07-14) | Price UNVERIFIED (GearVN 403s scrapers); the only candidate with a documented true AC adapter | `hub usb 3.0 ugreen 7 cổng 20296 gearvn` |
| Alt hub: UNITEK 4-port "nguồn riêng" | unknown (Shopee) | UNVERIFIED — confirm the AC adapter ships in-box; many "có nguồn" hubs are bus-powered with a charging port only (e.g. Ugreen CM219, 315,000 VND at CellphoneS, verified — Micro-USB 5V/2.4A supplement, *not* a true powered hub) | `hub usb 3.0 unitek 4 cổng nguồn riêng` |
| **Gooseneck/clamp camera mount, 1/4-20** | est. 80,000–200,000 | No exact 1/4-20 gooseneck+clamp confirmed on VN marketplaces this pass; generic clamp arms at witstore.vn/Shopee are the fallback | `giá đỡ camera gooseneck kẹp bàn ren 1/4 xoay đa năng` |
| **High-CRI clamp lamp — Mopi Light, claimed CRI 95–97** | est. 150,000–300,000 (Shopee, 2026-07-14) | Price & CRI claim UNVERIFIED (self-reported) | `đèn kẹp bàn CRI 95 Mopi Light chống cận` |
| Ring light 26–45 cm (classroom/fill) | 100,000–779,000 (various Shopee sellers) | UNVERIFIED snippets; note ring ≠ dome lighting — glare pattern on glossy beans differs | `đèn ring light livestream 26cm 36cm` |
| **White plastic trays (with dividers) + reject cups** | 30,000–100,000 (Shopee, plentiful) | Low risk | `khay nhựa trắng chữ nhật có vách ngăn` |
| **Colored cubes 25–40 mm** | 30,000–80,000 | Pre-cut colored *foam* cubes in this size were not found on VN marketplaces — painted wooden blocks are the practical substitute; verify dimensions in-app | `khối gỗ màu 30mm đồ chơi xếp hình` |
| **Green coffee beans, 1 kg + ask for defect lot** | ~150,000–300,000/kg | **Saigon Coffee Roastery**, 232/13 Võ Thị Sáu Q3, hotline 0938.80.83.85 — explicitly sells green beans (Đà Lạt + imports). "A Roaster" advertises sample testing (per hello5.vn listicle whose price bands, 120,000–520,000/kg, look templated — UNVERIFIED). **No source confirmed defect-lot sales; call ahead.** | `Saigon Coffee Roastery cà phê nhân xanh` |

---

## 6. Eight application ideas — verdicts

Grounded in the verified SO-101 benchmark (Yu & Qiu, arXiv 2606.08881: pick-transfer 70–95%, precision insert 45–80%, multi-object packing 10–55%, **color sorting 0–10% across all four policies**; recovery 3.2–30.8%).

### 6.1 Coffee-bean defect sort (FLAGSHIP) — **GO**
One tray of green beans; the policy picks *already-flagged* beans into a fixed reject cup. Detection (high-CRI light + fixed inspection cam + classical CV) is **decoupled from the policy** — that single architecture decision is the whole ballgame. As a decoupled pick-and-discard it's the robust Pen-Transfer class (70–95% benchmark); pushed into the policy as "sort by appearance" it collapses to the 0–10% regime. HCMC fit is the strongest of any idea: Vietnam is the #2 coffee exporter, hand-sorting is real paid labor at Q3 roasteries, and the identical skill covers cashew and yến sào (bird's-nest) impurity picking. ~90–100 demos; expected 55–75% end-to-end. **Binding constraint: keep discrimination out of the policy.**

### 6.2 Pharmacy blister / small-box handling — **GO**
Single-SKU blister strips or pill boxes into fixed organizer slots — the precision-insert class (45–80%), mirroring the verified Ez_2_AI hackathon pill-box prototype. HCMC's dense nhà thuốc network is a clear customer. ~80–100 demos; expected 45–70% supervised. **Binding constraint: one rigid geometry per policy — mixed SKUs or floppy blisters break it.**

### 6.3 Desk / small-item organization (single class) — **GO**
One rigid item class into one fixed holder: a Pen-Transfer/insert blend, 55–80% expected, ~75–90 demos. The easiest credible "useful" demo and the template for kitting. **Binding constraint: the instant it becomes "sort mixed clutter by category" it inherits the 0–10% sort failure and flips NO-GO.**

### 6.4 STEM education demo — **GO**
Packaged teleop + autonomous cube pick-place with curriculum, for HCMC's booming private STEM-education market. Canonical task, 50–75 demos, 70–90% expected — far above what a supervised classroom demo needs. **Binding constraint: framing, not tech — sell it as education, not automation.**

### 6.5 E-commerce / TikTok-Shop micro-kitting — **MAYBE**
The strongest commercial narrative (live-selling kit assembly is huge in HCMC) mapped onto the *worst-fit* verified capability: multi-object packing benchmarks at 10–55%, with zero hobby-arm prior art found (a real absence, not an unindexed niche), compounded by 3–31% recovery rates. Expected 10–45% for a real 3–4-item kit. **Binding constraint: only viable degraded to one-item-per-box — which is just idea 6.3 wearing a business plan.**

### 6.6 Sock pairing by color — **NO-GO**
Stacks the uniformly-failing color-sort regime (0–10%, verified) on deformable-object grasping, plus two-item matching. Unlike coffee, the color-matching *is* the task and cannot be decoupled. Expected <15%. Not worth accessories money.

### 6.7 Laundry folding — **NO-GO**
The verified prior art (Ez_2_AI: ~70% success over **86 demos** — note: 86 is the demo count, not a success rate; the "86% SmolVLA folding" claim was REFUTED, see §7) ran on a full-size arm over a large table. A folded T-shirt's footprint exceeds this build's ~10 cm workspace by 5–10×. **Binding constraint: the garment physically doesn't fit.**

### 6.8 Cleaning / surface wiping — **NO-GO**
Wiping needs regulated contact force; the SO-101 is position-controlled with no force feedback, so the required control mode isn't expressible — no demo count fixes that. Wrong task class for the imitation-learning pipeline entirely.

---

## 7. Verification log

Three-vote adversarial panel on load-bearing claims, plus per-angle source checks. **REFUTED items show the correction and are not asserted as fact elsewhere in this report.**

| Claim | Status | Evidence / correction |
|---|---|---|
| C270 fixed focus is sharp at 20–40 cm | **REFUTED (3/3 votes)** | **Correction:** C270 is fixed-focus, but factory focus is sharp only from **~40 cm to infinity**; 20 cm is out of focus stock. Wrist use at close range requires the un-glue/refocus lens mod (community-measured; Logitech publishes no min-focus figure). Report recommends the C270 *with this mod*. |
| C920 autofocus can be locked on macOS | **SURVIVES (3/3)** | Via **Logi Tune** (C920 officially supported) or UVC tools (`uvcc`, `uvc-util`, Webcam Settings app). **Correction:** not Logi Options+ (mice/keyboards only); lock may not survive replug — re-apply at device init via script. |
| Printable SO-101 wrist mounts exist for common cameras | **SURVIVES (3/3)** | Official repo ships D405/D435/Vinmooog/32×32-UVC mounts; community C270 mount confirmed (Thingiverse thing:7246089, ProtoFlux). |
| 640×480@30 is the standard SO-101 recorded format; >1080p gives no training benefit | **SURVIVES (3/3, refined)** | ~66–72% of LeRobot dataset cameras; a convention, not mandatory. SmolVLA resizes to 512×512 (hard fact); for ACT "no benefit" is sound engineering inference, not a spec — extra pixels cost compute rather than help. |
| 2 cams + 2 Feetech adapters coexist on M1 Pro if MJPEG; dual YUY2 on shared USB2 hub risks saturation | **SURVIVES (3/3)** | 2× YUY2 640×480@30 ≈ 295 Mbps vs ~384 Mbps isochronous ceiling; Feetech adapters are bulk-transfer serial, negligible. Separate physical ports avoid sharing entirely. |
| HF SmolVLA blog reports 86% T-shirt folding with H=50 flow-matching | **REFUTED** | **Correction:** the blog contains no folding eval; reported rates are ~51.7%/~78.3% on pick-place/stack/sort. "86" was the *demo count* in the separate Ez_2_AI project (~70% folding success). Report uses only the corrected figures. |
| C920e Shopee band 900,000–1,480,000 VND | **REFUTED** | **Correction:** observed Shopee floor is **~1,399,000 VND** (range to ~2,650,000). The 900k bound is unsupported. |
| `fourcc` field in OpenCVCameraConfig, MJPG unlocks higher fps | CONFIRMED | Source file verified on GitHub main. |
| Official 32×32 mount designed for InnoMaker U20CAM-1080P (ASIN B0CNCSFQC1) | CONFIRMED (caveat) | README confirms ASIN/form-factor; FOV/M2-hole/dual-stream details come from the product page, not the README. |
| Official overhead mount targets XPCAM B082X91MPP at 640×480 | CONFIRMED | README verified. |
| macOS AVFoundation index-swap; ffmpeg name-mapping is the only workaround | CONFIRMED (caveat) | Thread verified; the "upcoming OpenCV PRs" sub-claim is UNVERIFIED — dropped from this report. |
| LeRobot #2754: second identical UVC camera fails to read | CONFIRMED | Open issue, reproduced on Ubuntu 24.04 — basis for the "don't buy identical pairs" rule. |
| ggand0/vla-so101 uses C920 + D405 (RGB-only); D405 silently throttled on USB2 | CONFIRMED | Blog verified; `lsusb -t` diagnosis. |
| RealSense D405 11,148,000 VND (Tiki/BrandPC); D435i 19,328,800 VND | CONFIRMED | Live page load 2026-07-14. |
| ProE D435 13,600,000 / D435i 14,150,000 VND, Q11 HCMC | CONFIRMED | Live fetch 2026-07-14; 5.2M gap vs Tiki flagged, SKU match unverified. |
| SO-101 VLA benchmark bands (70–95 / 45–80 / 10–55 / 0–10%) | CONFIRMED | arXiv 2606.08881 verified in full, incl. recovery rates 3.2–30.8%. |
| FiberTune 72.7→78.1% over 128 trials | CONFIRMED | arXiv 2606.08653 verified. |
| Ez_2_AI: 86 demos, ~70% folding, pill-sort prototype, #2 worldwide | CONFIRMED | Corroborated by Lightning AI post; "40 countries" is actually ~44. |
| No VN marketplace/community listings for SO-101 kits | UNVERIFIED | Corroborated negative, but VN-language *news* coverage exists; re-check in-app. |
| Razer Kiyo VND price | UNVERIFIED | Original discontinued at APSHOP (confirmed); GearVN 403-blocked. Dropped from recommendations. |
| Shopee/Lazada prices generally | UNVERIFIED | Both platforms blocked scraping (confirmed); all such prices are snippet-derived. |
| roboticscenter.ai "$230 assembled SO-101 Pro SKU" | CONFIRMED w/ correction | Page confirms ~500 g / ~500 mm / $100–200 DIY, but $230 refers to a follower+leader comparison figure, not an assembled SKU. |
| hshop.vn stocks CSI Pi cameras, not USB/UVC modules | CONFIRMED | Verified; ProE is the HCMC source for USB modules. |

---

## 8. Open questions / re-verify on purchase day

1. **C920 live price & authenticity** — open Shopee app → `LOGITECH OFFICIAL STORE` (Mall) → `logitech c920 hd pro webcam`; confirm ~1.5–1.9M and Mall badge. If CellphoneS has restocked at 1,890,000, prefer it (walk-in, invoice). Everything Shopee-priced in this report is snippet-derived.
2. **Ugreen 20296 hub** — confirm on GearVN (in browser, site blocks bots) that the 12V AC adapter ships in-box and get the live price; the whole "powered hub" category is polluted with bus-powered hubs mislabeled "có nguồn".
3. **C270 refocus mod feasibility** — after purchase, verify the specific unit's lens ring un-glues cleanly and reaches sharp focus at the actual wrist working distance (~10–25 cm) before printing the ProtoFlux mount.
4. **OV5693 stock at ProE** — "Liên hệ" button means call 0938946849 before traveling to Q11; ask about the Arducam B0468 as on-the-spot fallback.
5. **Green-bean defect lots** — call Saigon Coffee Roastery (0938.80.83.85) and A Roaster: do they sell reject/defect-grade beans separately? No source confirmed this; budget for buying standard grade and hand-salting defects if not.
6. **Dual-camera bring-up test (day 1)** — both cameras on separate physical ports first, `fourcc="MJPG"`, run `lerobot-find-cameras`, then script the macOS name→index mapping via ffmpeg; test a bad-cable false positive by swapping cables before blaming software.
7. **Camera order discipline** — fix and document overhead-vs-wrist config order before recording demo #1; inference order must match training order (issue #1763).
8. **Colored cubes & gooseneck mount** — both were unresolved on VN marketplaces; run the in-app search strings (`khối gỗ màu 30mm`, `giá đỡ camera gooseneck kẹp bàn ren 1/4`) and accept substitutes (painted wood cubes; generic clamp arm).
9. **Semester-2 decision point** — before buying the inspection camera, re-test whether the C920 (focus-locked, moved to ~15 cm over the tray) already hits ≥8 px/mm sharp — it may make the third camera purchase cheaper or unnecessary.