---
name: hardware-bringup
description: Arrival-day and power-up procedure for the SO-101 (SO-ARM101 Pro DIY) leader/follower kit — inventory before power, 5V/12V rule, one-motor-at-a-time ID assignment, calibration and backup, stop conditions. Use for ANY task involving unboxing, power, wiring, servo IDs, assembly, or calibration.
---

# Hardware bring-up and safety

Full authority: `docs/hardware_and_safety.md` and `docs/runbook.md` §3–5. Restate the relevant
safety rule in every power/wiring/motor instruction you give.

## Non-negotiables

- **Leader arm = 5 V. Follower arm = 12 V. Never swap** — a wrong supply can burn motors.
- **No power until the inventory is signed off.** Connector fit never implies identity.
- **Servo IDs one motor at a time.** Never flash a daisy chain (#1 documented assembly failure).
- Supervised operation only; switched power strip within reach; never run unattended.

## 1. Unboxing and inventory (before ANY power)

1. Film one continuous unboxing. Photograph shipping label, sealed box, every tray, part counts —
   evidence for a missing-part claim before the buyer-protection window closes.
2. Expected Pro DIY kit contents: 12 servos (6 follower + 6 leader; leader set has MIXED gear
   ratios — three 1/147, two 1/191, one 1/345 — not interchangeable), 2 bus-servo controller
   boards, 2 USB-C data cables, 5 V 3 A + 12 V 3 A supplies, clamps, printed parts, screws,
   three-wire leads. Read every printed label; verify against the invoice.
3. Photograph and record: every servo label/variant, both controller boards, both supply labels
   (voltage AND current), barrel size + center polarity, which arm each supply belongs to.
4. Only after records agree with the WitMotion docs and seller confirmation: apply a permanent,
   distinct color to each arm + its supply + barrel + USB cable. Inspect thin gripper parts for cracks.

## 2. Motor IDs (one at a time)

1. Sort/label the 12 motors by printed model and intended joint before assembly.
2. Check the controller's bus-channel jumper position against its documentation.
3. Connect ONE motor, assign its ID, disconnect, repeat. Joint map: shoulder pan 1, shoulder
   lift 2, elbow flex 3, wrist flex 4, wrist roll 5, gripper 6.

   ```bash
   lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/REPLACE_FOLLOWER
   lerobot-setup-motors --teleop.type=so101_leader  --teleop.port=/dev/REPLACE_LEADER
   ```

4. After all six pass individually, connect the chain and verify each responds once.
5. Assemble without forcing printed threads (they strip) or sharply bending three-wire leads.
   Never substitute a servo across arms because the housing looks the same.

## 3. Calibrate and back up

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/REPLACE_FOLLOWER --robot.id=beansight_follower
lerobot-calibrate --teleop.type=so101_leader  --teleop.port=/dev/REPLACE_LEADER  --teleop.id=beansight_leader
```

Back up both JSONs from `~/.cache/huggingface/lerobot/calibration/` immediately. Keep the same
`--robot.id`/`--teleop.id` everywhere afterward. Then teleoperate WITHOUT cameras first, then with
both, starting with wooden blocks.

## 4. Operating rules and stop conditions

- Clamp arm and camera mount; mark all fixture positions; if a mark moves, new session ID.
- Check the full reachable range by hand BEFORE enabling torque; never force a joint with torque on.
- Start autonomous work from a low pose over a soft surface (torque loss lets the arm fall).
- Fingers/hair/jewelry outside the reachable volume; one operator; observers behind the boundary.
- **Cut power immediately** on: unexpected direction, grinding, repeated comm errors, rising servo
  temperature, taut camera cable, shifted base, or contact off the planned nest/cup path. Do not
  retry before identifying the cause. Log the trial with failure code `safety_stop`.
- "Incorrect status packet"/missing motor model → suspect the USB cable (charge-only?), adapter
  jumpers, or port first. Never try a different power supply by guesswork.
