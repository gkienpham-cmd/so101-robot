# Hidden Gaps and Unexplored Opportunities

**Project:** SO-ARM101 (WitMotion, AliExpress) + LeRobot v0.6.0 pipeline, HCMC
**Status as of 2026-07-15:** Week 1 done in simulation on macOS M1 Pro. Hardware arrives Jul 20–25. Cloud budget: $0.22 spent of $40 (~$39.78 ≈ 1,030,000 VND remaining).

This document covers what the current pipeline is *missing* (not what it has), where the ecosystem has white space a Vietnam-based builder can uniquely fill, and a prioritized exploit-next list.

---

## 1. Technical gaps in the current pipeline

The Week-1 sim pipeline (gym-hil → v3 dataset → vast.ai ACT → MPS inference) proved the *plumbing*. Five things it did not prove:

### 1.1 No evaluation protocol exists yet

Nothing in the current setup measures whether a policy actually works. The community standard the pipeline is missing:

- **Record eval with the policy driving the arm** via `lerobot-rollout` (LeRobot v0.6 replaces the old "record with policy" flow). Use `--strategy.type=episodic` for episode-oriented eval with reset phases; `sentry` for continuous record + auto-upload. Keep the `eval_` prefix convention: `--dataset.repo_id=gkienpham/eval_so101_...`. Pin the checkpoint with `--policy.pretrained_revision=010000`. ([il_robots docs](https://huggingface.co/docs/lerobot/il_robots))
- **Stratified placement bins, not vibes.** The best community writeup ([sherryxychen](https://huggingface.co/blog/sherryxychen/train-act-on-so-101)) taped 5–6 fixed object positions, ran ~10 trials per bin, and reported **in-distribution vs out-of-distribution separately** (her try 2: 60% ID / 10% OOD; try 3: 90% ID / 75% OOD). She also scored 0–1 partial credit (reach/grasp/transport) — valuable at hobbyist trial counts.
- **The formal reference:** the SO-101 VLA benchmark ([arXiv 2606.08881](https://arxiv.org/abs/2606.08881)) — 4 tasks, unified placement protocol, semantic-vs-execution failure taxonomy. Key finding: **execution instability is the dominant failure mode on SO-101-class hardware**, not policy "understanding."
- **Hardware drift kills comparisons.** Community reports show ~90% → ~40% success over days as joints loosen, camera mounts shift, and lighting changes ([RoboCloud tutorial](https://robocloud-dashboard.vercel.app/learn/blog/lerobot-tutorial)). Saigon daylight through a window will shift auto-exposure — fix exposure and white balance manually.

**Concrete protocol to adopt before recording episode 1:** tape 5–6 object positions, hold 1–2 out as OOD, 10 trials/position with `lerobot-rollout --strategy.type=episodic`, log success + progress score in a spreadsheet, and **eval within hours of data collection using the same calibration files**.

### 1.2 No safety layer beyond the PSU rule

There is **no hardware e-stop** on the SO-101. The standing 5V-leader / 12V-follower rule is correct (wrong PSU triggers overvoltage alarm / flashing red LED and can burn motors — [issue #1010](https://github.com/huggingface/lerobot/issues/1010)) but incomplete:

- **`max_relative_target`** in the follower config clamps per-step relative position commands (scalar or per-motor list). This is the only runaway-policy guard. Set it **tighter for autonomous rollouts than for teleop** — too tight makes teleop laggy. ([SO-101 docs](https://huggingface.co/docs/lerobot/so101))
- **`disable_torque_on_disconnect=true`** means Ctrl-C kills torque and **the arm falls**. Start from a low pose over a soft surface. Recording keys: ESC/`q` ends session, right-arrow/`n` ends episode, left-arrow/`r` re-records the episode.
- **Practical e-stop = the follower's 12V PSU switch within arm's reach.** Make that a physical habit before the first autonomous run.
- **STS3215 self-protection:** overload trips at ~80% of stall sustained 2 s, then drops output to ~20% for 2 s; overcurrent/overvoltage/overtemp also built in. Sustained 15 kg·cm hold stabilized at ~48°C — thermal death comes from **prolonged gripper stall**, not motion ([Robonine testing](https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/)).
- **The gripper servo is the #1 documented casualty.** sherryxychen wore hers out crush-holding objects during teleop: "Buy spare motors. Trust me on this one." Servo faults also in [#2819](https://github.com/huggingface/lerobot/issues/2819), setup issues in [#1244](https://github.com/huggingface/lerobot/issues/1244). Train yourself to squeeze gently from day one. Spare 7.4V STS3215 ≈ $14–18 (≈ 360,000–470,000 VND) each ([Amazon example](https://www.amazon.com/SO-ARM101-Debugging-Reduction-345-Compatible/dp/B0FLW54PJB)) — order 1–2 now, they take 1–3 weeks to reach HCMC.

### 1.3 Policy strategy is undecided (decision: stay on ACT, budget SmolVLA as experiment #2)

| Policy | Trained params | Train hardware | Time | Cost per run at vast.ai 4090 rates (~$0.35–0.45/h) |
|---|---|---|---|---|
| **ACT** | 52M from scratch | 8–12 GB VRAM (watch OOM at bs=64 with dual 640×480 cams — reduce bs or resize) | ~4 h solid run | **~$1.5–2.5 (40–65k VND)** |
| **SmolVLA (0.45B)** | ~50M fine-tuned, VLM frozen | single 24 GB GPU | 20k steps ≈ 10.4 h on 3090 ([ggando](https://ggando.com/blog/smolvla-so101/)) | **~$3–5 (80–130k VND)** |
| **π0/π0.5 (3–4B)** | LoRA ≈ 24 GB VRAM; full FT = A100-class | rented A6000/4090 possible | ~$10–20 LoRA | Marginal — and **M1 Pro inference latency is the real blocker** ([EmbodiFlow guide](https://io-ai.tech/platform/en/guides/Pipeline/LeRobot/Pi0/)) |

Head-to-heads on SO-101: the arXiv benchmark found π0.5 best overall, SmolVLA ≈ ACT on average (32.5% vs 33.75%), but single-task SmolVLA beat ACT on Pick-Place-Lego (90% vs 70% ID; 50% vs 40% OOD). ggando's same-75-episode comparison: SmolVLA 60–80% vs ACT 80% — parity, with SmolVLA better at language/generalization and ACT far cheaper. `--inference.type=rtc` (real-time chunking) now smooths slow VLA inference. If IL plateaus: HIL-SERL hit 80% on reach-and-grasp after ~750 online-RL episodes ([ggando HIL-SERL](https://ggando.com/blog/so101-hil-serl/)) — a bigger project, shelve it.

**Budget math:** ~$39.78 remaining supports **~8–12 full ACT iterations plus 2–3 SmolVLA fine-tunes**. Iteration will be limited by data-collection time, not cloud cost. Skip π0/π0.5 entirely.

### 1.4 No dataset size/quality targets set

- **Target: ≥50 episodes, ~10 per placement location** for single-task ACT ([il_robots docs](https://huggingface.co/docs/lerobot/il_robots)). Hub-wide analysis (14,997 datasets, Sept 2025): median is 10 episodes, ~43% are 1–5-episode dead experiments, and the practical hobbyist cluster is 50–60; 200+ marks "serious effort" ([kamenski.me](https://www.kamenski.me/articles/analyzing-lerobot-datasets-on-hugging-face)).
- **Spatial density beats raw count:** ggando needed 75 episodes in a **10 cm workspace** after 50 episodes spread over 30 cm failed.
- **Documented quality killers, each of which bit someone:**
  1. Camera/arm position shift between recording and eval — the #1 silent killer. Tape everything; fix exposure/white balance.
  2. **Two identical webcam models causing USB device-index conflicts** — directly relevant to the two Shopee cameras in delivery, on top of the already-flagged USB-bandwidth risk.
  3. Mixed demonstration strategies (nudge vs direct grasp) → pick one grasp technique, never deviate.
  4. Clustered placements → use stratified bins; include grasp-middle-of-object examples.
  5. Stale calibration between sessions → re-verify each session.
- **Sanity rule from the docs:** you should be able to do the task yourself watching only the camera feeds. Check this *before* burning 50 episodes ([what-makes-a-good-dataset](https://huggingface.co/blog/lerobot-datasets#what-makes-a-good-dataset)).

**First real task spec:** one cube, one bin, ~10 cm placement zone, 5 taped positions × 10 episodes = 50 episodes, one grasp style, fixed exposure, and `r`-key delete-and-redo any jerky episode on the spot.

### 1.5 Sim-to-real expectation is uncalibrated

- **No community report shows a gym-hil-trained policy working zero-shot on a real SO-101.** `gkienpham/sim_practice_dataset` and `gkienpham/act_dryrun` are pipeline rehearsal, not deployable policies. What transfers 100%: dataset format, train/eval workflow, wandb + vast.ai flow, MPS inference path, teleop muscle memory.
- Sim data *can* help via **co-training**: NVIDIA's free SO-101 sim-to-real course mixes as few as **5 real episodes with 70–100 sim episodes** for a deployable checkpoint ([strategy 2](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/13-strategy2-cotraining.html)). Caveats: GR00T-based (not ACT), Isaac Lab needs an RTX GPU (would eat vast.ai budget). Its [sim-eval module](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/11-sim-evaluation.html) is worth reading for eval design regardless.
- **Plan:** fresh 100% real-arm dataset for policy #1. Shelve Isaac co-training unless real-only ACT plateaus with budget left.

---

## 2. Ecosystem white space (what exists vs what doesn't)

### 2.1 Saturated — do not build here

1. Generic install/setup guides (English/Japanese/Windows-WSL2/Linux) — official docs, Seeed wiki, kamenski.me, fresh install-note repos. Even Apple Silicon is covered — *in Japanese* ([note.com/kimitoto](https://note.com/kimitoto/n/nb80665f0af50), [smartphone-zine.com](https://smartphone-zine.com/so-arm101-m1-mac-lerobot-install/)).
2. Cube pick-and-place demos/datasets — thousands of 1–5-episode near-duplicates on the Hub.
3. Dataset conversion/versioning — [any4lerobot](https://github.com/Tavish9/any4lerobot) (1.1k★) + [forge](https://github.com/arpitg1304/forge) own it.
4. Dataset quality linting — [trajlens](https://github.com/Kunal-Somani/trajlens) + forge (contribute, don't compete — see 2.2 #8).
5. Sim environments / sim-to-real bridges — [isaac_so_arm101](https://github.com/MuammerBay/isaac_so_arm101) (289★), [squint](https://github.com/aalmuzairee/squint), [so101-nexus](https://github.com/johnsutor/so101-nexus) (updated today), plus NVIDIA's official course.
6. Browser/GUI control — [leLab](https://github.com/huggingface/leLab) (official) + [phosphobot](https://github.com/phospho-app/phosphobot) (384★).
7. ESP32 wireless teleop — two repos already claim it (ghost-hands, SoArm101-WaveshareEsp32).

### 2.2 Open niches, ranked for this builder (Vietnam / M1 / $40 budget / sim-first pipeline)

1. **Vietnamese-language SO-101 + LeRobot end-to-end guide.** Confirmed vacuum: the *only* Vietnamese SO-101 content is one news rewrite ([techtimes.vn](https://www.techtimes.vn/hugging-face-ra-mat-canh-tay-robot-in-3d-so-101-voi-gia-tu-100-usd/)). Zero Viblo posts, zero Vietnamese YouTube channels, zero VN datasets. 100M-speaker market, robotics demand rising on Vingroup news. The AliExpress-kit + Shopee-camera sourcing detail is exactly what Vietnamese buyers need and no English guide covers.
2. **Ultra-low-budget vast.ai training cookbook (<$5/policy).** Community norm is HF Jobs or local GPUs; nobody publishes a costed, reproducible vast.ai pipeline. The $0.22 receipt + wandb logs already exist — "train ACT for the price of a cà phê sữa đá" is instantly credible and globally useful.
3. **Host the HCMC node of the next LeRobot Worldwide Hackathon.** 2025 edition: 3,000+ participants, 44 countries, 100+ sites — **no Vietnam site ever** ([worldwide map](https://huggingface.co/spaces/LeRobot-worldwide-hackathon/worldwide-map)). Anyone with an arm can register to host.
4. **English macOS Apple-Silicon reference guide.** The two existing ones are Japanese; the exact failure modes (parallel_encoding crash, MPS inference, USB enumeration, macOS permissions) are already solved in the Week-1 logs — ~70% written.
5. **Culturally distinctive task datasets** — chopstick manipulation, Vietnamese-ingredient sorting, cà phê phin assembly. Hub task diversity beyond cubes is near-zero; hackathon winners (t-shirt folding, medicine sorting at ~70% success, [lightning.ai](https://lightning.ai/blog/lerobot-hackathon-winners)) prove novel tasks win attention. A clean 50-episode set would be unique on the Hub and press-worthy locally.
6. **Cheap-webcam benchmark for the 640×480@30fps standard.** 66.5% of Hub cameras are 640×480@30fps, but nobody documents which sub-$10 Shopee/AliExpress cameras hit it reliably on constrained USB buses. The two-cameras-on-M1 bandwidth problem *is* the experiment.
7. **Tropical-climate hardware notes.** All existing lore assumes temperate makerspaces; HCMC's 80–90% humidity vs servo behavior and 3D-print warping (relevant to the "3D Printed Parts" variant) is unstudied. Pairs naturally with niche #1.
8. **Contribute a "sim dataset" quality profile to trajlens/forge.** Both linters target real-robot data; gym-hil sim→v3 datasets are a category they validate poorly (trajlens' audit: 47/100 Hub datasets failed to even load). A few PRs builds reputation with the maintainers who index the ecosystem.

---

## 3. Content, community, and career angles (Vietnam-specific)

### 3.1 The content vacuum is total

- No Vietnamese hands-on LeRobot/SO-101 tutorial exists on Viblo, YouTube, or Facebook-indexed content (mid-2026). Vietnamese YouTube searches return only English channels. First-mover keyword ownership is available on all platforms simultaneously.
- Distribution channels that matter: **Viblo** (written), **Facebook groups** ([Cộng Đồng AI & Machine Learning Việt Nam](https://www.facebook.com/groups/congdongaimlvietnam/), Machine Learning cơ bản), **YouTube/TikTok** short-form (assembly timelapses and "robot learns to pick up X" clips are proven viral formats in English, nonexistent in Vietnamese), **VietAI** ([vietai.org](https://vietai.org/)) for credibility.
- **Dual-track strategy:** English YouTube (global ceiling) + Vietnamese Viblo/Facebook cross-posts (zero competition, compounds into local credibility exactly when Vingroup is hiring).

### 3.2 HCMC community entry points

- **Fablab Saigon** ([fablabsaigon.org](https://fablabsaigon.org/)) — HCMC's first makerspace, runs workshops, no embodied-AI content ever; has 3D printers (doubles as spare-parts supply for printed frame pieces). Natural hackathon-node venue.
- **GDG HCMC / GDG Cloud HCMC** ([gdg.community.dev/gdg-ho-chi-minh-city](https://gdg.community.dev/gdg-ho-chi-minh-city/)) — strong 2025 cadence (Build with AI, I/O Extended, DevFest Dec 6). Takes community speakers; a live "physical AI on a $120 arm" demo is differentiated in an LLM-heavy agenda.
- **Luma HCMC AI circuit** ([luma.com/discover/ho-chi-minh-city/ai](https://luma.com/discover/ho-chi-minh-city/ai)) — busy calendar, **zero robotics/hardware events listed**. The physical-AI slot is unclaimed.
- **HCMUT/BKRA student robotics club** ([facebook.com/BKRACLUB](https://www.facebook.com/BKRACLUB/)) — realistic guest-demo entry; no VN university publicly teaches with LeRobot (a lab could adopt the Vietnamese tutorial as course material).

### 3.3 Career signal: the timing is unusually good

- **VinRobotics** launched a project-based **Talent Program in 2026** explicitly to build scarce Robotics+AI talent ([vinrobotics.net/vi/career](https://vinrobotics.net/vi/career)); sister company **VinMotion** ($37.9M charter capital, humanoids in VinFast factories, led by CMU-PhD Quan Nguyen) is hiring **"Embodied AI Engineer"** ([vinmotion.net/career/embodied-ai-engineer](https://vinmotion.net/career/embodied-ai-engineer)) and perception/manipulation roles. A public teleop→dataset→ACT→deployment portfolio maps directly onto their imitation-learning stack.
- **Salary ladder (VND/month):** junior AI 12–22M (~$470–865); 2–5 yrs 22–42M (~$865–1,650); mid 50–85M (~$1,965–3,340); senior 85–125M+ (~$3,340–4,900+). AI/robot engineer demand grew 67% (2024 IT labor report). ~97 robotics listings on CareerViet beyond Vingroup.
- **Realistic chain:** content → vendor-sponsored hardware (Waveshare/Seeed/Hiwonder actively seed review units) → visibility → interviews. No verified case of "content → job" directly; treat content as portfolio, not lottery ticket.
- **FPT's competition machine** (FARC: ~800 teams; FAnRoC targets 10,000+ students) runs on kit robots, not IL — a large funded education market that will eventually want imitation-learning mentors/content.

---

## 4. Hardware and sourcing gaps

### 4.1 Arrival-day kit verification (Pro DIY Kit ordered — full kit, buyer-confirmed)

The AliExpress order ([listing](https://vi.aliexpress.com/item/1005011826373928.html)) is the **Pro DIY Kit**: 12x servos + 2 driver boards + both PSUs + cables + clamps + both arms' printed parts (WitMotion's store lists it around $245–269; Seeed's servos-only equivalent is [$260](https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html)). Cross-border kits still occasionally arrive with missing servos, wrong leader gear ratios, or a dead driver board — and the dispute window is 15 days — so run the checklist below before confirming receipt.

**Reference full BOM** (leader + follower, [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100)):
- Follower: 6× STS3215 1/345 gear (7.4V C001; Pro kits use 12V C047/C018 30 kg·cm)
- Leader (mixed gearing): 1× 1/345 (C001) + 2× 1/191 (C044) + 3× 1/147 (C046), all 7.4V
- 2× motor control boards (Waveshare bus-servo adapter style), 2× USB-C cables, **5V PSU (leader) + 12V 2A PSU (follower)**, 4× table clamps, screw set

**Arrival-day unboxing checklist:**
1. Count servos — **12 total**. Any shortfall = open a dispute with the unboxing video.
2. Read each servo label: leader needs low-gear variants (turn freely by hand; 1/345 resists). Verify 3× 1/147, 2× 1/191, 1× 1/345 leader; 6× identical 1/345 follower. Pro follower servos say 12V / 30 kg.
3. 2× driver boards with USB-C ports.
4. **2× PSUs — read the voltage stamped on each: one 5V, one 12V.** Mislabeled/duplicate PSUs are a known kit QC issue; this backs the standing never-swap rule.
5. Printed parts vs the repo STL list (base, 5 segments ×2 arms, gripper jaws, wrist-camera mount); inspect thin gripper features for shipping cracks.
6. ~12+ 3-pin daisy-chain servo leads, 2× USB-C data cables.
7. Camera often excluded from WitMotion Pro listings — not blocking (2 Shopee cams inbound).
8. **Photograph everything before assembly** — AliExpress dispute window; dispute immediately if servo count ≠ listing promise.

### 4.2 Spares in Vietnam: local STS3215 stock is effectively zero

- hshop.vn search for STS3215 returns "Không tìm thấy bất kỳ Sản Phẩm nào" ([hshop.vn](https://hshop.vn/search?q=STS3215)); nothing on Shopee.vn/Lazada.vn; no Nhật Tảo distributor found. **Feetech bus servos have no Vietnamese distributor as of mid-2026.**
- Realistic spares channel: AliExpress/Seeed re-order, **7–20 days to HCMC** — which is why spare gripper servos (7.4V STS3215, $14–18 / 360–470k VND each) should be ordered *before* the first one dies, not after.
- hshop.vn (HCMC, hotline 028.6670.4455) stocks Waveshare/DFRobot lines — the **Waveshare bus-servo adapter board may be available locally or via their Zalo order line**. Worth one phone call; a fried driver board otherwise means a 2–3 week stall.
- Printed-part spares: Fablab Saigon's 3D printers (see 3.2) cover frame breakage locally — another reason to build that relationship early.
- This sourcing pain is itself content: niche #1's Vietnamese guide should include the exact "what to buy, from where, at what price in VND" section that does not exist anywhere.

---

## 5. Exploit next — prioritized

| # | Action | When | Cost | Why now |
|---|---|---|---|---|
| 1 | **Run the §4.1 unboxing checklist before tapping "Confirm Received"; dispute immediately if anything is missing** | Jul 20–25 | $0 | The dispute window is 15 days and unboxing evidence cannot be re-shot. |
| 2 | **Order 1–2 spare 7.4V STS3215 (gripper joint)** | Today | $14–36 (360–940k VND) | #1 documented failure part; 7–20 day lead to HCMC; zero local stock. |
| 3 | **Write the eval protocol + first-task spec before hardware arrives** (5 taped bins, 10 trials/bin, ID/OOD split, progress score; task = cube→bin in 10 cm zone, 50 episodes) | This week | $0 | Cheapest possible week — pure planning while hardware is in transit; prevents the #1 waste (50 bad episodes). |
| 4 | **Film everything from unboxing onward** (phone on tripod is enough) | Jul 20–25 | $0 | Raw material for niches #1, #2, #4; unboxing/variant-verification footage cannot be re-shot. |
| 5 | **Set `max_relative_target` conservatively + 12V PSU switch as e-stop habit for first autonomous rollout** | First rollout | $0 | Only guard against a runaway policy; protects the servos there are no local spares for. |
| 6 | **Publish the Vietnamese end-to-end series (Viblo + YouTube) as the build progresses** | Weeks 2–8, alongside the build | $0 | Confirmed first-mover vacuum; compounds into #8 and #9. Effort is 4–8 weekends *of work already being done*. |
| 7 | **Publish the <$5-per-policy vast.ai cookbook (English)** with real receipts and wandb links | After first real ACT run | ~$2 (the run itself) | Universally useful, uniquely credible, small scope. |
| 8 | **Register to host the HCMC node of the next LeRobot Worldwide Hackathon; venue ask to Fablab Saigon** | When registration opens ([map](https://huggingface.co/spaces/LeRobot-worldwide-hackathon/worldwide-map)) | ~$0 + a weekend | Instant "the LeRobot person in Vietnam" status; Vietnam has never had a site. |
| 9 | **Apply to VinRobotics Talent Program / VinMotion Embodied AI with the public build-log as portfolio** | Once #6 has 3+ posts and one autonomous demo video | $0 | 50–125M VND/month roles; their manipulation stack = this exact pipeline; scarce-talent framing is their own words. |
| 10 | **SmolVLA fine-tune on the same 50-episode dataset as experiment #2** | After ACT baseline works | ~$3–5 | Budget allows it; language-conditioning demo differentiates content and portfolio. |
| 11 | **GDG/Luma live-demo talk; BKRA club demo** | After first reliable autonomous demo | ~$0 | HCMC's AI circuit has zero hardware content; a robot learning on stage is the memorable talk. |
| 12 | **Later, only if ACT plateaus with budget left:** NVIDIA co-training (5 real + 70–100 sim episodes) or trajlens/forge sim-profile PRs | Week 5+ | $5–15 | Advanced paths; explicitly deprioritized behind real-data basics. |

**Deliberately skipped:** π0/π0.5 (M1 inference latency + budget), HIL-SERL (~750 episodes, separate project), any new GUI/converter/linter/ESP32 tooling (saturated), English-language generic setup guides (saturated except the macOS gap in #4 above).

---

## Sources

**Technical pipeline:**
- https://huggingface.co/docs/lerobot/il_robots
- https://huggingface.co/docs/lerobot/so101
- https://huggingface.co/blog/sherryxychen/train-act-on-so-101
- https://arxiv.org/abs/2606.08881
- https://ggando.com/blog/smolvla-so101/
- https://ggando.com/blog/so101-hil-serl/
- https://www.kamenski.me/articles/analyzing-lerobot-datasets-on-hugging-face
- https://huggingface.co/blog/lerobot-datasets#what-makes-a-good-dataset
- https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/
- https://github.com/huggingface/lerobot/issues/1010 ; /issues/1244 ; /issues/2819
- https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/index.html
- https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/13-strategy2-cotraining.html
- https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/11-sim-evaluation.html
- https://io-ai.tech/platform/en/guides/Pipeline/LeRobot/Pi0/
- https://robocloud-dashboard.vercel.app/learn/blog/lerobot-tutorial

**Ecosystem:**
- https://github.com/topics/so-101 ; https://github.com/topics/so101
- https://github.com/Tavish9/any4lerobot ; https://github.com/arpitg1304/forge ; https://github.com/Kunal-Somani/trajlens
- https://github.com/huggingface/leLab ; https://github.com/phospho-app/phosphobot
- https://github.com/MuammerBay/isaac_so_arm101 ; https://github.com/johnsutor/so101-nexus ; https://github.com/aalmuzairee/squint
- https://www.kamenski.me/articles/lerobot-datasets-oct-2025
- https://huggingface.co/spaces/LeRobot-worldwide-hackathon/worldwide-map
- https://lightning.ai/blog/lerobot-hackathon-winners

**Vietnam content/community/career:**
- https://www.techtimes.vn/hugging-face-ra-mat-canh-tay-robot-in-3d-so-101-voi-gia-tu-100-usd/
- https://www.facebook.com/groups/congdongaimlvietnam/ ; https://vietai.org/
- https://fablabsaigon.org/ ; https://gdg.community.dev/gdg-ho-chi-minh-city/ ; https://luma.com/discover/ho-chi-minh-city/ai
- https://www.facebook.com/BKRACLUB/ ; https://fschool.fpt.edu.vn/fptu-ai-robotics-challenge/
- https://vinrobotics.net/vi/career ; https://vinmotion.net/career/embodied-ai-engineer
- https://theinvestor.vn/vingroup-forms-new-company-for-humanoid-robot-production-d17105.html
- https://hr1tech.com/vi/news/luong-ky-su-ai-2026-bang-luong-chi-tiet-tu-fresher-den-senior-1402.html
- https://careerviet.vn/viec-lam/robotics-k-vi.html

**Hardware/sourcing:**
- https://vi.aliexpress.com/item/1005011826373928.html (the order)
- https://witmotion-sensor.com/products/so-arm101-kit-pro-low-cost-open-source-6-axis-ai-robotic-arm-servo-motor-kit-for-lerobot-hugging-face-projects
- https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html ; https://www.seeedstudio.com/SO-ARM101-3D-printed-Enclosure-p-6428.html
- https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html
- https://github.com/TheRobotStudio/SO-ARM100
- https://www.waveshare.com/so-arm100-3dp-parts-kit.htm ; https://www.waveshare.com/wiki/SO-ARM100/101_Kit_Aassembly
- https://thinkrobotics.com/products/so-arm101-hugging-face-lerobot
- https://www.amazon.com/SO-ARM101-Debugging-Reduction-345-Compatible/dp/B0FLW54PJB
- https://hshop.vn/search?q=STS3215 (zero local stock confirmation)
