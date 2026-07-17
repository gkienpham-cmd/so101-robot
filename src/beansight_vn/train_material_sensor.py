from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from .material_sensing import (
    WAVELENGTHS_NM,
    ItemSpectrum,
    SpectralScan,
    aggregate_item_spectra,
    apply_abstention,
    class_item_counts,
    material_classification_report,
    read_spectral_manifest,
    softmax_confidence,
    validate_spectral_dataset,
)
from .material_sorting import EvidenceMethod, MaterialDecision, Resin
from .metrics import percentile

LABEL_ORDER = tuple(resin.value for resin in Resin)


@dataclass(frozen=True, slots=True)
class ModelSelection:
    c: float
    gamma: str | float
    temperature: float
    threshold: float
    validation_macro_f1: float
    validation_threshold_feasible: bool


class NearestCentroid:
    def fit(self, features: np.ndarray, labels: np.ndarray) -> NearestCentroid:
        self.classes_ = np.unique(labels)
        self.centroids_ = np.stack(
            [np.mean(features[labels == label], axis=0) for label in self.classes_]
        )
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        distances = np.linalg.norm(
            features[:, np.newaxis, :] - self.centroids_[np.newaxis, :, :], axis=2
        )
        return self.classes_[np.argmin(distances, axis=1)]


def _sklearn_components() -> tuple[Any, Any, Any, Any]:
    try:
        import joblib
        from sklearn.metrics import f1_score
        from sklearn.model_selection import StratifiedGroupKFold
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Install the material-sensing extra: pip install -e '.[materials]'"
        ) from exc
    return joblib, f1_score, StratifiedGroupKFold, (make_pipeline, StandardScaler, SVC)


def _build_svc(c: float, gamma: str | float) -> Any:
    _, _, _, (make_pipeline, StandardScaler, SVC) = _sklearn_components()
    return make_pipeline(
        StandardScaler(),
        SVC(
            C=c,
            gamma=gamma,
            kernel="rbf",
            class_weight="balanced",
            decision_function_shape="ovr",
        ),
    )


def _aligned_scores(model: Any, features: np.ndarray) -> np.ndarray:
    scores = np.asarray(model.decision_function(features), dtype=float)
    if scores.ndim != 2:
        raise ValueError("material model must be fitted on all four resin classes")
    aligned = np.full((len(features), len(LABEL_ORDER)), -1e9, dtype=float)
    for model_index, label in enumerate(model.classes_):
        aligned[:, LABEL_ORDER.index(str(label))] = scores[:, model_index]
    return aligned


def _group_count_by_class(labels: np.ndarray, groups: np.ndarray) -> dict[str, int]:
    return {
        label: len(set(groups[labels == label].tolist()))
        for label in LABEL_ORDER
    }


def _effective_splits(labels: np.ndarray, groups: np.ndarray, requested: int) -> int:
    if requested < 2:
        raise ValueError("cross-validation requires at least two folds")
    counts = _group_count_by_class(labels, groups)
    insufficient = {label: count for label, count in counts.items() if count < requested}
    if insufficient:
        raise ValueError(
            f"{requested}-fold grouped evaluation requires at least {requested} "
            f"parent_sku groups per class; insufficient groups: {insufficient}"
        )
    return requested


def _oof_scores(
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    *,
    c: float,
    gamma: str | float,
    folds: int,
    seed: int,
) -> np.ndarray:
    _, _, StratifiedGroupKFold, _ = _sklearn_components()
    splits = _effective_splits(labels, groups, folds)
    splitter = StratifiedGroupKFold(n_splits=splits, shuffle=True, random_state=seed)
    scores = np.empty((len(features), len(LABEL_ORDER)), dtype=float)
    seen = np.zeros(len(features), dtype=bool)
    for train_index, validation_index in splitter.split(features, labels, groups):
        model = _build_svc(c, gamma).fit(features[train_index], labels[train_index])
        scores[validation_index] = _aligned_scores(model, features[validation_index])
        seen[validation_index] = True
    if not seen.all():
        raise RuntimeError("grouped cross-validation did not score every item")
    return scores


