---
name: workcell-geometry
description: Freeze and document the BeanSight physical workcell — millimetre drawing, ruler photo, arm/camera/nest/cup/lamp/grid geometry, tape identities, desk power budget, cable relief, and session invalidation. Use when laying out, measuring, moving, rebuilding, or documenting the workcell.
---

# Workcell geometry

Full authority: `docs/hardware_and_safety.md` (electrical, layout, and stop rules),
`docs/HANDOFF.md` §3, and `docs/execution_and_portfolio.md` (required workcell artifact).

## Non-negotiable boundary

- **Leader arm = 5 V. Follower arm = 12 V. Never swap.** A wrong supply can burn motors.
- Inventory before power: do not connect a supply until servo, controller, voltage, current,
  barrel, polarity, and invoice photographs agree with documentation and seller confirmation.
- If motor IDs are touched, stop and load `skills/hardware-bringup/SKILL.md`: connect one motor at
  a time and never flash a daisy chain.
- Keep `BeanSightController` unarmed during layout and reach checks. If motion is later enabled,
  operate supervised with the switched power strip within reach.

## 1. Assemble the physical reference set

Have the stable table, follower clamp, C920 mount, C270 bracket and strain relief, one-bean nest,
reject cup, fixed bins, five-position block grid, fixed diffused lamp, diffuser, matte backdrop,
ruler or calipers, labels, and position tape present before declaring the geometry frozen.

Do not record coordinates from memory. Photograph a ruler in the same scene as the measured
fixtures and keep one annotated millimetre drawing as the geometry artifact.

## 2. Reserve electrical and identity colors

- Red = 12 V follower arm, supply, barrel, USB cable, and matching band at the arm socket.
- Blue/white = 5 V leader arm, supply, barrel, USB cable, and matching socket band.
- Yellow = object bands.
- Green/white = camera-cable and port flags.
- Never reuse red or blue as sorting-task colors near the workspace.

Photograph both cable ends and their matching arm labels. Connector fit never proves identity.

## 3. Check the desk power and USB layout

- Reserve four AC sockets: MacBook charger, Orico hub adapter, 5 V leader supply, and 12 V
  follower supply.
- Reserve two USB-A power ports for the two ring lights; do not draw their power from the Mac.
- Keep Mac ports available for cameras. Do not use USB extension cables for the C920 or C270.
- Keep two USB-A-to-C adapters as the documented direct-port fallback if the powered hub fails
  the dual-camera bandwidth test.

This power count establishes connector capacity; it does not replace the photographed electrical
inventory or qualify the hub under the later four-device load.

## 4. Measure and mark the geometry

Record in millimetres and photograph:

1. Follower-base origin, orientation, clamp, and workspace boundary.
2. C920 clamp position, height, pitch, and inspection ROI.
3. Inspection-nest center and the four controlled offset positions.
4. Five-position wooden-block grid.
5. Reject-cup center, rim height, and orientation; fixed-bin locations.
6. Lamp position, diffuser distance, and matte-backdrop boundary.
7. C270 bracket, wrist-cable slack loop, and every cable-relief point.

Check the full reachable range by hand before torque is enabled. The cable must remain slack and
the arm must not contact anything outside the planned nest-to-cup path.

## 5. Freeze, identify, and invalidate

- Assign the frozen arrangement a session ID and reference the drawing/photo in the experiment
  manifest or same-day decision record.
- Mark every base, clamp, nest, cup, lamp, backdrop, grid, and cable route.
- If any mark moves, stop collection and start a new `session_id`; never silently mix data.
- Cut power on unexpected direction, grinding, repeated communication errors, rising temperature,
  a taut camera cable, a shifted base, or off-path contact. Log a scored stop as `safety_stop`.

Fixed geometry reduces presentation variance. It does not repair calibration, weak demonstrations,
camera bandwidth, or an end effector that cannot grasp an 8–12 mm bean.
