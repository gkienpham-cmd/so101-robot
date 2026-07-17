# SO-101 arrival-day bring-up checklist

Print this worksheet and complete it in order. The authority for safety is
[hardware_and_safety.md](hardware_and_safety.md); the operational sequence is
[runbook.md](runbook.md). Blank fields may point to private evidence, but receipts, addresses,
seller messages, shipping labels, and photographs must not be committed.

**Stop rule: no arm power or controller USB connection before Gate A is signed. Leader arm = 5 V.
Follower arm = 12 V. Never swap them. Connector fit is not evidence of identity.**

## Session record

- Date and local time: ____________________
- Operator: ____________________
- Kit/invoice reference: ____________________
- Private evidence folder/reference: ____________________
- Official kit assembly guide revision/reference: ____________________
- Pinned LeRobot revision: `30da8e687a6dfc617fcd94afc367ac7071c376ce`
- Switched power cutoff location: ____________________
- Soft landing surface installed: [ ]
- One operator designated; observers outside the marked boundary: [ ]

Before opening, place the switched power strip within reach but leave it off. Remove jewelry and
loose clothing, tie back hair, clear the reachable volume, and prepare a small-parts tray, labels,
calipers/ruler, and the invoice and packing list.

## 1. Continuous unboxing — no power

- [ ] Start one continuous video before breaking the seal.
- [ ] Record the sealed box and shipping condition.
- [ ] Record every tray before removing parts.
- [ ] Photograph every component group and its count.
- [ ] Preserve packaging until the inventory and damage checks pass.

Record only private evidence references here:

| Evidence | Private reference | Checked |
|---|---|---|
| Sealed box and shipping condition | ____________________ | [ ] |
| Continuous unboxing video | ____________________ | [ ] |
| Every tray and component count | ____________________ | [ ] |
| Invoice and packing list | ____________________ | [ ] |
| Damage/shortage close-ups, if any | ____________________ | [ ] |

## 2. Mechanical and electrical inventory — still no power

Do not connect an arm supply, controller USB cable, or motor lead. Read printed labels; do not infer
identity from housing shape, cable color, resistance, or connector fit.

| Item | Expected | Actual/evidence reference | Pass |
|---|---|---|---|
| Follower servos | 6; identical ordered Pro variants | ____________________ | [ ] |
| Leader servos | 6; three 1/147, two 1/191, one 1/345, subject to invoice | ____________________ | [ ] |
| Separate follower spares | 2× **ST-3215-C018**, 12 V, 1:345; each printed label photographed | ____________________ | [ ] |
| Bus-servo controller boards | 2; markings photographed | ____________________ | [ ] |
| Controller USB-C data cables | 2 | ____________________ | [ ] |
| Leader supply | Label expected 5 V, 3 A; verify actual label and polarity | ____________________ | [ ] |
| Follower supply | Label expected 12 V, 3 A; verify actual label and polarity | ____________________ | [ ] |
| Clamps and printed structures | Match packing list; no cracks or warping | ____________________ | [ ] |
| Thin gripper parts | No cracks, splits, or stripped holes | ____________________ | [ ] |
| Screws and three-wire leads | Counts match packing list | ____________________ | [ ] |

Electrical identity record:

| Arm | Servo evidence | Board marking | Supply label | Barrel | Polarity | Records agree |
|---|---|---|---|---|---|---|
| Leader | ____________________ | ____________________ | ____________________ | __________ | __________ | [ ] |
| Follower | ____________________ | ____________________ | ____________________ | __________ | __________ | [ ] |

### Gate A — inventory approval before any power

All physical labels, motor variants, controller markings, voltage, current, barrel size, polarity,
invoice, packing list, and official kit documentation must agree. An expectation in this repository
does not authorize power-up.

- [ ] No unresolved shortage, crack, label mismatch, polarity ambiguity, or servo-variant ambiguity.
- [ ] **Leader supply is physically verified as 5 V and assigned only to the leader.**
- [ ] **Follower supply is physically verified as 12 V and assigned only to the follower.**
- [ ] If anything is unclear, stop and obtain written confirmation; do not test by trying a supply.

Operator signature: ____________________  Date/time: ____________________