def _choose_hyperparameters(
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    *,
    c_values: Sequence[float],
    gamma_values: Sequence[str | float],
    folds: int,
    seed: int,
) -> tuple[float, str | float, float, np.ndarray]:
    _, f1_score, _, _ = _sklearn_components()
    candidates: list[tuple[float, float, str | float, np.ndarray]] = []
    for c in c_values:
        for gamma in gamma_values:
            scores = _oof_scores(
                features, labels, groups, c=float(c), gamma=gamma, folds=folds, seed=seed
            )
            predicted = np.asarray(LABEL_ORDER)[np.argmax(scores, axis=1)]
            macro_f1 = float(
                f1_score(labels, predicted, labels=list(LABEL_ORDER), average="macro")
            )
            candidates.append((macro_f1, float(c), gamma, scores))
    macro_f1, c, gamma, scores = max(candidates, key=lambda item: (item[0], -item[1]))
    return c, gamma, macro_f1, scores


def _select_temperature(
    scores: np.ndarray, labels: np.ndarray, temperatures: Sequence[float]
) -> float:
    label_indexes = np.asarray([LABEL_ORDER.index(str(label)) for label in labels])
    losses: list[tuple[float, float]] = []
    for temperature in temperatures:
        probabilities = softmax_confidence(scores, temperature=float(temperature))
        selected = np.clip(probabilities[np.arange(len(labels)), label_indexes], 1e-12, 1.0)
        losses.append((float(-np.mean(np.log(selected))), float(temperature)))
    return min(losses)[1]


def _select_threshold(
    labels: np.ndarray,
    raw_predictions: Sequence[str],
    confidence: np.ndarray,
    thresholds: Sequence[float],
    *,
    min_correctness: float,
    min_target_coverage: float,
    max_unknown_false_rate: float,
) -> tuple[float, bool]:
    if not 0.0 <= min_target_coverage <= 1.0:
        raise ValueError("min_target_coverage must be in [0, 1]")
    actual = [Resin(value) for value in labels]
    candidates: list[tuple[bool, int, float, float, float]] = []
    for threshold in thresholds:
        predictions = apply_abstention(raw_predictions, confidence, threshold=float(threshold))
        target_checks: list[bool] = []
        accepted_count = 0
        correctness_values: list[float] = []
        for resin in (Resin.PET, Resin.HDPE, Resin.PP):
            indexes = [index for index, label in enumerate(actual) if label is resin]
            accepted = [index for index in indexes if predictions[index] is not Resin.UNKNOWN]
            accepted_count += len(accepted)
            correctness = (
                sum(predictions[index] is resin for index in accepted) / len(accepted)
                if accepted
                else 0.0
            )
            coverage = len(accepted) / len(indexes) if indexes else 0.0
            correctness_values.append(correctness)
            target_checks.append(
                correctness >= min_correctness and coverage >= min_target_coverage
            )
        unknown_indexes = [
            index for index, label in enumerate(actual) if label is Resin.UNKNOWN
        ]
        false_rate = (
            sum(predictions[index] is not Resin.UNKNOWN for index in unknown_indexes)
            / len(unknown_indexes)
            if unknown_indexes
            else 1.0
        )
        feasible = all(target_checks) and false_rate <= max_unknown_false_rate
        candidates.append(
            (
                feasible,
                accepted_count,
                min(correctness_values),
                -false_rate,
                float(threshold),
            )
        )
    selected = max(candidates)
    return selected[4], selected[0]


def _evaluate_predictions(
    actual: np.ndarray,
    predicted: Sequence[Resin | str],
    confidence: Sequence[float],
    *,
    gates: dict[str, Any],
    latency_ms: Sequence[float] | None = None,
) -> dict[str, object]:
    report = material_classification_report(
        actual,
        predicted,
        confidence,
        min_accepted_per_target=int(gates["min_accepted_per_target"]),
        min_accepted_correctness=float(gates["min_accepted_correctness"]),
        max_unknown_false_accepts=int(gates["max_unknown_false_accepts"]),
    )
    values = list(latency_ms or [])
    report["latency_ms"] = {
        "n": len(values),
        "median": median(values) if values else None,
        "p95": percentile(values, 0.95),
    }
    return report


