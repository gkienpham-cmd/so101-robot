import hashlib
import json
from datetime import UTC, datetime

import pytest

import beansight_vn.perception_capture as perception_capture_module
from beansight_vn.camera_attestation import preflight_sha256
from beansight_vn.perception_capture import (
    PNG_SIGNATURE,
    CapturedPng,
    OperatorSettingsSnapshot,
    capture_perception,
    load_operator_settings,
    main,
    validate_operator_settings,
    validate_preflight_top,
)


def preflight(*, passed=True, top_model="Logitech HD Pro Webcam C920"):
    return {
        "passed": passed,
        "session_id": "preflight-1",
        "cameras": {
            "top": {
                "passed": True,
                "semantic_name": "top",
                "index": 3,
                "device_name": top_model,
            },
            "wrist": {
                "passed": True,
                "semantic_name": "wrist",
                "index": 7,
                "device_name": "Logitech HD Webcam C270",
            },
        },
    }


def settings_content():
    return {
        "focus": {"mode": "manual", "value": 37},
        "exposure": {"mode": "locked", "value": -6},
        "white_balance": {"mode": "manual", "value": 4100},
        "power_line_frequency": 50,
        "controller": "Logi Tune",
        "version": "test-version",
        "notes": "Operator-recorded values; not camera-verified.",
    }


def settings_snapshot():
    content = settings_content()
    raw = json.dumps(content, sort_keys=True).encode()
    return OperatorSettingsSnapshot(content, hashlib.sha256(raw).hexdigest())


class FakeBackend:
    def __init__(self, *, width=640, height=480, data=PNG_SIGNATURE + b"png-payload"):
        self.width = width
        self.height = height
        self.data = data
        self.calls = []

    def capture_png(self, camera, settings):
        self.calls.append((camera, settings))
        return CapturedPng(
            data=self.data,
            width=self.width,
            height=self.height,
            channels=3,
            camera_reported={"width": 640.0, "height": 480.0, "fps": 30.0},
        )


FIXED_TIME = datetime(2026, 7, 19, 3, 4, 5, tzinfo=UTC)


def capture(tmp_path, backend, **overrides):
    arguments = {
        "operator_settings": settings_snapshot(),
        "output_dir": tmp_path,
        "session_id": "S01",
        "lot_id": "LOT_A",
        "geometry_id": "G01",
        "backend": backend,
        "bean_id": "B001",
        "clock": lambda: FIXED_TIME,
    }
    arguments.update(overrides)
    return capture_perception(preflight(), **arguments)


def test_preflight_requires_passed_semantic_c920_top():
    identity = validate_preflight_top(preflight())
    assert (identity.role, identity.model, identity.index) == (
        "top",
        "Logitech HD Pro Webcam C920",
        3,
    )

    with pytest.raises(ValueError, match="did not pass"):
        validate_preflight_top(preflight(passed=False))
    with pytest.raises(ValueError, match="C270"):
        validate_preflight_top(preflight(top_model="Logitech HD Webcam C270"))
    with pytest.raises(ValueError, match="must be a C920"):
        validate_preflight_top(preflight(top_model="FaceTime HD Camera"))


def test_operator_settings_are_validated_and_hashed_from_exact_file_bytes(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings_content(), indent=2) + "\n", encoding="utf-8")
    snapshot = load_operator_settings(path)
    assert snapshot.content == settings_content()
    assert snapshot.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()

    invalid = settings_content()
    invalid["power_line_frequency"] = 60
    with pytest.raises(ValueError, match="50 Hz"):
        validate_operator_settings(invalid)

    placeholder = settings_content()
    placeholder["version"] = "REPLACE_WITH_EXACT_VERSION"
    with pytest.raises(ValueError, match="recorded exactly"):
        validate_operator_settings(placeholder)

    placeholder = settings_content()
    placeholder["focus"] = {"mode": "manual", "value": "TODO_MEASURE"}
    with pytest.raises(ValueError, match="placeholder"):
        validate_operator_settings(placeholder)


@pytest.mark.parametrize("field", ["focus", "white_balance"])
def test_operator_settings_require_locked_or_manual_values(field):
    invalid = settings_content()
    invalid[field] = {"mode": "auto", "value": 1}
    with pytest.raises(ValueError, match="manual.*locked"):
        validate_operator_settings(invalid)


def test_operator_settings_allow_honest_auto_exposure_only():
    # macOS AVFoundation force-reverts C920 exposure to auto on every open, so
    # exposure may be declared auto — but only with a null value (no fiction).
    auto = settings_content()
    auto["exposure"] = {"mode": "auto", "value": None}
    assert validate_operator_settings(auto) == auto

    fabricated = settings_content()
    fabricated["exposure"] = {"mode": "auto", "value": 200}
    with pytest.raises(ValueError, match="null"):
        validate_operator_settings(fabricated)


