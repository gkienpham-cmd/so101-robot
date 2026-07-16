# Skills — portable task playbooks

Thirteen self-contained playbooks in the open Agent Skills format (one folder per skill, a `SKILL.md`
with `name`/`description` frontmatter and the full procedure). Each distills the relevant repo
docs into an execute-ready checklist, so an agent can act correctly without re-deriving the
procedure — but the source docs in `docs/` remain the authority if anything conflicts.

| Skill | Use when |
|---|---|
| [lerobot-pinned-env](lerobot-pinned-env/SKILL.md) | Installing, patching, verifying, or debugging the pinned LeRobot v0.6.0 environment |
| [hardware-bringup](hardware-bringup/SKILL.md) | The kit arrives; anything involving power, servo IDs, assembly, calibration |
| [workcell-geometry](workcell-geometry/SKILL.md) | Freezing or documenting workcell layout, power/tape identity, fixtures, and session boundaries |
| [camera-and-recording](camera-and-recording/SKILL.md) | Camera preflight, port resolution, generating the record config, recording episodes |
| [bean-sourcing-and-labeling](bean-sourcing-and-labeling/SKILL.md) | Roaster outreach, sample purchasing, blind labels, ambiguity, and publication permissions |
| [perception-training](perception-training/SKILL.md) | Preparing perception splits, training the baseline/ResNet-18, selecting thresholds, reporting metrics |
| [perception-controller-integration](perception-controller-integration/SKILL.md) | Connecting the classifier to the unarmed controller and supervised ACT reject rollout |
| [dataset-qa-and-publish](dataset-qa-and-publish/SKILL.md) | Gating a recorded dataset and publishing it to the HF Hub |
| [train-act-vastai](train-act-vastai/SKILL.md) | Any paid GPU training run (ACT, retrain, optional SmolVLA) |
| [gripper-doe-and-singulation](gripper-doe-and-singulation/SKILL.md) | Testing bean-scale fingertips, applying the grasp gate, and documenting singulation |
| [frozen-evaluation](frozen-evaluation/SKILL.md) | Running or scoring the frozen v1 evaluation protocol |
| [honest-reporting](honest-reporting/SKILL.md) | Producing any public number, figure, video, or writeup |
| [coffee-dataset-release](coffee-dataset-release/SKILL.md) | Preparing the permission-safe public dataset card, license, provenance, and release links |

## Loading these into OpenAI Codex

Codex discovers skills from skill directories containing `SKILL.md` files. Two options:

1. **Repo-local (already works):** [AGENTS.md](../AGENTS.md) instructs the agent to open the
   matching skill before executing a matching task, so any agent that honors AGENTS.md picks these
   up with zero installation.
2. **Global install:** copy the skill folders into Codex's skills directory so they're available
   in every session:

   ```bash
   mkdir -p ~/.codex/skills
   cp -R skills/lerobot-pinned-env skills/hardware-bringup skills/workcell-geometry \
         skills/camera-and-recording skills/bean-sourcing-and-labeling \
         skills/perception-training skills/perception-controller-integration \
         skills/dataset-qa-and-publish skills/train-act-vastai \
         skills/gripper-doe-and-singulation skills/frozen-evaluation \
         skills/honest-reporting skills/coffee-dataset-release ~/.codex/skills/
   ```

   (If your Codex version uses a different skills location, check `codex --help` or its docs;
   the folders are plain markdown and portable to any agent that reads SKILL.md.)

Each skill is deliberately standalone — safe to copy out of this repo — but skills reference repo
files by relative path, so repo-local use gives the best results.
