import csv
import hashlib
import json

import numpy as np
import pytest

from beansight_vn.perception_manifest import (
    MANIFEST_COLUMNS,
    ManifestValidationError,
    build_perception_manifest,
    main,
    read_pilot_ids_file,
    resolve_capture_metadata_sources,
)

Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _token(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _write_pattern(path, seed):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (640, 480), (20 + seed % 40, 30, 40))
    draw = ImageDraw.Draw(image)
    rng = np.random.default_rng(seed)
    for grid_y in range(16):
        for grid_x in range(16):
            color = tuple(int(value) for value in rng.integers(0, 256, size=3))
            left = 160 + grid_x * 20
            top = 80 + grid_y * 20
            draw.rectangle((left, top, left + 19, top + 19), fill=color)
    draw.rectangle((10, 10, 120, 60), fill=(seed * 17 % 256, seed * 29 % 256, 100))
    image.save(path)


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sidecar_record(
    image_path,
    *,
    bean_id,
    lot_id,
    session_id,
    reference_position=None,
):
    canonical = bean_id is not None
    return {
        "schema_version": "1.0",
        "capture_kind": "canonical_bean" if canonical else "neutral_reference",
        "canonical": canonical,
        "reference_position": reference_position,
        "bean_id": bean_id,
        "lot_id": lot_id,
        "session_id": session_id,
        "geometry_id": f"G_{session_id}",
        "preflight_sha256": _token(f"preflight-{session_id}"),
        "operator_settings": {
            "sha256": _token(f"settings-{session_id}"),
            "provenance": "operator_recorded",
            "hardware_verified_by_capture": False,
        },
        "camera_role": "top",
        "camera_model": "Logitech HD Pro Webcam C920",
        "camera": {"role": "top", "model": "Logitech HD Pro Webcam C920"},
        "path": image_path.name,
        "image_path": image_path.name,
        "image_sha256": _sha256(image_path),
        "sha256": _sha256(image_path),
    }


