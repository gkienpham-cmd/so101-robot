# Hardware, arrival, and safety

BeanSight is a supervised research rig. The arm is small, but it can still pinch fingers, snag a
cable, drive into a hard stop, damage a servo, or move unexpectedly when calibration is wrong. This
document is the single arrival and power-up gate.

## Purchased equipment

| Item | Intended use | Check on arrival |
|---|---|---|
| WitMotion Pro DIY SO-101 leader/follower | Teleoperation and learned rejection motion | Servo models, controllers, 5 V/12 V supplies, current ratings, polarity, connectors |
| Logitech C920 | Fixed inspection/top view | Focus, exposure, white balance, 640×480/30 MJPG |
| Logitech C270 | Wrist view | Focus chart at the actual working distance |
| Ulanzi LS08 | Reproducible C920 mount | Clamp stability; mark height and angle |
| ORICO PW7U | Supplemental USB ports | Exact model; USB-C 5 V/3 A supply and cable included or not |
| 25 wooden blocks, 3 cm | Bring-up and five-position test | Dimensions, damaged pieces, high-contrast markers |

The visible Shopee accessories total 3,435,151₫, excluding the arm.

## Add before the arm arrives

- USB-C 5 V/3 A hub supply and cable if absent
- USB-C-to-USB-A adapters for the Mac
- C270 wrist bracket, Velcro ties, and cable strain relief
- fixed diffused high-CRI lamp and matte backdrop
- shallow one-bean inspection nest, reject cup, fixed bins, and position markers
- Phillips #0/#1 screwdrivers, calipers or ruler, labels, and small-parts tray
- spare M2/M3 screws and cable ties
- reachable switched power strip
- high-friction gripper tape and silicone/TPU fingertip material
- two spare M3 screws for a compliant-gripper revision
- green Vietnamese Robusta from at least two lots, with at least 50 expert-reviewed visible rejects

An exact follower servo, spare three-wire cable, and filming tripod are useful but optional.

Do not buy a Jetson, depth camera, Raspberry Pi, 4K camera, suction system, or force sensor during this
month. They add integration work without resolving the current risks: presentation, grasping,
calibration, and disciplined evaluation.

## Before any power is applied

Photograph and record:

- every servo label and motor variant
- both controller boards and their markings
- both power-supply labels, including output voltage and current
- barrel size, center polarity, cable color, and which arm each supply belongs to
- the seller invoice and packing list

Compare those records with the WitMotion documentation and seller confirmation. Do not infer a
supply from connector fit. The expected setup is a 5 V leader and 12 V follower, but that expectation
does not authorize power-up; the physical labels and polarity must agree first.

Once confirmed, put a different permanent color on each arm, supply, barrel connector, and USB
cable. Never swap them. Connect only one servo while assigning IDs.

## Workcell layout

Record dimensions in millimetres and photograph a ruler in the scene:

- follower base origin and orientation
- top-camera clamp, height, pitch, and ROI
- inspection-nest center and four offset positions
- reject-cup center, rim height, and orientation
- lamp position, diffuser distance, and backdrop boundary
- wrist-camera bracket and cable-relief points

If any mark moves, start a new session ID. Do not quietly combine the data.

## Operating rules

- Clamp the arm and C920 mount to a stable table. Mark every fixture position.
- Keep the switched power strip within the operator's reach.
- Route the wrist cable with a slack loop and strain relief. Check the full reachable range by hand
  before enabling torque.
- Start with a low relative-target limit, slow motions, and an empty workspace.
- Keep fingers, hair, jewelry, and loose clothing outside the reachable volume while torque is on.
- One person operates; observers stay outside the marked boundary.
- Never run unattended. A safety stop ends the trial and receives the `safety_stop` code.
- Do not use wet objects, hot objects, glass, sharp foreign matter, loose pills, or biological samples.
- Research beans and all beans touched by the gripper are permanently removed from food use.

## Software interlocks

`BeanSightController` starts with `armed=False`. It logs a confident reject decision without moving
until the operator supplies an explicit reject callback and arms it. An acceptable or uncertain
classification always routes to `no_motion`.

The camera soak must pass before a recording config can be generated. Dataset QA must pass before
cloud training. These checks reduce risk; they do not replace supervision or the physical cutoff.

## Stop conditions

Cut power immediately for unexpected direction, grinding, repeated communication errors, rising
servo temperature, a taut camera cable, a shifted base, or contact outside the planned nest/cup path.
Do not retry until the cause has been identified.

Stop a training run on NaN/Inf or a flat loss after roughly 1,000 steps and inspect the dataset and
configuration. If ACT is below 30%, repair calibration, geometry, demonstrations, or task scope before
changing models. If it remains below 40% after one targeted iteration, narrow the workspace or object
and publish the negative result honestly.