def test_canonical_capture_writes_lossless_png_and_manifest_aliases(tmp_path):
    backend = FakeBackend()
    result = capture(tmp_path, backend)

    assert result.image_path == tmp_path / "canonical" / "B001.png"
    assert result.metadata_path == tmp_path / "canonical" / "B001.json"
    assert result.image_path.read_bytes() == backend.data
    sidecar = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(backend.data).hexdigest()
    assert sidecar["canonical"] is True
    assert sidecar["capture_kind"] == "canonical_bean"
    assert sidecar["camera_role"] == "top"
    assert "C920" in sidecar["camera_model"]
    assert sidecar["camera_index"] == 3
    assert sidecar["session_id"] == "S01"
    assert sidecar["bean_id"] == "B001"
    assert sidecar["lot_id"] == "LOT_A"
    assert sidecar["geometry_id"] == "G01"
    assert sidecar["image_path"] == sidecar["path"] == "B001.png"
    assert result.metadata_path.parent / sidecar["image_path"] == result.image_path
    assert sidecar["image_sha256"] == sidecar["sha256"] == digest
    assert sidecar["preflight_sha256"] == preflight_sha256(preflight())
    assert sidecar["captured_at_utc"] == "2026-07-19T03:04:05Z"
    assert sidecar["capture_settings"]["requested"]["width"] == 640
    assert sidecar["capture_settings"]["requested"]["height"] == 480
    assert sidecar["capture_settings"]["requested"]["image_format"] == "PNG"
    assert sidecar["capture_settings"]["requested"]["lossless"] is True
    assert sidecar["operator_settings"]["provenance"] == "operator_recorded"
    assert sidecar["operator_settings"]["hardware_verified_by_capture"] is False
    assert sidecar["operator_settings"]["content"] == settings_content()

    camera, requested = backend.calls[0]
    assert camera.role == "top"
    assert camera.index == 3
    assert (requested.width, requested.height, requested.fps, requested.fourcc) == (
        640,
        480,
        30.0,
        "MJPG",
    )


def test_capture_refuses_overwrite_before_opening_camera(tmp_path):
    backend = FakeBackend()
    capture(tmp_path, backend)
    with pytest.raises(FileExistsError, match="overwrite"):
        capture(tmp_path, backend)
    assert len(backend.calls) == 1


def test_pair_commit_cleans_image_if_metadata_publish_fails(tmp_path, monkeypatch):
    backend = FakeBackend()
    real_link = perception_capture_module.os.link
    link_count = 0

    def fail_second_link(source, target):
        nonlocal link_count
        link_count += 1
        if link_count == 2:
            raise OSError("simulated metadata commit failure")
        return real_link(source, target)

    monkeypatch.setattr(perception_capture_module.os, "link", fail_second_link)
    with pytest.raises(OSError, match="metadata commit failure"):
        capture(tmp_path, backend)
    assert not (tmp_path / "canonical" / "B001.png").exists()
    assert not (tmp_path / "canonical" / "B001.json").exists()
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session_id", ""),
        ("lot_id", "  "),
        ("geometry_id", ""),
        ("bean_id", ""),
        ("bean_id", "../B001"),
    ],
)
def test_capture_rejects_empty_or_unsafe_identifiers_without_hardware(tmp_path, field, value):
    backend = FakeBackend()
    with pytest.raises(ValueError):
        capture(tmp_path, backend, **{field: value})
    assert backend.calls == []


def test_capture_rejects_non_640_by_480_or_non_png_frames_without_outputs(tmp_path):
    wrong_size = FakeBackend(width=1280, height=720)
    with pytest.raises(ValueError, match="require full 640x480"):
        capture(tmp_path, wrong_size)
    assert not (tmp_path / "canonical" / "B001.png").exists()

    not_png = FakeBackend(data=b"not-a-png")
    with pytest.raises(ValueError, match="PNG"):
        capture(tmp_path, not_png, bean_id="B002")
    assert not (tmp_path / "canonical" / "B002.png").exists()

    four_channels = FakeBackend()
    original_capture = four_channels.capture_png

    def capture_with_four_channels(camera, settings):
        frame = original_capture(camera, settings)
        return CapturedPng(
            data=frame.data,
            width=frame.width,
            height=frame.height,
            channels=4,
            camera_reported=frame.camera_reported,
        )

    four_channels.capture_png = capture_with_four_channels
    with pytest.raises(ValueError, match="exactly 3 channels"):
        capture(tmp_path, four_channels, bean_id="B003")
    assert not (tmp_path / "canonical" / "B003.png").exists()


def test_begin_and_end_neutral_references_are_distinct_and_noncanonical(tmp_path):
    backend = FakeBackend()
    begin = capture(
        tmp_path,
        backend,
        bean_id=None,
        reference_position="begin",
    )
    end = capture(
        tmp_path,
        backend,
        bean_id=None,
        reference_position="end",
    )
    assert begin.image_path.name == "S01__neutral_begin.png"
    assert end.image_path.name == "S01__neutral_end.png"
    assert begin.image_path != end.image_path
    for result, position in ((begin, "begin"), (end, "end")):
        sidecar = json.loads(result.metadata_path.read_text(encoding="utf-8"))
        assert sidecar["canonical"] is False
        assert sidecar["capture_kind"] == "neutral_reference"
        assert sidecar["reference_position"] == position
        assert sidecar["bean_id"] is None
        assert sidecar["image_path"] == result.image_path.name
        assert result.metadata_path.parent / sidecar["image_path"] == result.image_path
        assert sidecar["preflight_sha256"] == preflight_sha256(preflight())


def test_neutral_reference_rejects_a_bean_id(tmp_path):
    backend = FakeBackend()
    with pytest.raises(ValueError, match="must not have a bean_id"):
        capture(tmp_path, backend, reference_position="begin")
    assert backend.calls == []


def test_cli_uses_injected_camera_backend(tmp_path, capsys):
    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(json.dumps(preflight()), encoding="utf-8")
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings_content()), encoding="utf-8")
    output = tmp_path / "output"
    backend = FakeBackend()

    assert (
        main(
            [
                str(preflight_path),
                "--settings",
                str(settings_path),
                "--output",
                str(output),
                "--session-id",
                "S01",
                "--lot-id",
                "LOT_A",
                "--geometry-id",
                "G01",
                "--bean-id",
                "B001",
            ],
            backend=backend,
            clock=lambda: FIXED_TIME,
        )
        == 0
    )
    metadata_path = output / "canonical" / "B001.json"
    assert metadata_path.exists()
    assert str(metadata_path) in capsys.readouterr().out
    assert len(backend.calls) == 1
