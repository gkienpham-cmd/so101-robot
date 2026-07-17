import numpy as np
import pytest

from beansight_vn.material_sensing import WAVELENGTHS_NM, ItemSpectrum, SpectralScan
from beansight_vn.material_sorting import EvidenceMethod, Resin
from beansight_vn.train_material_sensor import classify_repeated_scans, nested_evaluate


def synthetic_items():
    centers = {
        Resin.PET: np.asarray([1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0, -1.0]),
        Resin.HDPE: np.asarray([1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0]),
        Resin.PP: np.asarray([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]),
        Resin.UNKNOWN: np.asarray([-1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0]),
    }
    items = []
    for resin, center in centers.items():
        for index in range(6):
            items.append(
                ItemSpectrum(
                    item_id=f"{resin.value}-{index}",
                    parent_sku=f"{resin.value}-sku-{index // 2}",
                    resin=resin,
                    evidence_method=(
                        EvidenceMethod.UNVERIFIED
                        if resin is Resin.UNKNOWN
                        else EvidenceMethod.REFERENCE_SAMPLE
                    ),
                    sessions=("s1", "s2", "s3"),
                    scan_count=10,
                    features=center + index * 0.01,
                )
            )
    return items


def test_nested_grouped_evaluation_and_model_classification():
    evaluation = {
        "seed": 1000,
        "outer_folds": 3,
        "inner_folds": 2,
        "c_values": [1.0],
        "gamma_values": ["scale"],
        "temperature_values": [1.0],
        "threshold_values": [0.5, 0.9],
        "threshold_target_correctness": 0.9,
        "threshold_min_target_coverage": 0.5,
        "threshold_unknown_false_rate": 0.1,
        "gates": {
            "min_accepted_per_target": 1,
            "min_accepted_correctness": 0.9,
            "max_unknown_false_accepts": 1,
        },
    }
    report, artifact = nested_evaluate(
        synthetic_items(), sensor_revision="fixture-r1", evaluation=evaluation
    )
    assert report["rbf_svm"]["gate"]["passed"]
    pattern = synthetic_items()[0].features
    repeated_scans = [
        SpectralScan(
            scan_id=f"runtime-{index}",
            item_id="new-pet",
            parent_sku="new-pet-sku",
            session_id="runtime-session",
            resin=Resin.UNKNOWN,
            evidence_method=EvidenceMethod.UNVERIFIED,
            reference_id="runtime-reference",
            raw=0.5 + 0.1 * pattern,
            dark=np.zeros(len(WAVELENGTHS_NM)),
            white=np.ones(len(WAVELENGTHS_NM)),
            sensor_revision="fixture-r1",
        )
        for index in range(5)
    ]
    decision = classify_repeated_scans(
        artifact,
        item_id="new-pet",
        scans=repeated_scans,
    )
    assert decision.resin is Resin.PET
    assert decision.sensor_revision == "fixture-r1"

    with pytest.raises(ValueError, match="exactly 5"):
        classify_repeated_scans(artifact, item_id="new-pet", scans=repeated_scans[:4])
    artifact["gate_passed"] = False
    with pytest.raises(RuntimeError, match="did not pass"):
        classify_repeated_scans(artifact, item_id="new-pet", scans=repeated_scans)


def test_outer_evaluation_does_not_silently_reduce_requested_folds():
    evaluation = {
        "seed": 1000,
        "outer_folds": 7,
        "inner_folds": 2,
        "c_values": [1.0],
        "gamma_values": ["scale"],
        "temperature_values": [1.0],
        "threshold_values": [0.5],
        "threshold_target_correctness": 0.9,
        "threshold_min_target_coverage": 0.5,
        "threshold_unknown_false_rate": 0.1,
        "gates": {
            "min_accepted_per_target": 1,
            "min_accepted_correctness": 0.9,
            "max_unknown_false_accepts": 1,
        },
    }
    with pytest.raises(ValueError, match="requires at least 7 parent_sku groups"):
        nested_evaluate(
            synthetic_items(), sensor_revision="fixture-r1", evaluation=evaluation
        )
