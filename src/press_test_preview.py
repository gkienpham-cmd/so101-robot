"""Live C920 preview for the rigidity press-test, aiming, and height dial-in.

Run from repo root:  .venv/bin/python3 src/press_test_preview.py
Press q in the window to quit.

Camera selection trusts NOTHING named: ffmpeg's device-list order and OpenCV's
open-by-index order diverged on 2026-07-22, so names can lie. Instead every
index is probed and the one showing the bean-scene grid fingerprint
(~110 px gridline pitch) wins. Overlay shows the fixed ROI, live mean, and
live pitch (target 110; green when 108-112).
"""
import sys

import cv2
import numpy as np


def grid_pitch(frame):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)
    strip = g[400:470, :].mean(axis=0)
    strip -= strip.mean()
    ac = np.correlate(strip, strip, mode="full")[len(strip) - 1:]
    return 10 + int(np.argmax(ac[10:120]))


def probe(index):
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    frame = None
    for _ in range(20):
        ok, cand = cap.read()
        if ok and cand is not None:
            frame = cand
    cap.release()
    return None if frame is None else grid_pitch(frame)


matches = []
for idx in range(4):
    p = probe(idx)
    if p is None:
        continue
    tag = " <-- bean scene" if 80 <= p <= 130 else ""
    print(f"index {idx}: grid pitch {p}px{tag}")
    if 80 <= p <= 130:
        matches.append(idx)

if len(matches) != 1:
    sys.exit(f"Could not identify the bean-scene camera uniquely (matches: {matches}). "
             "Check aim/lighting and rerun.")

INDEX = matches[0]
print(f"opening bean-scene camera at OpenCV index {INDEX}")

cap = cv2.VideoCapture(INDEX, cv2.CAP_AVFOUNDATION)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

name = "press-test (q to quit)"
while True:
    ok, frame = cap.read()
    if not ok:
        print("frame read failed")
        break
    cv2.rectangle(frame, (160, 80), (160 + 320, 80 + 320), (0, 255, 0), 1)
    pitch = grid_pitch(frame)
    color = (0, 255, 0) if 108 <= pitch <= 112 else (0, 0, 255)
    cv2.putText(frame, f"mean {frame.mean():5.1f}  pitch {pitch}px (target 110)", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    cv2.imshow(name, frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