Second review/sign-off: ____________________  Date/time: ____________________

The second reviewer may join by live video, but must be a named human who can read the photographed
servo and power-supply labels back to the operator. An AI review or a second pass by the operator is
not the second sign-off. **Do not continue without both sign-offs.**

## 3. Permanent identity labels — power remains off

- [ ] Apply **red** labels to the 12 V follower arm, supply, barrel, controller cable, and the arm's
  power-socket end.
- [ ] Apply **blue/white** labels to the 5 V leader arm, supply, barrel, controller cable, and the
  arm's power-socket end.
- [ ] Store each spare in a red-labeled bag marked **FOLLOWER ONLY — 12 V C018 — UNASSIGNED**;
  keep it physically separate from every 5 V leader servo.
- [ ] Reserve red and blue/white for power identity; do not reuse them as workspace class colors.
- [ ] Apply green/white camera cable and physical-port flags.
- [ ] Verify that both ends of every power path show the same arm identity before connection.

Labeling evidence reference: ____________________

## 4. Joint and servo map — no ID assignment yet

The leader motors have mixed gear ratios and are not interchangeable. Populate every printed model
and ratio from the actual kit, then map it to a joint using the verified official kit guide. If that
guide does not unambiguously map every leader ratio to a joint, stop before connecting a motor.

| Arm | Joint | Required ID | Printed model | Printed ratio/voltage | Label/evidence ref | Official map verified |
|---|---|---:|---|---|---|---|
| Leader | shoulder pan | 1 | __________ | __________ | __________ | [ ] |
| Leader | shoulder lift | 2 | __________ | __________ | __________ | [ ] |
| Leader | elbow flex | 3 | __________ | __________ | __________ | [ ] |
| Leader | wrist flex | 4 | __________ | __________ | __________ | [ ] |
| Leader | wrist roll | 5 | __________ | __________ | __________ | [ ] |
| Leader | gripper | 6 | __________ | __________ | __________ | [ ] |
| Follower | shoulder pan | 1 | __________ | __________ | __________ | [ ] |
| Follower | shoulder lift | 2 | __________ | __________ | __________ | [ ] |
| Follower | elbow flex | 3 | __________ | __________ | __________ | [ ] |
| Follower | wrist flex | 4 | __________ | __________ | __________ | [ ] |
| Follower | wrist roll | 5 | __________ | __________ | __________ | [ ] |
| Follower | gripper | 6 | __________ | __________ | __________ | [ ] |

- [ ] Controller bus-channel jumper positions match the actual controller documentation.
- [ ] Each physical motor has an arm, joint, and intended ID label before setup begins.
- [ ] No motor is substituted across arms because its housing looks similar.

### Gate B — motor map approval

Operator signature: ____________________  Reviewer: ____________________  Date/time: __________

## 5. Resolve current controller ports

**Power rule for every step below: leader uses only the verified 5 V leader supply; follower uses
only the verified 12 V follower supply; never swap. Keep the switched cutoff within reach.**

Use the pinned environment at `~/robotics/lerobot`. Resolve one controller at a time. Connect that
controller, run `lerobot-find-port`, then unplug it when the interactive command asks and press Enter.
Never reuse a `/dev/tty.*` value from an older launch.

```bash
cd ~/robotics/lerobot
source .venv/bin/activate
lerobot-find-port
```

- Current leader port: `/dev/____________________`
- Current follower port: `/dev/____________________`
- Port-resolution terminal log reference: ____________________

If macOS reports an incorrect status packet or cannot find a motor, check the data cable, adapter
jumper, and current port first. Never try the other arm's supply as a diagnostic.

## 6. Assign motor IDs — exactly one motor at a time

**Leader = verified 5 V only. Follower = verified 12 V only. Never swap. Connect exactly one motor
to the active controller; never flash a daisy chain.**

Run one arm's interactive command at a time:

```bash
lerobot-setup-motors \
  --robot.type=so101_follower \
  --robot.port=/dev/REPLACE_FOLLOWER

lerobot-setup-motors \
  --teleop.type=so101_leader \
  --teleop.port=/dev/REPLACE_LEADER
```

