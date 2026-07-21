import json
from pathlib import Path

import numpy as np
import pytest

from beansight_vn.train_perception import (
    ImageRow,
    ManifestDataset,
    build_parser,
    classifier_eval_tensor,
    load_perception_training_config,
    metrics_at_threshold,
    select_operating_threshold,
    threshold_curve,
    validate_manifest,
)


def row(bean, lot, session, split, label="acceptable"):
    return ImageRow(Path(f"{bean}.jpg"), label, bean, lot, session, split)


def test_manifest_requires_groupwise_split_isolation():
    rows = [
        row("B1", "L1", "S1", "train"),
        row("B1R", "L1", "S1", "train", "visible_reject"),
        row("B2", "L2", "S2", "val"),
        row("B2R", "L2", "S2", "val", "visible_reject"),
        row("B3", "L1", "S3", "test", "visible_reject"),
        row("B3A", "L1", "S3", "test"),
    ]
    with pytest.raises(ValueError, match="lot_id crosses train and test"):
        validate_manifest(rows, check_files=False)


def test_manifest_with_isolated_groups_passes():
    rows = [
        row("B1", "L1", "S1", "train"),
        row("B1R", "L1", "S1", "train", "visible_reject"),
        row("B2", "L1", "S2", "val", "visible_reject"),
        row("B2A", "L1", "S2", "val"),
        row("B3", "L2", "S3", "test"),
        row("B3R", "L2", "S3", "test", "visible_reject"),
    ]
    validate_manifest(rows, check_files=False)


def test_manifest_rejects_empty_ids_and_repeated_beans_or_paths():
    valid = [
        row("B1", "L1", "S1", "train"),
        row("B1R", "L1", "S1", "train", "visible_reject"),
        row("B2", "L1", "S2", "val"),
        row("B2R", "L1", "S2", "val", "visible_reject"),
        row("B3", "L2", "S3", "test"),
        row("B3R", "L2", "S3", "test", "visible_reject"),
    ]
    with pytest.raises(ValueError, match="empty lot_id"):
        invalid = [*valid[:-1], row("B3R", "", "S3", "test", "visible_reject")]
        validate_manifest(invalid, check_files=False)

    repeated_bean = [*valid, row("B1", "L1", "S1", "train")]
    with pytest.raises(ValueError, match="repeats bean_id"):
        validate_manifest(repeated_bean, check_files=False)

    repeated_path = [*valid]
    repeated_path[-1] = ImageRow(
        valid[0].path,
        repeated_path[-1].label,
        repeated_path[-1].bean_id,
        repeated_path[-1].lot_id,
        repeated_path[-1].session_id,
        repeated_path[-1].split,
    )
    with pytest.raises(ValueError, match="repeats image paths"):
        validate_manifest(repeated_path, check_files=False)


def test_threshold_curve_exposes_false_accept_tradeoff():
    curve = threshold_curve([0, 1], [0.6, 0.7], thresholds=[0.5, 0.65, 0.8])
    assert curve[0]["false_reject_rate"] == 1.0
    assert curve[1]["false_accept_rate"] == 0.0
    assert curve[2]["false_accept_rate"] == 1.0


def test_operating_threshold_comes_from_validation_curve_tie_breaks_fail_still():
    curve = [
        {"threshold": 0.5, "macro_f1": 0.8, "false_accept_rate": 0.2},
        {"threshold": 0.6, "macro_f1": 0.8, "false_accept_rate": 0.1},
        {"threshold": 0.7, "macro_f1": 0.8, "false_accept_rate": 0.1},
    ]

    assert select_operating_threshold(curve) == 0.7


def test_fixed_threshold_metrics_do_not_expose_test_tuning_setting():
    metrics = metrics_at_threshold([0, 1], [0.2, 0.7], threshold=0.65)

    assert metrics["threshold"] == 0.65
    assert metrics["macro_f1"] == 1.0
    assert "best_macro_f1_threshold" not in metrics
    assert "threshold_curve" not in metrics


def test_perception_config_loads_full_frame_roi_and_image_size(tmp_path):
    config = tmp_path / "perception.json"
    config.write_text(
        json.dumps(
            {
                "color_order": "RGB",
                "roi": {"x": 160, "y": 80, "width": 320, "height": 320},
                "transfer_model": {
                    "architecture": "resnet18",
                    "image_size": 224,
                    "classes": ["acceptable", "visible_reject"],
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_perception_training_config(config)

    assert loaded.roi.as_tuple() == (160, 80, 320, 320)
    assert loaded.image_size == 224
    assert loaded.color_order == "RGB"
    assert loaded.architecture == "resnet18"


@pytest.mark.parametrize(
    ("roi", "image_size", "message"),
    [
        ({"x": 160.5, "y": 80, "width": 320, "height": 320}, 224, "invalid"),
        ({"x": 400, "y": 80, "width": 320, "height": 320}, 224, "640x480"),
        ({"x": 160, "y": 80, "width": 320, "height": 320}, True, "invalid"),
    ],
)
def test_perception_config_rejects_coerced_or_out_of_frame_values(
    tmp_path, roi, image_size, message
):
    config = tmp_path / "perception.json"
    config.write_text(
        json.dumps(
            {
                "color_order": "RGB",
                "roi": roi,
                "transfer_model": {
                    "architecture": "resnet18",
                    "image_size": image_size,
                    "classes": ["acceptable", "visible_reject"],
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_perception_training_config(config)


def test_cli_requires_dataset_revision():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["manifest.csv"])

    parsed = build_parser().parse_args(
        ["manifest.csv", "--dataset-revision", "local:sha256-deadbeef"]
    )
    assert parsed.dataset_revision == "local:sha256-deadbeef"


def test_manifest_eval_and_runtime_preprocessing_are_tensor_identical(tmp_path):
    torch = pytest.importorskip("torch")
    image_module = pytest.importorskip("PIL.Image")

    config = load_perception_training_config(
        Path(__file__).parents[1] / "configs" / "perception.json"
    )
    frame = np.arange(480 * 640 * 3, dtype=np.uint8).reshape(480, 640, 3)
    image_path = tmp_path / "full-c920-frame.png"
    image_module.fromarray(frame).save(image_path)
    dataset = ManifestDataset(
        [ImageRow(image_path, "acceptable", "B001", "L001", "S001", "val")],
        lambda image: classifier_eval_tensor(image, config),
    )
    manifest_tensor, _label = dataset[0]

    from beansight_vn.perception import TorchScriptClassifier

    runtime = object.__new__(TorchScriptClassifier)
    runtime.roi = config.roi
    runtime.image_size = config.image_size
    runtime.device = "cpu"
    runtime.input_color_order = config.color_order
    runtime_tensor = runtime._tensor(frame)

    torch.testing.assert_close(
        manifest_tensor.unsqueeze(0), runtime_tensor, rtol=0.0, atol=0.0
    )
