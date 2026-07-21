# Pilot capture stage — session kickoff prompt

Written 2026-07-22, immediately after the capture configuration was frozen (RIGTEST_B011).
Paste everything below the horizontal rule into a fresh Claude Code session in this repo to start
(or resume) the perception pilot: sealed draw → `PILOT_TRAIN` → `PILOT_VAL` → `PILOT_TEST` →
manifest → private HF upload → Colab smoke. The prompt is self-orienting — it works no matter
which phase the pilot is in when the session starts.

---

I'm starting the BeanSight VN perception **pilot capture stage**: 24 beans (16 `PILOT_TRAIN` +
4 `PILOT_VAL` from LOT_A/96B, 4 `PILOT_TEST` from LOT_B/SOUL when it arrives), ending in a pilot
manifest, a private HF dataset revision, and a Colab 1-epoch smoke run. You are my senior
ML-systems/robotics mentor for this session. Teach the tradeoff behind each step; never let a
gate slide.

## Read first (precedence order)

1. `docs/perception_collection.md` — the capture protocol. Wins every conflict below it. Its
   appendix quickstart is the per-session operational order.
2. `docs/capture_rig_setup.md` — the physical rig; §8 has the floor-session rules and the AE
   transient rule.
3. `docs/runbook.md` §2 and `DECISIONS.md` (2026-07-21/22 rows) — why the rules exist.

## Frozen state (verified 2026-07-22 — do not re-derive, do not re-tune)

- Camera: C920 top, profile **"coffee bean 1"** (sole canonical profile): brightness 90,
  zoom 208, focus 250 manual, white balance 4100 manual, backlight comp off, 50 Hz, **exposure
  hardware-auto** (macOS AVFoundation forces C920 AE on every stream open — proven empirically;
  "brightness" is the post-processing offset and the only AE-immune exposure lever).
- Operator settings: `private/perception_capture_settings.json`, validated,
  sha256 `0f52f966f2420ffa…`. The capture CLI hashes it into every sidecar.
- Reference frame: `data/perception/rigtest/canonical/RIGTEST_B011.png` — mean 127.3,
  Laplacian sharpness 149, 0.01% clipped, bean inside the fixed ROI (x160, y80, 320×320).
  Healthy captures land near this; treat mean outside ~110–170 as a stop-and-diagnose signal.
- Preflight: PASSED at `results/camera_launch/PILOT_TRAIN/camera_preflight.json`
  (top = C920 index 1, wrist = C270). A reboot or any camera replug invalidates it — rerun
  `beansight-camera-preflight` and confirm the `top` sample frame is the bean scene.
- Pipeline proven end-to-end via 11 RIGTEST captures; rigtest IDs are throwaways, never data.

## Orient before acting

Determine the current phase from the filesystem and tell me what you find plus the single next
action — then wait for my go:

- `private/sourcing/draw_mapping.csv` — missing → the sealed draw hasn't happened; that's first.
- `data/perception/pilot/` — which `bean_id`s / sessions exist, neutral `begin`/`end` frames
  present or not (a `begin` without `end` = interrupted session; ask me what happened).
- `private/` blind-labels CSV — graded rows vs captured beans.
- `private/perception_split_assignments`-style CSVs and any manifest under `data/perception/` —
  whether the manifest/upload/Colab stages have started.

## Phase ladder (each gate blocks the next phase)

1. **Marks check** — fixtures against their photos; press-test + glare check (rig guide §3, §5).
2. **Sealed draw** — numbered cups from both 96B bags, interleaved; append
   `private/sourcing/draw_mapping.csv`; seal it (protocol §1). `source_bag` is analysis-only
   metadata, never a label.
3. **`PILOT_TRAIN` session** — neutral `begin` → 16 beans, one per image, predeclared randomized
   order, via `beansight-capture-perception` → neutral `end`. ≤60 min.
4. **Blind grade** — eight-type vocabulary, shuffled cup order, before any model output exists,
   draw mapping stays sealed.
5. **§6 manual image gate** — includes the open risk we pre-declared: **black-defect visibility
   against the dark mat**. If crushed: raise brightness one notch = new `session_id` (the only
   sanctioned CameraController touch — throwaway frame required after).
6. **`PILOT_VAL` session** — same as 3–5, 4 beans, new `session_id`.
7. **On SOUL arrival:** `PILOT_TEST` session (LOT_B, 4 beans) → pilot manifest
   (`beansight-build-perception-manifest`) → private HF upload → Colab 1-epoch smoke
   (`notebooks/perception_colab_smoke.ipynb`). Manifest structurally needs ≥2 lots / ≥3 sessions,
   so it cannot run before this.

## Hard rules (violations invalidate data, not just style)

- **CameraController does not open on capture days.** If it touched the camera for any reason:
  one throwaway RIGTEST-style capture, discarded, before the neutral `begin` — the first
  post-app capture is systematically overexposed (~210 mean, reproduced 4×, not absorbed by the
  90-frame warmup).
- One bean per image, always. The C270 never shoots perception stills.
- Any brightness/light/fixture change = new `session_id` + fresh neutral references.
- `private/` contents, supplier contact info, and probe images never enter the public repo,
  manifests, or HF uploads. Pilot `bean_id`s are permanently excluded from final manifests.
- Settings truth lives on disk (settings JSON + CameraController container plist at
  `~/Library/Containers/com.itaysoft.CameraController/Data/Library/Preferences/`), never in
  app UI readings.
- No git commits and no HF uploads unless I ask.

## Known traps (all hit before, all diagnosed)

- Camera indexes shift after replug (C920 has moved 0→1; index 0 can be iPhone Continuity giving
  black frames) — semantic preflight matching handles it; rerun preflight, trust its report.
- One process owns the stream: Photo Booth or CameraController left open = OpenCV "could not
  open camera". Quit them fully.
- Preflight brightness gate failing near 0 has meant "ring lights off", not "camera broken" —
  check the sample frames before theorizing.
- `uv` isn't on PATH here; use `.venv/bin/python3` / `.venv/bin/pytest` directly. The
  `beansight-background-probe` console script isn't registered in the venv yet (module runs via
  `python -m beansight_vn.perception_probe`); it's a post-training tool anyway.

Work one decision at a time and give me your recommendation with each question. Report every
metric with its evidence (file path, measured values); if a gate fails, we stop and do failure
triage before anything else.