def _write_sidecar(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _make_dataset(tmp_path):
    capture_dir = tmp_path / "capture"
    canonical_dir = capture_dir / "canonical"
    reference_dir = capture_dir / "references"
    specs = [
        ("T_A", "LOT_TRAIN", "S_TRAIN", "acceptable", "", False, "train"),
        ("T_R", "LOT_TRAIN", "S_TRAIN", "visible_reject", "insect_damage", False, "train"),
        ("P_A", "LOT_TRAIN", "S_TRAIN", "acceptable", "", False, "train"),
        ("V_A", "LOT_VAL", "S_VAL", "acceptable", "", False, "val"),
        ("V_R", "LOT_VAL", "S_VAL", "visible_reject", "broken", False, "val"),
        ("X_A", "LOT_TEST", "S_TEST", "acceptable", "", False, "test"),
        (
            "X_R",
            "LOT_TEST",
            "S_TEST",
            "visible_reject",
            "foreign_matter",
            False,
            "test",
        ),
        ("A_01", "LOT_VAL", "S_VAL", "", "", True, None),
    ]
    sidecars = {}
    images = {}
    label_rows = []
    split_rows = []
    for seed, (bean_id, lot_id, session_id, label, defect, ambiguous, split) in enumerate(
        specs, start=1
    ):
        image_path = canonical_dir / f"{bean_id}.png"
        _write_pattern(image_path, seed)
        sidecar_path = canonical_dir / f"{bean_id}.json"
        _write_sidecar(
            sidecar_path,
            _sidecar_record(
                image_path,
                bean_id=bean_id,
                lot_id=lot_id,
                session_id=session_id,
            ),
        )
        sidecars[bean_id] = sidecar_path
        images[bean_id] = image_path
        label_rows.append(
            {
                "bean_id": bean_id,
                "lot_id": lot_id,
                "grader_label": label,
                "visible_defect_type": defect,
                "ambiguous": str(ambiguous).lower(),
            }
        )
        if split is not None:
            split_rows.append({"bean_id": bean_id, "split": split})

    for seed, (session_id, lot_id) in enumerate(
        (("S_TRAIN", "LOT_TRAIN"), ("S_VAL", "LOT_VAL"), ("S_TEST", "LOT_TEST")),
        start=101,
    ):
        for offset, position in enumerate(("begin", "end")):
            image_path = reference_dir / f"{session_id}__neutral_{position}.png"
            _write_pattern(image_path, seed + offset)
            _write_sidecar(
                reference_dir / f"{session_id}__neutral_{position}.json",
                _sidecar_record(
                    image_path,
                    bean_id=None,
                    lot_id=lot_id,
                    session_id=session_id,
                    reference_position=position,
                ),
            )

    labels_path = tmp_path / "blind_labels.csv"
    splits_path = tmp_path / "splits.csv"
    config_path = tmp_path / "perception.json"
    _write_csv(
        labels_path,
        ("bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"),
        label_rows,
    )
    _write_csv(splits_path, ("bean_id", "split"), split_rows)
    config_path.write_text(
        json.dumps(
            {
                "image_key": "observation.images.top",
                "color_order": "RGB",
                "roi": {"x": 160, "y": 80, "width": 320, "height": 320},
            }
        ),
        encoding="utf-8",
    )
    return {
        "capture_dir": capture_dir,
        "sidecars": sidecars,
        "images": images,
        "labels": labels_path,
        "label_rows": label_rows,
        "splits": splits_path,
        "split_map": {row["bean_id"]: row["split"] for row in split_rows},
        "config": config_path,
        "output": tmp_path / "generated" / "manifest.csv",
        "qa": tmp_path / "qa" / "perception_manifest_qa.json",
    }


def _build(data, **overrides):
    arguments = {
        "config_path": data["config"],
        "split_map": data["split_map"],
    }
    arguments.update(overrides)
    return build_perception_manifest(
        data["capture_dir"],
        data["labels"],
        data["output"],
        data["qa"],
        **arguments,
    )


def _update_sidecar(data, bean_id, **updates):
    path = data["sidecars"][bean_id]
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(updates)
    _write_sidecar(path, record)


def test_builds_exact_manifest_from_capture_directory_and_split_csv(tmp_path):
    data = _make_dataset(tmp_path)
    summary = _build(data, split_map=None, split_assignments_csv=data["splits"])

    with data["output"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert tuple(reader.fieldnames) == MANIFEST_COLUMNS
    assert [row["bean_id"] for row in rows] == [
        "P_A",
        "T_A",
        "T_R",
        "V_A",
        "V_R",
        "X_A",
        "X_R",
    ]
    assert summary["status"] == "passed"
    assert summary["counts"]["ambiguous_excluded"] == 1
    assert summary["counts"]["neutral_reference_records"] == 6
    assert summary["checks"]["neutral_reference_pair_per_session"] is True
    assert summary["final_target_readiness"]["ready"] is False
    assert json.loads(data["qa"].read_text(encoding="utf-8")) == summary


def test_pilot_file_excludes_ids_and_records_only_count_and_hash(tmp_path):
    data = _make_dataset(tmp_path)
    pilot_file = tmp_path / "pilot_ids.csv"
    pilot_file.write_text("bean_id\nP_A\n", encoding="utf-8")

    summary = _build(data, pilot_bean_ids=read_pilot_ids_file(pilot_file))
    manifest_text = data["output"].read_text(encoding="utf-8")
    assert "P_A" not in manifest_text
    assert summary["pilot_exclusions"]["count"] == 1
    assert summary["pilot_exclusions"]["capture_overlap_excluded"] == 1
    assert summary["pilot_exclusions"]["final_manifest_overlap"] == 0
    assert summary["pilot_exclusions"]["ids_sha256"] == _token('["P_A"]')
    assert "P_A" not in json.dumps(summary)


def test_final_only_capture_can_verify_separate_pilot_registry(tmp_path):
    data = _make_dataset(tmp_path)

    summary = _build(data, pilot_bean_ids={"PILOT_B001", "PILOT_B002"})

    assert summary["pilot_exclusions"]["count"] == 2
    assert summary["pilot_exclusions"]["capture_overlap_excluded"] == 0
    assert summary["pilot_exclusions"]["final_manifest_overlap"] == 0
    assert "PILOT_B001" not in json.dumps(summary)


def test_cli_accepts_pilot_ids_file_and_explicit_split_map(tmp_path, capsys):
    data = _make_dataset(tmp_path)
    split_map_path = tmp_path / "split_map.json"
    split_map_path.write_text(json.dumps(data["split_map"]), encoding="utf-8")
    pilot_file = tmp_path / "pilot_ids.txt"
    pilot_file.write_text("P_A\n", encoding="utf-8")

    result = main(
        [
            str(data["capture_dir"]),
            str(data["labels"]),
            "--split-map-json",
            str(split_map_path),
            "--config",
            str(data["config"]),
            "--output",
            str(data["output"]),
            "--qa-summary",
            str(data["qa"]),
            "--exclude-pilot-ids-file",
            str(pilot_file),
        ]
    )

    assert result == 0
    assert json.loads(capsys.readouterr().out)["rows"] == 6


def test_capture_source_resolution_accepts_directory_glob_and_deduplicates(tmp_path):
    data = _make_dataset(tmp_path)
    pattern = str(data["capture_dir"] / "**" / "*.json")
    resolved = resolve_capture_metadata_sources(
        [data["capture_dir"], pattern, data["sidecars"]["T_A"]]
    )
    assert resolved == sorted(set(resolved), key=lambda path: path.as_posix())
    assert len(resolved) == 14


def test_rejects_noncanonical_bean_and_duplicate_canonical_capture(tmp_path):
    data = _make_dataset(tmp_path)
    _update_sidecar(data, "T_A", canonical=False)
    with pytest.raises(ManifestValidationError, match="noncanonical bean"):
        _build(data)

    data = _make_dataset(tmp_path / "duplicate")
    duplicate = json.loads(data["sidecars"]["T_A"].read_text(encoding="utf-8"))
    _write_sidecar(data["capture_dir"] / "canonical" / "T_A_copy.json", duplicate)
    with pytest.raises(ManifestValidationError, match="exactly one canonical"):
        _build(data)


def test_neutral_reference_requires_kind_and_exact_begin_end_pair(tmp_path):
    data = _make_dataset(tmp_path)
    reference = data["capture_dir"] / "references" / "S_TRAIN__neutral_begin.json"
    record = json.loads(reference.read_text(encoding="utf-8"))
    record["capture_kind"] = "unknown"
    _write_sidecar(reference, record)
    with pytest.raises(ManifestValidationError, match="neutral_reference"):
        _build(data)

    data = _make_dataset(tmp_path / "missing_end")
    end_sidecar = data["capture_dir"] / "references" / "S_TEST__neutral_end.json"
    end_sidecar.rename(end_sidecar.with_suffix(".ignored"))
    with pytest.raises(ManifestValidationError, match="exactly one begin and one end"):
        _build(data)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"geometry_id": ""}, "geometry_id"),
        ({"preflight_sha256": "bad"}, "preflight_sha256"),
        (
            {
                "operator_settings": {
                    "sha256": _token("settings-S_TRAIN"),
                    "provenance": "guessed",
                    "hardware_verified_by_capture": False,
                }
            },
            "operator_recorded",
        ),
        (
            {
                "operator_settings": {
                    "sha256": _token("settings-S_TRAIN"),
                    "provenance": "operator_recorded",
                    "hardware_verified_by_capture": True,
                }
            },
            "hardware_verified_by_capture=false",
        ),
        (
            {
                "camera_role": "wrist",
                "camera": {
                    "role": "wrist",
                    "model": "Logitech HD Pro Webcam C920",
                },
            },
            "top",
        ),
        (
            {
                "camera_model": "Logitech C270",
                "camera": {"role": "top", "model": "Logitech C270"},
            },
            "C920",
        ),
    ],
)
def test_rejects_invalid_capture_identity_or_provenance(tmp_path, updates, message):
    data = _make_dataset(tmp_path)
    _update_sidecar(data, "T_A", **updates)
    with pytest.raises(ManifestValidationError, match=message):
        _build(data)


