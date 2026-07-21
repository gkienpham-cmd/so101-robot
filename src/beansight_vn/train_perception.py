from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .metrics import percentile
from .models import Label
from .perception import Roi, classifier_image_crop, classifier_tensor

CLASS_TO_INDEX = {Label.ACCEPTABLE.value: 0, Label.VISIBLE_REJECT.value: 1}
REQUIRED_COLUMNS = {"path", "label", "bean_id", "lot_id", "session_id", "split"}
DEFAULT_PERCEPTION_CONFIG = Path("configs/perception.json")


@dataclass(frozen=True, slots=True)
class ImageRow:
    path: Path
    label: str
    bean_id: str
    lot_id: str
    session_id: str
    split: str


@dataclass(frozen=True, slots=True)
class PerceptionTrainingConfig:
    roi: Roi
    image_size: int
    color_order: str
    architecture: str


def load_perception_training_config(path: Path) -> PerceptionTrainingConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read perception training config: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"invalid perception training config: {path}")
    try:
        roi_raw = raw["roi"]
        transfer = raw["transfer_model"]
        if not isinstance(roi_raw, dict) or not isinstance(transfer, dict):
            raise TypeError
        roi_values = [roi_raw[field] for field in ("x", "y", "width", "height")]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in roi_values):
            raise TypeError
        raw_image_size = transfer["image_size"]
        if isinstance(raw_image_size, bool) or not isinstance(raw_image_size, int):
            raise TypeError
        roi = Roi(
            x=roi_values[0],
            y=roi_values[1],
            width=roi_values[2],
            height=roi_values[3],
        )
        image_size = raw_image_size
        architecture = str(transfer["architecture"])
        color_order = str(raw["color_order"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid perception training config: {path}") from exc
    if min(roi.x, roi.y, roi.width, roi.height) < 0 or roi.width == 0 or roi.height == 0:
        raise ValueError(
            "perception ROI must have non-negative coordinates and positive dimensions"
        )
    if roi.x + roi.width > 640 or roi.y + roi.height > 480:
        raise ValueError("perception ROI must fit within a full 640x480 C920 frame")
    if image_size <= 0:
        raise ValueError("transfer_model.image_size must be positive")
    if color_order != "RGB":
        raise ValueError("training config color_order must be RGB for saved C920 images")
    classes = transfer.get("classes")
    if classes != list(CLASS_TO_INDEX):
        raise ValueError(f"transfer_model.classes must be {list(CLASS_TO_INDEX)}")
    if architecture not in {"resnet18", "mobilenet_v3_small"}:
        raise ValueError("transfer_model.architecture is unsupported")
    return PerceptionTrainingConfig(
        roi=roi,
        image_size=image_size,
        color_order=color_order,
        architecture=architecture,
    )


def classifier_eval_tensor(
    image: Any,
    preprocessing: PerceptionTrainingConfig,
    *,
    device: str = "cpu",
) -> Any:
    """Apply the deterministic manifest/runtime classifier preprocessing."""

    return classifier_tensor(
        image,
        preprocessing.roi,
        image_size=preprocessing.image_size,
        device=device,
        input_color_order=preprocessing.color_order,
    ).squeeze(0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[ImageRow]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"manifest is missing columns: {sorted(missing)}")
        rows = [
            ImageRow(
                path=(path.parent / str(row["path"] or "").strip()).resolve(),
                label=str(row["label"] or "").strip(),
                bean_id=str(row["bean_id"] or "").strip(),
                lot_id=str(row["lot_id"] or "").strip(),
                session_id=str(row["session_id"] or "").strip(),
                split=str(row["split"] or "").strip().lower(),
            )
            for row in reader
        ]
    validate_manifest(rows)
    return rows


def validate_manifest(rows: list[ImageRow], *, check_files: bool = True) -> None:
    if not rows:
        raise ValueError("manifest contains no images")
    for index, row in enumerate(rows, start=1):
        for field in ("label", "bean_id", "lot_id", "session_id", "split"):
            if not getattr(row, field).strip():
                raise ValueError(f"manifest row {index} has an empty {field}")
    repeated_beans = sorted(
        bean_id for bean_id, count in Counter(row.bean_id for row in rows).items() if count > 1
    )
    if repeated_beans:
        raise ValueError(f"manifest repeats bean_id: {repeated_beans[:10]}")
    repeated_paths = sorted(
        str(path) for path, count in Counter(row.path for row in rows).items() if count > 1
    )
    if repeated_paths:
        raise ValueError(f"manifest repeats image paths: {repeated_paths[:10]}")
    invalid_labels = sorted({row.label for row in rows} - set(CLASS_TO_INDEX))
    if invalid_labels:
        raise ValueError(f"unknown labels: {invalid_labels}")
    invalid_splits = sorted({row.split for row in rows} - {"train", "val", "test"})
    if invalid_splits:
        raise ValueError(f"unknown splits: {invalid_splits}")
    absent = {"train", "val", "test"} - {row.split for row in rows}
    if absent:
        raise ValueError(f"manifest must include train/val/test; missing {sorted(absent)}")
    for split in ("train", "val", "test"):
        split_labels = {row.label for row in rows if row.split == split}
        missing_labels = set(CLASS_TO_INDEX) - split_labels
        if missing_labels:
            raise ValueError(f"{split} split is missing labels: {sorted(missing_labels)}")

    # A bean or capture session in two splits would let nearly identical
    # workcell images leak into evaluation.
    for field in ("bean_id", "session_id"):
        splits: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            splits[getattr(row, field)].add(row.split)
        leaked = sorted(key for key, values in splits.items() if len(values) > 1)
        if leaked:
            preview = leaked[:10]
            raise ValueError(f"{field} crosses dataset splits: {preview}")
    train_lots = {row.lot_id for row in rows if row.split == "train"}
    test_lots = {row.lot_id for row in rows if row.split == "test"}
    shared_train_test_lots = sorted(train_lots & test_lots)
    if shared_train_test_lots:
        raise ValueError(f"lot_id crosses train and test splits: {shared_train_test_lots}")
    if check_files:
        missing_files = [str(row.path) for row in rows if not row.path.is_file()]
        if missing_files:
            raise ValueError(f"manifest references missing files: {missing_files[:10]}")


class ManifestDataset:
    def __init__(self, rows: list[ImageRow], transform: Callable[[Any], Any]) -> None:
        self.rows = rows
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[Any, int]:
        from PIL import Image

        row = self.rows[index]
        with Image.open(row.path) as image:
            rgb = image.convert("RGB")
        return self.transform(rgb), CLASS_TO_INDEX[row.label]


def _classification_summary(actual: list[int], predicted: list[int]) -> dict[str, Any]:
    matrix = [[0, 0], [0, 0]]
    for truth, prediction in zip(actual, predicted, strict=True):
        matrix[truth][prediction] += 1
    classes: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label, index in CLASS_TO_INDEX.items():
        tp = matrix[index][index]
        fp = sum(matrix[row][index] for row in range(2) if row != index)
        fn = sum(matrix[index][column] for column in range(2) if column != index)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_values.append(f1)
        classes[label] = {
            "support": sum(matrix[index]),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    acceptable, reject = 0, 1
    return {
        "confusion_matrix": matrix,
        "per_class": classes,
        "macro_f1": sum(f1_values) / 2,
        "false_accept_rate": matrix[reject][acceptable] / sum(matrix[reject])
        if sum(matrix[reject])
        else 0.0,
        "false_reject_rate": matrix[acceptable][reject] / sum(matrix[acceptable])
        if sum(matrix[acceptable])
        else 0.0,
    }


def threshold_curve(
    actual: list[int], reject_probabilities: list[float], thresholds: list[float] | None = None
) -> list[dict[str, float]]:
    if len(actual) != len(reject_probabilities):
        raise ValueError("labels and probabilities must have the same length")
    thresholds = thresholds or [index / 20 for index in range(1, 20)]
    curve: list[dict[str, float]] = []
    for threshold in thresholds:
        summary = metrics_at_threshold(actual, reject_probabilities, threshold)
        curve.append(
            {
                "threshold": threshold,
                "macro_f1": float(summary["macro_f1"]),
                "false_accept_rate": float(summary["false_accept_rate"]),
                "false_reject_rate": float(summary["false_reject_rate"]),
            }
        )
    return curve


def metrics_at_threshold(
    actual: list[int], reject_probabilities: list[float], threshold: float
) -> dict[str, Any]:
    if len(actual) != len(reject_probabilities):
        raise ValueError("labels and probabilities must have the same length")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    predicted = [int(probability >= threshold) for probability in reject_probabilities]
    summary = _classification_summary(actual, predicted)
    summary["threshold"] = threshold
    return summary


def select_operating_threshold(curve: list[dict[str, float]]) -> float:
    if not curve:
        raise ValueError("validation threshold curve is empty")
    required = {"threshold", "macro_f1", "false_accept_rate"}
    if any(required - set(point) for point in curve):
        raise ValueError("validation threshold curve is missing required metrics")
    selected = max(
        curve,
        key=lambda point: (
            point["macro_f1"],
            -point["false_accept_rate"],
            point["threshold"],
        ),
    )
    return float(selected["threshold"])


def _evaluate(
    model: Any,
    loader: Any,
    device: str,
    *,
    threshold: float = 0.5,
    include_threshold_curve: bool = False,
) -> tuple[float, dict[str, Any]]:
    import torch

    model.eval()
    loss_fn = torch.nn.CrossEntropyLoss()
    total_loss = 0.0
    actual: list[int] = []
    reject_probabilities: list[float] = []
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            total_loss += float(loss_fn(logits, labels).item()) * len(labels)
            probabilities = torch.softmax(logits, dim=1)
            actual.extend(labels.cpu().tolist())
            reject_probabilities.extend(probabilities[:, 1].cpu().tolist())
    metrics = metrics_at_threshold(actual, reject_probabilities, threshold)
    metrics["loss"] = total_loss / len(actual) if actual else 0.0
    if include_threshold_curve:
        metrics["threshold_curve"] = threshold_curve(actual, reject_probabilities)
    return float(metrics["macro_f1"]), metrics


def _build_model(architecture: str, pretrained: bool) -> Any:
    import torch
    from torchvision import models

    if architecture == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        model.fc = torch.nn.Linear(model.fc.in_features, 2)
        return model
    if architecture == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)
        model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, 2)
        return model
    raise ValueError(f"unsupported architecture: {architecture}")


def train(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from torch.utils.data import DataLoader
    from torchvision import transforms

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = read_manifest(args.manifest)
    by_split = {
        name: [row for row in rows if row.split == name] for name in ("train", "val", "test")
    }
    config_path = Path(getattr(args, "config", DEFAULT_PERCEPTION_CONFIG))
    preprocessing = load_perception_training_config(config_path)
    dataset_revision = str(getattr(args, "dataset_revision", "")).strip()
    if not dataset_revision:
        raise ValueError(
            "--dataset-revision is required; use an immutable Hub revision "
            "or explicit local identity"
        )
    requested_image_size = getattr(args, "image_size", None)
    if requested_image_size is not None and requested_image_size != preprocessing.image_size:
        raise ValueError(
            "--image-size must match transfer_model.image_size in the perception config"
        )
    architecture = getattr(args, "architecture", None) or preprocessing.architecture

    # Crop the full C920 frame before any augmentation. Evaluation and runtime
    # both call classifier_tensor directly, giving one deterministic path for
    # ROI, resize, RGB conversion, and ImageNet normalization.
    crop_roi = Roi(0, 0, preprocessing.roi.width, preprocessing.roi.height)
    train_augmentation = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(8),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
        ]
    )

    def train_transform(image: Any) -> Any:
        crop = classifier_image_crop(
            image, preprocessing.roi, input_color_order=preprocessing.color_order
        )
        augmented = train_augmentation(crop)
        return classifier_tensor(
            augmented,
            crop_roi,
            image_size=preprocessing.image_size,
            device="cpu",
            input_color_order="RGB",
        ).squeeze(0)

    def eval_transform(image: Any) -> Any:
        return classifier_eval_tensor(image, preprocessing)

    datasets = {
        "train": ManifestDataset(by_split["train"], train_transform),
        "val": ManifestDataset(by_split["val"], eval_transform),
        "test": ManifestDataset(by_split["test"], eval_transform),
    }
    loaders = {
        name: DataLoader(
            dataset,
            batch_size=args.batch_size,
            shuffle=name == "train",
            num_workers=args.workers,
        )
        for name, dataset in datasets.items()
    }

    device = args.device
    if device == "auto":
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
    model = _build_model(architecture, not args.no_pretrained).to(device)
    counts = Counter(CLASS_TO_INDEX[row.label] for row in by_split["train"])
    class_weights = torch.tensor(
        [len(by_split["train"]) / (2 * counts[index]) for index in range(2)],
        dtype=torch.float32,
        device=device,
    )
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)

    args.output.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    best_f1 = -1.0
    best_state: dict[str, Any] | None = None
    selected_epoch: int | None = None
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: list[float] = []
        for images, labels in loaders["train"]:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(images), labels)
            if not torch.isfinite(loss):
                raise RuntimeError("training loss is NaN or Inf; aborting")
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))
        val_f1, val_metrics = _evaluate(model, loaders["val"], device, threshold=0.5)
        history.append(
            {
                "epoch": epoch,
                "train_loss_median": percentile(train_losses, 0.5),
                "validation": val_metrics,
            }
        )
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_state = {
                key: value.detach().cpu().clone() for key, value in model.state_dict().items()
            }
            selected_epoch = epoch

    if best_state is None or selected_epoch is None:
        raise RuntimeError("training produced no checkpoint")
    model.load_state_dict(best_state)
    model.to(device)
    _, selected_validation = _evaluate(
        model,
        loaders["val"],
        device,
        threshold=0.5,
        include_threshold_curve=True,
    )
    operating_threshold = select_operating_threshold(selected_validation["threshold_curve"])
    _, test_metrics = _evaluate(
        model,
        loaders["test"],
        device,
        threshold=operating_threshold,
    )
    torch.save(best_state, args.output / "model_state.pt")
    example = torch.zeros(
        1, 3, preprocessing.image_size, preprocessing.image_size, device=device
    )
    scripted = torch.jit.trace(model.eval(), example)
    scripted.save(str(args.output / "model.ts"))

    provenance = {
        "schema_version": "1.0",
        "dataset_revision": dataset_revision,
        "manifest": str(args.manifest),
        "manifest_sha256": _sha256(args.manifest),
        "perception_config": str(config_path),
        "perception_config_sha256": _sha256(config_path),
        "roi": {
            "x": preprocessing.roi.x,
            "y": preprocessing.roi.y,
            "width": preprocessing.roi.width,
            "height": preprocessing.roi.height,
        },
        "image_size": preprocessing.image_size,
        "color_order": preprocessing.color_order,
        "selected_epoch": selected_epoch,
        "checkpoint_selection": "validation_macro_f1_at_threshold_0.5",
        "operating_threshold": operating_threshold,
        "threshold_source": "selected_checkpoint_validation_curve",
        "seed": args.seed,
    }
    threshold_artifact = {
        "schema_version": "1.0",
        "operating_threshold": operating_threshold,
        "source_split": "val",
        "selected_epoch": selected_epoch,
        "dataset_revision": dataset_revision,
        "manifest_sha256": provenance["manifest_sha256"],
        "perception_config_sha256": provenance["perception_config_sha256"],
    }
    result = {
        "schema_version": "1.0",
        "architecture": architecture,
        "pretrained": not args.no_pretrained,
        "seed": args.seed,
        "device": device,
        "dataset_revision": dataset_revision,
        "class_to_index": CLASS_TO_INDEX,
        "preprocessing": {
            "roi": provenance["roi"],
            "image_size": preprocessing.image_size,
            "color_order": preprocessing.color_order,
        },
        "counts": {
            split: Counter(row.label for row in split_rows)
            for split, split_rows in by_split.items()
        },
        "history": history,
        "selected_epoch": selected_epoch,
        "validation": selected_validation,
        "operating_threshold": operating_threshold,
        "test": test_metrics,
        "provenance": provenance,
        "artifacts": {
            "torchscript": "model.ts",
            "state_dict": "model_state.pt",
            "operating_threshold": "operating_threshold.json",
            "provenance": "provenance.json",
        },
    }
    (args.output / "operating_threshold.json").write_text(
        json.dumps(threshold_artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "metrics.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the BeanSight two-class transfer baseline.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/perception/resnet18"))
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_PERCEPTION_CONFIG,
        help="Perception config that freezes the C920 ROI and transfer-model image size",
    )
    parser.add_argument(
        "--dataset-revision",
        required=True,
        help="Immutable dataset revision or local dataset identity recorded in provenance",
    )
    parser.add_argument(
        "--architecture",
        choices=("resnet18", "mobilenet_v3_small"),
        help="Override the architecture named by the perception config",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        help="Compatibility check only; must equal transfer_model.image_size in --config",
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--no-pretrained", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = train(args)
    print(json.dumps(result["test"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
