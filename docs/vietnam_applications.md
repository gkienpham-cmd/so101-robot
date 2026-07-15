# SO-101 applications and opportunities in Vietnam

**Prepared for:** Kien (HCMC) — WitMotion SO-ARM101 Kit (Pro), 1,443,860 VND + 459,436 VND shipping (~$55 + $18 at ~26,000 VND/USD), arriving Jul 20–25, 2026 ([AliExpress listing](https://vi.aliexpress.com/item/1005011826373928.html))
**Status baseline:** Full sim pipeline proven (gym-hil → HF Hub → vast.ai ACT 5k steps at $0.22 → MPS inference). Real arm, calibration, motor IDs, dual-camera USB bandwidth, and teleop latency all untested. Cloud budget: $8–40 total, $0.22 spent.
**Date:** 2026-07-15

> **Project decision:** this is the retained idea bank, not the current execution order. BeanSight VN
> is the one-month flagship. Bottle-cap sorting is an optional transfer test only after the coffee
> evaluation protocol is frozen. The safety, data, and model gates in the repository root supersede
> conflicting schedules or purchase suggestions below.

---

## 1. Method

This document is the output of a three-stage process:

1. **Research.** Three parallel research tracks on (a) Vietnamese household and food-culture pain points, (b) HCMC waste-separation reality and the ve chai economy, (c) SME/retail/micro-manufacturing repetitive labor costs in HCMC — all with primary Vietnamese-language sources (VnExpress, Thanh Niên, PLO, TGM Research, UNDP, scrap-price tables, job boards).
2. **Ideation.** Twelve application concepts were developed against the arm's *real* envelope: 0.2–0.3 kg payload, ~35–40 cm reach, single parallel gripper, no force sensing, 2× 640×480 webcams, ACT trained from 50–150 teleop demos, no heat or liquid near electronics. Your two seed ideas — instant noodles and trash/plastic sorting — were developed first and kept central.
3. **Adversarial verification.** Every idea was attacked by a skeptic pass focused on grasp physics, perception at 640×480, imitation-learning horizon math (per-stage success compounds: 0.9⁶ ≈ 53%), thermal limits of STS3215 servos, and honest VND economics against ~25,500 VND/hr ($0.98/hr) Region-1 minimum-wage labor. Each idea carries its skeptic score, the critique verbatim in substance, and a concrete rescope. **No idea survived unmodified. None was fully killed either.**

The headline finding: on a $55 arm, **the winning ideas are the ones where the task is honestly inside the envelope and the value is learning, content, education, or awareness — not labor replacement.** Vietnamese labor at $1/hr beats this arm on throughput at everything. What the arm can be first-in-Vietnam at: imitation-learning content in Vietnamese, waste-education demos, and a paid workshop product.

---

## 2. Ranked summary of all ideas

| # | Idea | Skeptic score | Effort | Verdict |
|---|------|:---:|---|---|
| 1 | **"Teach a Robot by Showing It" Workshop Kit** | **7.0/10** | Medium (needs cap-sorter first) | **TIER 1 — best long-term asset; education flywheel** |
| 2 | **Battery & E-Waste Pull-Out Guard** | **6.5/10** | Medium | **TIER 1 — best waste demo; teaches selective grasping + abstention** |
| 3 | **Mock Feeding Assist (mannequin-only)** | **6.5/10** | Medium-High | **TIER 1 — ambitious week-5+ target after quick wins** |
| 4 | **3-Stream Recyclables Sorter** (trash seed) | **6.0/10** | Medium | **TIER 1 — seed idea; rescoped, PRO Vietnam/UNDP angle** |
| 5 | **Bottle-Cap Color Sorter** (transfer test) | **6.0/10** | Low | **TIER 1 — optional after the BeanSight protocol is frozen** |
| 6 | Cà Phê Phin Robot Barista | 6.0/10 | High (grasp engineering) | TIER 2 — viable only with printed grasp fixtures; news peg stale |
| 7 | Microgreen Tray Seeder | 6.0/10 | Medium | TIER 2 — content-only; mushroom size-sort is the better half |
| 8 | **Mì Gói Topping Bar** (noodle seed) | **5.5/10** | High (wet objects) | **TIER 1 — seed idea; feasible only per-stage with props** |
| 9 | TikTok Shop Livestream Presenter | 5.0/10 | Medium | TIER 2 — buildable, but a 200k VND turntable does 90% of it |
| 10 | Tết Gift-Box / Shopee Kitting Cell | 5.0/10 | High | TIER 2 — "overnight unattended" claim is false as scoped |
| 11 | Pharmacy Blister-Pack Sorter | 4.5/10 | High | TIER 2 — flat-object grasp + open-set SKUs; salvage as portfolio piece |
| 12 | Weekly Pill-Organizer Assistant | 4.0/10 | High | TIER 2 — counting is safety-critical and exactly what IL can't guarantee |

Seed-idea honesty up front: **the trash-sorting seed (ideas 2, 4, 5) verified better than the noodle seed (idea 8).** The noodle demo is culturally the strongest but physically the hardest — wet, deformable food is the worst object class for a no-force-sensing gripper. Both survive, rescoped.

---

## 3. TIER 1 — build these

If these ideas are pursued after BeanSight, the risk-reducing sequence is:
**Cap Sorter transfer test → Battery Pull-Out + 3-Stream Sorter → Mì Gói v1 (dry triad) → Mock Feeding → Workshop Kit** (which can reuse the cap sorter as its curriculum). This is a backlog order, not the flagship's 30-day schedule.

---

### 3.1 Bottle-Cap Color Sorter — optional post-flagship transfer test (6.0/10)

**Problem & evidence.** Two problems, one small one real: (a) HDPE/PP caps sell at 20,000–35,000 VND/kg vs 4,000–7,000 VND/kg for PET bodies — every price tier in the ve chai chain is created purely by manual sorting labor, done mostly by informal women workers (~90% of Vietnam's hundreds of thousands of collectors, per [UNDP](https://www.undp.org/vietnam/press-releases/acknowledge-and-promote-role-informal-waste-workers-towards-just-transition-implementing-extended-producer-responsibility-epr); prices per [muaphelieu247.com](https://muaphelieu247.com/bang-gia-phe-lieu-nhua), [phelieunhatminh.com](https://phelieunhatminh.com/bang-gia-ve-chai-moi-nhat-hom-nay/)). (b) You personally need the lowest-risk first task to shake down calibration, motor-ID assignment (one servo at a time), USB bandwidth for 2 cameras, and teleop latency — all currently untested.

**Skeptic verdict, honestly stated.** The core survives — this is the canonical LeRobot cube-sort with caps. But: metal crown caps are a **physics trap** (6 mm tall, dead flat, crimped skirt — one of the *harder* tabletop grasps, plus specular glare that shifts between 3pm and 8pm light). "Mixed pile" contradicts feasibility — touching caps mean occluded grasps. And the economics are decoration: the real ve chai labor is *removing* caps from bottles (torque, two hands, out of envelope), and steel-vs-HDPE separation is done instantly by a 20,000 VND magnet. Say that on camera — the honesty is itself good content.

**What the arm does (rescoped v1).** Three colors of **upright plastic screw caps only** — no crown caps, no lying-on-side poses, no piles. One cap spawns at a time in a marked 15×15 cm region; arm picks it and drops it into the matching wide-mouth jar (≥80 mm mouth). Crown caps return later as an explicitly labeled "hard mode" dataset.

**Workspace setup.**
- 25×25 cm work area + 3 jars at permanently fixed positions within 25 cm of the spawn zone
- Low rim or tray around the zone so bounced caps stay in frame
- One fixed lamp, curtains closed — record all of v1 in a single lighting condition
- Top cam + wrist cam at 640×480; record with `--dataset.streaming_encoding=true --dataset.encoder_threads=2` (the macOS crash workaround — `parallel_encoding` is a Python-API parameter, not a v0.6.0 CLI flag; see `docs/runbook.md`)
- 5V PSU = leader, 12V PSU = follower. Never swap.

**First dataset.** `gkienpham/cap_sort_v1` — **60–75 episodes** (~20–25 per color), single pick-and-drop, randomized cap color and position within the spawn zone. (Original plan said 50; skeptic math says 50 across 3 jars × types × positions is ~5–15 per condition bucket — too thin for ACT.)

**4-week milestone.** Week 1: assembly, calibration, motor IDs, camera bandwidth check, first teleop. Week 2: record 60–75 episodes, train on vast.ai (~$0.25–0.50), deploy. Success metric: **end-to-end pipeline runs on real hardware and the policy beats random jar assignment** — not throughput. Weeks 3–4: iterate to ≥80% per-pick success; cut the first "satisfying sorting loop" short-form video, stating on camera that a magnet beats the robot for metal. This dataset and rig become the Workshop Kit curriculum (§3.6).

---

### 3.2 Battery & E-Waste Pull-Out Guard (6.5/10) — best-in-class waste demo

**Problem & evidence.** Hazardous waste is a legally named separate stream under Vietnam's 2020 Law on Environmental Protection and Decree 45/2022, but batteries and small electronics routinely end up in recyclables, creating fire risk in the informal chain where collectors hand-pick them out at the vựa table. HCMC has **no organized hazardous-recovery network** ([VOV](https://vov.vn/xa-hoi/tphcm-van-chua-dat-ky-vong-viec-phan-loai-rac-tai-nguon-post1061033.vov), [Tuổi Trẻ](https://tuoitre.vn/nld/thuc-trang-phan-loai-rac-tai-nguon-o-tp-hcm-ghi-nhan-qua-tung-hinh-anh-196250109112111232.htm)), and the city's 2026 environment plan is centered on communication/awareness ([Báo Pháp Luật VN](https://baophapluat.vn/tp-ho-chi-minh-day-manh-phong-trao-bao-ve-moi-truong-giai-doan-2026-2030.html)) — a robot that *performs* the rule beats any poster.

**Skeptic verdict.** Mechanically a AA battery (14.5×50.5 mm, 23 g, rigid cylinder) is near-perfect; **visually it is not** — specular metal next to specular crushed-can distractors is where a ResNet on 60 episodes fails silently, and a battery is a ~10–15 px sliver in the overhead cam. Ten "do nothing" episodes will NOT teach abstention — behavior-cloned policies reach for *something*, and the worst possible failure in front of schoolkids is the robot theatrically putting cardboard in the red hazard cup. Venue shift (gym fluorescents, stage lights) kills untraveled policies. Cylinders roll on off-center jaw contact. As waste tech, value is nil — a vựa sorter clears the table in 3 seconds. Its honest value is a communication prop — and per the skeptic, still **one of the better SO-101 ideas anywhere**: rigid dense target, sparse scene, short horizon, real social hook, and it teaches two skills most hobbyist ACT projects never touch: *selective grasping among distractors* and *learned abstention*.

**What the arm does (rescoped).** A dry tray with a **fixed distractor kit** (6–8 specific matte, visually distinct items: cardboard, colored caps, paper — **no crushed cans in v1**; reintroduce one in v2 only) salted with **exactly 2 AA batteries** per episode (fixed count = trivial termination). Arm extracts only the batteries into a red hazard cup, then returns to an explicit scripted "home + idle" pose. Variable battery count is a v3 stretch goal.

**Workspace setup.**
- 30×30 cm tray; **portable rig**: tray, both camera mounts, and an LED light bar rigidly fixed to one plywood baseboard, so the deployed scene is pixel-similar to training in any room — this is the venue-shift fix, solved with hardware not data
- Record across 3–4 backdrops/lighting settings anyway
- Red hazard cup fixed position; matte battery sleeves only as a documented last resort if glare proves fatal

**First dataset.** `gkienpham/ewaste_pullout_v1` — **100–150 episodes** (not the originally planned 60): 4–6 kit distractors + exactly 2 batteries at random poses; **20–25% zero-battery abstention episodes** with the explicit idle terminal behavior demonstrated.

**4-week milestone.** Weeks 1–2 (after cap-sorter shakedown): build the plywood rig, record 100–150 episodes, train (~$0.50–1.50). Week 3: eval — report battery recall, distractor false-grab rate, and abstention success separately. Week 4: run it as an **interactive booth demo** (kids place the battery themselves and watch the robot find it — a failed grasp is a retry, not an assembly-wide flop); pitch footage to PRO Vietnam ([provietnam.com.vn](https://provietnam.com.vn/tin-tuc/tu-1-1-2025-nguoi-dan-khong-phan-loai-rac-bi-phat-den-mot-trieu-dong/)) and UNDP EPPIC ([undp.org/vietnam](https://www.undp.org/vietnam/projects/scaling-socialised-model-domestic-waste-and-plastic-management)).

---

### 3.3 3-Stream Recyclables Sorter — your trash-sorting seed, rescoped (6.0/10)

**Problem & evidence.** Vietnam made 3-stream at-source separation (recyclables / food / other) **mandatory from 1 Jan 2025** with fines of 500,000–1,000,000 VND ([VnExpress](https://vnexpress.net/tu-1-1-2025-nguoi-dan-khong-phan-loai-rac-bi-phat-den-mot-trieu-dong-4833792.html)) — yet **HCMC has fined no one** ([PLO](https://plo.vn/nguoi-dan-tphcm-neu-chua-phan-loai-rac-co-bi-phat-post829099.html)) and only 48% of residents separate into 3 streams. The killer stat: **49% don't separate because they don't trust collectors won't re-mix it** (TGM Research × PRO Vietnam 2025, N=1,925: [tgmresearch.vn](https://tgmresearch.vn/tgm-pro-vietnam-bao-cao-phan-loai-rac-tai-nguon-2025.html)). HCMC generates 14,000+ t/day, ~69% landfilled ([Thanh Niên](https://thanhnien.vn/tphcm-thai-ra-14000-tan-rac-sinh-hoat-moi-ngay-chu-yeu-la-chon-lap-185251021133850676.htm)); the ve chai chain recovers ~23% purely by hand, and sorted+clean material sells for **2–4× the mixed price** (aluminum 30–45k VND/kg vs steel 13–25k). **No one in Vietnam does robotic recyclables sorting at any scale** — coverage is only translated foreign news ([T-Tech](https://t-tech.vn/tin-tuc/tin-trong-nganh/cach-mang-cong-nghe-robot-va-tu-dong-hoa-trong-phan-loai-rac-thai.html), [Nhân Dân](https://nhandan.vn/ung-dung-ai-trong-phan-loai-rac-post725333.html)). A working demo is genuinely first-of-kind Vietnamese content.

**Skeptic verdict.** Four objections bite: (1) a **flat cardboard scrap on a flat table is nearly unpickable** for a parallel jaw — canonical failure mode; (2) crushed *clear* PET is transparent+specular (among the hardest classes in robot vision) and a crushed can is a mirror; (3) V2 "pick recyclables, leave the rest" with 30 episodes is a variable-length sequential-decision task — it will fail as specified; (4) the narrative has a seam: the 49% trust failure is a *collection-logistics* problem (re-mixing at the truck), which a tabletop arm doing 2–4 picks/min at ~80% doesn't fix — a ve chai worker does 30+ picks/min at ~100% for ~$1.5/hr. The saving grace is the honest framing: this demos **the cognition** (a $55 arm learns the mandated sort from demos), not throughput.

**What the arm does (rescoped v1).** One item per episode — crushed aluminum can (~15 g), **labeled** PET bottle pre-crushed identically each time and gripped at the (colored) cap (~20 g), and **folded/tented cardboard with a raised edge or a boxy Tetra Pak-style carton** (never flat scraps) — placed into the correct of 3 labeled bins. V2: **fixed-count pile** (always exactly 3 items, one per class, pick all three in any order), 100–150 episodes; add a single "leave it" distractor only after fixed-count works.

**Workspace setup.**
- 3 bins inside the 38 cm reach arc, fixed positions, high-contrast labels
- Diffuse fixed lighting to tame can specularity; **matte non-white mat** under the pick zone so clear plastic silhouettes
- Keep PET labels ON (huge visual signal); identical pre-crush each episode so the cap-pose distribution stays narrow

**First dataset.** `gkienpham/3stream_sort_v1` — **50 episodes PER CLASS (150 total)**, not 50 total: class-conditional placement into 3 bins is three policies' worth of behavior. Randomize item position and identity.

**4-week milestone.** Weeks 1–2: record and train v1 (~$0.50–1.50); target ≥75% per-class placement, reported per class in the README. Week 3: fixed-count 3-item pile v2. Week 4: publish the dataset as **"the first public Vietnamese-waste teleop dataset on Hugging Face"** (genuinely novel, useful to others) and cut the awareness video: "the robot does the sort 49% of you don't trust the truck to do" — while stating explicitly that the trust problem is a logistics problem the demo *illustrates*, not solves. That honesty lands better with UNDP/PRO Vietnam evaluators than an implied capability claim.

---

### 3.4 Mì Gói Topping Bar — your instant-noodle seed, honestly assessed (5.5/10)

**Problem & evidence.** Vietnam is the world's **#1 per-capita instant-noodle consumer**: 81 packs/person/year, 8.1 billion servings in 2024 ([VnExpress/WINA](https://e.vnexpress.net/news/travel/food-recipes/a-vietnamese-eats-81-packs-of-instant-noodles-a-year-surpassing-koreans-4959375.html)). Customization (quail egg, sausage, lime, chili) is a national daily micro-ritual; 64.6% of students choose noodles for time ([doc.edu.vn](https://doc.edu.vn/tai-lieu/khao-sat-nhu-cau-su-dung-mi-an-lien-trong-sinh-vien-23918/)); a viral Feb-2025 survey found **61% of Gen Z can't fry an egg** ([CafeF](https://cafef.vn/61-gen-z-khong-biet-ran-trung-42-nguoi-o-do-tuoi-18-28-khong-nau-duoc-mon-xao-co-ban-188250214202908787.chn)) and "lazy cooking" (cơm lười) is a mainstream TikTok genre ([tcorder.vn](https://tcorder.vn/do-gia-dung-ban-chay-nhat-tren-tiktok/)). This is the single most culturally legible task an HCMC robot can do. Bonus price framing: the arm costs less than a family's monthly noodle habit.

**Skeptic verdict — the seed's hard truths.** (1) **The peeled quail egg is the hardest object in the lineup**: wet, near-frictionless, tears at roughly the force needed to hold it; the STS3215 gripper is position-controlled with no force sensing, so failure is bimodal (squirts out / splits and coats the fingers, degrading every later grasp). Expect 40–70% per-grasp success. (2) The lime wedge compounds it — two of five items are wet-deformable. (3) **Horizon math kills the single end-to-end policy**: six stages at an optimistic 90% each = 0.9⁶ ≈ 53% full-sequence success; realistically under 25%. 60 episodes over 6 stages ≈ 10 episodes per skill; published LeRobot results use 50+ for ONE pick-place. (4) The sand-timer flip is a hidden regrasp-and-reorient at the END of the error chain, with glass as the failure mode. (5) The metallized sachet is pure specular highlights at 640×480. (6) Hygiene/spoilage: PLA fingers + servo grease means nobody eats the output, and real egg/sausage at 32°C will visually drift *mid-dataset*. Economic value: zero — a human does this in 15 seconds and must also reload every station. It lives or dies as content — and a demo that completes 1 run in 4 is not a demo.

**What the arm does (rescoped).**
- **v1 — the dry triad:** sachet (in an upright holder for a side grasp) → sausage slice → lid, plus placing a **plastic** timer upright from an upright holder (no 180° flip). Get this to 90%+ before any wet item.
- **v2 — +egg via tooling, not learning:** either a spoon/scoop end-effector or fixed-geometry ladle motion for the egg stage, or an **unpeeled** quail egg (rigid, dry, still culturally legible — "peeling is future work" on camera).
- **Architecture:** kill the single end-to-end policy. Train **per-stage** (separate checkpoints or stage-conditioning, chained by a trivial completion-keyed state machine) — converts 0.9⁶ into independent, retryable, individually re-recordable stages.
- **Props:** silicone egg/lime for the hundreds of training/eval grasps; real food only for final hero takes. Solves spoilage, appearance drift, and hygiene optics at once.

**Workspace setup.** Dry bowl + noodle block at center; trays at fixed stations, all within 35×35 cm; sachet holder vertical; ±3 cm tray randomization **plus lighting randomization** (HCMC window light shifts across sessions); human adds hot water off-camera; narrate on camera what it can't do (tear sachets — bimanual; hot water) — honesty performs well.

**First dataset.** `gkienpham/migoi_topping_v1` — the dry triad, recorded per-stage, **100–150 episodes total** if 5 stages are ever kept; top + wrist cams, `--dataset.streaming_encoding=true --dataset.encoder_threads=2` (macOS crash workaround; see `docs/runbook.md`). Instrument per-stage success rates from day one and publish them in the README — the honesty framing only lands with numbers.

**4-week milestone (weeks 3–6 of the real-arm calendar).** Week 1: stations built, dry-triad per-stage recording. Week 2: train stages (~$1–2), chain with the state machine, measure per-stage rates. Week 3: iterate the weakest stage only; hero video of the reliable triad. Week 4: v2 egg experiments with scoop tooling on silicone props. The "quốc dân" relatability video ships from v1 — don't gate it on the egg.

---

### 3.5 Mock Feeding Assist — mannequin-only assistive-tech concept (6.5/10)

**Problem & evidence.** Vietnam's population is aging with a documented caregiver shortage (HCMC geriatric-capacity studies: [BMC Geriatrics 2025](https://link.springer.com/article/10.1186/s12877-025-06869-7), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122135/)). Assistive feeding robots exist precisely because self-feeding loss is devastating (ALS, stroke, frailty) — but the incumbent Obi Gen 3 is quote-only, several thousand USD, unavailable in Vietnam ([meetobi.com](https://meetobi.com/shop/product/obi-robot/)). A ~$150 rig doing even a toy version reframes cheap open-source hardware as assistive-tech research.

**Skeptic verdict.** Four underrated problems: (1) wet-food teleop is a throughput killer — 15–20 clean episodes/hour with refills, drips, and lens splatter, so the dataset spans sessions and session drift kills small-data ACT; (2) white glossy yogurt on two RGB cams gives weak fill-level signal, yet the original plan *randomized* fill level — forcing the policy to perceive the thing the sensors are worst at (expect confident air-scoops); (3) the real smoothness risk is the **5-DOF kinematic constraint**: keeping the spoon level across a 25 cm arc consumes wrist flex + roll entirely, and some placements make level transport simply infeasible; soft rice clumps and can stall the STS3215 against the bowl wall (thermal shutdown risk); (4) a spoon merely held in the gripper rotates under scoop load. Mixing yogurt AND rice splits a small dataset across two contact dynamics. Safety/economics are fine only because it's honestly a mannequin-only story — that also caps it at demo/narrative.

**What the arm does (rescoped, staged).**
- **V1 (week 1):** dry proxy — dry rice or water beads in a dark high-contrast bowl in a jig; **rigid 3D-printed spoon mount** (not gripper-held); before recording anything, teleop the arc manually and verify a level-transport posture exists within wrist limits for your bowl/mannequin placement.
- **V2 (weeks 2–3):** thick pudding or Greek yogurt only — **drop soft rice entirely**; fill level held in a narrow band (refill to a marked line each episode), not randomized.
- **Consider the hybrid architecture** — learned scoop (the contact-rich hard part) + scripted level waypoint trajectory for delivery. "We learned the part that needs learning" reads as sophistication, not cheating.

**Workspace setup.** Bowl-to-target arc ~25 cm; taped target at mannequin-mouth height; drip tray + cling-film on the forearm servos (drips happen regardless of rules); wipe lenses between episodes. **Hard rules in every video:** never near a real face (no force sensing), food never touches electronics, framed as "assistive-tech concept exploring what open-source hardware could unlock," never a product.

**First dataset.** `gkienpham/spoon_scoop_v1` — **100–120 episodes**, single medium per version, single session per condition where possible.

**4-week milestone (weeks 5–8, after three quick wins are banked).** Week 1: spoon mount printed, kinematic feasibility check, dry-proxy dataset. Week 2: train + eval on dry medium. Week 3: pudding/yogurt dataset. Week 4: quantitative eval — **weigh the bowl; report grams-delivered-to-target per scoop and success over 20 consecutive trials.** That rigor is exactly what makes the assistive framing defensible when scrutiny comes.

---

### 3.6 "Teach a Robot by Showing It" Workshop Kit — the education flywheel (7.0/10, top score)

**Problem & evidence.** HCMC parents pay 15–18M VND (~$577–692) for MindX's 42-session VEX-block robotics course ([mindx.edu.vn](https://mindx.edu.vn)) and ~3.5M VND/month market rate; Teky courses run 4–6M VND ([teky.edu.vn](https://teky.edu.vn)). Yet **no Vietnamese center or university lab teaches real-servo arms or imitation learning**, and there is **zero Vietnamese-language LeRobot/SO-101 content anywhere** (GitHub/YouTube search) — while Vingroup's VinMotion humanoid program (imitation learning + human-in-the-loop) dominates national robotics hype ([theinvestor.vn](https://theinvestor.vn), [vinrobotics.net](https://vinrobotics.net)). STEM instructors earn 8–12M VND/mo, so paid weekend workshops at 300k–1M VND/head are viable side income.

**Skeptic verdict.** The rare idea where physics isn't the attack surface — caps are squarely in-envelope. The attack surface is the **live-demo reliability chain**: ACT is brittle to camera pose/lighting/table shift, and a rented venue with overnight teardown practically guarantees distribution shift — a 2 cm camera bump can drop success from 80% to near-zero in front of paying parents. Fifty episodes from 10–15 novices yields wildly multimodal data (plausibly a 30–60% policy); overnight vast.ai training is a hard no-retry dependency (upload on consumer internet, preemption); one leader pair = each teen puppeteers ~3–5 minutes in hours; the economics are side-income (~10 × 500k = 5M VND gross/weekend minus venue and 20+ hours of prep), not a business; and the "zero VN content" moat is a weekend of work for a competitor to erase.

**What the workshop is (rescoped).** A repeatable 2-session product built on the cap sorter (§3.1): Session 1 — participants puppeteer the leader arm and record demos live ("you are the training data"); overnight — ACT trains on vast.ai (~$0.25–2, inside the existing budget); Session 2 — the arm replays their skill. Five de-risks:
1. **Decouple the wow moment:** pre-train a proven fallback policy on your own demos in the exact venue rig; the participants' model is "the experiment," yours is "the baseline" — honest pedagogy, no catastrophic-failure mode.
2. **Kill distribution shift mechanically:** bolt both arms, both webcams, bins, and staging area to one plywood base; bring your own LED panel — Saturday and Sunday are pixel-identical. (Same rig philosophy as §3.2 — build it once.)
3. **De-risk the overnight run:** full dress rehearsal (record→upload→train→deploy) in the venue a week prior; automated retry script; locally cached pretrained checkpoint as insurance.
4. **Curate novice data live:** quick per-episode quality check; record 70–80 to keep 50 good ones.
5. **Fix engagement:** cap at 8–10 attendees, rotate stations (teleop / labeling-QA / "design the sorting task"); a second arm pair (~$250) once workshop #1 pays for it. Rebrand Session 2 as **"watch a robot learn — including its mistakes"** so a 60% policy reads as science, not a broken product.

**First dataset.** `gkienpham/workshop_capsort_batch01` — the first participant-recorded set: 50 kept episodes of 3-color cap sorting teleoperated by attendees, doubling as a measurement of pipeline robustness to novice demonstrators.

**4-week milestone (month 2–3, after the cap sorter is solid).** Week 1: plywood workshop rig + fallback policy trained on it. Week 2: dress rehearsal end-to-end in the target venue. Week 3: **first workshop free or near-free at a school or makerspace** — generates Vietnamese-language content and testimonials, and works even if the demo partially fails ("here's what went wrong and why" is itself excellent content). Week 4: publish the build series + shorts with VinMotion as the "why this matters" hook (same imitation-learning ideas, $55 hardware); price workshop #2. The content flywheel is the real asset; every other Tier-1 project feeds it.

---

## 4. TIER 2 — researched, critiqued, shelved with rescopes (nothing lost)

### 4.1 Cà Phê Phin Robot Barista (6.0/10)
**Hook:** Robot baristas are viral in Vietnam — HCMC's "Blooms and Brews by Ellum Saigon" (Mar 2026) uses ~2 billion VND (~$77,000) arms serving 60,000 VND cups ([Thanh Niên](https://thanhnien.vn/robot-pha-ca-phe-tai-tphcm-tu-hao-duoc-xay-dung-boi-doi-ngu-viet-nam-185260313210328239.htm), [Dân Trí](https://dantri.com.vn/du-lich/quan-nho-o-tphcm-choi-lon-dung-robot-pha-ca-phe-2-phut-co-ngay-mot-ly-20260312201518460.460.htm)); Hanoi has a 4-robot café ([VietnamNet](https://vietnamnet.vn/quan-ca-phe-tuong-lai-tai-ha-noi-robot-pha-che-bung-tan-ban-cho-khach-2398902.html)); automatic phin machines cost ~3.19M VND ([FPT Shop](https://fptshop.com.vn/tin-tuc/dien-may/may-pha-ca-phe-gia-re-nhat-2025-176431)). Dry-only 5-step phin assembly; human pours hot water; 8–10-min drip as time-lapse.
**Skeptic:** Grasp geometry is the unexamined killer — the ~6.5 cm phin body with 9–10 cm base flange is at/beyond gripper aperture, the knob-less lid is a near-impossible flat top-grasp, polished aluminum is specular and featureless, pouring grounds is granular-media manipulation and the press insert lands on an *uneven mound* (tilt/jam, which no taper fixes), 5 steps ≈ 50–60% full-sequence success on 80 episodes, and the "1/1400th the price" hook invites "it does 1/1400th of the job" — plus the Mar-2026 news peg is stale by a 3-month build.
**Rescope if revived:** 3D-print grasp features (collar band, tall insert stem-knob, lid knob/edge-stand) and verify aperture fit on day 1; fixed printed nests, no randomized tray in v1; human pre-loads or levels grounds on camera; per-step policies (30–50 eps each, 60+ for the insert) chained by script; matte/anodized dark phin; reframe as "everything it took to teach a $60 arm the phin ritual — including the 40% failure reel." Dataset: `gkienpham/phin_assembly_v1`.

### 4.2 Microgreen Tray Seeder + Mushroom Size-Sort (6.0/10)
**Hook:** HCMC urban micro-farms are real businesses (Củ Chi mushroom farm at 1.5–2 tỷ VND/yr, workers 300–500k VND/day — [danviet.vn](https://danviet.vn)); agritech is a beloved Vietnamese content genre and no one has shot "robot farmer" with a $55 arm. Honest finding baked in: 1.2 kg substrate bags are 4–6× over payload — production ROI is dead; this is content.
**Skeptic:** The S-pattern seed scatter is a *mirage of control* — IL copies trajectories, not "even coverage"; the lid placement is the trap step in a 4-stage chain on only 60 episodes; and the buried companion clip (sorting harvested mushrooms into two size crates) is actually the stronger, more transferable demo.
**Rescope if revived:** sell the sweep as choreography, not seeding quality (show the honest top-down uneven-spread shot); chamfered lid + raised rim or drop the lid from the hero clip; 100–120 episodes if the chain stays; **promote the mushroom two-bin size-sort to co-lead**. Dataset: `gkienpham/tray_seed_v1`.

### 4.3 TikTok Shop Livestream Product Presenter (5.0/10)
**Hook:** Livestream hosts/assistants earn 8–15M VND/mo (to 30M with commission — [topcv.vn](https://topcv.vn)); 88% of F&B report staff shortages ([NLĐ](https://nld.com.vn)). Arm picks the cued product from a 6-slot tray, holds a hero pose, wrist-rolls for the camera. Motion-wise among the easiest credible IL tasks on an SO-101.
**Skeptic:** A ~200k VND motorized turntable already does the rotate-for-camera job and never drops anything; phone cases (flat slabs) and hair accessories (springy) don't survive a parallel jaw; "hours unattended" is fiction (STS3215 thermal shutdown under sustained extended holds; someone restocks the tray; real lives run 20–60 SKUs not 6); ring-light glare + moving host = distribution shift; and with fixed slots and a fixed pose, scripted trajectories beat a learned policy — IL as a lookup table. Dropping a client's lipstick is charming in week 1, a fired vendor in week 4.
**Rescope if revived:** "robot co-host segment," rigid cosmetics tubes upright in foam cutouts only; foot-pedal/StreamDeck cue (kill the colored token); train in the actual studio with 120–150 episodes; rest pose between holds, 15–20 s hold cap, 60–90-min segments; scripted-trajectory fallback so the stream never stalls; success = "the seller asks for a second session." Dataset: `gkienpham/livestream_presenter_v1`.

### 4.4 Tết Gift-Box / Shopee Order Kitting Cell (5.0/10)
**Hook:** Packers cost ~8M VND/mo; 3PLs charge 5–8k VND/order ([allship.vn](https://allship.vn), [eimskip.vn](https://eimskip.vn)); pre-Tết kitting spikes when temp wages jump 1.5–2×; Region-1 minimum wage is 25,500 VND/hr from 1 Jan 2026 ([baochinhphu.vn](https://baochinhphu.vn/tang-luong-toi-thieu-vung-tu-1-1-2026-102251110175033018.htm)). Arm places tea/coffee/candy sachets into molded gift-box compartments in a jig.
**Skeptic:** Vietnamese drip-coffee and tea sachets are flat floppy foil — no graspable top surface, specular and crinkled; "randomized bin contents" smuggles in bin picking (the hardest version); 4 picks at 85% = 52% flawless boxes; and **"unattended overnight" is false as scoped** — the run ends when the jigged box is full (minutes), and one silent double-pick means a shift of mis-kitted orders. Even at 100% reliability: ~30–40 boxes/stint ≈ 150–320k VND of 3PL-equivalent value, for a 4–6-week seasonal spike.
**Rescope if revived:** singulated single-layer trays or gravity-fed edge-up dispensers (never jumbled bins); stiffest SKUs first (boxed tea bags, hard candy); state machine calling a single pick-place policy with a webcam-diff success check between steps; ArUco/barcode scan outside the policy for SKU cueing (no OCR-by-ACT); 150–200 episodes, diffuse matte lighting; deliverable = supervised batch-kitting demo + Tết marketing footage + public dataset; drop "while you sleep" until a jam watchdog and box feed exist. Dataset: `gkienpham/giftbox_kitting_v1`.

### 4.5 Pharmacy Blister-Pack Sorter/Counter (4.5/10)
**Hook:** Vietnam has 57,000+ independent pharmacies; retail "ra lẻ" dispensing and blister inventory are documented time sinks ([webnhathuoc.com](https://webnhathuoc.com)); pill counters are industrial-only ([congnghemaythienphu.com](https://congnghemaythienphu.com)); assistants cost 6–8M VND/mo.
**Skeptic:** Flat 3–6 mm cards lying flat are among the hardest parallel-jaw grasps (crush the blisters or need a slide-to-edge with force feedback the arm lacks); bin picking from shingled cards is research-grade; foil is specular, clear PVC transparent, and real SKUs differ only by small dosage text (Amoxicillin 250 vs 500 — the confusion that matters most) — a closed-set 3-way classifier wearing a robot costume; **counting-by-ACT is architecturally broken** (no persistent state → off-by-one, i.e., a medication error); real stock lives in boxes and "ra lẻ" produces jagged cut strips; if a human must verify 100% anyway, the sort is advisory and the value deletes itself.
**Rescope if revived:** singulated packs on a mat or ramp-fed edge-up; compliant fingertips with a thin lip; external CV counter, never ACT-held count state; **decouple classification** — wrist-cam OCR/CNN picks the goal bin, the policy learns only SKU-agnostic grasp-present-place (new SKU = retrain a classifier, not recollect teleop); 3–5 distinct SKUs, 100+ consecutive attempts reported with jams; position as a "present-and-classify manipulation with decoupled perception" portfolio piece, not a pharmacy product. Dataset: `gkienpham/blister_sort_v1`.

### 4.6 Weekly Pill-Organizer Assistant (4.0/10)
**Hook:** HCMC elderly medication adherence is 49.8–76.4% ([BMC Geriatrics 2025](https://link.springer.com/article/10.1186/s12877-025-06869-7), [Br J Clin Pharmacol](https://bpspubs.onlinelibrary.wiley.com/doi/10.1111/bcp.16405)); a 7-day hộp chia thuốc costs 15–60k VND on Shopee; Obi is thousands of USD.
**Skeptic:** The demo and the problem don't connect — adherence is behavioral (forgetting, cost, beliefs), not box-filling; a caregiver fills the box in 3–5 minutes weekly; Obi is a *feeding* robot (wrong comparison), and the real competitor is a $30–100 automatic dispenser or abundant family labor. **Counting is safety-critical and exactly what IL cannot guarantee** — no force sensing, self-occluded wrist cam, silent double-picks; 21 pick cycles at 90% ≈ 11% full-task success; gummies are tacky and won't release; cup-picking is bin-picking; real 8–12 mm pills are ~15–30 px at 640×480 — the plan itself concedes the real use case. The healthcare framing raises a bar the demo can't meet.
**Rescope if revived (the architecture is genuinely instructive):** learned short-horizon primitive ("pick one item, place in cued slot") + **scripted outer loop for counting** + fixed top-down classical blob-count verification after each placement — deterministic code counts, the policy only moves; size-000 matte capsules (~26 mm), one color per day-slot; shallow wide tray instead of a cup; printed funnel collar widening drop tolerance to ~30 mm; 100–140 episodes (15–20 per slot); report per-cycle success with confidence intervals; present as "low-cost testbed for cue-conditioned precise placement," citing adherence data as context, not the solved problem. Dataset: `gkienpham/pill_organizer_v1`.

### 4.7 Research backlog — additional candidates screened (from the food-culture and waste tracks)

| Candidate | One-line assessment |
|---|---|
| Sachet color-sorting (bột nêm / dầu / rau sấy → 3 cups) | Trivially in-envelope; superseded by the cap sorter as the shakedown task |
| Steel-vs-aluminum can triage into 2 crates | Real money (13–25k vs 30–45k VND/kg) but visual-ambiguity risk; curate distinct SKUs; a magnet does it for 20k VND |
| Paper-grade sorting (office / newspaper / cardboard) | Mirrors the 12–22k vs 4–10k VND/kg grade split; flat items = hard grasp, needs pre-fanned pieces |
| Tetra Pak stacking prep | PRO Vietnam member priority stream with near-zero collection; use intact dry cartons only |
| Glass vs plastic bottle split | Glass ≥300 g + breakage — edge of payload; miniature jars only, ranked last |
| Bánh tráng trộn portioning | Use pre-portioned mini-cups (pour, don't pinch loose herbs); quail eggs in shell are a good gentle-grip showcase |
| Bánh mì mise-en-place | Tray assembly only — inserting fillings into bread is deformable insertion, out of envelope; cold cuts need silicone fingertips |
| Table setting (chén, đũa, muỗng) | Culturally legible, weak pain point; chopsticks are a hard thin-object grasp — raised holder or skip |
| Phở herb sorting (húng quế vs ngò gai) | Worst case for ACT at 640×480; only viable rubber-banded (becomes rigid-object sorting) |
| Xiên que skewering | REJECT as-is (bimanual + insertion force); salvage: placing pre-made skewers on racks |
| Sachet tearing / pour into hot bowl | REJECT — bimanual tear + force + steam; use as "what the robot CAN'T do yet" content |
| Stirring noodles / 3-min steep | REJECT for real use — hot water above electronics; the lid + sand-timer beat replaces it safely |

---

## 5. Cross-cutting insights about the Vietnamese market

1. **The $1/hr wall.** Region-1 minimum wage is 25,500 VND/hr (~$0.98) from 1 Jan 2026; milk-tea staff earn 20–30k VND/hr; a ve chai sorter does 30+ picks/min at ~100% accuracy for ~$1.5/hr. **No SO-101 application closes on labor replacement.** Every verified idea that survived did so on a different axis: learning value, content, education revenue, or institutional awareness. Any pitch implying labor economics will be — correctly — torn apart.

2. **The trust gap, not the sorting gap, is Vietnam's waste story.** 49% of residents don't separate because they believe collectors re-mix it (TGM/PRO Vietnam 2025). That is a collection-logistics and incentive failure. A demo can *illustrate* the mandated behavior powerfully (and should — the law exists, fines exist on paper, HCMC has fined no one), but must never claim to *solve* it. Framing the demo as illustration is also what makes it credible to PRO Vietnam, UNDP EPPIC, and CSR sponsors (Unilever×VietCycle, Coca-Cola×VECA precedents) who already pay for waste-education content.

3. **There is a genuine first-mover vacuum in Vietnamese-language embodied AI.** Zero Vietnamese LeRobot/SO-101 content, no robotic recyclables sorting at any scale, no imitation-learning teaching anywhere below VinMotion's corporate program — while robot cafés (2 tỷ VND arms) and VinMotion dominate hype. The durable asset is the content + workshop flywheel, not any single demo. The moat is thin (a competitor could start any weekend), so speed matters more than polish.

4. **Culture picks the demos; physics picks the order.** Instant noodles (81 packs/person/yr), cà phê phin, Tết gifting, and the ve chai economy are the legible hooks. But the skeptic pass shows the *physics* ranking is nearly inverted from the *cultural* ranking: caps and AA batteries (rigid, dry, dense) before sachets and quail eggs (flat, specular, wet-deformable). Ship the physics-easy demos first and spend the earned credibility on the culturally big ones.

5. **Recurring failure modes to design against, everywhere:**
   - **Flat things on flat tables** (cardboard, blister packs, phone cases, crown caps) — a parallel jaw's canonical failure; fix with tenting, ramps, holders, or different objects.
   - **Specular and transparent objects** (foil sachets, clear PET, polished aluminum, wet egg) — worst case at 640×480; fix with matte props, labels-on, fixed diffuse lighting, matte backdrops.
   - **Wet-deformable + no force sensing** is a *hardware* problem — solve with tooling (scoops, spoon mounts) or props, never with more data.
   - **Horizon math**: N stages at p per-stage = pᴺ; always train per-stage and chain with a scripted state machine; never let ACT hold count state.
   - **Distribution shift** (venue, lighting, camera bump) — solve mechanically with a plywood rig bolting arms + cameras + lights to one base; build this rig once, reuse for the battery demo and the workshop.
   - **STS3215 thermals** — rest poses between actions, cap static holds at 15–20 s, monitor temps.

6. **Honesty is the differentiator, but only with instrumentation.** Every rescope converged on the same content strategy: state on camera what the arm can't do (tear sachets, touch hot water, beat a magnet, replace a worker), publish per-stage success rates in every dataset README, and ship the failure reel. In a market where the incumbent robot story is a 2-billion-VND café arm, "here is exactly what $55 buys, with numbers" is the position no one else occupies.

7. **Budget reality check.** All Tier-1 training runs fit comfortably in the remaining $7.78–39.78: cap sorter ~$0.50, battery pull-out ~$1.50, 3-stream ~$1.50, mì gói per-stage ~$2, feeding ~$2, workshop reruns ~$2 each — roughly $10 for the entire Tier-1 program at the $0.22/5k-step RTX 4090 rate already measured.

---

## 6. Ecosystem gaps and what this repository closes

The parallel gap audit found several real openings, but some were already closed when BeanSight was
implemented. Keeping the status here avoids maintaining a second, stale “missing work” document.

| Gap identified | Current status |
|---|---|
| No fixed evaluation or failure taxonomy | Closed by `docs/evaluation_protocol.md`, JSONL contracts, Wilson intervals, and frozen-strata comparison |
| Safety limited to the PSU rule | Closed in `docs/hardware_and_safety.md` and the unarmed fail-still controller; a physical cutoff still remains mandatory |
| ACT versus SmolVLA undecided | Closed: ACT required; SmolVLA only after the 40% gate |
| No dataset size, split, or QA rules | Closed by the 300–500-bean image target, 50–75 manipulation episodes, groupwise splits, and dataset QA |
| Numeric camera identities and macOS encoding instability | Closed in software by semantic preflight, streaming real-arm encoding, and the versioned HIL patch; physical soak remains pending |
| Bean grasp and singulation unknown | Open until hardware: run the fingertip DOE and fixed-nest gate before expanding task scope |
| No Vietnamese Robusta defect labels | Open until roaster review and capture; this is the most valuable pre-arm data contribution |

Broader white space remains useful after the flagship:

- a Vietnamese-language SO-101/LeRobot guide with actual HCMC sourcing and measured failures
- a costed Vast.ai training cookbook using the already measured $0.22 ACT dry run
- a cheap dual-webcam reliability benchmark for Apple Silicon
- an HCMC LeRobot workshop or hackathon node, potentially with
  [Fablab Saigon](https://fablabsaigon.org/) or
  [GDG HCMC](https://gdg.community.dev/gdg-ho-chi-minh-city/)
- tropical-climate servo, print, and camera-mount notes rather than assuming a temperate makerspace

These are communication and community opportunities, not reasons to widen the 30-day robot task.

## Appendix: source index

**Noodles & food culture:** [VnExpress WINA](https://e.vnexpress.net/news/travel/food-recipes/a-vietnamese-eats-81-packs-of-instant-noodles-a-year-surpassing-koreans-4959375.html) · [CafeF Gen Z survey](https://cafef.vn/61-gen-z-khong-biet-ran-trung-42-nguoi-o-do-tuoi-18-28-khong-nau-duoc-mon-xao-co-ban-188250214202908787.chn) · [doc.edu.vn student survey](https://doc.edu.vn/tai-lieu/khao-sat-nhu-cau-su-dung-mi-an-lien-trong-sinh-vien-23918/) · [tcorder.vn TikTok appliances](https://tcorder.vn/do-gia-dung-ban-chay-nhat-tren-tiktok/) · [Nguyen Coffee Supply phin guide](https://nguyencoffeesupply.com/blogs/vietnamese-coffee-brew-guide/traditional-vietnamese-drip-phin)

**Robot cafés:** [Thanh Niên](https://thanhnien.vn/robot-pha-ca-phe-tai-tphcm-tu-hao-duoc-xay-dung-boi-doi-ngu-viet-nam-185260313210328239.htm) · [Dân Trí](https://dantri.com.vn/du-lich/quan-nho-o-tphcm-choi-lon-dung-robot-pha-ca-phe-2-phut-co-ngay-mot-ly-20260312201518460.htm) · [Mực Tím/Tuổi Trẻ](https://muctim.tuoitre.vn/quan-ca-phe-o-tphcm-gay-sot-voi-robot-pha-che-tu-dong-gan-2-ti-dong-10126031420323659.htm) · [VietnamNet Hanoi](https://vietnamnet.vn/quan-ca-phe-tuong-lai-tai-ha-noi-robot-pha-che-bung-tan-ban-cho-khach-2398902.html) · [FPT Shop phin machines](https://fptshop.com.vn/tin-tuc/dien-may/may-pha-ca-phe-gia-re-nhat-2025-176431) · [procaffe.vn](https://procaffe.vn/may-pha-ca-phe-phin/)

**Waste & ve chai:** [TGM Research × PRO Vietnam 2025](https://tgmresearch.vn/tgm-pro-vietnam-bao-cao-phan-loai-rac-tai-nguon-2025.html) · [VnExpress Decree 45/2022](https://vnexpress.net/tu-1-1-2025-nguoi-dan-khong-phan-loai-rac-bi-phat-den-mot-trieu-dong-4833792.html) · [PLO zero enforcement](https://plo.vn/nguoi-dan-tphcm-neu-chua-phan-loai-rac-co-bi-phat-post829099.html) · [Thanh Niên 14,000 t/day](https://thanhnien.vn/tphcm-thai-ra-14000-tan-rac-sinh-hoat-moi-ngay-chu-yeu-la-chon-lap-185251021133850676.htm) · [VOV](https://vov.vn/xa-hoi/tphcm-van-chua-dat-ky-vong-viec-phan-loai-rac-tai-nguon-post1061033.vov) · [Tuổi Trẻ photo essay](https://tuoitre.vn/nld/thuc-trang-phan-loai-rac-tai-nguon-o-tp-hcm-ghi-nhan-qua-tung-hinh-anh-196250109112111232.htm) · scrap prices: [thumuaphelieutrungy.com](https://thumuaphelieutrungy.com/tin-tuc/gia-ve-chai-moi-nhat-hom-nay-631.html), [muaphelieu247.com](https://muaphelieu247.com/bang-gia-phe-lieu-nhua), [phelieunhatminh.com](https://phelieunhatminh.com/bang-gia-ve-chai-moi-nhat-hom-nay/) · [UNDP informal workers](https://www.undp.org/vietnam/press-releases/acknowledge-and-promote-role-informal-waste-workers-towards-just-transition-implementing-extended-producer-responsibility-epr) · [VECA](https://www.veca.app/gioi-thieu) · [T-Tech](https://t-tech.vn/tin-tuc/tin-trong-nganh/cach-mang-cong-nghe-robot-va-tu-dong-hoa-trong-phan-loai-rac-thai.html) · [Nhân Dân](https://nhandan.vn/ung-dung-ai-trong-phan-loai-rac-post725333.html) · [provietnam.com.vn](https://provietnam.com.vn/tin-tuc/tu-1-1-2025-nguoi-dan-khong-phan-loai-rac-bi-phat-den-mot-trieu-dong/) · [UNDP EPPIC/waste project](https://www.undp.org/vietnam/projects/scaling-socialised-model-domestic-waste-and-plastic-management)

**Labor & SME economics:** [baochinhphu.vn Decree 293/2025 minimum wage](https://baochinhphu.vn/tang-luong-toi-thieu-vung-tu-1-1-2026-102251110175033018.htm) · [vieclamtot.com](https://www.vieclamtot.com/tags/tra-sua-tuyen-dung-part-time) · [topcv.vn livestream hosts](https://topcv.vn) · [NLĐ F&B shortage](https://nld.com.vn) · [allship.vn](https://allship.vn) / [eimskip.vn](https://eimskip.vn) 3PL pricing

**Healthcare & education:** [BMC Geriatrics 2025](https://link.springer.com/article/10.1186/s12877-025-06869-7) · [Br J Clin Pharmacol 2025](https://bpspubs.onlinelibrary.wiley.com/doi/10.1111/bcp.16405) · [PMC HCMC geriatrics](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122135/) · [meetobi.com](https://meetobi.com/shop/product/obi-robot/) · [mindx.edu.vn](https://mindx.edu.vn) · [teky.edu.vn](https://teky.edu.vn) · [vinrobotics.net](https://vinrobotics.net)

**Agritech:** [danviet.vn Củ Chi mushroom farm](https://danviet.vn) · [namxanh.vn](https://namxanh.vn) · [lamtho.vn](https://lamtho.vn)