def nested_evaluate(
    items: Sequence[ItemSpectrum],
    *,
    sensor_revision: str,
    evaluation: dict[str, Any],
    repeats_per_decision: int = 5,
) -> tuple[dict[str, object], dict[str, Any]]:
    if not sensor_revision.strip() or "REPLACE" in sensor_revision:
        raise ValueError("sensor_revision must identify the actual fixed fixture")
    if repeats_per_decision < 1:
        raise ValueError("repeats_per_decision must be positive")
    _, _, StratifiedGroupKFold, _ = _sklearn_components()
    features = np.stack([item.features for item in items])
    labels = np.asarray([item.resin.value for item in items])
    groups = np.asarray([item.group_id for item in items])
    outer_folds = int(evaluation["outer_folds"])
    group_counts = _group_count_by_class(labels, groups)
    insufficient = {
        label: count for label, count in group_counts.items() if count < outer_folds
    }
    if insufficient:
        raise ValueError(
            f"outer {outer_folds}-fold evaluation requires at least {outer_folds} "
            f"parent_sku groups per class; insufficient groups: {insufficient}"
        )
    seed = int(evaluation["seed"])
    outer = StratifiedGroupKFold(n_splits=outer_folds, shuffle=True, random_state=seed)

    svm_predictions: list[Resin | None] = [None] * len(items)
    svm_confidence = np.zeros(len(items), dtype=float)
    baseline_predictions: list[Resin | None] = [None] * len(items)
    latency_ms = np.zeros(len(items), dtype=float)
    selections: list[ModelSelection] = []
    fold_audit: list[dict[str, object]] = []

    for fold, (train_index, test_index) in enumerate(outer.split(features, labels, groups)):
        train_features = features[train_index]
        train_labels = labels[train_index]
        train_groups = groups[train_index]
        fold_audit.append(
            {
                "fold": fold,
                "train_parent_skus": sorted(set(train_groups.tolist())),
                "test_parent_skus": sorted(set(groups[test_index].tolist())),
                "test_item_ids": [items[index].item_id for index in test_index],
            }
        )
        c, gamma, macro_f1, inner_scores = _choose_hyperparameters(
            train_features,
            train_labels,
            train_groups,
            c_values=evaluation["c_values"],
            gamma_values=evaluation["gamma_values"],
            folds=int(evaluation["inner_folds"]),
            seed=seed + fold,
        )
        temperature = _select_temperature(
            inner_scores, train_labels, evaluation["temperature_values"]
        )
        inner_probabilities = softmax_confidence(inner_scores, temperature=temperature)
        inner_raw = np.asarray(LABEL_ORDER)[np.argmax(inner_probabilities, axis=1)]
        threshold, feasible = _select_threshold(
            train_labels,
            inner_raw,
            np.max(inner_probabilities, axis=1),
            evaluation["threshold_values"],
            min_correctness=float(evaluation["threshold_target_correctness"]),
            min_target_coverage=float(evaluation["threshold_min_target_coverage"]),
            max_unknown_false_rate=float(evaluation["threshold_unknown_false_rate"]),
        )
        selections.append(
            ModelSelection(c, gamma, temperature, threshold, macro_f1, feasible)
        )

        model = _build_svc(c, gamma).fit(train_features, train_labels)
        score_rows: list[np.ndarray] = []
        fold_latency_ms: list[float] = []
        for global_index in test_index:
            start = time.perf_counter()
            score_rows.append(_aligned_scores(model, features[global_index : global_index + 1])[0])
            fold_latency_ms.append((time.perf_counter() - start) * 1000.0)
        scores = np.stack(score_rows)
        probabilities = softmax_confidence(scores, temperature=temperature)
        raw_predictions = np.asarray(LABEL_ORDER)[np.argmax(probabilities, axis=1)]
        confidence = np.max(probabilities, axis=1)
        predictions = apply_abstention(raw_predictions, confidence, threshold=threshold)
        for local_index, global_index in enumerate(test_index):
            svm_predictions[global_index] = predictions[local_index]
            svm_confidence[global_index] = confidence[local_index]
            latency_ms[global_index] = fold_latency_ms[local_index]

        baseline = NearestCentroid().fit(train_features, train_labels)
        for global_index, label in zip(
            test_index, baseline.predict(features[test_index]), strict=True
        ):
            baseline_predictions[global_index] = Resin(label)

    if any(value is None for value in svm_predictions + baseline_predictions):
        raise RuntimeError("nested evaluation did not predict every item")
    svm_final = [value for value in svm_predictions if value is not None]
    baseline_final = [value for value in baseline_predictions if value is not None]
    gates = evaluation["gates"]
    report = {
        "schema_version": "1.0",
        "protocol_id": "plastic-material-sensor-v1",
        "sensor_revision": sensor_revision,
        "item_counts": class_item_counts(items),
        "group_counts": group_counts,
        "outer_folds": outer_folds,
        "rbf_svm": _evaluate_predictions(
            labels, svm_final, svm_confidence, gates=gates, latency_ms=latency_ms.tolist()
        ),
        "nearest_centroid": _evaluate_predictions(
            labels, baseline_final, [1.0] * len(items), gates=gates
        ),
        "fold_selections": [asdict(selection) for selection in selections],
        "fold_audit": fold_audit,
    }

    final_c, final_gamma, final_macro_f1, final_inner_scores = _choose_hyperparameters(
        features,
        labels,
        groups,
        c_values=evaluation["c_values"],
        gamma_values=evaluation["gamma_values"],
        folds=int(evaluation["inner_folds"]),
        seed=seed + outer_folds,
    )
    final_temperature = _select_temperature(
        final_inner_scores, labels, evaluation["temperature_values"]
    )
    final_probabilities = softmax_confidence(
        final_inner_scores, temperature=final_temperature
    )
    final_raw = np.asarray(LABEL_ORDER)[np.argmax(final_probabilities, axis=1)]
    final_threshold, final_feasible = _select_threshold(
        labels,
        final_raw,
        np.max(final_probabilities, axis=1),
        evaluation["threshold_values"],
        min_correctness=float(evaluation["threshold_target_correctness"]),
        min_target_coverage=float(evaluation["threshold_min_target_coverage"]),
        max_unknown_false_rate=float(evaluation["threshold_unknown_false_rate"]),
    )
    final_model = _build_svc(final_c, final_gamma).fit(features, labels)
    fold_thresholds_feasible = all(
        selection.validation_threshold_feasible for selection in selections
    )
    report["threshold_selection_all_folds_feasible"] = fold_thresholds_feasible
    gate_passed = bool(
        report["rbf_svm"]["gate"]["passed"]
        and fold_thresholds_feasible
        and final_feasible
    )
    artifact = {
        "schema_version": "1.0",
        "sensor_revision": sensor_revision,
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "repeats_per_decision": repeats_per_decision,
        "labels": list(LABEL_ORDER),
        "temperature": final_temperature,
        "threshold": final_threshold,
        "c": final_c,
        "gamma": final_gamma,
        "gate_passed": gate_passed,
        "model": final_model,
    }
    report["final_model"] = {
        **{key: value for key, value in artifact.items() if key != "model"},
        "selection_macro_f1": final_macro_f1,
        "selection_threshold_feasible": final_feasible,
    }
    qualification_digest = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    artifact["qualification_payload_sha256"] = qualification_digest
    report["final_model"]["qualification_payload_sha256"] = qualification_digest
    return report, artifact


