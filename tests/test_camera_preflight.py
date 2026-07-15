import pytest

from beansight_vn.camera_preflight import (
    CameraDevice,
    parse_avfoundation_devices,
    resolve_semantic_camera,
)

FFMPEG_OUTPUT = """
[AVFoundation indev @ 0x123] AVFoundation video devices:
[AVFoundation indev @ 0x123] [0] FaceTime HD Camera
[AVFoundation indev @ 0x123] [1] Logitech C920
[AVFoundation indev @ 0x123] [2] Logitech HD Webcam C270
[AVFoundation indev @ 0x123] AVFoundation audio devices:
[AVFoundation indev @ 0x123] [0] MacBook Microphone
"""


def test_parse_avfoundation_video_devices_only():
    assert parse_avfoundation_devices(FFMPEG_OUTPUT) == [
        CameraDevice(0, "FaceTime HD Camera"),
        CameraDevice(1, "Logitech C920"),
        CameraDevice(2, "Logitech HD Webcam C270"),
    ]


def test_semantic_resolution_ignores_old_indexes():
    devices = parse_avfoundation_devices(FFMPEG_OUTPUT)
    top = resolve_semantic_camera(devices, "top", "C920")
    wrist = resolve_semantic_camera(devices, "wrist", "C270")
    assert (top.index, wrist.index) == (1, 2)


def test_ambiguous_semantic_resolution_fails():
    devices = [CameraDevice(0, "C920"), CameraDevice(2, "C920 duplicate")]
    with pytest.raises(ValueError, match="exactly one"):
        resolve_semantic_camera(devices, "top", "C920")
