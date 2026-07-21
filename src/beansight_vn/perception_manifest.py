from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import io
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

MANIFEST_COLUMNS = ("path", "label", "bean_id", "lot_id", "session_id", "split")
ALLOWED_LABELS = frozenset({"acceptable", "visible_reject"})
ALLOWED_DEFECTS = frozenset(
    {
        "black",
        "broken",
        "insect_damage",
        "dried_cherry",
        "shell_husk",
        "immature_faded",
        "moldy",
        "foreign_matter",
    }
)
ALLOWED_SPLITS = frozenset({"train", "val", "test"})
EXPECTED_IMAGE_SIZE = (640, 480)
EXPECTED_IMAGE_MODE = "RGB"
PERCEPTUAL_HASH_ALGORITHM = "phash-dct-64-v1"
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}")
C920_PATTERN = re.compile(r"(?<![A-Z0-9])C920(?![A-Z0-9])", re.IGNORECASE)


class ManifestValidationError(ValueError):
    """A validation failure whose message is safe to include in a public QA log."""


def resolve_capture_metadata_sources(
    sources: str | Path | Sequence[str | Path],
) -> list[Path]:
    """Expand metadata files, directories, and quoted glob patterns deterministically."""

    if isinstance(sources, (str, Path)):
        raw_sources: Sequence[str | Path] = (sources,)
    else:
        raw_sources = sources
    if not raw_sources:
        raise ManifestValidationError("at least one capture metadata source is required")

    discovered: set[Path] = set()
    for source in raw_sources:
        source_text = _required_text(
            str(source), field="source", context="capture metadata source list"
        )
        candidates: list[Path]
        if glob.has_magic(source_text):
            candidates = [Path(match) for match in glob.glob(source_text, recursive=True)]
            if not candidates:
                raise ManifestValidationError("a capture metadata glob matched no files")
        else:
            candidates = [Path(source_text)]

        for candidate in candidates:
            if candidate.is_dir():
                for suffix in ("*.json", "*.jsonl", "*.ndjson"):
                    discovered.update(path.resolve() for path in candidate.rglob(suffix))
            elif candidate.is_file():
                if candidate.suffix.lower() not in {".json", ".jsonl", ".ndjson"}:
                    raise ManifestValidationError(
                        "capture metadata sources must be JSON, JSONL, or NDJSON files"
                    )
                discovered.add(candidate.resolve())
            else:
                raise ManifestValidationError("a capture metadata source does not exist")

    if not discovered:
        raise ManifestValidationError("capture metadata sources contain no metadata files")
    return sorted(discovered, key=lambda path: path.as_posix())


@dataclass(frozen=True, slots=True)
class CaptureRecord:
    path: Path
    bean_id: str
    lot_id: str
    session_id: str
    image_sha256: str
    camera_role: str
    camera_model: str
    canonical: bool
    geometry_id: str
    operator_settings_sha256: str
    preflight_sha256: str


@dataclass(frozen=True, slots=True)
class NeutralReference:
    path: Path
    session_id: str
    image_sha256: str
    camera_role: str
    camera_model: str
    reference_position: str
    geometry_id: str
    operator_settings_sha256: str
    preflight_sha256: str


@dataclass(frozen=True, slots=True)
class BlindLabel:
    bean_id: str
    lot_id: str
    label: str
    visible_defect_type: str
    ambiguous: bool


@dataclass(frozen=True, slots=True)
class ManifestRow:
    path: Path
    label: str
    bean_id: str
    lot_id: str
    session_id: str
    split: str
    visible_defect_type: str
    image_sha256: str
    perceptual_hash: int


