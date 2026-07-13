"""Camera-arrival-day smoke test.

Enumerates every camera macOS exposes, grabs a test frame from each, and saves
it to videos/camera_test/ so you can tell which index maps to which physical
camera. Run once per camera plugged in, then with both, and tape a label
(index number) on each camera body.

Usage (from the lerobot venv):
    python src/camera_check.py [--max-index 6]

If every frame is black or capture fails: System Settings -> Privacy &
Security -> Camera -> enable your terminal app, then retry.
"""

import argparse
import sys
from pathlib import Path

import cv2

OUT_DIR = Path(__file__).resolve().parent.parent / "videos" / "camera_test"


def probe(index: int) -> dict | None:
    # CAP_AVFOUNDATION is the native macOS backend; the default autodetect
    # sometimes picks a slower/flakier path.
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap.release()
        return None
    ok, frame = cap.read()
    info = None
    if ok and frame is not None:
        h, w = frame.shape[:2]
        fps = cap.get(cv2.CAP_PROP_FPS)
        out_path = OUT_DIR / f"camera_{index}.jpg"
        cv2.imwrite(str(out_path), frame)
        info = {
            "index": index,
            "width": w,
            "height": h,
            "fps": fps,
            "mean_brightness": float(frame.mean()),
            "saved": str(out_path),
        }
    cap.release()
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-index", type=int, default=6)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    found = []
    for i in range(args.max_index):
        info = probe(i)
        if info is None:
            continue
        found.append(info)
        black = " (BLACK FRAME — check camera permission!)" if info["mean_brightness"] < 5 else ""
        print(
            f"index {info['index']}: {info['width']}x{info['height']} "
            f"@ {info['fps']:.0f} fps -> {info['saved']}{black}"
        )

    if not found:
        print("No cameras found. Check USB connections and terminal camera permission.")
        return 1
    print(f"\n{len(found)} camera(s) working. Label each physical camera with its index.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