Pinned LeRobot prompts in reverse joint order: gripper 6, wrist roll 5, wrist flex 4, elbow flex 3,
shoulder lift 2, shoulder pan 1. At every prompt:

1. Switch the assigned arm supply off and verify the motor bus is de-energized.
2. Disconnect the previous motor; connect only the specifically prompted motor.
3. Recheck the motor's arm, model/ratio, joint, intended ID, lead orientation, and controller jumper.
4. Restore only that arm's assigned supply and press Enter once.
5. Record the success or error below. Cut power before touching the next motor lead.

| Arm | Prompted joint/ID | Only one motor confirmed | ID result | Error/evidence reference |
|---|---|---|---|---|
| Follower | gripper / 6 | [ ] | __________ | __________ |
| Follower | wrist roll / 5 | [ ] | __________ | __________ |
| Follower | wrist flex / 4 | [ ] | __________ | __________ |
| Follower | elbow flex / 3 | [ ] | __________ | __________ |
| Follower | shoulder lift / 2 | [ ] | __________ | __________ |
| Follower | shoulder pan / 1 | [ ] | __________ | __________ |
| Leader | gripper / 6 | [ ] | __________ | __________ |
| Leader | wrist roll / 5 | [ ] | __________ | __________ |
| Leader | wrist flex / 4 | [ ] | __________ | __________ |
| Leader | elbow flex / 3 | [ ] | __________ | __________ |
| Leader | shoulder lift / 2 | [ ] | __________ | __________ |
| Leader | shoulder pan / 1 | [ ] | __________ | __________ |

### Gate C — individual IDs complete

- [ ] All twelve motors passed individually; no daisy chain was flashed.
- [ ] Any error was diagnosed before retry; no supply was changed by guesswork.

Operator signature: ____________________  Reviewer: ____________________  Date/time: __________

## 7. Assemble and verify each chain

Switch both arm supplies off and disconnect them before assembly. **When power is restored for a
check, leader remains 5 V and follower remains 12 V; never swap.**

- [ ] Assemble against the verified official kit guide.
- [ ] Do not force screws into printed threads or overtighten them.
- [ ] Do not sharply bend a three-wire lead or remove internal servo gears unless the exact guide
  explicitly requires it.
- [ ] After assembly, connect each six-motor chain and verify IDs 1–6 respond once.
- [ ] Clamp both arms to the stable table.
- [ ] With torque off, move every joint through its planned reachable range by hand.
- [ ] Install the wrist-camera slack loop and strain relief; the cable stays slack across the full
  reachable range.
- [ ] Mark both bases, the top-camera mount, nest, cup, lamp, and workspace boundary.

Unexpected ID, binding, cable tension, or mechanical interference: ______________________________

### Gate D — mechanical range and chain approval

Operator signature: ____________________  Reviewer: ____________________  Date/time: __________

## 8. Calibrate and back up immediately

**Leader = verified 5 V only; follower = verified 12 V only; never swap. Supervised operation and a
reachable cutoff are mandatory. Cut power on unexpected direction, grinding, repeated communication
errors, rising servo temperature, or a taut cable.**

Use the current ports and stable IDs:

```bash
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/REPLACE_FOLLOWER \
  --robot.id=beansight_follower

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/REPLACE_LEADER \
  --teleop.id=beansight_leader
```

- [ ] Follow the interactive prompts without forcing a joint.
- [ ] Record the exact calibration paths printed by LeRobot.
- [ ] Confirm each JSON is readable and contains all six motor IDs.
- [ ] Copy both JSONs immediately to an ignored `calibration/backup-YYYYMMDD/` directory.
- [ ] Record hashes for the originals and backups and confirm they match.

From the BeanSight repo root, replace the date and exact paths with the paths printed by LeRobot:

```bash
mkdir -p calibration/backup-YYYYMMDD
cp /EXACT/FOLLOWER/CALIBRATION.json calibration/backup-YYYYMMDD/beansight_follower.json
cp /EXACT/LEADER/CALIBRATION.json calibration/backup-YYYYMMDD/beansight_leader.json
shasum -a 256 \
  /EXACT/FOLLOWER/CALIBRATION.json \
  calibration/backup-YYYYMMDD/beansight_follower.json \
  /EXACT/LEADER/CALIBRATION.json \
  calibration/backup-YYYYMMDD/beansight_leader.json
```