def test_rejects_session_provenance_drift(tmp_path):
    data = _make_dataset(tmp_path)
    _update_sidecar(data, "T_R", geometry_id="G_MOVED")
    with pytest.raises(ManifestValidationError, match="multiple geometry_id"):
        _build(data)


@pytest.mark.parametrize("failure", ["missing", "sha256", "mode", "size", "decode"])
def test_rejects_missing_corrupt_or_noncontract_images(tmp_path, failure):
    data = _make_dataset(tmp_path)
    image_path = data["images"]["T_A"]
    if failure == "missing":
        image_path.rename(image_path.with_suffix(".missing"))
    elif failure == "sha256":
        _update_sidecar(data, "T_A", image_sha256="0" * 64, sha256="0" * 64)
    elif failure == "mode":
        Image.new("L", (640, 480), 120).save(image_path)
        digest = _sha256(image_path)
        _update_sidecar(data, "T_A", image_sha256=digest, sha256=digest)
    elif failure == "size":
        Image.new("RGB", (320, 240), (1, 2, 3)).save(image_path)
        digest = _sha256(image_path)
        _update_sidecar(data, "T_A", image_sha256=digest, sha256=digest)
    else:
        image_path.write_bytes(b"not an image")
        digest = _sha256(image_path)
        _update_sidecar(data, "T_A", image_sha256=digest, sha256=digest)

    with pytest.raises(ManifestValidationError):
        _build(data)