def classify_repeated_scans(
    artifact: dict[str, Any], *, item_id: str, scans: Sequence[SpectralScan]
) -> MaterialDecision:
    if not artifact.get("gate_passed"):
        raise RuntimeError("material model did not pass the frozen integration gate")
    if not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("qualification_payload_sha256", ""))):
        raise RuntimeError("material model lacks qualification-payload provenance")
    if tuple(artifact.get("labels", ())) != LABEL_ORDER:
        raise RuntimeError("material model label contract does not match this runtime")
    expected_repeats = int(artifact.get("repeats_per_decision", 0))
    if len(scans) != expected_repeats:
        raise ValueError(
            f"material decision requires exactly {expected_repeats} repeated scans"
        )
    if any(scan.item_id != item_id for scan in scans):
        raise ValueError("all repeated scans must match the requested item_id")
    if len({scan.scan_id for scan in scans}) != len(scans):
        raise ValueError("repeated material scans must have unique scan_id values")
    if any(scan.sensor_revision != artifact["sensor_revision"] for scan in scans):
        raise ValueError("repeated scans do not match the qualified sensor revision")
    expected_wavelengths = tuple(artifact.get("wavelengths_nm", ()))
    if expected_wavelengths != WAVELENGTHS_NM or any(
        scan.wavelengths_nm != expected_wavelengths for scan in scans
    ):
        raise ValueError("repeated scans do not match the qualified wavelength contract")
    values = np.median(np.stack([scan.processed() for scan in scans]), axis=0).reshape(1, -1)
    scores = _aligned_scores(artifact["model"], values)
    probabilities = softmax_confidence(scores, temperature=float(artifact["temperature"]))
    raw = Resin(LABEL_ORDER[int(np.argmax(probabilities[0]))])
    confidence = float(np.max(probabilities[0]))
    if raw is Resin.UNKNOWN:
        return MaterialDecision(
            item_id,
            Resin.UNKNOWN,
            confidence,
            artifact["sensor_revision"],
            EvidenceMethod.DISCRETE_NIR,
            "model_predicted_unknown",
        )
    if confidence < float(artifact["threshold"]):
        return MaterialDecision(
            item_id,
            Resin.UNKNOWN,
            confidence,
            artifact["sensor_revision"],
            EvidenceMethod.DISCRETE_NIR,
            "below_validation_threshold",
        )
    return MaterialDecision(
        item_id,
        raw,
        confidence,
        artifact["sensor_revision"],
        EvidenceMethod.DISCRETE_NIR,
    )


