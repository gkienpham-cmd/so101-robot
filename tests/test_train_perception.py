from pathlib import Path

import pytest

from beansight_vn.train_perception import ImageRow, threshold_curve, validate_manifest


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


def test_threshold_curve_exposes_false_accept_tradeoff():
    curve = threshold_curve([0, 1], [0.6, 0.7], thresholds=[0.5, 0.65, 0.8])
    assert curve[0]["false_reject_rate"] == 1.0
    assert curve[1]["false_accept_rate"] == 0.0
    assert curve[2]["false_accept_rate"] == 1.0
