# DECISIONS.md — One line per significant choice, with rationale

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-14 | Pinned LeRobot to release tag **v0.6.0** (commit `30da8e687a6dfc617fcd94afc367ac7071c376ce`), editable install at `~/robotics/lerobot` | Releases match PyPI/Docker images for dataset `codebase_version` compat; HEAD is unpinned risk. Editable clone so source is readable/patchable. |
| 2026-07-14 | Venv: Python 3.12.4 via `uv`, extras `[feetech,smolvla,dataset,training,viz,core_scripts]` | v0.6.0 modularized extras (setup guide was v0.5.x-era); `dataset`+`training` are required for `lerobot-train`, `core_scripts` for record/teleop, `viz` for dataset visualization. |
| 2026-07-14 | Project repo = `~/Documents/so101-robot` (this folder); LeRobot clone kept outside at `~/robotics/lerobot` | CLAUDE.md + research docs already live here; external source tree stays out of project git. |
| 2026-07-14 | wandb enabled for all training runs | User has account + API key; loss-curve monitoring is the cheap early-abort signal for bad runs. |
| 2026-07-14 | torch 2.11.0, MPS verified available on M1 Pro | Inference target is `--policy.device=mps`; training stays on cloud GPUs per plan. |

## Known issues (watch list)

- **Duplicate libavdevice dylibs** (`cv2` vs `av` both bundle ffmpeg 61.3.100) → objc class-collision warning at import. Documented macOS annoyance; may cause spurious crashes during camera capture. Do nothing unless camera capture actually crashes; then swap to `opencv-python-headless` or align ffmpeg versions.