def run(manifest: Path, config_path: Path, output_dir: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    wavelengths = tuple(config["sensor"]["wavelengths_nm"])
    if wavelengths != WAVELENGTHS_NM:
        raise ValueError(
            f"configured wavelengths {wavelengths} do not match the v1 contract {WAVELENGTHS_NM}"
        )
    scans = read_spectral_manifest(manifest, wavelengths_nm=wavelengths)
    if {scan.sensor_revision for scan in scans} != {config["sensor"]["revision"]}:
        raise ValueError("manifest sensor revision does not match the experiment config")
    dataset = config["dataset"]
    validate_spectral_dataset(
        scans,
        min_scans_per_item=int(dataset["scans_per_item"]),
        min_sessions_per_item=int(dataset["sessions_per_item"]),
        min_items_per_class=int(dataset["items_per_class"]),
        min_parent_sku_groups_per_class=int(
            dataset["parent_sku_groups_per_class_min"]
        ),
        exact_scans_per_item=bool(dataset["exact_scans_per_item"]),
        exact_items_per_class=bool(dataset["exact_items_per_class"]),
    )
    items = aggregate_item_spectra(
        scans,
        min_scans_per_item=int(dataset["scans_per_item"]),
        min_sessions_per_item=int(dataset["sessions_per_item"]),
    )
    report, artifact = nested_evaluate(
        items,
        sensor_revision=config["sensor"]["revision"],
        evaluation=config["evaluation"],
        repeats_per_decision=int(config["preprocessing"]["repeats_per_decision"]),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_passed = bool(artifact["gate_passed"])
    artifact_name = (
        "material_model.joblib" if gate_passed else "candidate_material_model.UNQUALIFIED.joblib"
    )
    report["artifact"] = {"filename": artifact_name, "deployable": gate_passed}
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    joblib, _, _, _ = _sklearn_components()
    joblib.dump(artifact, output_dir / artifact_name)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate the leakage-safe PET/HDPE/PP/unknown spectral classifier."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/material_sensor.json"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/material_sensor/db23_r1")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(args.manifest, args.config, args.output_dir)
    print(json.dumps(report["rbf_svm"], indent=2, sort_keys=True))
    return 0 if report["artifact"]["deployable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
