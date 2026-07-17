from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .material_sorting import EvidenceMethod, Resin
from .metrics import rate_summary

WAVELENGTHS_NM = (855, 940, 1050, 1200, 1300, 1450, 1550, 1650)
IDENTITY_COLUMNS = {
    "scan_id",
    "item_id",
    "parent_sku",
    "session_id",
    "resin",
    "evidence_method",
    "reference_id",
    "sensor_revision",
}


def spectral_columns(wavelengths_nm: Sequence[int] = WAVELENGTHS_NM) -> set[str]:
    return {
        f"{kind}_{wavelength}"
        for kind in ("raw", "dark", "white")
        for wavelength in wavelengths_nm
    }


@dataclass(frozen=True, slots=True)
class SpectralScan:
    scan_id: str
    item_id: str
    parent_sku: str
    session_id: str
    resin: Resin
    evidence_method: EvidenceMethod
    reference_id: str
    raw: np.ndarray
    dark: np.ndarray
    white: np.ndarray
    wavelengths_nm: tuple[int, ...] = WAVELENGTHS_NM
    sensor_revision: str = "unversioned"

    def __post_init__(self) -> None:
        object.__setattr__(self, "resin", Resin(self.resin))
        object.__setattr__(self, "evidence_method", EvidenceMethod(self.evidence_method))
        object.__setattr__(self, "wavelengths_nm", tuple(self.wavelengths_nm))
        for name in ("scan_id", "item_id", "parent_sku", "session_id", "reference_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not self.sensor_revision.strip():
            raise ValueError("sensor_revision must be non-empty")
        if self.resin is not Resin.UNKNOWN and self.evidence_method is EvidenceMethod.UNVERIFIED:
            raise ValueError("target-resin ground truth cannot use unverified evidence")
        expected_shape = (len(self.wavelengths_nm),)
        for name in ("raw", "dark", "white"):
            array = np.asarray(getattr(self, name), dtype=float)
            if array.shape != expected_shape:
                raise ValueError(f"{name} has shape {array.shape}; expected {expected_shape}")
            if not np.isfinite(array).all():
                raise ValueError(f"{name} contains NaN or Inf")
            object.__setattr__(self, name, array)
        if np.any(self.white <= self.dark):
            raise ValueError("every white reference channel must exceed its dark reference")

    def normalized_reflectance(self) -> np.ndarray:
        reflectance = (self.raw - self.dark) / (self.white - self.dark)
        if not np.isfinite(reflectance).all():
            raise ValueError(f"scan {self.scan_id} produced non-finite reflectance")
        return reflectance

    def processed(self) -> np.ndarray:
        reflectance = self.normalized_reflectance()
        standard_deviation = float(np.std(reflectance))
        if standard_deviation <= 1e-12:
            raise ValueError(f"scan {self.scan_id} has no spectral variation after referencing")
        return (reflectance - float(np.mean(reflectance))) / standard_deviation


@dataclass(frozen=True, slots=True)
class ItemSpectrum:
    item_id: str
    parent_sku: str
    resin: Resin
    evidence_method: EvidenceMethod
    sessions: tuple[str, ...]
    scan_count: int
    features: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "resin", Resin(self.resin))
        object.__setattr__(self, "evidence_method", EvidenceMethod(self.evidence_method))
        object.__setattr__(self, "sessions", tuple(self.sessions))
        if not self.item_id.strip() or not self.parent_sku.strip():
            raise ValueError("item_id and parent_sku must be non-empty")
        if not self.sessions or any(not session.strip() for session in self.sessions):
            raise ValueError("sessions must contain non-empty identifiers")
        if self.scan_count < len(self.sessions):
            raise ValueError("scan_count cannot be smaller than the session count")
        if self.resin is not Resin.UNKNOWN and self.evidence_method is EvidenceMethod.UNVERIFIED:
            raise ValueError("target-resin ground truth cannot use unverified evidence")
        features = np.asarray(self.features, dtype=float)
        expected = (len(WAVELENGTHS_NM),)
        if features.shape != expected:
            raise ValueError(f"features have shape {features.shape}; expected {expected}")
        if not np.isfinite(features).all():
            raise ValueError("features contain NaN or Inf")
        object.__setattr__(self, "features", features)

    @property
    def group_id(self) -> str:
        return self.parent_sku


