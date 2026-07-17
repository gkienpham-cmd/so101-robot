import csv

import numpy as np
import pytest

from beansight_vn.material_sensing import (
    WAVELENGTHS_NM,
    SpectralScan,
    aggregate_item_spectra,
    apply_abstention,
    material_classification_report,
    read_spectral_manifest,
    softmax_confidence,
    validate_spectral_dataset,
)
from beansight_vn.material_sorting import EvidenceMethod, Resin


def scan(
    item="item-1",
    sku="sku-1",
    session="session-1",
    resin=Resin.PET,
    scan_id="scan-1",
    evidence=EvidenceMethod.MOLDED_RIC,
):
    dark = np.full(len(WAVELENGTHS_NM), 10.0)
    white = np.full(len(WAVELENGTHS_NM), 110.0)
    reflectance = np.linspace(0.2, 0.8, len(WAVELENGTHS_NM))
    return SpectralScan(
        scan_id,
        item,
        sku,
        session,
        resin,
        evidence,
        f"reference-{session}",
        dark + reflectance * (white - dark),
        dark,
        white,
    )


def test_referencing_and_snv_are_deterministic():
    observation = scan()
    assert np.allclose(
        observation.normalized_reflectance(),
        np.linspace(0.2, 0.8, len(WAVELENGTHS_NM)),
    )
    processed = observation.processed()
    assert np.mean(processed) == pytest.approx(0.0)
    assert np.std(processed) == pytest.approx(1.0)


def test_target_ground_truth_requires_traceable_evidence():
    with pytest.raises(ValueError, match="unverified"):
        scan(evidence=EvidenceMethod.UNVERIFIED)


def test_dataset_validation_and_item_aggregation_enforce_groups():
    scans = []
    for resin in Resin:
        for index in range(1, 4):
            scans.append(
                scan(
                    item=f"{resin.value}-item",
                    sku=f"{resin.value}-sku",
                    session=f"session-{index}",
                    resin=resin,
                    scan_id=f"{resin.value}-scan-{index}",
                    evidence=(
                        EvidenceMethod.UNVERIFIED
                        if resin is Resin.UNKNOWN
                        else EvidenceMethod.MOLDED_RIC
                    ),
                )
            )
    validate_spectral_dataset(
        scans, min_scans_per_item=3, min_sessions_per_item=3, min_items_per_class=1
    )
    spectra = aggregate_item_spectra(scans, min_scans_per_item=3, min_sessions_per_item=3)
    assert len(spectra) == 4
    pet = next(spectrum for spectrum in spectra if spectrum.resin is Resin.PET)
    assert pet.group_id == "PET-sku"
    assert pet.scan_count == 3

    bad = scans + [
        scan(
            item="item-2",
            sku="PET-sku",
            resin=Resin.HDPE,
            scan_id="bad",
            evidence=EvidenceMethod.MANUFACTURER_RECORD,
        )
    ]
    with pytest.raises(ValueError, match="crosses resin labels"):
        validate_spectral_dataset(
            bad, min_scans_per_item=1, min_sessions_per_item=1, min_items_per_class=1
        )


def test_dataset_rejects_duplicate_scan_ids():
    observation = scan()
    with pytest.raises(ValueError, match="duplicate scan_id"):
        validate_spectral_dataset(
            [observation, observation],
            min_scans_per_item=1,
            min_sessions_per_item=1,
            min_items_per_class=1,
        )


def test_manifest_reader_reports_missing_columns(tmp_path):
    path = tmp_path / "manifest.csv"
    path.write_text("scan_id,item_id\nscan-1,item-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        read_spectral_manifest(path)


def test_manifest_reader_round_trips_a_scan(tmp_path):
    path = tmp_path / "manifest.csv"
    fieldnames = [
        "scan_id",
        "item_id",
        "parent_sku",
        "session_id",
        "resin",
        "evidence_method",
        "reference_id",
        "sensor_revision",
    ]
    for kind in ("raw", "dark", "white"):
        fieldnames.extend(f"{kind}_{wavelength}" for wavelength in WAVELENGTHS_NM)
    row = {
        "scan_id": "scan-1",
        "item_id": "item-1",
        "parent_sku": "sku-1",
        "session_id": "session-1",
        "resin": "PET",
        "evidence_method": "molded_ric",
        "reference_id": "reference-1",
        "sensor_revision": "fixture-r1",
    }
    for wavelength in WAVELENGTHS_NM:
        row[f"raw_{wavelength}"] = "60"
        row[f"dark_{wavelength}"] = "10"
        row[f"white_{wavelength}"] = "110"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)
    restored = read_spectral_manifest(path)
    assert restored[0].resin is Resin.PET
    assert restored[0].raw.tolist() == [60.0] * len(WAVELENGTHS_NM)


def test_confidence_abstention_and_gate_report():
    scores = np.asarray([[4.0, 1.0, 0.0, -1.0], [0.0, 0.0, 0.0, 0.0]])
    probabilities = softmax_confidence(scores, temperature=1.0)
    predicted = apply_abstention(
        [Resin.PET, Resin.HDPE], np.max(probabilities, axis=1), threshold=0.8
    )
    assert predicted == [Resin.PET, Resin.UNKNOWN]

    actual = [Resin.PET] * 2 + [Resin.HDPE] * 2 + [Resin.PP] * 2 + [Resin.UNKNOWN]
    guesses = [Resin.PET] * 2 + [Resin.HDPE] * 2 + [Resin.PP] * 2 + [Resin.UNKNOWN]
    report = material_classification_report(
        actual,
        guesses,
        [0.99] * len(actual),
        min_accepted_per_target=2,
        min_accepted_correctness=0.95,
        max_unknown_false_accepts=0,
    )
    assert report["gate"]["passed"]
    assert report["targets"]["PET"]["accepted_correctness"]["wilson_95"][1] <= 1.0
