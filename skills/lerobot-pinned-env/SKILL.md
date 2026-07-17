---
name: lerobot-pinned-env
description: Install, verify, patch, and debug BeanSight against the exact LeRobot v0.6.0 checkout — separate project and LeRobot environments, pinned-source-as-spec workflow, patch-state checks, and the five documented Week-1 failures. Use for environment setup, dependency or schema errors, patch verification, CLI drift, or macOS recording failures.
---

# Pinned LeRobot environment

Full authority: `docs/runbook.md` §1–2 (installation and patch path), `DECISIONS.md` (pinned
choices), and `RETRO.md` (observed failures). `AGENTS.md` wins for hardware safety.

## Keep the two environments separate

- This repo's venv runs pytest, Ruff, camera preflight, perception/material training, and analysis.
- `~/robotics/lerobot` runs teleoperation, recording, calibration, and policy training against
  LeRobot v0.6.0 commit `30da8e687a6dfc617fcd94afc367ac7071c376ce`.
- Pinned manipulation-dataset QA is the one bridge: install this project editable with `--no-deps`
  into the LeRobot venv so `beansight-dataset-qa` sees the exact checkout. Do not install LeRobot
  into the project venv.
- Never use the M1 Pro for policy training; use it for teleop, recording, calibration, and inference.

Before any hardware command: **leader = 5 V, follower = 12 V, never swap**; inventory before power;
assign IDs one motor at a time; and keep `BeanSightController` unarmed until an explicit callback is
installed and the operator arms it.

## 1. Install and verify the pinned checkout

```bash
brew install git ffmpeg
mkdir -p ~/robotics
cd ~/robotics
git clone https://github.com/huggingface/lerobot.git
cd lerobot
git checkout 30da8e687a6dfc617fcd94afc367ac7071c376ce
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e '.[feetech,smolvla,dataset,training,viz,core_scripts]'
uv pip install --no-deps -e /ABSOLUTE/PATH/TO/so101-robot
```

Verify and preserve `python --version`, `python -c 'import lerobot; print(lerobot.__version__)'`,
`git rev-parse HEAD`, LeRobot CLI help, `beansight-dataset-qa --help`, and `ffmpeg -version`. The Git
SHA must match exactly. The no-dependency project install exposes the QA command without allowing a
resolver to change the pinned LeRobot stack.

For this project venv, if pip or camera support is missing, use the documented recovery:

```bash
python -m ensurepip --upgrade
python -m pip install -e '.[dev,camera]'
python -c 'import cv2; print(cv2.__version__)'
```

## 2. Verify the macOS serial-encoding patch state

On a clean pinned checkout, verify and apply the versioned patch:

```bash
git apply --check --unidiff-zero /ABSOLUTE/PATH/TO/patches/lerobot-v0.6.0-macos-serial-encoding.patch
git apply --unidiff-zero /ABSOLUTE/PATH/TO/patches/lerobot-v0.6.0-macos-serial-encoding.patch
git diff --check
```

On an already-patched checkout, a forward check should fail. Verify the applied state instead:

```bash
git apply --reverse --check --unidiff-zero /ABSOLUTE/PATH/TO/patches/lerobot-v0.6.0-macos-serial-encoding.patch
git diff --check
```

Record the patch filename and LeRobot revision in every experiment manifest. The patch fixes the
confirmed gym-HIL encoding path; it does not prove every future video failure has the same cause.

## 3. Debug from the pinned source, not newer documentation

When a config or CLI disagrees with documentation, inspect the v0.6.0 dataclass, parser, and help
text in the pinned checkout. Validate the candidate through the actual pinned decoder before a paid
run. Do not copy schemas or flags from newer `main`.

Use the five observed Week-1 failures as the first diagnostic map:

1. Broken `lerobot-train` import: install the modular `dataset`, `training`, `core_scripts`, and
   `viz` extras; the old `[feetech,smolvla]` set is incomplete.
2. Rejected sim `env.type`: read `GymManipulatorConfig`; the v0.6.0 parser uses a concrete env
   config, so source is the schema spec.
3. Silent keyboard recording: grant the terminal both Accessibility and Input Monitoring, then
   fully quit with ⌘Q and reopen.
4. `BrokenProcessPool` on episode save: check the cv2/av duplicate-ffmpeg collision and verify the
   serial-encoding patch rather than deleting evidence.
5. Project venv has entry points but no pip/cv2: run `ensurepip`, install `.[dev,camera]`, and verify
   the import instead of inferring readiness from `.venv/bin`.

This workflow controls software drift. It does not qualify real USB bandwidth, motor identity,
calibration, teleoperation feel, or the physical workcell.