def read_spectral_manifest(
    path: str | Path, *, wavelengths_nm: Sequence[int] = WAVELENGTHS_NM
) -> list[SpectralScan]:
    source = Path(path)
    wavelengths = tuple(int(value) for value in wavelengths_nm)
    required = IDENTITY_COLUMNS | spectral_columns(wavelengths)
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"spectral manifest is missing columns: {sorted(missing)}")
        scans: list[SpectralScan] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                scans.append(
                    SpectralScan(
                        scan_id=row["scan_id"],
                        item_id=row["item_id"],
                        parent_sku=row["parent_sku"],
                        session_id=row["session_id"],
                        resin=Resin(row["resin"]),
                        evidence_method=EvidenceMethod(row["evidence_method"]),
                        reference_id=row["reference_id"],
                        raw=np.asarray([float(row[f"raw_{w}"]) for w in wavelengths]),
                        dark=np.asarray([float(row[f"dark_{w}"]) for w in wavelengths]),
                        white=np.asarray([float(row[f"white_{w}"]) for w in wavelengths]),
                        wavelengths_nm=wavelengths,
                        sensor_revision=row["sensor_revision"],
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid spectral scan at line {line_number}: {exc}") from exc
    if not scans:
        raise ValueError("spectral manifest contains no scans")
    return scans


def validate_spectral_dataset(
    scans: Sequence[SpectralScan],
    *,
    min_scans_per_item: int = 10,
    min_sessions_per_item: int = 3,
    min_items_per_class: int = 30,
    min_parent_sku_groups_per_class: int = 1,
    exact_scans_per_item: bool = False,
    exact_items_per_class: bool = False,
) -> None:
    if (
        min_scans_per_item < 1
        or min_sessions_per_item < 1
        or min_items_per_class < 1
        or min_parent_sku_groups_per_class < 1
    ):
        raise ValueError("minimum dataset counts must be positive")
    if not scans:
        raise ValueError("spectral dataset contains no scans")

    by_item: dict[str, list[SpectralScan]] = defaultdict(list)
    by_sku: dict[str, list[SpectralScan]] = defaultdict(list)
    seen_scan_ids: set[str] = set()
    for scan in scans:
        if scan.scan_id in seen_scan_ids:
            raise ValueError(f"duplicate scan_id: {scan.scan_id}")
        seen_scan_ids.add(scan.scan_id)
        by_item[scan.item_id].append(scan)
        by_sku[scan.parent_sku].append(scan)

    for item_id, item_scans in by_item.items():
        labels = {scan.resin for scan in item_scans}
        skus = {scan.parent_sku for scan in item_scans}
        evidence = {scan.evidence_method for scan in item_scans}
        sensor_revisions = {scan.sensor_revision for scan in item_scans}
        sessions = {scan.session_id for scan in item_scans}
        if (
            len(labels) != 1
            or len(skus) != 1
            or len(evidence) != 1
            or len(sensor_revisions) != 1
        ):
            raise ValueError(
                f"item {item_id} has inconsistent label, SKU, evidence, or sensor metadata"
            )
        if len(item_scans) < min_scans_per_item:
            raise ValueError(
                f"item {item_id} has {len(item_scans)} scans; require {min_scans_per_item}"
            )
        if exact_scans_per_item and len(item_scans) != min_scans_per_item:
            raise ValueError(
                f"item {item_id} has {len(item_scans)} scans; require exactly "
                f"{min_scans_per_item}"
            )
        if len(sessions) < min_sessions_per_item:
            raise ValueError(
                f"item {item_id} has {len(sessions)} sessions; require {min_sessions_per_item}"
            )

    for parent_sku, sku_scans in by_sku.items():
        labels = {scan.resin for scan in sku_scans}
        if len(labels) != 1:
            raise ValueError(f"parent_sku {parent_sku} crosses resin labels")

    sensor_revisions = {scan.sensor_revision for scan in scans}
    if len(sensor_revisions) != 1:
        raise ValueError(f"dataset crosses sensor revisions: {sorted(sensor_revisions)}")

    item_counts = {
        resin: sum(item_scans[0].resin is resin for item_scans in by_item.values())
        for resin in Resin
    }
    short = {
        resin.value: count for resin, count in item_counts.items() if count < min_items_per_class
    }
    if short:
        raise ValueError(
            f"insufficient unique items by class: {short}; require {min_items_per_class} each"
        )
    if exact_items_per_class:
        wrong = {
            resin.value: count
            for resin, count in item_counts.items()
            if count != min_items_per_class
        }
        if wrong:
            raise ValueError(
                f"wrong unique-item count by class: {wrong}; require exactly "
                f"{min_items_per_class} each"
            )
    sku_groups = {
        resin: len(
            {
                parent_sku
                for parent_sku, sku_scans in by_sku.items()
                if sku_scans[0].resin is resin
            }
        )
        for resin in Resin
    }
    short_groups = {
        resin.value: count
        for resin, count in sku_groups.items()
        if count < min_parent_sku_groups_per_class
    }
    if short_groups:
        raise ValueError(
            "insufficient parent_sku groups by class: "
            f"{short_groups}; require {min_parent_sku_groups_per_class} each"
        )


def aggregate_item_spectra(
    scans: Sequence[SpectralScan],
    *,
    min_scans_per_item: int = 10,
    min_sessions_per_item: int = 3,
) -> list[ItemSpectrum]:
    by_item: dict[str, list[SpectralScan]] = defaultdict(list)
    seen_scan_ids: set[str] = set()
    for scan in scans:
        if scan.scan_id in seen_scan_ids:
            raise ValueError(f"duplicate scan_id: {scan.scan_id}")
        seen_scan_ids.add(scan.scan_id)
        by_item[scan.item_id].append(scan)
    spectra: list[ItemSpectrum] = []
    for item_id, item_scans in sorted(by_item.items()):
        labels = {scan.resin for scan in item_scans}
        skus = {scan.parent_sku for scan in item_scans}
        evidence = {scan.evidence_method for scan in item_scans}
        sensor_revisions = {scan.sensor_revision for scan in item_scans}
        sessions = tuple(sorted({scan.session_id for scan in item_scans}))
        if (
            len(labels) != 1
            or len(skus) != 1
            or len(evidence) != 1
            or len(sensor_revisions) != 1
        ):
            raise ValueError(
                f"item {item_id} has inconsistent label, SKU, evidence, or sensor metadata"
            )
        if len(item_scans) < min_scans_per_item:
            raise ValueError(
                f"item {item_id} has {len(item_scans)} scans; require {min_scans_per_item}"
            )
        if len(sessions) < min_sessions_per_item:
            raise ValueError(
                f"item {item_id} has {len(sessions)} sessions; require {min_sessions_per_item}"
            )
        processed = np.stack([scan.processed() for scan in item_scans])
        spectra.append(
            ItemSpectrum(
                item_id=item_id,
                parent_sku=next(iter(skus)),
                resin=next(iter(labels)),
                evidence_method=next(iter(evidence)),
                sessions=sessions,
                scan_count=len(item_scans),
                features=np.median(processed, axis=0),
            )
        )
    return spectra


def softmax_confidence(scores: np.ndarray, *, temperature: float) -> np.ndarray:
    if temperature <= 0 or not math.isfinite(temperature):
        raise ValueError("temperature must be finite and positive")
    values = np.asarray(scores, dtype=float)
    if values.ndim != 2:
        raise ValueError("scores must have shape (items, classes)")
    scaled = values / temperature
    shifted = scaled - np.max(scaled, axis=1, keepdims=True)
    probabilities = np.exp(shifted)
    return probabilities / np.sum(probabilities, axis=1, keepdims=True)


def apply_abstention(
    predicted: Sequence[Resin | str], confidence: Sequence[float], *, threshold: float
) -> list[Resin]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    if len(predicted) != len(confidence):
        raise ValueError("predicted labels and confidence lengths differ")
    return [
        Resin.UNKNOWN if float(score) < threshold else Resin(label)
        for label, score in zip(predicted, confidence, strict=True)
    ]


def material_classification_report(
    actual: Sequence[Resin | str],
    predicted: Sequence[Resin | str],
    confidence: Sequence[float],
    *,
    min_accepted_per_target: int = 20,
    min_accepted_correctness: float = 0.95,
    max_unknown_false_accepts: int = 1,
) -> dict[str, object]:
    if not (len(actual) == len(predicted) == len(confidence)):
        raise ValueError("actual, predicted, and confidence lengths differ")
    truth = [Resin(value) for value in actual]
    guesses = [Resin(value) for value in predicted]
    if any(not 0.0 <= float(value) <= 1.0 for value in confidence):
        raise ValueError("confidence must be in [0, 1]")

    confusion = {label.value: {guess.value: 0 for guess in Resin} for label in Resin}
    for label, guess in zip(truth, guesses, strict=True):
        confusion[label.value][guess.value] += 1

    targets: dict[str, object] = {}
    gate_details: dict[str, bool] = {}
    for resin in (Resin.PET, Resin.HDPE, Resin.PP):
        indexes = [index for index, label in enumerate(truth) if label is resin]
        accepted_indexes = [index for index in indexes if guesses[index] is not Resin.UNKNOWN]
        accepted_correct = [guesses[index] is resin for index in accepted_indexes]
        targets[resin.value] = {
            "support": len(indexes),
            "accepted_count": len(accepted_indexes),
            "coverage": rate_summary(guesses[index] is not Resin.UNKNOWN for index in indexes),
            "correct": rate_summary(guesses[index] is resin for index in indexes),
            "accepted_correctness": rate_summary(accepted_correct),
        }
        correctness = sum(accepted_correct) / len(accepted_correct) if accepted_correct else 0.0
        gate_details[f"{resin.value}_accepted_count"] = (
            len(accepted_indexes) >= min_accepted_per_target
        )
        gate_details[f"{resin.value}_accepted_correctness"] = (
            correctness >= min_accepted_correctness
        )

    unknown_indexes = [index for index, label in enumerate(truth) if label is Resin.UNKNOWN]
    unknown_false_accepts = sum(guesses[index] is not Resin.UNKNOWN for index in unknown_indexes)
    gate_details["unknown_false_accepts"] = unknown_false_accepts <= max_unknown_false_accepts
    return {
        "item_count": len(truth),
        "confusion_matrix": confusion,
        "targets": targets,
        "unknown_false_accept": rate_summary(
            guesses[index] is not Resin.UNKNOWN for index in unknown_indexes
        ),
        "abstention": rate_summary(guess is Resin.UNKNOWN for guess in guesses),
        "confidence": {
            "n": len(confidence),
            "min": float(min(confidence)) if len(confidence) else None,
            "max": float(max(confidence)) if len(confidence) else None,
        },
        "gate": {
            "passed": all(gate_details.values()),
            "checks": gate_details,
            "criteria": {
                "min_accepted_per_target": min_accepted_per_target,
                "min_accepted_correctness": min_accepted_correctness,
                "max_unknown_false_accepts": max_unknown_false_accepts,
            },
        },
    }


def class_item_counts(items: Iterable[ItemSpectrum]) -> dict[str, int]:
    counts = {resin.value: 0 for resin in Resin}
    for item in items:
        counts[item.resin.value] += 1
    return counts