def test_rejects_duplicate_canonical_path_and_hash(tmp_path):
    data = _make_dataset(tmp_path)
    t_record = json.loads(data["sidecars"]["T_A"].read_text(encoding="utf-8"))
    x_record = json.loads(data["sidecars"]["X_A"].read_text(encoding="utf-8"))
    x_record["path"] = x_record["image_path"] = str(data["images"]["T_A"])
    x_record["image_sha256"] = x_record["sha256"] = t_record["sha256"]
    _write_sidecar(data["sidecars"]["X_A"], x_record)
    with pytest.raises(ManifestValidationError, match="same canonical path"):
        _build(data)

    data = _make_dataset(tmp_path / "hash")
    data["images"]["X_A"].write_bytes(data["images"]["T_A"].read_bytes())
    duplicate_hash = _sha256(data["images"]["X_A"])
    _update_sidecar(data, "X_A", image_sha256=duplicate_hash, sha256=duplicate_hash)
    with pytest.raises(ManifestValidationError, match="duplicate canonical image hashes"):
        _build(data)


def test_rejects_missing_split_label_session_leak_and_test_lot_leak(tmp_path):
    data = _make_dataset(tmp_path)
    rows = data["label_rows"]
    for row in rows:
        if row["bean_id"] == "V_R":
            row["grader_label"] = "acceptable"
            row["visible_defect_type"] = ""
    _write_csv(
        data["labels"],
        ("bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"),
        rows,
    )
    with pytest.raises(ManifestValidationError, match="val split is missing labels"):
        _build(data)

    data = _make_dataset(tmp_path / "session")
    _update_sidecar(
        data,
        "V_A",
        session_id="S_TRAIN",
        geometry_id="G_S_TRAIN",
        preflight_sha256=_token("preflight-S_TRAIN"),
        operator_settings={
            "sha256": _token("settings-S_TRAIN"),
            "provenance": "operator_recorded",
            "hardware_verified_by_capture": False,
        },
    )
    with pytest.raises(ManifestValidationError, match="session_id crosses splits"):
        _build(data)

    data = _make_dataset(tmp_path / "lot")
    for bean_id in ("X_A", "X_R"):
        _update_sidecar(data, bean_id, lot_id="LOT_TRAIN")
        for row in data["label_rows"]:
            if row["bean_id"] == bean_id:
                row["lot_id"] = "LOT_TRAIN"
    _write_csv(
        data["labels"],
        ("bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"),
        data["label_rows"],
    )
    with pytest.raises(ManifestValidationError, match="test lot appears in train"):
        _build(data)


def test_roi_near_duplicate_fails_until_documented_pair_waiver(tmp_path):
    data = _make_dataset(tmp_path)
    with Image.open(data["images"]["T_A"]) as train_image:
        roi = train_image.crop((160, 80, 480, 400))
    with Image.open(data["images"]["X_A"]) as test_image:
        changed = test_image.copy()
    changed.paste(roi, (160, 80))
    changed.putpixel((0, 0), (255, 0, 255))
    changed.save(data["images"]["X_A"])
    digest = _sha256(data["images"]["X_A"])
    _update_sidecar(data, "X_A", image_sha256=digest, sha256=digest)

    with pytest.raises(ManifestValidationError, match="documented waiver.*T_A.*X_A"):
        _build(data)
    summary = _build(
        data,
        near_duplicate_waivers={"T_A|X_A": "Same bean-like ROI retained for QA fixture."},
    )
    assert summary["status"] == "passed_with_waivers"
    warning = summary["near_duplicate_check"]["warnings"][0]
    assert warning["hamming_distance"] == 0
    assert warning["waiver_reason"]


def test_refuses_results_qa_and_existing_outputs_without_explicit_overwrite(tmp_path):
    data = _make_dataset(tmp_path)
    _build(data)
    with pytest.raises(ManifestValidationError, match="overwrite"):
        _build(data)
    _build(data, overwrite=True)

    data = _make_dataset(tmp_path / "results_case")
    data["qa"] = tmp_path / "results" / "qa.json"
    with pytest.raises(ManifestValidationError, match="outside results"):
        _build(data)
    assert not data["output"].exists()


def test_label_contract_rejects_unsupported_and_incomplete_rows(tmp_path):
    data = _make_dataset(tmp_path)
    for row in data["label_rows"]:
        if row["bean_id"] == "T_R":
            row["visible_defect_type"] = "mold"
    _write_csv(
        data["labels"],
        ("bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"),
        data["label_rows"],
    )
    with pytest.raises(ManifestValidationError, match="unsupported visible_defect_type"):
        _build(data)

    data = _make_dataset(tmp_path / "empty")
    data["label_rows"][0]["bean_id"] = ""
    _write_csv(
        data["labels"],
        ("bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"),
        data["label_rows"],
    )
    with pytest.raises(ManifestValidationError, match="empty or invalid bean_id"):
        _build(data)
