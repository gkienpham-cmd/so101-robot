# SO-ARM101 Arrival Guide: Unboxing, Assembly, Calibration, First Teleop, First Dataset

**Buyer:** Kien, HCMC. Order: WitMotion "SO-ARM101 Kit (Pro)" — **Pro DIY Kit variant (full kit: 12 servos + electronics + both arms' 3D printed parts, buyer-confirmed)** — AliExpress listing [1005011826373928](https://vi.aliexpress.com/item/1005011826373928.html), delivery Jul 20–25, 2026.
**Machine:** MacBook Pro M1 Pro, LeRobot v0.6.0 already installed and proven end-to-end in sim (dataset → vast.ai ACT training → MPS inference).
**Standing safety rule (never break it):** **5V PSU → LEADER arm. 12V PSU → FOLLOWER arm. Never swap.**

Every step below is numbered and checkable. Work top to bottom; do not skip Section 0.

---

## Section 0 — Unboxing & inventory (do this BEFORE confirming receipt on AliExpress)

### 0.1 Which variant you ordered — and why you still verify on arrival

The order is the **Pro DIY Kit** (buyer-confirmed): the full kit — 12x servos, 2x driver boards, both PSUs, cables, clamps, plus both arms' 3D printed parts. For reference, the listing's SKU ladder:

| Variant (SKU) | Live price | ≈ USD | Contents |
|---|---|---|---|
| 3D Printed Parts | ₫1,441,932–1,444,822 | ~$55 | Forearm + main-arm structural plastic for both arms, nothing else |
| Professional Version Servo Kit ("No 3D Printed Parts") | ₫6,643,294 | ~$253 | 12x Pro servos, 2x driver boards, 12V 3A + 5V 5A adapters, 4x G-clamps, 2x USB-C cables, screw packs, servo cables |
| **Professional Version Kit (full DIY)** ← ordered | ₫7,076,740 | ~$269 | Servo Kit + both arms' printed parts |

Even with the right SKU ordered, run the five-minute protocol below before confirming receipt — cross-border kits do occasionally ship with missing servos, wrong gear ratios, or a dead driver board (see §0.5), and the AliExpress dispute window is only 15 days.

### 0.2 Five-minute arrival protocol (film everything)

- [ ] **1.** Record continuous video from sealed parcel → all contents laid out. AliExpress missing-item disputes live or die on unboxing video.
- [ ] **2.** **Weigh the unopened box.** The full Pro DIY kit ships at 2.949 kg (12 servos ≈ 0.75 kg + 2 PSUs + 4 metal G-clamps + boards). **Under ~1.2 kg means the servos/electronics are missing — go straight to Case B (§0.4).**
- [ ] **3.** Count servos — a complete kit needs **12x Feetech STS3215**. If present, sort by the model code printed on the case: leader mix = 1x **C001** (1/345) + 2x **C044** (1/191) + 3x **C046** (1/147), all 7.4V; follower = 6x identical 1/345 (12V **C047/C018** 30 kg·cm in Pro kits, or 7.4V C001).
- [ ] **4.** Look for: 2x servo driver boards, 2x PSUs (read labels: 5V and 12V outputs), 2x USB-C data cables, 4x G-clamps, screw packs, 3-pin servo cables.
- [ ] **5.** Inspect plastic parts against the [SO-ARM100/101 STL manifest](https://github.com/TheRobotStudio/SO-ARM100): one leader set (has **handle + trigger**), one follower set (has **moving jaw**), no warping or cracks. WitMotion print quality is reportedly good ("minimal printing artefacts").
- [ ] **6.** Open AliExpress app → My Orders → this order → tap the item. The **frozen order snapshot** shows exactly which SKU was charged. This decides your path below.
- [ ] **7.** **Do NOT tap "Confirm Received"** until inventory is verified.

### 0.3 Case A — contingency: sourcing electronics separately (only if the kit somehow arrives without them and a dispute fails)

You shouldn't need this section — the Pro DIY Kit includes everything. Kept as the sourcing reference for spares or a worst-case reorder:

1. **Reorder the "Professional Version Servo Kit" variant from the same listing**: ₫6,643,294 + ₫459,743 ship ≈ $253 + $17.5, quoted 6–11 days to HCMC. It is explicitly the complement ("No 3D Printed Parts"). Also check the WitMotion motor-kit listing in "Related items" at **₫5,898,851 ≈ $225** — if contents are identical, save ~₫745k.
2. Seeed Studio direct: [motors-only kit $260 ≈ ₫6.83M](https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html) + DHL to Vietnam ($25–45, 3–7 days).
3. Piecewise AliExpress: 12x STS3215 @ ~$14–16 (₫370–420k) each + 2x Waveshare Bus Servo Adapter @ ~$11 (₫290k) ≈ **$190–215 / ₫5.0–5.6M** — cheapest, but you must hand-pick gear ratios (search "STS3215 1/345 1/191 1/147 SO-101"); easy to mis-order.
4. **Do not plan on local Vietnam stock**: hshop.vn and nshopvn.com return zero STS3215 results (checked 2026-07-15); Shopee has occasional 1/345-only listings at ~₫450–650k each; the 1/147 and 1/191 leader ratios are unobtainable domestically.

### 0.4 Case B — full kit ordered but items missing on arrival

Open a dispute **within 15 days of delivery confirmation**: My Orders → Open Dispute → "Item not as described / missing items". Attach unboxing video + box-weight photo + variant screenshot. Seller has ~3 days to respond, then AliExpress mediates; refunds land in 7–15 business days ([policy summary](https://news.astools.app/en/blog/aliexpress-buyer-protection-return-policy-2026)). If near the deadline, open the dispute immediately — the timer pauses while it's active.

### 0.5 Reliability warning from this exact listing's reviews

2 of 4 reviewers (all on the full kit) report a **servo driver board failing** — one "blew up on plug-in", one died after a day — both fixed with a **Waveshare serial bus servo driver board (~$13 / ₫340k)**. On arrival: inspect both boards for scorched components, and **power the follower board the first time with only ONE servo connected.** Budget one spare Waveshare Bus Servo Adapter into any reorder.

### 0.6 Vietnam power check

WitMotion adapter photos show US flat-two-pin (Type A) plugs — they fit Vietnam's 220V Type A/C sockets, **but verify the label says "Input: 100–240V" before plugging in.** If it says 110V only, do not use it; buy a local 12V 3A or 5V 3A 5.5×2.1mm barrel adapter (₫60,000–120,000 on Shopee).

---

## Section 1 — Tools & workspace

- [ ] Small Phillips screwdrivers: **PH0 and PH1** (only two screw types exist in the whole build: M2x6mm motor screws, M3x6mm horn/structural screws)
- [ ] Small flathead screwdriver or hobby knife — stripping 3D-print support material
- [ ] Label maker or masking tape + marker — label servos **L1–L6 / F1–F6**, both PSU barrel plugs, both USB cables
- [ ] Kitchen/luggage scale (Section 0 box weigh-in)
- [ ] Phone on a stand (unboxing video, and later the assembly videos side-by-side)
- [ ] Sturdy table edge for the 4 G-clamps (arm bases clamp to the table)
- [ ] Two free physical USB/Thunderbolt ports on the Mac (cameras will need one per side later — Section 6)
- [ ] Budget **3–6 hours** for first-time assembly of the pair, plus 30–60 min for motor IDs + calibration. Community logs warn real time runs ~3x the uncut videos.

---

## Section 2 — Motor ID flashing (ONE servo at a time, BEFORE assembly)

**Do this with all 12 servos loose on the desk, not in the frame.** New Feetech servos all ship as ID=1; the setup write goes to whatever is on the bus, so if several servos are connected they ALL get the same ID → bus collisions → disassemble and re-flash. Official rule: *"Make sure it's the only motor connected to the board, and that the motor itself is not yet daisy-chained to any other motor."*

**Power rule applies here too: leader board on 5V, follower board on 12V (assuming 12V follower servos — verify labels first, see 2.1). USB alone powers nothing — the barrel PSU must be plugged in as well.**

### 2.1 Pre-flash sort

- [ ] **1.** Sort the six 7.4V leader servos by case model code and pre-assign joints — the ID scripts cannot detect gear ratio, so physical placement must be right before IDs go on:

| Leader joint | Motor ID | Gear ratio | Model code |
|---|---|---|---|
| shoulder_pan (base) | 1 | 1/191 | ST-3215-**C044** |
| shoulder_lift | 2 | 1/345 | ST-3215-**C001** |
| elbow_flex | 3 | 1/191 | ST-3215-**C044** |
| wrist_flex | 4 | 1/147 | ST-3215-**C046** |
| wrist_roll | 5 | 1/147 | ST-3215-**C046** |
| gripper | 6 | 1/147 | ST-3215-**C046** |

- [ ] **2.** Confirm the six follower servos are identical 1/345 and note their voltage (12V C047/C018 → 12V PSU; if the kit shipped all-7.4V, then **both** arms run on 5V and plugging 12V into either would burn motors).
- [ ] **3.** If the kit shipped **12 identical 1/345 servos** (SO-100 style): it still works — Seeed's SO-ARM100 kit did exactly this, leader torque simply stays disabled. The leader will feel stiffer to backdrive. Do **not** perform SO-100 gear surgery (see Section 4.2). Optionally order the 3-ratio leader set later.

### 2.2 Find each board's port

- [ ] **4.** Plug in the follower board (USB + 12V), run:
```bash
lerobot-find-port
```
Follow the unplug prompt; note the port, e.g. `/dev/tty.usbmodem575E0032081`.
- [ ] **5.** Repeat for the leader board (USB + 5V). If no `/dev/tty.usbmodem*` appears, the #1 culprit is a **charge-only USB-C cable** — swap cables before hunting drivers (none are needed on macOS; the board is native USB-CDC). Waveshare boards: both jumpers on channel **B** (USB).

### 2.3 Flash

- [ ] **6.** Follower (12V PSU connected):
```bash
lerobot-setup-motors \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodemXXXX
```
- [ ] **7.** Leader (5V PSU connected):
```bash
lerobot-setup-motors \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodemYYYY
```
The script walks **gripper-first**: "Connect the controller board to the 'gripper' motor only and press enter" → writes ID 6 + baudrate 1,000,000 to EEPROM (one-time, non-volatile), then wrist_roll=5, wrist_flex=4, elbow_flex=3, shoulder_lift=2, shoulder_pan=1. Expect `'gripper' motor id set to 6` per motor. For the leader, hand the physically-correct gear-ratio servo to each prompt per the table above.
- [ ] **8.** Label each servo immediately after its flash (**F6…F1, L6…L1**) and leave the 3-pin cable plugged into it — it's near-impossible to insert after mounting.
- [ ] **9.** If a step errors, check in order: DC power present, USB data cable, 3-pin cable seated, only one motor attached. Barrel plugs slip out while handling the board — recheck before every Enter.

Official video: [setup_motors_so101_2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/setup_motors_so101_2.mp4)

---

## Section 3 — Follower assembly

Source of truth with per-joint videos: https://huggingface.co/docs/lerobot/so101. Only two screw types: **M2x6** (motor→plastic) and **M3x6** (horns/structure). Horn pattern for every joint: install both horns, secure the **top horn only** with one M3x6 into the servo output shaft; the bottom horn needs no screw.

- [ ] **1. Prep:** strip print supports; confirm a 3-pin cable is already inserted in every motor (Section 2.8).
- [ ] **2. Joint 1 — shoulder_pan (F1):** horns on; drop motor into base; 4x M2x6 (2 top + 2 bottom); slide motor holder over, 2x M2x6 (one per side); attach shoulder part, 4x M3x6 top + 4x M3x6 bottom; add shoulder motor holder. [Joint1_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Joint1_v2.mp4)
- [ ] **3. Joint 2 — shoulder_lift (F2):** horns on; slide motor in from top; 4x M2x6; attach upper arm, 4x M3x6 per side. [Joint2_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Joint2_v2.mp4)
- [ ] **4. Joint 3 — elbow_flex (F3):** horns on; insert motor, 4x M2x6; connect forearm, 4x M3x6 per side. [Joint3_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Joint3_v2.mp4)
- [ ] **5. Joint 4 — wrist_flex (F4):** horns on; slide motor holder 4 over, slide in motor, 4x M2x6. [Joint4_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Joint4_v2.mp4)
- [ ] **6. Joint 5 — wrist_roll (F5):** insert into wrist holder, 2x M2x6 front; **only one horn** here, secured with an M3x6 horn screw; fasten wrist to motor 4, 4x M3x6 both sides. [Joint5_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Joint5_v2.mp4)
- [ ] **7. Gripper (F6):** attach gripper body to motor-5 horn, 4x M3x6; insert gripper motor, 2x M2x6 each side; both horns, top secured with M3x6; attach moving jaw, 4x M3x6 both sides. [Gripper_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Gripper_v2.mp4)
- [ ] **8. Wiring:** mount the controller board on the back of the base; daisy-chain 3-pin cables gripper (F6) → F5 → F4 → F3 → F2 → F1 → controller board; route every cable through the SO-101's wire clips so nothing unplugs during motion.
- [ ] **9.** Clamp the base to the table with 2 G-clamps. **Label the arm, its PSU (12V), and its USB cable "FOLLOWER".**

---

## Section 4 — Leader assembly

### 4.1 Build

Joints 1–5 are identical in structure to the follower (Section 3 steps 2–6), using servos **L1–L5** — remember L2 is the single C001 (1/345). Then:

- [ ] **1. Leader end-effector (L6):** mount leader holder on the wrist, 4x M3x6; attach the **handle** to motor 5 with 1x M2x6; insert gripper motor, 2x M2x6 each side; one horn + M3x6; attach the **trigger** with 4x M3x6. [Leader_v2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/Leader_v2.mp4)
- [ ] **2. Wiring:** daisy-chain L6 → … → L1 → controller board, cables through clips.
- [ ] **3.** Clamp to table; **label arm, PSU (5V), USB cable "LEADER".**

If a printed part looks ambiguous: handle/trigger = leader; moving jaw = follower. Leader and follower also use different wrist-roll printed variants.

### 4.2 About gear removal — you almost certainly should NOT do it

The old **SO-100** design required opening leader servos and removing gears for backdrivability. The **SO-101 eliminates gear removal entirely** — that's what the mixed 1/191 + 1/345 + 1/147 leader servo set is for ("no gear removal", TheRobotStudio README). If your kit shipped the correct mixed ratios, there is nothing to remove.

If your kit shipped 12 identical 1/345 servos, your options:
- **(a) Use as-is (recommended):** fully functional, calibration and teleop identical; the leader is just stiffer/more tiring to move.
- **(b) SO-100-style gear removal:** makes the leader freely backdrivable but it can no longer hold its own weight, and the mod is effectively irreversible. Not recommended.
- **(c)** Order the 3-ratio leader servo set later (TheRobotStudio README links a single bundle of all six leader servos).

---

## Section 5 — Software bring-up on macOS M1 Pro (LeRobot v0.6.0)

All commands verified against the v0.6.0 tag. Prereqs (likely already done from Week 1):

```bash
pip install 'lerobot[feetech]'   # Feetech SDK extra — required for STS3215
hf auth login --token ${HUGGINGFACE_TOKEN} --add-to-git-credential
HF_USER=$(NO_COLOR=1 hf auth whoami | awk -F': *' 'NR==1 {print $2}')   # → gkienpham
```

### 5.1 Ports (every session)

- [ ] **1.** `lerobot-find-port` twice (follower plugged, then leader). **Ports can change across replug/reboot** — always plug the two arms into the same physical ports in the same order, and re-run find-port whenever behavior looks wrong. No `chmod` needed on macOS.

### 5.2 Calibration (once per arm; power ON, correct PSU per arm)

- [ ] **2.** Follower:
```bash
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodemXXXX \
    --robot.id=follower_arm
```
- [ ] **3.** Leader:
```bash
lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodemYYYY \
    --teleop.id=leader_arm
```
Ritual (see [calibrate_so101_2.mp4](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/calibrate_so101_2.mp4)): (1) move **every joint to the middle of its range**, press Enter; (2) sweep **each joint through its full range of motion** while min/max is recorded; press Enter. Seeed's wiki has per-joint reference photos.

- [ ] **4.** Verify files exist: `~/.cache/huggingface/lerobot/calibration/robots/so101_follower/follower_arm.json` and `.../calibration/teleoperators/so101_leader/leader_arm.json`. **The `--robot.id`/`--teleop.id` string IS the calibration filename** — reuse the exact same ids in every later command or LeRobot silently re-calibrates. To redo: delete the JSON and re-run.

### 5.3 First teleop — no cameras

- [ ] **5.**
```bash
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodemXXXX \
    --robot.id=follower_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodemYYYY \
    --teleop.id=leader_arm
```
- [ ] **6.** **Support the follower with one hand at first power-on** — it snaps to the leader's pose. Loop runs ~30 Hz; lag should be imperceptible (<100 ms). Visible lag/stutter = serial problem (cable, hub), not tuning.
- [ ] **7.** Pass criterion: follower mirrors leader through all 6 DOF smoothly for 2+ minutes, no oscillation, no serial errors. If the **wrong arm** twitches, the two identical boards' ports are swapped — re-run find-port.

---

## Section 6 — Cameras (2x 640x480 USB, from Shopee)

### 6.1 macOS permissions (known pitfall)

- [ ] **1.** First camera access triggers "Terminal would like to access the camera" — **approve it.** If you ever denied it, `lerobot-find-cameras` returns 0 cameras *silently*: fix in System Settings → Privacy & Security → Camera.
- [ ] **2.** Disable iPhone Continuity Camera (or move the iPhone away / disable its Wi-Fi/BT proximity) so it doesn't grab a camera index mid-session.

### 6.2 Discover and identify

- [ ] **3.**
```bash
lerobot-find-cameras opencv
```
Expect entries with `Backend api: AVFOUNDATION` and integer `Id: 0, 1, ...` — macOS uses **integer indices, not /dev/video paths**, and the built-in FaceTime camera occupies an index too (expect 3+ entries). **Indices can change after reboot/replug** — re-run each session and identify top vs wrist from the sample images written to `outputs/captured_images/`.

### 6.3 USB bandwidth (untested risk from Week 1)

Two 640x480@30 cams are fine if each negotiates MJPEG (~1–3 MB/s); two uncompressed YUYV streams (~17.6 MB/s each) can exhaust one controller → a camera fails to open or drops to ~15 fps. AVFoundation picks the format automatically. Mitigations in order:
- [ ] **4.** Plug each camera into a **different physical Thunderbolt port (left vs right side of the M1 Pro — separate buses)**; never both through one unpowered hub. Put the two low-bandwidth servo boards on a hub instead if you run out of ports.
- [ ] **5.** If frames drop: lower one camera to `fps: 15`, then to 320x240; replace any USB extension cable (a Hackaday SO-101 log traced "software" camera failures to a bad extension: https://hackaday.io/project/204187/log/243773).

### 6.4 Teleop with cameras + live view

- [ ] **6.**
```bash
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodemXXXX \
    --robot.id=follower_arm \
    --robot.cameras="{ top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodemYYYY \
    --teleop.id=leader_arm \
    --display_data=true
```
**Camera keys are `top` and `wrist` (in that order) — standing decision from doc 03 §2.5.** ACT bakes exact feature names (`observation.images.top`) into checkpoints, so any other key (e.g. `front`) silently forks your dataset/checkpoint namespace.

`--display_data=true` opens a rerun viewer with both feeds + joint plots. A width/height-mismatch error means the camera refused the requested mode — lower fps/res.

### 6.5 The parallel-encoding crash — v0.6.0 ground truth

The macOS crash you hit in sim comes from multi-camera **process-pool video encoding**. In v0.6.0, `parallel_encoding` is **NOT a CLI flag** — it's a Python-API parameter (`LeRobotDataset.save_episode(parallel_encoding=True)` default), and `lerobot-record` calls `save_episode()` bare, so the CLI always takes the crash-prone path with ≥2 cameras. The real CLI mitigation:

- **`--dataset.streaming_encoding=true`** — encodes frames in real time in encoder threads, bypassing the post-episode process pool entirely. **Use this as your macOS default**, paired with `--dataset.encoder_threads=2`.
- If recording via the Python API instead (like your sim scripts): keep passing `save_episode(parallel_encoding=False)`.
- Keep `--dataset.num_image_writer_processes=0` (the default — threads-only image writing) on macOS.
- Note: v0.6.0 renamed `--dataset.vcodec` → `--dataset.rgb_encoder.vcodec`; older tutorials using the old flag will fail. And a post-v0.6.0 commit changed parallel-encoding defaults — re-test this whole path if you ever upgrade.

---

## Section 7 — First real dataset recording

- [ ] **1.** Pick one simple, repeatable task (e.g., cube → bin), fixed object start zone, fixed camera mounts (top-down/front-facing + wrist — camera keys stay `top` and `wrist` per doc 03 §2.5 regardless of physical placement).
- [ ] **2.** Record a 5-episode smoke test first:
```bash
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodemXXXX \
    --robot.id=follower_arm \
    --robot.cameras="{ top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodemYYYY \
    --teleop.id=leader_arm \
    --display_data=true \
    --dataset.repo_id=gkienpham/so101_first_recording \
    --dataset.num_episodes=5 \
    --dataset.single_task="Grab the cube and place it in the bin" \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=10 \
    --dataset.streaming_encoding=true \
    --dataset.encoder_threads=2
```
(Other v0.6.0 defaults: `fps=30`, `video=True`, `push_to_hub=True`, `num_image_writer_threads_per_camera=4`. Add `--dataset.private=true` if wanted.)

> **Timestamp gotcha (doc 03 §5.1, verified in v0.6.0 source — `stamp_repo_id()` in `configs/dataset.py`):** every non-resume run appends `_YYYYMMDD_HHMMSS` to `repo_id`, so the dataset actually lands as `gkienpham/so101_first_recording_<timestamp>`, e.g. `..._20260722_141230`. **Copy the stamped name from the log** — every later command (verify, replay, resume, training) must use it, not the plain name. Set it once: `DS=gkienpham/so101_first_recording_<timestamp>`.
- [ ] **3.** Keyboard controls (v0.6.0 has a terminal-fallback reader — **no macOS Accessibility permission needed**, just keep the launching terminal focused): **Right-arrow / `n`** = end episode early or skip reset; **Left-arrow / `r`** = cancel + re-record episode; **`Esc` / `q`** = stop, encode, upload.
- [ ] **4.** Watch the first `save_episode` complete without crashing — that's the exact failure point from sim.
- [ ] **5.** Verify the dataset at `https://huggingface.co/datasets/$DS` — the **stamped** name from the record log, NOT plain `so101_first_recording` (that URL will 404). Local copy: `~/.cache/huggingface/lerobot/$DS`. Inspect episodes at https://huggingface.co/spaces/lerobot/visualize_dataset.
- [ ] **6.** Replay sanity check (follower re-executes episode 0 — clear the workspace first):
```bash
lerobot-replay --robot.type=so101_follower --robot.port=/dev/tty.usbmodemXXXX \
    --robot.id=follower_arm \
    --dataset.repo_id=$DS --dataset.episode=0     # stamped name, from the record log
```
- [ ] **7.** Crash/resume (verified in v0.6.0 source, `lerobot_record.py` + `LeRobotDataset.resume()` — this resolves doc 03 §5.7's flag): re-run the record command with `--resume=true`, `--dataset.repo_id=$DS` (the stamped name — resume does NOT re-stamp), **and** `--dataset.root=~/.cache/huggingface/lerobot/$DS` — `resume()` hard-errors without an explicit `root`. `--dataset.num_episodes` then means *additional* episodes recorded this session, not the total.
- [ ] **8.** Once the 5-episode pipeline is clean, record the real training set (typically 30–50 episodes) and reuse the Week-1 vast.ai ACT recipe (wandb project `so101`; $0.22 of the $8–40 budget spent).

**main-docs traps:** `--save_checkpoint_to_hub`, `--job.target`, `--policy.pretrained_revision` in current main docs are post-v0.6.0 — ignore. Main docs' 1920x1080 front-camera example: use 640x480 instead (matches your cameras, quarters the USB load).

---

## Section 8 — Safety rules & first-day failure catalogue

### 8.1 Hard rules

1. **5V PSU = leader, 12V PSU = follower. Never swap.** Official wording: plug in the wrong supply "otherwise you might burn your motors." Leader on 12V can permanently burn motor/driver. Follower on 5V is non-destructive (weak/no torque, `Input voltage error!`). Both barrel jacks are identical 5.5mm — **label both plugs and both arm bases before first power-up.** Exception check: if the kit shipped all-7.4V servos, both arms are 5V and the 12V brick must never touch either.
2. **Never move a joint by hand while torque is enabled** — that's how STS3215 gears strip. Disable first (`robot.bus.disable_torque()`).
3. **Never disconnect power/USB during a servo firmware update** — it bricks the motor with no documented recovery. Don't update firmware on day one at all.
4. USB alone never powers motors — DC barrel in before any motor command; re-seat it after handling the board.
5. First power-up of each driver board: **one servo attached only** (blown-board history on this listing, Section 0.5).
6. First teleop: hand under the follower; gentle gripper actions (stall-crushing a rigid object grinds the gripper gears).

### 8.2 Failure → fix table

| Symptom | Cause | Fix |
|---|---|---|
| `Motor 'gripper' (sts3215) was not found` during setup | No DC power (USB-only), bad 3-pin cable, or Waveshare jumpers not on B | Barrel PSU in; cable reseated; jumpers → B ([issue #1244](https://github.com/huggingface/lerobot/issues/1244)) |
| No `/dev/tty.usbmodem*` on Mac | Charge-only USB-C cable | Swap for a data cable; no driver needed |
| Multiple joints answer as one / garbled bus | Duplicate IDs (servos flashed while daisy-chained) | Disconnect all, re-run `lerobot-setup-motors` one servo at a time |
| `[RxPacketError] Input voltage error!` | Follower on 5V | Correct PSU ([issue #2387](https://github.com/huggingface/lerobot/issues/2387)) |
| Wrong arm moves in teleop | Identical boards, swapped ports | Re-run `lerobot-find-port`; standardize physical ports; ids must match arms |
| Weird offsets / arm lurches at connect | Wrong calibration file (id mismatch) or bad ranges | Delete `~/.cache/huggingface/lerobot/calibration/...json`, recalibrate |
| "Magnitude 30841 exceeds 2047" | Corrupted encoder mid-position | Write current position as **2048** with Seeed's middle-position tool, recalibrate ([Seeed wiki](https://wiki.seeedstudio.com/lerobot_so100m_new/)) |
| Clicking/grinding joint, position drift, gritty gripper | Stripped gears | Replacement gear set $3–6 / ₫80–160k (AliExpress, match ratio!) or whole servo: 7.4V ≈ $14–20 / ₫365–520k, 12V 30kg ≈ $25–30 / ₫650–780k. Order spares reactively, via AliExpress (Feetech official store, 1–2 wks to HCMC) — not Shopee |
| Camera opens but partner camera fails / ~15 fps | USB bandwidth (YUYV) or bad extension cable | Separate physical ports (left/right); fps 15; 320x240; replace extension cable |
| `lerobot-find-cameras` shows 0 cameras | Terminal camera permission denied earlier | System Settings → Privacy & Security → Camera |
| Crash at end-of-episode encoding | Multi-camera process-pool encode (known from sim) | `--dataset.streaming_encoding=true --dataset.encoder_threads=2`; Python API: `parallel_encoding=False` |
| Servo totally unresponsive after all checks | Unknown ID/baud from factory | Scan/rewrite with FT_SCServo_Debug_Qt on macOS (build from https://github.com/CarolinePascal/FT_SCServo_Debug_Qt/tree/fix/port-search-timer) or Feetech FD software (Windows) |
| `termios error 22` on macOS serial | Known baudrate bug | See https://github.com/TheRobotStudio/SO-ARM100/issues/150 |

### 8.3 Stage gates (don't advance until the row passes)

| Stage | Pass criterion |
|---|---|
| Ports | Distinct `/dev/tty.usbmodem*` per arm, identity known |
| Motor IDs | Both setup runs completed all 6 prompts; arms work fully daisy-chained |
| Calibration | Both JSONs on disk; re-running teleoperate does NOT re-prompt calibration |
| Teleop (no cam) | 2+ min smooth 6-DOF mirroring, no oscillation, no serial errors |
| Cameras | Both USB cams listed (AVFOUNDATION); both open simultaneously 640x480@30, no drop warnings |
| Teleop + cams | rerun shows both feeds + joint traces at target rate |
| Recording | 5 episodes, no encode crash, `n`/`r`/`q` work, dataset on Hub, replay of episode 0 reproduces the motion |

---

## Section 9 — Reference links

**Official docs & videos**
- Canonical SO-101 guide (motors + assembly + calibration, all videos): https://huggingface.co/docs/lerobot/so101 — note the v0.6.0-pinned docs URL 404s; use this or https://huggingface.co/docs/lerobot/main/en/assemble_so101
- Cameras: https://huggingface.co/docs/lerobot/en/cameras · Teleop/record/replay: https://huggingface.co/docs/lerobot/en/il_robots · Feetech notes (firmware warning): https://huggingface.co/docs/lerobot/feetech
- Videos (`huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/`): `setup_motors_so101_2.mp4`, `Joint1_v2.mp4`…`Joint5_v2.mp4`, `Gripper_v2.mp4`, `Leader_v2.mp4`, `calibrate_so101_2.mp4`
- v0.6.0 release notes (vcodec rename, keyboard fallback): https://github.com/huggingface/lerobot/releases/tag/v0.6.0

**Hardware**
- TheRobotStudio SO-ARM100/101 (BOM, STLs, servo codes C001/C044/C046, ~$230/₫6.04M self-source benchmark): https://github.com/TheRobotStudio/SO-ARM100
- Seeed wiki (PSU table 5V 4A / 12V 2A, calibration reference photos, 2048 recovery): https://wiki.seeedstudio.com/lerobot_so100m_new/
- Seeed kits: [Pro servo kit $260](https://www.seeedstudio.com/SO-ARM101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html) · [Assembled $299](https://www.seeedstudio.com/SO-ARM-101-Assembled-Kit-Pro-p-6691.html)
- Waveshare: [3DP parts kit](https://www.waveshare.com/so-arm100-3dp-parts-kit.htm) · [wiki](https://www.waveshare.com/wiki/SO-ARM100/101)
- STS3215 specs: [7.4V 19kg $13.89](https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html) · [12V 30kg](https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html) · [Feetech](https://www.feetechrc.com/2020-05-13_56655.html)

**Community & troubleshooting**
- Build tutorial with practical tips (pre-insert cables, real build times): https://arturhabuda.com/2025/07/01/build-tutorial-so-101-robot-arms/
- Dual-camera USB cable failure log: https://hackaday.io/project/204187/log/243773
- Backlash/torque baseline (~0.9°): https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/
- Dataset viewer: https://huggingface.co/spaces/lerobot/visualize_dataset

**Purchase & disputes**
- Your listing: https://vi.aliexpress.com/item/1005011826373928.html
- AliExpress dispute rules (15-day window): https://news.astools.app/en/blog/aliexpress-buyer-protection-return-policy-2026 · https://alixblog.com/en/claims-disputes-returns/
- Vietnam stock checks (both zero): https://hshop.vn/search?q=STS3215 · https://nshopvn.com/?s=STS3215

*Exchange rate used throughout: ~26,260 VND/USD (2026-07-14, tradingeconomics.com/vietnam/currency). Compiled 2026-07-15; hardware ETA Jul 20–25.*
