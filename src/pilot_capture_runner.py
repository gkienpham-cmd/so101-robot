"""PILOT_TRAIN capture runner: neutral begin -> 16 beans (predeclared order) -> neutral end.

Run from repo root:  .venv/bin/python3 <this file>

Per capture: prompts for bean placement, invokes beansight-capture-perception,
then gates on the sidecar image (mean must be in 110-170) before continuing.
Resumes safely: skips beans whose canonical PNG already exists (CLI refuses
overwrites anyway). Aborts the session on any out-of-window frame.
"""
import json, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

SESSION = "PILOT_TRAIN"
LOT = "LOT_A"
GEOM = "PILOT_GEOM_02"  # re-frozen 2026-07-23: rings moved closer (max brightness), new marks
PREFLIGHT = "results/camera_launch/PILOT_TRAIN/camera_preflight.json"
SETTINGS = "private/perception_capture_settings.json"
OUTPUT = Path("data/perception/pilot")
ORDER = Path("private/sourcing/capture_order_PILOT_TRAIN.txt")
MEAN_LO, MEAN_HI = 110.0, 170.0

# refuse to run if a camera app is open
apps = subprocess.run(["pgrep", "-fl", "CameraController|Photo Booth"],
                      capture_output=True, text=True)
if apps.stdout.strip():
    sys.exit(f"ABORT: camera app running:\n{apps.stdout}Quit it (Cmd-Q) and rerun.")

def scene_fingerprint_ok(img):
    """The bean scene has ~110 px gridline pitch; wrong camera / wrong aim does not."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float)
    strip = g[400:470, :].mean(axis=0)
    strip -= strip.mean()
    ac = np.correlate(strip, strip, mode="full")[len(strip) - 1:]
    pitch = 10 + int(np.argmax(ac[10:120]))
    return 100 <= pitch <= 120, pitch

# ffmpeg's device-list order and OpenCV's open-by-index order diverged tonight
# (discovered 2026-07-22: the preflight's name->index mapping can label the C270
# stream "C920"). Names are unreliable; the bean scene's ~110 px gridline pitch
# is not. Probe the preflight's stored index and require the fingerprint before
# any capture.
stored = json.load(open(PREFLIGHT))["cameras"]["top"]["index"]
probe = cv2.VideoCapture(stored, cv2.CAP_AVFOUNDATION)
probe.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
probe.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
probe.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
frame = None
for _ in range(30):
    ok, cand = probe.read()
    if ok and cand is not None:
        frame = cand
probe.release()
if frame is None:
    sys.exit(f"ABORT: no frames from preflight index {stored}. Is another app holding it?")
fp_ok, fp_pitch = scene_fingerprint_ok(frame)
if not fp_ok:
    sys.exit(f"ABORT: preflight index {stored} shows grid pitch {fp_pitch}px, not the "
             "~110px bean scene — the preflight is mislabeled or stale. Rerun preflight "
             "until its top sample is the bean scene, then rerun this script.")
print(f"scene check OK: index {stored} shows the bean scene (grid pitch {fp_pitch}px)")

def capture(extra):
    cmd = [".venv/bin/beansight-capture-perception", PREFLIGHT,
           "--settings", SETTINGS, "--output", str(OUTPUT),
           "--session-id", SESSION, "--lot-id", LOT, "--geometry-id", GEOM] + extra
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ABORT: capture failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()

def check(png_path, label):
    img = cv2.imread(str(png_path))
    if img is None:
        sys.exit(f"ABORT: cannot read {png_path}")
    mean = img.mean()
    ok = MEAN_LO <= mean <= MEAN_HI
    grid_ok, pitch = scene_fingerprint_ok(img)
    print(f"   {label}: mean {mean:.1f} [{'OK' if ok else 'OUT OF WINDOW'}] | "
          f"grid pitch {pitch}px [{'OK' if grid_ok else 'WRONG SCENE?'}]")
    if not ok:
        sys.exit(f"ABORT: {label} mean {mean:.1f} outside {MEAN_LO}-{MEAN_HI}. "
                 "Stop and diagnose — do not continue the session.")
    if not grid_ok:
        sys.exit(f"ABORT: {label} gridline pitch {pitch}px is not ~110px — wrong camera, "
                 "wrong aim, or moved rig. Stop and diagnose.")

beans = [b.strip() for b in ORDER.read_text().split()]
assert len(beans) == 16, f"expected 16 beans, got {len(beans)}"

canon = OUTPUT / "canonical"
refs = OUTPUT / "references"

# neutral begin (empty nest)
begin_exists = refs.exists() and any(SESSION in p.name and "begin" in p.name
                                     for p in refs.glob("*.png"))
if not begin_exists:
    input("NEUTRAL BEGIN: nest must be EMPTY, rings on, room dark. Enter to capture... ")
    out = capture(["--neutral", "begin"])
    pngs = sorted(refs.glob("*.png")) if refs.exists() else []
    if pngs:
        check(pngs[-1], "neutral begin")
    print(f"   {out}")

done = {p.stem for p in canon.glob("*.png")} if canon.exists() else set()
todo = [b for b in beans if b not in done]
print(f"\n{len(done)} beans already captured; {len(todo)} to go. Order is predeclared — follow it.")

for b in todo:
    cup = int(b.split("_B")[1])
    input(f"\nPlace the bean from bag P{cup} alone in the nest, hands clear. Enter... ")
    capture(["--bean-id", b])
    check(canon / f"{b}.png", b)

input("\nNEUTRAL END: remove the last bean, nest EMPTY. Enter to capture... ")
out = capture(["--neutral", "end"])
pngs = sorted(refs.glob("*.png")) if refs.exists() else []
if pngs:
    check(pngs[-1], "neutral end")
print(f"   {out}")

print("\nPILOT_TRAIN capture complete. Every bean back in its own P-numbered zip bag. "
      "Do NOT open the draw mapping. Grading happens later, shuffled, blind.")