Expected pinned-v0.6 locations, unless the CLI prints a configured override:

- Follower: `~/.cache/huggingface/lerobot/calibration/robots/so_follower/beansight_follower.json`
- Leader: `~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/beansight_leader.json`

| Arm | Exact original path | Backup path | Hash match |
|---|---|---|---|
| Follower | ______________________________ | ______________________________ | [ ] |
| Leader | ______________________________ | ______________________________ | [ ] |

### Gate E — calibration backup approval

Operator signature: ____________________  Reviewer: ____________________  Date/time: __________

## 9. First supervised teleoperation without cameras

**Leader = verified 5 V only; follower = verified 12 V only; never swap. Keep the switched cutoff in
reach. A 10-degree relative-target limit reduces command jumps but does not fix a bad calibration,
wrong motor map, obstruction, or unexpected direction.**

Start over a soft surface with an empty workspace and both arms in low, supported poses:

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/REPLACE_FOLLOWER \
  --robot.id=beansight_follower \
  --robot.max_relative_target=10.0 \
  --teleop.type=so101_leader \
  --teleop.port=/dev/REPLACE_LEADER \
  --teleop.id=beansight_leader \
  --fps=30 \
  --teleop_time_s=30
```

- [ ] Start with small, slow leader movements.
- [ ] Verify each follower joint moves in the expected direction before increasing range.
- [ ] Keep fingers, hair, jewelry, and loose clothing outside the reachable volume while torque is on.
- [ ] Never force a joint by hand with torque enabled.
- [ ] End the run immediately if any stop condition occurs.

Outcome and terminal-log reference: _____________________________________________________________

## 10. First supervised teleoperation with both cameras

Complete and review the semantic camera preflight first. Resolve C920=`top` and C270=`wrist` again
for this launch; never reuse remembered numeric indexes. Check C270 focus at the mounted working
distance and recheck the wrist cable over the full range with torque off.

**The arm power rule remains unchanged: leader 5 V, follower 12 V, never swap. If the PW7U is used,
power it only with its verified USB-C 5 V/3 A hub adapter; never substitute either arm supply.**

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/REPLACE_FOLLOWER \
  --robot.id=beansight_follower \
  --robot.max_relative_target=10.0 \
  --robot.cameras='{
    top: {
      type: opencv,
      index_or_path: REPLACE_TOP,
      width: 640,
      height: 480,
      fps: 30,
      fourcc: MJPG
    },
    wrist: {
      type: opencv,
      index_or_path: REPLACE_WRIST,
      width: 640,
      height: 480,
      fps: 30,
      fourcc: MJPG
    }
  }' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/REPLACE_LEADER \
  --teleop.id=beansight_leader \
  --fps=30 \
  --teleop_time_s=30 \
  --display_data=true
```

- [ ] `top` visibly shows the C920 scene; `wrist` visibly shows the C270 view.
- [ ] No camera cable becomes taut and neither base or fixture shifts.
- [ ] If hub cameras are the only passing topology, repeat the hub load test with both controller
  boards present before recording.
- [ ] This teleop does not qualify video recording; five smoke episodes and first-save inspection
  remain required by runbook section 6.

Outcome and terminal-log reference: _____________________________________________________________

## 11. Stop conditions and arrival-day closeout

Cut power immediately on unexpected direction, grinding, repeated communication errors, rising
servo temperature, a taut camera cable, a shifted base, or contact outside the planned path. Do not
retry until the cause is identified. If this occurs during a trial, retain the trial and use the
primary failure code `safety_stop`.

- [ ] No autonomous or learned-policy rollout was attempted on arrival day.
- [ ] `BeanSightController` remains unarmed; no reject callback can cause motion.
- [ ] Arms are powered down in supported poses.
- [ ] Beans touched by the gripper, if any, are permanently removed from food use.
- [ ] Calibration backups and private evidence are present and readable.
- [ ] Open damage, mismatch, temperature, communication, or cable issues are recorded below.

Open issues: ___________________________________________________________________________________

Final operator signature: ____________________  Date/time: ____________________

Final reviewer signature: ____________________  Date/time: ____________________
