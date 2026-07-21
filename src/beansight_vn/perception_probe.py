"""Background-dependence probe for the trained perception classifier.

The training and test splits share one fixed printed-mat background, so a
model that exploits background artifacts scores *higher* in-domain, never
lower. This tool is the declared detection gate: it scores the same physical
beans re-photographed on a plain background (out-of-domain probe) and can
render occlusion-sensitivity maps showing where the model's evidence sits.

Probe images and their scores are diagnostics only. They never enter a
manifest, a split, a Hugging Face upload, or a headline metric, and the
operating threshold is never tuned against them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .metrics import wilson_interval
from .models import Label
from .perception import TorchScriptClassifier
from .train_perception import load_perception_training_config

EXPECTED_IMAGE_SIZE = (640, 480)
ALLOWED_LABELS = frozenset({Label.ACCEPTABLE.value, Label.VISIBLE_REJECT.value})
# Pre-declared in the 2026-07-21 spec, before any model existed. Never tuned.
BACKGROUND_DEPENDENCE_GAP = 0.15


def load_probe_labels(path: Path) -> dict[str, str]:
    """Read scored labels from a blind-labels CSV, skipping ambiguous rows."""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = {"bean_id", "grader_label", "ambiguous"} - columns
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        labels: dict[str, str] = {}
        for line, raw in enumerate(reader, start=2):
            bean_id = str(raw.get("bean_id") or "").strip()
            if not bean_id:
                raise ValueError(f"{path} line {line} has an empty bean_id")
            if bean_id in labels:
                raise ValueError(f"{path} repeats bean_id {bean_id}")
            ambiguous = str(raw.get("ambiguous") or "").strip().lower()
            if ambiguous not in {"true", "false"}:
                raise ValueError(f"{path} line {line} has non-boolean ambiguous value")
            if ambiguous == "true":
                continue
            label = str(raw.get("grader_label") or "").strip().lower()
            if label not in ALLOWED_LABELS:
                raise ValueError(f"{path} line {line} has unsupported grader_label")
            labels[bean_id] = label
    if not labels:
        raise ValueError(f"{path} contains no unambiguous scored labels")
    return labels


def collect_probe_images(probe_dir: Path) -> list[tuple[str, Path]]:
    """Return (bean_id, path) pairs for every probe PNG, validated up front."""

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install pillow to read probe images") from exc

    if not probe_dir.is_dir():
        raise ValueError(f"probe directory {probe_dir} does not exist")
    images = sorted(probe_dir.glob("*.png"))
    if not images:
        raise ValueError(f"probe directory {probe_dir} contains no PNG images")
    validated: list[tuple[str, Path]] = []
    for path in images:
        with Image.open(path) as image:
            if image.mode != "RGB" or image.size != EXPECTED_IMAGE_SIZE:
                raise ValueError(
                    f"{path} is {image.mode} {image.size}; probe images must be RGB "
                    f"{EXPECTED_IMAGE_SIZE} full C920 frames"
                )
        validated.append((path.stem, path))
    return validated


def _load_frame(path: Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def score_probe(
    images: list[tuple[str, Path]],
    labels: Mapping[str, str],
    classify: Callable[[np.ndarray], float],
    *,
    operating_threshold: float,
) -> dict[str, Any]:
    """Score every probe image; every image must have an unambiguous label."""

    unlabeled = [bean_id for bean_id, _ in images if bean_id not in labels]
    if unlabeled:
        raise ValueError(
            "probe images without an unambiguous label (bean_id must match the "
            f"PNG stem): {sorted(unlabeled)}"
        )
    rows: list[dict[str, Any]] = []
    false_accepts = 0
    false_rejects = 0
    for bean_id, path in images:
        reject_probability = float(classify(_load_frame(path)))
        predicted = (
            Label.VISIBLE_REJECT.value
            if reject_probability >= operating_threshold
            else Label.ACCEPTABLE.value
        )
        actual = labels[bean_id]
        correct = predicted == actual
        if not correct and actual == Label.VISIBLE_REJECT.value:
            false_accepts += 1
        if not correct and actual == Label.ACCEPTABLE.value:
            false_rejects += 1
        rows.append(
            {
                "bean_id": bean_id,
                "path": str(path),
                "grader_label": actual,
                "reject_probability": reject_probability,
                "predicted_label": predicted,
                "correct": correct,
            }
        )
    successes = sum(row["correct"] for row in rows)
    low, high = wilson_interval(successes, len(rows))
    return {
        "per_image": rows,
        "accuracy": {
            "successes": successes,
            "trials": len(rows),
            "rate": successes / len(rows),
            "wilson_95": [low, high],
        },
        "false_accepts": false_accepts,
        "false_rejects": false_rejects,
    }


def background_dependence_verdict(
    probe_accuracy: Mapping[str, Any],
    in_domain_successes: int | None,
    in_domain_trials: int | None,
) -> dict[str, Any]:
    """Apply the pre-declared gate: >=15pp gap AND non-overlapping Wilson CIs."""

    if in_domain_successes is None or in_domain_trials is None:
        return {
            "gap_threshold": BACKGROUND_DEPENDENCE_GAP,
            "flag": None,
            "reason": "in-domain successes/trials not supplied; verdict deferred",
        }
    in_low, in_high = wilson_interval(in_domain_successes, in_domain_trials)
    in_rate = in_domain_successes / in_domain_trials if in_domain_trials else 0.0
    probe_low, probe_high = probe_accuracy["wilson_95"]
    gap = in_rate - probe_accuracy["rate"]
    intervals_disjoint = probe_high < in_low
    flag = gap >= BACKGROUND_DEPENDENCE_GAP and intervals_disjoint
    return {
        "gap_threshold": BACKGROUND_DEPENDENCE_GAP,
        "in_domain": {
            "successes": in_domain_successes,
            "trials": in_domain_trials,
            "rate": in_rate,
            "wilson_95": [in_low, in_high],
        },
        "gap": gap,
        "intervals_disjoint": intervals_disjoint,
        "flag": flag,
        "reason": (
            "probe accuracy is >=15pp below in-domain with disjoint Wilson CIs; "
            "treat the dataset as background-dependent"
            if flag
            else "gap below the pre-declared threshold or CIs overlap"
        ),
    }


def occlusion_saliency(
    classifier: TorchScriptClassifier,
    frame: np.ndarray,
    *,
    patch: int,
    stride: int,
) -> dict[str, Any]:
    """Occlusion sweep in model-input space; returns the raw score-delta grid.

    The patch is zero in normalized space, i.e. the ImageNet mean color, so
    occlusion removes evidence instead of injecting an artificial edge color.
    """

    if patch <= 0 or stride <= 0:
        raise ValueError("patch and stride must be positive")
    torch = classifier.torch
    tensor = classifier._tensor(frame)
    size = classifier.image_size
    if patch > size:
        raise ValueError("patch must not exceed the model input size")

    def reject_probability(batch: Any) -> float:
        with torch.inference_mode():
            probabilities = torch.softmax(classifier.model(batch), dim=1)[0]
        return float(probabilities[classifier.reject_class_index].item())

    baseline = reject_probability(tensor)
    positions = range(0, size - patch + 1, stride)
    grid = [[0.0 for _ in positions] for _ in positions]
    for row, top in enumerate(positions):
        for column, left in enumerate(positions):
            occluded = tensor.clone()
            occluded[:, :, top : top + patch, left : left + patch] = 0.0
            grid[row][column] = baseline - reject_probability(occluded)
    return {"baseline_reject_probability": baseline, "patch": patch, "stride": stride, "grid": grid}


def save_saliency_png(grid: list[list[float]], path: Path, *, upscale: int = 16) -> None:
    from PIL import Image

    deltas = np.asarray(grid, dtype=np.float64)
    span = float(deltas.max() - deltas.min())
    normalized = (deltas - deltas.min()) / span if span > 0 else np.zeros_like(deltas)
    pixels = (normalized * 255.0).round().astype(np.uint8)
    image = Image.fromarray(pixels)
    image = image.resize((pixels.shape[1] * upscale, pixels.shape[0] * upscale), Image.NEAREST)
    image.save(path, format="PNG")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_threshold(args: argparse.Namespace) -> tuple[float, str]:
    if args.threshold is not None:
        return float(args.threshold), "command line"
    artifact = json.loads(args.threshold_artifact.read_text(encoding="utf-8"))
    threshold = artifact.get("operating_threshold")
    if not isinstance(threshold, (int, float)) or not 0.0 <= float(threshold) <= 1.0:
        raise ValueError(f"{args.threshold_artifact} has no valid operating_threshold")
    return float(threshold), str(args.threshold_artifact)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Score plain-background probe images with the frozen classifier and "
            "optionally render occlusion-sensitivity maps. Diagnostics only: "
            "probe results never tune thresholds or enter reported benchmarks."
        )
    )
    parser.add_argument("probe_dir", type=Path, help="directory of <bean_id>.png probe frames")
    parser.add_argument("labels_csv", type=Path, help="blind-labels CSV covering the probe beans")
    parser.add_argument("--model", required=True, type=Path, help="trained model.ts")
    parser.add_argument("--config", required=True, type=Path, help="perception config JSON")
    threshold = parser.add_mutually_exclusive_group(required=True)
    threshold.add_argument("--threshold-artifact", type=Path, help="operating_threshold.json")
    threshold.add_argument("--threshold", type=float, help="explicit frozen operating threshold")
    parser.add_argument("--in-domain-successes", type=int, default=None)
    parser.add_argument("--in-domain-trials", type=int, default=None)
    parser.add_argument("--saliency", type=int, default=0, metavar="N")
    parser.add_argument("--saliency-patch", type=int, default=32)
    parser.add_argument("--saliency-stride", type=int, default=16)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", required=True, type=Path, help="report JSON path")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _reject_probability_from(classifier: TorchScriptClassifier, frame: np.ndarray) -> float:
    result = classifier.classify(frame)
    if result.label is Label.VISIBLE_REJECT:
        return result.confidence
    return 1.0 - result.confidence


def main(
    argv: list[str] | None = None,
    *,
    classifier_factory: Callable[..., TorchScriptClassifier] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.in_domain_successes is None) != (args.in_domain_trials is None):
        parser.error("--in-domain-successes and --in-domain-trials must be supplied together")
    if args.saliency < 0:
        parser.error("--saliency must be >= 0")
    try:
        if args.output.exists() and not args.overwrite:
            raise FileExistsError(f"{args.output} exists; pass --overwrite to replace it")
        threshold_value, threshold_source = _resolve_threshold(args)
        config = load_perception_training_config(args.config)
        labels = load_probe_labels(args.labels_csv)
        images = collect_probe_images(args.probe_dir)
        factory = classifier_factory or TorchScriptClassifier
        classifier = factory(
            args.model,
            config.roi,
            operating_threshold=threshold_value,
            image_size=config.image_size,
            device=args.device,
            input_color_order=config.color_order,
        )
        probe = score_probe(
            images,
            labels,
            lambda frame: _reject_probability_from(classifier, frame),
            operating_threshold=threshold_value,
        )
        verdict = background_dependence_verdict(
            probe["accuracy"], args.in_domain_successes, args.in_domain_trials
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        saliency_entries: list[dict[str, Any]] = []
        for bean_id, path in images[: args.saliency]:
            sweep = occlusion_saliency(
                classifier,
                _load_frame(path),
                patch=args.saliency_patch,
                stride=args.saliency_stride,
            )
            heatmap = args.output.with_name(f"{args.output.stem}_saliency_{bean_id}.png")
            save_saliency_png(sweep["grid"], heatmap)
            saliency_entries.append(
                {
                    "bean_id": bean_id,
                    "heatmap": str(heatmap),
                    "baseline_reject_probability": sweep["baseline_reject_probability"],
                    "delta_min": min(min(row) for row in sweep["grid"]),
                    "delta_max": max(max(row) for row in sweep["grid"]),
                }
            )
        report = {
            "schema_version": "1.0",
            "purpose": "background-dependence diagnostic; never a benchmark",
            "model": {"path": str(args.model), "sha256": _sha256(args.model)},
            "perception_config": {"path": str(args.config), "sha256": _sha256(args.config)},
            "operating_threshold": {"value": threshold_value, "source": threshold_source},
            "probe": probe,
            "background_dependence": verdict,
            "saliency": {
                "patch": args.saliency_patch,
                "stride": args.saliency_stride,
                "images": saliency_entries,
            },
        }
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (FileExistsError, OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
