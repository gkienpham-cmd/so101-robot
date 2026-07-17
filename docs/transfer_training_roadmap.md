# SO-101 transfer training roadmap

This is the maintained path from the first real wooden-block policy to bottle caps and, eventually,
material-sorted bottles. It does not replace the BeanSight roadmap. Coffee remains first, and no
transfer task may consume physical-trial or GPU budget until `beansight-v1-frozen` is complete.

## The short answer

Use real leader/follower demonstrations and ACT first. The M1 Pro handles recording, QA, MuJoCo,
small perception/material-classifier experiments, and inference; it does not train ACT or a VLA.
Rent an RTX 4090 for policy training. MuJoCo is useful for reach and fixture work, but it is not a
substitute for real contact data. Isaac Lab is a later, capped comparison once a real cap baseline
exists.

[Seeed Studio](https://wiki.seeedstudio.com/lerobot_so100m/) is a hardware vendor and tutorial
source, not a separate policy-training platform. If its examples disagree with the pinned LeRobot
v0.6.0 checkout, the pinned source wins.

| Route | Use now | What it does not fix |
|---|---|---|
| Real demonstrations + ACT | Primary manipulation path | Poor grasps, bad fixtures, or weak demonstrations |
| MuJoCo on the M1 | Reach, collision, camera, and fixture checks | Servo backlash, friction, cable behavior, or sim-to-real |
| Vast.ai RTX 4090 | ACT training after dataset QA | Bad data or an infeasible gripper-object pair |
| Isaac Lab/LeIsaac | Optional cap sim-to-real comparison | Polymer identification or unmeasured actuator/contact gaps |
| Seeed Studio guides | Hardware orientation and examples | Version control for this repository |

The current NVIDIA SO-101 workshop is useful but separate. It pins Isaac Sim 5.1.0, Isaac Lab
2.3.2, GR00T N1.6, and a different LeRobot revision. Do not combine that environment with the
BeanSight checkout. Sources: [NVIDIA course](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/index.html),
[workshop repository](https://github.com/isaac-sim/Sim-to-Real-SO-101-Workshop), and
[Isaac requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html).

## 1. First real policy: wooden blocks

Before any power instruction: **leader arm = 5 V; follower arm = 12 V; never swap. Complete the
photographed inventory first, and assign motor IDs one motor at a time.** Keep the switched cutoff
within reach and run supervised.

After calibration and backup, generate the block recording config from a newly resolved camera
report:

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile blocks \
  --camera-attestation results/camera_launch/current/attestation.json \
  --episodes 5 \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/beansight-blocks-smoke-v1 \
  --output configs/generated/record_blocks_smoke.json
```

Record five smoke episodes and inspect the first completed save. Then regenerate `--profile blocks`
without the episode override, using a separate `beansight-blocks-v1` repo ID, for the 50-episode run.
Run full dataset QA, watch sample episodes, upload privately, and record the immutable Hub commit.

Build two training configs from the passing QA report. The builder refuses mutable revisions,
failed QA, and sampled QA reports:

```bash
beansight-build-act-config results/blocks_dataset_qa.json \
  --dataset-repo-id YOUR_HF_USER/beansight-blocks-v1_TIMESTAMP \
  --dataset-revision 40_CHARACTER_HF_COMMIT \
  --policy-repo-id YOUR_HF_USER/beansight-blocks-act-v1 \
  --job-name blocks-act-v1 \
  --train-output-dir outputs/train/blocks-act-v1 \
  --mode smoke

beansight-build-act-config results/blocks_dataset_qa.json \
  --dataset-repo-id YOUR_HF_USER/beansight-blocks-v1_TIMESTAMP \
  --dataset-revision 40_CHARACTER_HF_COMMIT \
  --policy-repo-id YOUR_HF_USER/beansight-blocks-act-v1 \
  --job-name blocks-act-v1 \
  --train-output-dir outputs/train/blocks-act-v1 \
  --mode full
```

The smoke config uses 5,000 steps. The full config calculates five data epochs from the complete QA
frame count and batch size 8. The QA report must name the same dataset ID and immutable revision as
the generated config. Train in the pinned LeRobot environment on one RTX 4090, stop on NaN/Inf or a
flat first 1,000 steps, push the checkpoint privately, pin its immutable revision, verify the exact
checkpoint on M1 MPS, log the actual spend, and destroy the instance.

## 2. BeanSight remains the gate

Complete the 20-grasp mechanical gate, 50-75 coffee demonstrations, immutable-dataset QA, ACT
training, and the frozen evaluation. Only the single documented 10-25-demo targeted iteration is
allowed. The cap task starts after those results are frozen, even if the first result is poor.

## 3. Loose cap transfer

The cap task uses one upright plastic screw cap at a time in a 150 x 150 mm marked zone. Exclude
crown caps, touching caps, piles, attached-cap removal, and uncontrolled side poses. The generated
profile contains 75 short demonstrations:

```bash
beansight-build-record-config results/camera_launch/current/camera_preflight.json \
  --profile caps \
  --camera-attestation results/camera_launch/current/attestation.json \
  --gate-evidence /ABSOLUTE/PATH/TO/filled_transfer_gate_evidence.json \
  --follower-port /dev/REPLACE_FOLLOWER \
  --leader-port /dev/REPLACE_LEADER \
  --repo-id YOUR_HF_USER/cap-grasp-v1
```

The cap profile refuses to generate until the evidence file contains the frozen BeanSight summary
hash. The policy learns only `approach -> grasp -> lift to safe handoff`. A dated classifier or sensor
selects the bin. Supervised waypoint motion handles the bin transport and release. This avoids
asking ACT to identify an object and manipulate it in one long policy.

That separation is also consistent with one recent SO-101 preprint: ACT reached 15/20 on simple
transfer but 0/20 on selective color sorting. It is one small benchmark, not a universal result, but
it is enough reason not to make semantic routing part of the first motion policy
([paper](https://arxiv.org/html/2606.08881v2)).

The `MaterialSortController` starts unarmed. One sensor decision consumes one fresh call to `arm()`,
even when that decision correctly fails still; it disarms before any callback. Unknown resin, low
confidence, an inactive route profile, or a manual-review target never invokes the callback.

## 4. Material sensing before bottle motion

RGB can find a bottle and read a visible marking. It cannot prove the chemistry of an unlabeled
polymer. The material study is a separate experiment using an enclosed DB2.3-derived discrete-NIR
fixture. The budget is capped at $300 and one week of bring-up.

Install the optional dependency and follow [material_sensing_protocol.md](material_sensing_protocol.md):

```bash
pip install -e '.[dev,materials]'
beansight-train-material-sensor data/materials/manifest.csv \
  --config configs/material_sensor.json \
  --output-dir outputs/material_sensor/db23_r1
```

The command exits nonzero when the frozen gate or final pipeline qualification fails. It still writes
the confusion matrix, abstention evidence, Wilson intervals, fold audit, and model-selection record,
but labels the saved model candidate unqualified. Runtime inference requires five same-item scans and
refuses that candidate. A failed sensor result stops arm integration; it does not authorize an RGB
substitute or a weaker resin claim.

## 5. Bottle sorting

Start with one empty, dry, uncrushed bottle in a V-cradle. Use a neck grasp. Keep three material bins
inside the measured reach envelope and route uncertainty to manual review.

Run 20 supervised waypoint grasp/lift/drop trials for each representative geometry. If at least
16/20 succeed, keep the waypoint trajectory. Learning is unnecessary for a repeatable cradle. If
pose variation is the largest measured failure category, generate the `bottles` recording profile
and collect 75 demonstrations for `approach -> grasp -> safe handoff`; keep bin transport scripted.

Do not decide that branch by eye. `beansight-material-trial-summary` groups the frozen primary
failure codes into pose variation, mechanical feasibility, transport/place, safety/intervention,
and material/routing. The bottle config generator reads the hashed summary and opens ACT collection
only when all three or more geometries have exactly 20 trials, the waypoint gate failed, and pose
variation is the unique largest group. A hand-entered Boolean cannot override the report.

Payload, jaw opening, friction, and bottle deformation failures trigger a fixture or fingertip
change, not another training run. Attached-cap removal, crushed bottles, piles, dirty waste,
singulation, and conveyor operation stay out of v1.

The example HCMC and Boston route profiles in `configs/route_profiles/` are disabled. Copy one to a
dated file, verify the current local route, and enable that copy only after the sensor gate passes.
Material identity and local recycling acceptance remain separate fields.

## 6. Optional Isaac comparison

`configs/isaac_vastai_spike.json` is a disabled planning template. Enable a copied experiment only
after the real cap ACT baseline, pinned dataset QA, modified SO-101 asset, and physical actuator,
camera, gripper, contact, cap, and workcell measurements exist. Validate the filled copy before
renting anything:

```bash
beansight-validate-isaac-spike /ABSOLUTE/PATH/TO/filled_isaac_spike.json
```

The validator rejects placeholders, missing evidence, mutable revisions/images, cached or mismatched
dataset QA, weak host specifications, excess time or cost, and unsafe physical-evaluation settings.

Use a Vast VM or a prebuilt flattened image on an RTX 4090 with 64 GB RAM and 100 GB disk. The first
gate is headless and limited to two paid GPU-hours: verify the driver and resources, run the Isaac
compatibility checker, render one RGB/depth observation, sustain a ten-minute rollout, cleanly
terminate and relaunch the Isaac application in the same running instance, save evidence under
`outputs/`, then destroy the instance. Do not use A100/H100 for Isaac rendering, and never
teleoperate the physical arm over the public internet.

The enabled config must retain the complete evidence bundle: live offer and host specification,
`nvidia-smi`, compatibility output, immutable version/digest manifest, RGB/depth render, ten-minute
rollout log, both clean-boot logs, GPU-hours/cost, and destruction confirmation. Simulated evidence
never goes under `results/`.

The $10 total includes infrastructure and custom-task work. If infrastructure passes, compare the
five-real control, 75-sim-plus-five-real GR00T policy, and 60-75-real ACT baseline on the same 20
physical starts. The M1 Pro cannot host the GR00T physical policies. This comparison therefore also
requires a local, supervised Linux RTX inference machine; Vast remains training/simulation only. If
that local host is unavailable, stop the optional study before physical comparison.

Before those physical trials: **inventory before power; leader = 5 V, follower = 12 V, never swap;
assign motor IDs one at a time; keep the controller unarmed until an explicit callback and fresh arm
action; operate supervised with the switched cutoff within reach.** Keep Isaac only if every
predeclared count and failure-regression condition passes. This is a pragmatic sample-efficiency
screen, not statistical proof that Isaac is superior.

## Reporting

Use `beansight-material-trial-summary` for bottle/cap JSONL logs. Every rate includes its numerator,
denominator, and Wilson 95% interval. Latency includes sample count, median, and p95. Each failed
attempt keeps one primary failure code. Records also preserve route-profile hashes, supervision and
safety state, whether motion occurred, method/geometry/revision, observed bin, and stage outcomes.
The summary computes the exact 16/20 scripted-waypoint gate per geometry and the permitted next
branch. Its taxonomy distinguishes invalid sensing/routing, approach/grasp variation, jaw opening,
payload, friction slip, deformation, transport/place, intervention, and safety stops. No transfer
result belongs in `results/` until real hardware produced it.