def _required_text(value: Any, *, field: str, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{context} has an empty or invalid {field}")
    return value.strip()


def _aliased_value(record: Mapping[str, Any], names: Sequence[str], *, context: str) -> Any:
    present = [(name, record[name]) for name in names if name in record]
    if not present:
        raise ManifestValidationError(f"{context} is missing {names[0]}")
    first = present[0][1]
    if any(value != first for _, value in present[1:]):
        raise ManifestValidationError(f"{context} has conflicting {names[0]} fields")
    return first


def _camera_value(record: Mapping[str, Any], field: str, *, context: str) -> Any:
    direct_name = f"camera_{field}"
    direct = record.get(direct_name)
    camera = record.get("camera")
    nested = camera.get(field) if isinstance(camera, Mapping) else None
    if direct is None and nested is None:
        raise ManifestValidationError(f"{context} is missing {direct_name}")
    if direct is not None and nested is not None and direct != nested:
        raise ManifestValidationError(f"{context} has conflicting {direct_name} fields")
    return direct if direct is not None else nested


def _required_sha256(value: Any, *, field: str, context: str) -> str:
    digest = _required_text(value, field=field, context=context)
    if SHA256_PATTERN.fullmatch(digest) is None:
        raise ManifestValidationError(f"{context} has an invalid {field}")
    return digest.lower()


def _capture_provenance(
    record: Mapping[str, Any], *, context: str
) -> tuple[str, str, str]:
    geometry_id = _required_text(record.get("geometry_id"), field="geometry_id", context=context)
    preflight_sha256 = _required_sha256(
        record.get("preflight_sha256"), field="preflight_sha256", context=context
    )
    operator_settings = record.get("operator_settings")
    if not isinstance(operator_settings, Mapping):
        raise ManifestValidationError(f"{context} has invalid operator_settings")
    if operator_settings.get("provenance") != "operator_recorded":
        raise ManifestValidationError(
            f"{context} operator_settings provenance must be operator_recorded"
        )
    if operator_settings.get("hardware_verified_by_capture") is not False:
        raise ManifestValidationError(
            f"{context} operator settings must record hardware_verified_by_capture=false"
        )
    settings_sha256 = _required_sha256(
        operator_settings.get("sha256"),
        field="operator_settings.sha256",
        context=context,
    )
    return geometry_id, settings_sha256, preflight_sha256


def _load_json_records(path: Path) -> list[Mapping[str, Any]]:
    try:
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            records: list[Any] = []
            with path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        raise ManifestValidationError(
                            f"capture metadata JSONL is invalid at line {line_number}"
                        ) from exc
            payload: Any = records
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
    except ManifestValidationError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError("capture metadata could not be read as JSON") from exc

    if isinstance(payload, Mapping):
        payload = payload.get("records", [payload])
    if not isinstance(payload, list) or not payload:
        raise ManifestValidationError("capture metadata must contain at least one record")
    if not all(isinstance(record, Mapping) for record in payload):
        raise ManifestValidationError("capture metadata records must be JSON objects")
    return list(payload)


def _read_capture_metadata(
    path: Path,
) -> tuple[list[CaptureRecord], list[NeutralReference]]:
    path = Path(path)
    records: list[CaptureRecord] = []
    neutral_references: list[NeutralReference] = []
    for index, raw in enumerate(_load_json_records(path), start=1):
        context = f"capture record {index}"
        canonical = _aliased_value(raw, ("canonical", "is_canonical"), context=context)
        if not isinstance(canonical, bool):
            raise ManifestValidationError(f"{context} canonical must be a JSON boolean")
        if "bean_id" not in raw:
            raise ManifestValidationError(f"{context} is missing bean_id")
        capture_kind = _required_text(
            raw.get("capture_kind"), field="capture_kind", context=context
        )
        _required_text(raw.get("lot_id"), field="lot_id", context=context)
        session_id = _required_text(raw.get("session_id"), field="session_id", context=context)
        geometry_id, settings_sha256, preflight_sha256 = _capture_provenance(
            raw, context=context
        )
        raw_path = _required_text(
            _aliased_value(raw, ("path", "image_path"), context=context),
            field="path",
            context=context,
        )
        digest = _required_sha256(
            _aliased_value(raw, ("image_sha256", "sha256"), context=context),
            field="image_sha256", context=context
        )
        camera_role = _required_text(
            _camera_value(raw, "role", context=context), field="camera_role", context=context
        )
        camera_model = _required_text(
            _camera_value(raw, "model", context=context), field="camera_model", context=context
        )
        image_path = Path(raw_path)
        if not image_path.is_absolute():
            image_path = path.parent / image_path
        image_path = image_path.resolve()

        if "reference_position" not in raw:
            raise ManifestValidationError(f"{context} is missing reference_position")
        position = raw["reference_position"]
        if raw["bean_id"] is None:
            if canonical:
                raise ManifestValidationError(f"{context} has no bean_id for a canonical capture")
            if capture_kind != "neutral_reference":
                raise ManifestValidationError(
                    f"{context} with no bean_id must be a neutral_reference"
                )
            if position not in {"begin", "end"}:
                raise ManifestValidationError(
                    f"{context} neutral reference must have begin or end position"
                )
            neutral_references.append(
                NeutralReference(
                    path=image_path,
                    session_id=session_id,
                    image_sha256=digest,
                    camera_role=camera_role,
                    camera_model=camera_model,
                    reference_position=position,
                    geometry_id=geometry_id,
                    operator_settings_sha256=settings_sha256,
                    preflight_sha256=preflight_sha256,
                )
            )
            continue

        bean_id = _required_text(raw["bean_id"], field="bean_id", context=context)
        if not canonical:
            raise ManifestValidationError(
                f"{context} is a noncanonical bean capture; "
                "only neutral records may be noncanonical"
            )
        if capture_kind != "canonical_bean":
            raise ManifestValidationError(f"{context} bean capture has invalid capture_kind")
        if position is not None:
            raise ManifestValidationError(f"{context} canonical bean has a neutral position")
        lot_id = _required_text(raw.get("lot_id"), field="lot_id", context=context)
        records.append(
            CaptureRecord(
                path=image_path,
                bean_id=bean_id,
                lot_id=lot_id,
                session_id=session_id,
                image_sha256=digest.lower(),
                camera_role=camera_role,
                camera_model=camera_model,
                canonical=canonical,
                geometry_id=geometry_id,
                operator_settings_sha256=settings_sha256,
                preflight_sha256=preflight_sha256,
            )
        )
    return records, neutral_references


def read_capture_metadata(path: Path) -> list[CaptureRecord]:
    """Read one metadata file and return its canonical bean captures."""

    records, _ = _read_capture_metadata(Path(path))
    return records


def _parse_ambiguous(value: Any, *, row_number: int) -> bool:
    if not isinstance(value, str):
        raise ManifestValidationError(f"blind-label row {row_number} has invalid ambiguous flag")
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ManifestValidationError(f"blind-label row {row_number} has invalid ambiguous flag")


def read_blind_labels(path: Path) -> list[BlindLabel]:
    path = Path(path)
    required = {"bean_id", "lot_id", "grader_label", "visible_defect_type", "ambiguous"}
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ManifestValidationError(
                    f"blind-label CSV is missing columns: {sorted(missing)}"
                )
            raw_rows = list(reader)
    except ManifestValidationError:
        raise
    except OSError as exc:
        raise ManifestValidationError("blind-label CSV could not be read") from exc
    if not raw_rows:
        raise ManifestValidationError("blind-label CSV contains no records")

    labels: list[BlindLabel] = []
    seen: set[str] = set()
    for row_number, raw in enumerate(raw_rows, start=2):
        context = f"blind-label row {row_number}"
        bean_id = _required_text(raw.get("bean_id"), field="bean_id", context=context)
        lot_id = _required_text(raw.get("lot_id"), field="lot_id", context=context)
        if bean_id in seen:
            raise ManifestValidationError(f"blind-label CSV repeats bean_id {bean_id}")
        seen.add(bean_id)
        ambiguous = _parse_ambiguous(raw.get("ambiguous"), row_number=row_number)
        label = str(raw.get("grader_label") or "").strip().lower()
        defect = str(raw.get("visible_defect_type") or "").strip().lower()
        if label and label not in ALLOWED_LABELS:
            raise ManifestValidationError(f"{context} has an unsupported grader_label")
        if defect and defect not in ALLOWED_DEFECTS:
            raise ManifestValidationError(f"{context} has an unsupported visible_defect_type")
        if not ambiguous:
            if not label:
                raise ManifestValidationError(f"{context} has no grader_label")
            if label == "acceptable" and defect:
                raise ManifestValidationError(
                    f"{context} gives an acceptable bean a visible defect"
                )
            if label == "visible_reject" and not defect:
                raise ManifestValidationError(
                    f"{context} gives a visible reject no supported defect type"
                )
        labels.append(
            BlindLabel(
                bean_id=bean_id,
                lot_id=lot_id,
                label=label,
                visible_defect_type=defect,
                ambiguous=ambiguous,
            )
        )
    return labels


def read_split_assignments(path: Path) -> dict[str, str]:
    path = Path(path)
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing = {"bean_id", "split"} - set(reader.fieldnames or [])
            if missing:
                raise ManifestValidationError(
                    f"split-assignment CSV is missing columns: {sorted(missing)}"
                )
            raw_rows = list(reader)
    except ManifestValidationError:
        raise
    except OSError as exc:
        raise ManifestValidationError("split-assignment CSV could not be read") from exc
    if not raw_rows:
        raise ManifestValidationError("split-assignment CSV contains no records")

    assignments: dict[str, str] = {}
    for row_number, raw in enumerate(raw_rows, start=2):
        context = f"split-assignment row {row_number}"
        bean_id = _required_text(raw.get("bean_id"), field="bean_id", context=context)
        split = _required_text(raw.get("split"), field="split", context=context).lower()
        if split not in ALLOWED_SPLITS:
            raise ManifestValidationError(f"{context} has an unsupported split")
        if bean_id in assignments:
            raise ManifestValidationError(f"split-assignment CSV repeats bean_id {bean_id}")
        assignments[bean_id] = split
    return assignments


def _normalize_split_map(split_map: Mapping[str, str]) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for bean_id_raw, split_raw in split_map.items():
        bean_id = _required_text(bean_id_raw, field="bean_id", context="explicit split map")
        split = _required_text(split_raw, field="split", context="explicit split map").lower()
        if split not in ALLOWED_SPLITS:
            raise ManifestValidationError("explicit split map contains an unsupported split")
        assignments[bean_id] = split
    if not assignments:
        raise ManifestValidationError("explicit split map contains no assignments")
    return assignments


def read_perception_roi(path: Path) -> tuple[int, int, int, int]:
    """Load the frozen ROI and image contract used by capture and pHash QA."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError("perception config could not be read as JSON") from exc
    if not isinstance(payload, Mapping):
        raise ManifestValidationError("perception config must be a JSON object")
    if payload.get("image_key") != "observation.images.top":
        raise ManifestValidationError("perception config image_key must select the top camera")
    if payload.get("color_order") != EXPECTED_IMAGE_MODE:
        raise ManifestValidationError("perception config color_order must be RGB")
    raw_roi = payload.get("roi")
    if not isinstance(raw_roi, Mapping):
        raise ManifestValidationError("perception config is missing a valid ROI")

    values: dict[str, int] = {}
    for field in ("x", "y", "width", "height"):
        value = raw_roi.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ManifestValidationError(f"perception config ROI {field} must be an integer")
        values[field] = value
    x, y, width, height = (
        values["x"],
        values["y"],
        values["width"],
        values["height"],
    )
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ManifestValidationError("perception config ROI has invalid bounds")
    if x + width > EXPECTED_IMAGE_SIZE[0] or y + height > EXPECTED_IMAGE_SIZE[1]:
        raise ManifestValidationError("perception config ROI exceeds the 640x480 image")
    return x, y, width, height


def _file_sha256(path: Path, *, context: str = "file") -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ManifestValidationError(f"{context} could not be read") from exc
    return digest.hexdigest()


def _validate_camera(camera_role: str, camera_model: str, *, subject: str) -> None:
    if camera_role.strip().lower() != "top":
        raise ManifestValidationError(f"{subject} was not captured by the top camera")
    if C920_PATTERN.search(camera_model) is None:
        raise ManifestValidationError(f"{subject} was not captured by a C920")


def _validate_image(
    path: Path,
    expected_sha256: str,
    *,
    subject: str,
    roi: tuple[int, int, int, int] | None,
) -> tuple[str, int | None]:
    if not path.is_file():
        raise ManifestValidationError(f"{subject} references a missing image")
    actual_sha256 = _file_sha256(path, context="an image file")
    if actual_sha256 != expected_sha256:
        raise ManifestValidationError(f"{subject} image SHA-256 does not match metadata")

    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:  # pragma: no cover - environment-specific dependency message
        raise RuntimeError("Pillow is required to validate perception images") from exc
    try:
        with Image.open(path) as image:
            image.load()
            if image.mode != EXPECTED_IMAGE_MODE:
                raise ManifestValidationError(f"{subject} image is not stored in RGB mode")
            if image.size != EXPECTED_IMAGE_SIZE:
                raise ManifestValidationError(f"{subject} image is not 640x480 pixels")
            perceptual_hash = _perceptual_hash(image, roi=roi) if roi is not None else None
    except ManifestValidationError:
        raise
    except (OSError, UnidentifiedImageError) as exc:
        raise ManifestValidationError(f"{subject} image cannot be decoded") from exc
    return actual_sha256, perceptual_hash


def _decode_and_hash(
    record: CaptureRecord, *, roi: tuple[int, int, int, int]
) -> tuple[str, int]:
    subject = f"bean {record.bean_id}"
    _validate_camera(record.camera_role, record.camera_model, subject=subject)
    actual_sha256, perceptual_hash = _validate_image(
        record.path, record.image_sha256, subject=subject, roi=roi
    )
    assert perceptual_hash is not None
    return actual_sha256, perceptual_hash


def _perceptual_hash(image: Any, *, roi: tuple[int, int, int, int]) -> int:
    from PIL import Image

    x, y, width, height = roi
    cropped = image.crop((x, y, x + width, y + height))
    pixels = np.asarray(
        cropped.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float64
    )
    coordinates = np.arange(32, dtype=np.float64)
    frequencies = np.arange(8, dtype=np.float64)[:, None]
    basis = np.cos((2 * coordinates + 1) * frequencies * math.pi / 64)
    basis[0] /= math.sqrt(2)
    low_frequency = basis @ pixels @ basis.T
    coefficients = low_frequency.ravel()
    threshold = float(np.median(coefficients[1:]))
    result = 0
    for coefficient in coefficients:
        result = (result << 1) | int(coefficient >= threshold)
    return result


def _select_canonical(records: Sequence[CaptureRecord]) -> dict[str, CaptureRecord]:
    grouped: dict[str, list[CaptureRecord]] = defaultdict(list)
    for record in records:
        grouped[record.bean_id].append(record)
    selected: dict[str, CaptureRecord] = {}
    for bean_id, bean_records in grouped.items():
        canonical = [record for record in bean_records if record.canonical]
        if len(canonical) != 1:
            raise ManifestValidationError(
                f"bean {bean_id} must have exactly one canonical capture; found {len(canonical)}"
            )
        selected[bean_id] = canonical[0]
    return selected


def _validate_session_capture_provenance(
    records: Sequence[CaptureRecord],
    references: Sequence[NeutralReference],
) -> None:
    bean_sessions = {record.session_id for record in records}
    reference_sessions = {reference.session_id for reference in references}
    missing_references = sorted(bean_sessions - reference_sessions)
    if missing_references:
        raise ManifestValidationError(
            f"capture sessions are missing neutral references: {missing_references[:10]}"
        )
    unknown_references = sorted(reference_sessions - bean_sessions)
    if unknown_references:
        raise ManifestValidationError(
            f"neutral references have no canonical bean session: {unknown_references[:10]}"
        )

    for session_id in sorted(bean_sessions):
        session_records = [record for record in records if record.session_id == session_id]
        session_references = [
            reference for reference in references if reference.session_id == session_id
        ]
        positions = Counter(reference.reference_position for reference in session_references)
        if positions != Counter({"begin": 1, "end": 1}):
            raise ManifestValidationError(
                f"session {session_id} must have exactly one begin and one end neutral reference"
            )

        combined = [*session_records, *session_references]
        provenance_fields = {
            "geometry_id": {item.geometry_id for item in combined},
            "operator_settings.sha256": {
                item.operator_settings_sha256 for item in combined
            },
            "preflight_sha256": {item.preflight_sha256 for item in combined},
        }
        for field, values in provenance_fields.items():
            if len(values) != 1:
                raise ManifestValidationError(f"session {session_id} has multiple {field} values")

        for reference in session_references:
            subject = f"session {session_id} {reference.reference_position} neutral reference"
            _validate_camera(reference.camera_role, reference.camera_model, subject=subject)
            _validate_image(
                reference.path,
                reference.image_sha256,
                subject=subject,
                roi=None,
            )


def _normalize_pilot_ids(pilot_bean_ids: Collection[str]) -> set[str]:
    normalized: set[str] = set()
    for bean_id_raw in pilot_bean_ids:
        normalized.add(_required_text(bean_id_raw, field="bean_id", context="pilot ID list"))
    return normalized


def read_pilot_ids_file(path: Path) -> set[str]:
    """Read pilot IDs from a one-ID-per-line file or a CSV with a bean_id column."""

    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ManifestValidationError("pilot ID file could not be read") from exc
    if not text.strip():
        raise ManifestValidationError("pilot ID file contains no bean IDs")

    lines = text.splitlines()
    first_row = next(csv.reader([lines[0]]), [])
    if "bean_id" in first_row:
        reader = csv.DictReader(io.StringIO(text))
        if "bean_id" not in (reader.fieldnames or []):  # pragma: no cover - guarded above
            raise ManifestValidationError("pilot ID CSV is missing bean_id")
        raw_ids = [row.get("bean_id") for row in reader]
    else:
        raw_ids = [line for line in lines if line.strip()]
    pilot_ids = _normalize_pilot_ids(raw_ids)
    if not pilot_ids:
        raise ManifestValidationError("pilot ID file contains no bean IDs")
    return pilot_ids


def _canonical_string_set_sha256(values: Collection[str]) -> str:
    encoded = json.dumps(sorted(values), separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _normalize_waiver_key(key: object) -> tuple[str, str]:
    if isinstance(key, str):
        parts = key.split("|")
    elif isinstance(key, tuple) and len(key) == 2:
        parts = list(key)
    else:
        raise ManifestValidationError("near-duplicate waiver keys must identify exactly two beans")
    if len(parts) != 2:
        raise ManifestValidationError("near-duplicate waiver keys must identify exactly two beans")
    first = _required_text(parts[0], field="bean_id", context="near-duplicate waiver")
    second = _required_text(parts[1], field="bean_id", context="near-duplicate waiver")
    if first == second:
        raise ManifestValidationError("near-duplicate waiver cannot name the same bean twice")
    return tuple(sorted((first, second)))


def _normalize_waivers(
    waivers: Mapping[tuple[str, str] | str, str] | None,
) -> dict[tuple[str, str], str]:
    normalized: dict[tuple[str, str], str] = {}
    for raw_key, raw_reason in (waivers or {}).items():
        key = _normalize_waiver_key(raw_key)
        reason = _required_text(
            raw_reason, field="reason", context=f"near-duplicate waiver {key[0]}|{key[1]}"
        )
        if key in normalized:
            raise ManifestValidationError("near-duplicate waiver pair is repeated")
        normalized[key] = reason
    return normalized


def _validate_split_invariants(rows: Sequence[ManifestRow]) -> None:
    if not rows:
        raise ManifestValidationError("no final images remain after exclusions")
    present_splits = {row.split for row in rows}
    missing_splits = ALLOWED_SPLITS - present_splits
    if missing_splits:
        raise ManifestValidationError(
            f"final manifest is missing splits: {sorted(missing_splits)}"
        )
    for split in ("train", "val", "test"):
        labels = {row.label for row in rows if row.split == split}
        missing_labels = ALLOWED_LABELS - labels
        if missing_labels:
            raise ManifestValidationError(
                f"{split} split is missing labels: {sorted(missing_labels)}"
            )
    for field in ("bean_id", "session_id"):
        split_by_value: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            split_by_value[getattr(row, field)].add(row.split)
        leaked = sorted(value for value, splits in split_by_value.items() if len(splits) > 1)
        if leaked:
            raise ManifestValidationError(f"{field} crosses splits: {leaked[:10]}")
    train_lots = {row.lot_id for row in rows if row.split == "train"}
    test_lots = {row.lot_id for row in rows if row.split == "test"}
    leaked_lots = sorted(train_lots & test_lots)
    if leaked_lots:
        raise ManifestValidationError(f"test lot appears in train: {leaked_lots[:10]}")


def _near_duplicate_warnings(
    rows: Sequence[ManifestRow],
    *,
    threshold: int,
    waivers: Mapping[tuple[str, str], str],
) -> list[dict[str, object]]:
    if not 0 <= threshold <= 64:
        raise ManifestValidationError("near-duplicate Hamming threshold must be between 0 and 64")
    warnings: list[dict[str, object]] = []
    used_waivers: set[tuple[str, str]] = set()
    for index, first in enumerate(rows):
        for second in rows[index + 1 :]:
            if first.split == second.split:
                continue
            distance = (first.perceptual_hash ^ second.perceptual_hash).bit_count()
            if distance > threshold:
                continue
            key = tuple(sorted((first.bean_id, second.bean_id)))
            reason = waivers.get(key)
            if reason is not None:
                used_waivers.add(key)
            warnings.append(
                {
                    "bean_id_a": key[0],
                    "bean_id_b": key[1],
                    "split_a": first.split if first.bean_id == key[0] else second.split,
                    "split_b": second.split if second.bean_id == key[1] else first.split,
                    "hamming_distance": distance,
                    "waived": reason is not None,
                    "waiver_reason": reason,
                }
            )
    unused = sorted(set(waivers) - used_waivers)
    if unused:
        preview = [f"{first}|{second}" for first, second in unused[:10]]
        raise ManifestValidationError(f"near-duplicate waivers did not match warnings: {preview}")
    unwaived = [warning for warning in warnings if not warning["waived"]]
    if unwaived:
        preview = [
            f"{warning['bean_id_a']}|{warning['bean_id_b']}" for warning in unwaived[:10]
        ]
        raise ManifestValidationError(
            "cross-split near-duplicate images require a documented waiver: " + ", ".join(preview)
        )
    return warnings


def _build_rows(
    capture_records: Sequence[CaptureRecord],
    neutral_references: Sequence[NeutralReference],
    blind_labels: Sequence[BlindLabel],
    assignments: Mapping[str, str],
    *,
    roi: tuple[int, int, int, int],
    pilot_bean_ids: Collection[str],
    near_duplicate_waivers: Mapping[tuple[str, str] | str, str] | None,
    near_duplicate_hamming_threshold: int,
) -> tuple[list[ManifestRow], dict[str, object]]:
    _validate_session_capture_provenance(capture_records, neutral_references)
    canonical = _select_canonical(capture_records)
    labels_by_bean = {label.bean_id: label for label in blind_labels}
    capture_ids = set(canonical)
    label_ids = set(labels_by_bean)
    if capture_ids != label_ids:
        missing_labels = sorted(capture_ids - label_ids)
        missing_captures = sorted(label_ids - capture_ids)
        raise ManifestValidationError(
            "capture/label join is not exact; "
            f"missing labels={missing_labels[:10]}, missing captures={missing_captures[:10]}"
        )
    unknown_assignments = sorted(set(assignments) - capture_ids)
    if unknown_assignments:
        raise ManifestValidationError(
            f"split assignments reference unknown beans: {unknown_assignments[:10]}"
        )

    pilots = _normalize_pilot_ids(pilot_bean_ids)
    # The pilot registry is authoritative even when the final collection is stored in a separate
    # directory. Any overlap is excluded; absent pilot IDs are still hashed into the QA evidence so
    # the final builder can prove which registry it checked without requiring pilot images/labels.
    present_pilots = pilots & capture_ids
    ambiguous = {label.bean_id for label in blind_labels if label.ambiguous}
    excluded = ambiguous | present_pilots
    included_ids = capture_ids - excluded
    missing_assignments = sorted(included_ids - set(assignments))
    if missing_assignments:
        raise ManifestValidationError(
            f"final beans have no explicit split assignment: {missing_assignments[:10]}"
        )

    rows: list[ManifestRow] = []
    path_owner: dict[Path, str] = {}
    hash_owner: dict[str, str] = {}
    for bean_id in sorted(included_ids):
        capture = canonical[bean_id]
        label = labels_by_bean[bean_id]
        if capture.lot_id != label.lot_id:
            raise ManifestValidationError(f"bean {bean_id} has conflicting lot_id values")
        actual_sha256, perceptual_hash = _decode_and_hash(capture, roi=roi)
        previous_path = path_owner.get(capture.path)
        if previous_path is not None:
            raise ManifestValidationError(
                f"beans {previous_path} and {bean_id} reference the same canonical path"
            )
        path_owner[capture.path] = bean_id
        previous_hash = hash_owner.get(actual_sha256)
        if previous_hash is not None:
            raise ManifestValidationError(
                f"beans {previous_hash} and {bean_id} have duplicate canonical image hashes"
            )
        hash_owner[actual_sha256] = bean_id
        rows.append(
            ManifestRow(
                path=capture.path,
                label=label.label,
                bean_id=bean_id,
                lot_id=capture.lot_id,
                session_id=capture.session_id,
                split=assignments[bean_id],
                visible_defect_type=label.visible_defect_type,
                image_sha256=actual_sha256,
                perceptual_hash=perceptual_hash,
            )
        )

    split_order = {"train": 0, "val": 1, "test": 2}
    rows.sort(key=lambda row: (split_order[row.split], row.bean_id))
    _validate_split_invariants(rows)
    waivers = _normalize_waivers(near_duplicate_waivers)
    warnings = _near_duplicate_warnings(
        rows, threshold=near_duplicate_hamming_threshold, waivers=waivers
    )
    details: dict[str, object] = {
        "canonical_count": len(canonical),
        "ambiguous_excluded_count": len(ambiguous),
        "pilot_registry_count": len(pilots),
        "pilot_excluded_count": len(present_pilots),
        "pilot_ids_sha256": _canonical_string_set_sha256(pilots),
        "total_excluded_count": len(excluded),
        "near_duplicate_warnings": warnings,
    }
    return rows, details


def _path_is_in_results(path: Path) -> bool:
    return any(part.lower() == "results" for part in path.resolve().parts)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            handle.write(text)
            temporary_name = handle.name
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _render_manifest(rows: Sequence[ManifestRow], output_path: Path) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        relative_path = Path(os.path.relpath(row.path, output_path.parent)).as_posix()
        writer.writerow(
            {
                "path": relative_path,
                "label": row.label,
                "bean_id": row.bean_id,
                "lot_id": row.lot_id,
                "session_id": row.session_id,
                "split": row.split,
            }
        )
    return stream.getvalue()


def _canonical_mapping_sha256(mapping: Mapping[str, str]) -> str:
    encoded = json.dumps(dict(sorted(mapping.items())), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _aggregate_files_sha256(paths: Sequence[Path]) -> str:
    digests = [_file_sha256(path, context="a capture metadata file") for path in paths]
    encoded = json.dumps(digests, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def build_perception_manifest(
    capture_metadata: str | Path | Sequence[str | Path],
    blind_labels_csv: Path,
    output_csv: Path,
    qa_summary_path: Path,
    *,
    config_path: Path,
    split_assignments_csv: Path | None = None,
    split_map: Mapping[str, str] | None = None,
    pilot_bean_ids: Collection[str] = (),
    near_duplicate_waivers: Mapping[tuple[str, str] | str, str] | None = None,
    near_duplicate_hamming_threshold: int = 4,
    overwrite: bool = False,
) -> dict[str, object]:
    """Build a leakage-gated six-column perception training manifest.

    Splits must be supplied explicitly through exactly one of ``split_assignments_csv`` or
    ``split_map``. The function writes no output until all joins, image checks, split invariants,
    and near-duplicate waivers have passed.
    """

    blind_labels_csv = Path(blind_labels_csv)
    output_csv = Path(output_csv)
    qa_summary_path = Path(qa_summary_path)
    config_path = Path(config_path)
    if split_assignments_csv is None and split_map is None:
        raise ManifestValidationError("an explicit split-assignment CSV or split map is required")
    if split_assignments_csv is not None and split_map is not None:
        raise ManifestValidationError("provide only one explicit split assignment source")
    if output_csv.resolve() == qa_summary_path.resolve():
        raise ManifestValidationError("manifest and QA summary must use different files")
    if not overwrite and (output_csv.exists() or qa_summary_path.exists()):
        raise ManifestValidationError(
            "refusing to overwrite an existing manifest or QA summary; use explicit overwrite"
        )
    if _path_is_in_results(qa_summary_path):
        raise ManifestValidationError("perception manifest QA summary must be outside results")

    capture_sources = resolve_capture_metadata_sources(capture_metadata)
    capture_records: list[CaptureRecord] = []
    neutral_references: list[NeutralReference] = []
    for source in capture_sources:
        source_records, source_references = _read_capture_metadata(source)
        capture_records.extend(source_records)
        neutral_references.extend(source_references)
    blind_labels = read_blind_labels(blind_labels_csv)
    roi = read_perception_roi(config_path)
    if split_assignments_csv is not None:
        split_assignments_csv = Path(split_assignments_csv)
        assignments = read_split_assignments(split_assignments_csv)
        split_source_sha256 = _file_sha256(
            split_assignments_csv, context="split-assignment CSV"
        )
        split_source_type = "csv"
    else:
        assert split_map is not None
        assignments = _normalize_split_map(split_map)
        split_source_sha256 = _canonical_mapping_sha256(assignments)
        split_source_type = "explicit_map"

    protected_inputs = {
        *(path.resolve() for path in capture_sources),
        blind_labels_csv.resolve(),
        config_path.resolve(),
    }
    if split_assignments_csv is not None:
        protected_inputs.add(split_assignments_csv.resolve())
    if output_csv.resolve() in protected_inputs or qa_summary_path.resolve() in protected_inputs:
        raise ManifestValidationError("output files must not replace an input artifact")

    rows, details = _build_rows(
        capture_records,
        neutral_references,
        blind_labels,
        assignments,
        roi=roi,
        pilot_bean_ids=pilot_bean_ids,
        near_duplicate_waivers=near_duplicate_waivers,
        near_duplicate_hamming_threshold=near_duplicate_hamming_threshold,
    )
    manifest_text = _render_manifest(rows, output_csv)
    manifest_sha256 = hashlib.sha256(manifest_text.encode()).hexdigest()
    warnings = details["near_duplicate_warnings"]
    assert isinstance(warnings, list)
    split_label_counts = Counter((row.split, row.label) for row in rows)
    label_counts = Counter(row.label for row in rows)
    defect_counts = Counter(row.visible_defect_type for row in rows if row.visible_defect_type)
    bean_count = len({row.bean_id for row in rows})
    lot_count = len({row.lot_id for row in rows})
    readiness_checks = {
        "bean_count_in_300_to_500_range": 300 <= bean_count <= 500,
        "visible_reject_count_at_least_50": label_counts["visible_reject"] >= 50,
        "lot_count_at_least_2": lot_count >= 2,
    }
    summary: dict[str, object] = {
        "schema_version": "1.0",
        "status": "passed_with_waivers" if warnings else "passed",
        "manifest_filename": output_csv.name,
        "manifest_sha256": manifest_sha256,
        "source_sha256": {
            "capture_metadata": _aggregate_files_sha256(capture_sources),
            "blind_labels": _file_sha256(blind_labels_csv, context="blind-label CSV"),
            "perception_config": _file_sha256(config_path, context="perception config"),
            "split_assignments": split_source_sha256,
        },
        "split_assignment_source": split_source_type,
        "counts": {
            "capture_records": len(capture_records),
            "capture_metadata_files": len(capture_sources),
            "neutral_reference_records": len(neutral_references),
            "canonical_images": details["canonical_count"],
            "blind_label_records": len(blind_labels),
            "final_manifest_rows": len(rows),
            "ambiguous_excluded": details["ambiguous_excluded_count"],
            "pilot_excluded": details["pilot_excluded_count"],
            "total_excluded": details["total_excluded_count"],
        },
        "pilot_exclusions": {
            "count": details["pilot_registry_count"],
            "capture_overlap_excluded": details["pilot_excluded_count"],
            "final_manifest_overlap": 0,
            "ids_sha256": details["pilot_ids_sha256"],
        },
        "rows_by_split_and_label": {
            split: {label: split_label_counts[(split, label)] for label in sorted(ALLOWED_LABELS)}
            for split in ("train", "val", "test")
        },
        "visible_defects": {defect: defect_counts[defect] for defect in sorted(defect_counts)},
        "final_target_readiness": {
            "actual": {
                "bean_count": bean_count,
                "label_counts": {
                    label: label_counts[label] for label in sorted(ALLOWED_LABELS)
                },
                "lot_count": lot_count,
            },
            "checks": readiness_checks,
            "ready": all(readiness_checks.values()),
        },
        "checks": {
            "canonical_images_per_bean": 1,
            "camera_role": "top",
            "camera_model": "C920",
            "image_mode": EXPECTED_IMAGE_MODE,
            "image_width": EXPECTED_IMAGE_SIZE[0],
            "image_height": EXPECTED_IMAGE_SIZE[1],
            "perceptual_hash_roi": {
                "x": roi[0],
                "y": roi[1],
                "width": roi[2],
                "height": roi[3],
            },
            "duplicate_paths": 0,
            "duplicate_sha256": 0,
            "bean_split_isolation": True,
            "session_split_isolation": True,
            "test_lot_absent_from_train": True,
            "session_capture_provenance_isolated": True,
            "neutral_reference_pair_per_session": True,
        },
        "near_duplicate_check": {
            "algorithm": PERCEPTUAL_HASH_ALGORITHM,
            "hamming_threshold": near_duplicate_hamming_threshold,
            "warning_count": len(warnings),
            "waived_warning_count": len(warnings),
            "warnings": warnings,
        },
    }
    qa_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(output_csv, manifest_text)
    _atomic_write_text(qa_summary_path, qa_text)
    return summary


def _read_json_mapping(path: Path, *, context: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"{context} could not be read as JSON") from exc
    if not isinstance(payload, Mapping):
        raise ManifestValidationError(f"{context} must be a JSON object")
    return payload


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="beansight-build-perception-manifest",
        description="Build and QA a leakage-safe BeanSight perception manifest.",
    )
    parser.add_argument(
        "capture_metadata",
        nargs="+",
        help="Capture metadata file(s), directories, or quoted glob pattern(s).",
    )
    parser.add_argument("blind_labels_csv", type=Path)
    split_group = parser.add_mutually_exclusive_group(required=True)
    split_group.add_argument("--split-assignments", type=Path)
    split_group.add_argument("--split-map-json", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qa-summary", type=Path, required=True)
    parser.add_argument("--exclude-pilot-id", action="append", default=[])
    parser.add_argument("--exclude-pilot-ids-file", type=Path)
    parser.add_argument("--near-duplicate-waivers", type=Path)
    parser.add_argument("--near-duplicate-hamming-threshold", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _argument_parser()
    args = parser.parse_args(argv)
    try:
        split_map: Mapping[str, str] | None = None
        if args.split_map_json is not None:
            split_payload = _read_json_mapping(args.split_map_json, context="split-map JSON")
            split_map = dict(split_payload)

        waivers: Mapping[str, str] | None = None
        if args.near_duplicate_waivers is not None:
            waiver_payload = _read_json_mapping(
                args.near_duplicate_waivers, context="near-duplicate waiver JSON"
            )
            waivers = dict(waiver_payload)

        pilot_ids = _normalize_pilot_ids(args.exclude_pilot_id)
        if args.exclude_pilot_ids_file is not None:
            pilot_ids.update(read_pilot_ids_file(args.exclude_pilot_ids_file))

        summary = build_perception_manifest(
            args.capture_metadata,
            args.blind_labels_csv,
            args.output,
            args.qa_summary,
            config_path=args.config,
            split_assignments_csv=args.split_assignments,
            split_map=split_map,
            pilot_bean_ids=pilot_ids,
            near_duplicate_waivers=waivers,
            near_duplicate_hamming_threshold=args.near_duplicate_hamming_threshold,
            overwrite=args.overwrite,
        )
    except ManifestValidationError as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "status": summary["status"],
                "manifest": args.output.name,
                "qa_summary": args.qa_summary.name,
                "rows": summary["counts"]["final_manifest_rows"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the console entry point
    raise SystemExit(main())
