import json
from contextlib import nullcontext

import numpy as np
import pytest
from PIL import Image

from beansight_vn.metrics import wilson_interval
from beansight_vn.models import Label, PerceptionResult
from beansight_vn.perception_probe import (
    background_dependence_verdict,
    collect_probe_images,
    load_probe_labels,
    main,
    occlusion_saliency,
    save_saliency_png,
    score_probe,
)

LABEL_COLUMNS = "bean_id,lot_id,grader_label,visible_defect_type,ambiguous,grader_notes,reviewed_at"


def _write_labels(path, rows):
    path.write_text(LABEL_COLUMNS + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def _write_probe_png(path, *, size=(640, 480), mode="RGB", value=120):
    fill = (value, value, value) if mode == "RGB" else value
    Image.new(mode, size, fill).save(path, format="PNG")


def test_load_probe_labels_skips_ambiguous_and_validates(tmp_path):
    labels_csv = tmp_path / "labels.csv"
    _write_labels(
        labels_csv,
        [
            "B001,LOT_A,acceptable,,false,,2026-07-21",
            "B002,LOT_A,visible_reject,black,false,,2026-07-21",
            "B003,LOT_A,visible_reject,broken,true,,2026-07-21",
        ],
    )
    labels = load_probe_labels(labels_csv)
    assert labels == {"B001": "acceptable", "B002": "visible_reject"}

    _write_labels(labels_csv, ["B001,LOT_A,maybe_fine,,false,,2026-07-21"])
    with pytest.raises(ValueError, match="unsupported grader_label"):
        load_probe_labels(labels_csv)

    _write_labels(labels_csv, ["B001,LOT_A,acceptable,,true,,2026-07-21"])
    with pytest.raises(ValueError, match="no unambiguous scored labels"):
        load_probe_labels(labels_csv)

    (tmp_path / "short.csv").write_text("bean_id,grader_label\nB001,acceptable\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_probe_labels(tmp_path / "short.csv")


def test_collect_probe_images_rejects_wrong_size_naming_the_file(tmp_path):
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    _write_probe_png(probe_dir / "B001.png")
    _write_probe_png(probe_dir / "B002.png", size=(320, 240))
    with pytest.raises(ValueError, match="B002.png"):
        collect_probe_images(probe_dir)

    (probe_dir / "B002.png").unlink()
    _write_probe_png(probe_dir / "B003.png", mode="L")
    with pytest.raises(ValueError, match="B003.png"):
        collect_probe_images(probe_dir)

    (probe_dir / "B003.png").unlink()
    assert [bean_id for bean_id, _ in collect_probe_images(probe_dir)] == ["B001"]

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no PNG images"):
        collect_probe_images(empty)


def test_score_probe_reports_wilson_and_error_split(tmp_path):
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    for bean_id in ("A1", "A2", "R1", "R2"):
        _write_probe_png(probe_dir / f"{bean_id}.png")
    images = collect_probe_images(probe_dir)
    labels = {
        "A1": "acceptable",
        "A2": "acceptable",
        "R1": "visible_reject",
        "R2": "visible_reject",
    }
    scores = {"A1": 0.1, "A2": 0.9, "R1": 0.8, "R2": 0.2}
    calls = iter([scores[bean_id] for bean_id, _ in images])
    summary = score_probe(images, labels, lambda _frame: next(calls), operating_threshold=0.5)
    assert summary["accuracy"]["successes"] == 2
    assert summary["accuracy"]["trials"] == 4
    assert summary["accuracy"]["wilson_95"] == list(wilson_interval(2, 4))
    assert summary["false_accepts"] == 1
    assert summary["false_rejects"] == 1

    with pytest.raises(ValueError, match="without an unambiguous label"):
        score_probe(images, {"A1": "acceptable"}, lambda _frame: 0.5, operating_threshold=0.5)


def test_background_dependence_verdict_applies_predeclared_gate():
    deferred = background_dependence_verdict({"rate": 0.5, "wilson_95": [0.3, 0.7]}, None, None)
    assert deferred["flag"] is None

    probe = {"rate": 12 / 30, "wilson_95": list(wilson_interval(12, 30))}
    flagged = background_dependence_verdict(probe, 55, 60)
    assert flagged["flag"] is True
    assert flagged["gap"] >= 0.15

    near = {"rate": 50 / 60, "wilson_95": list(wilson_interval(50, 60))}
    unflagged = background_dependence_verdict(near, 55, 60)
    assert unflagged["flag"] is False


def test_save_saliency_png_normalizes_grid(tmp_path):
    out = tmp_path / "map.png"
    save_saliency_png([[0.0, 0.5], [1.0, 0.25]], out, upscale=2)
    with Image.open(out) as image:
        assert image.mode == "L"
        assert image.size == (4, 4)
        pixels = np.asarray(image)
    assert pixels.max() == 255
    assert pixels.min() == 0


class _FakeScalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class _FakeTensor:
    def __init__(self, array):
        self.array = array

    def clone(self):
        return _FakeTensor(self.array.copy())

    def __setitem__(self, key, value):
        self.array[key] = value


class _FakeTorch:
    @staticmethod
    def inference_mode():
        return nullcontext()

    @staticmethod
    def softmax(tensor, *, dim):
        assert dim == 1
        probability = float(np.clip(tensor.array.mean(), 0.0, 1.0))
        return [[_FakeScalar(1.0 - probability), _FakeScalar(probability)]]


class _FakeClassifier:
    """Stands in for TorchScriptClassifier without torch installed."""

    def __init__(
        self, model_path, roi, *, operating_threshold, image_size, device, input_color_order
    ):
        assert input_color_order == "RGB"
        self.roi = roi
        self.operating_threshold = operating_threshold
        self.image_size = image_size
        self.reject_class_index = 1
        self.torch = _FakeTorch()
        self.model = lambda tensor: tensor

    def _tensor(self, frame):
        return _FakeTensor(np.full((1, 3, self.image_size, self.image_size), 0.5))

    def classify(self, frame, *, frame_id=None, session_id=None):
        # Deterministic per-frame score: darker probe frames read as rejects.
        reject_probability = float(np.asarray(frame).mean() / 255.0)
        rejected = reject_probability >= self.operating_threshold
        return PerceptionResult(
            label=Label.VISIBLE_REJECT if rejected else Label.ACCEPTABLE,
            confidence=reject_probability if rejected else 1.0 - reject_probability,
        )


def test_occlusion_saliency_grid_shape_and_baseline():
    classifier = _FakeClassifier(
        "model.ts",
        None,
        operating_threshold=0.5,
        image_size=64,
        device="cpu",
        input_color_order="RGB",
    )
    sweep = occlusion_saliency(classifier, np.zeros((480, 640, 3)), patch=32, stride=16)
    assert sweep["baseline_reject_probability"] == pytest.approx(0.5)
    assert len(sweep["grid"]) == 3
    assert all(len(row) == 3 for row in sweep["grid"])
    assert all(delta > 0 for row in sweep["grid"] for delta in row)


def _cli_workspace(tmp_path):
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    _write_probe_png(probe_dir / "B001.png", value=30)  # bright-mean 30/255 -> acceptable
    _write_probe_png(probe_dir / "B002.png", value=220)  # dark logic inverted: reject
    labels_csv = tmp_path / "labels.csv"
    _write_labels(
        labels_csv,
        [
            "B001,LOT_A,acceptable,,false,,2026-07-21",
            "B002,LOT_A,visible_reject,black,false,,2026-07-21",
        ],
    )
    model = tmp_path / "model.ts"
    model.write_bytes(b"stub torchscript bytes")
    config = tmp_path / "perception.json"
    config.write_text(
        json.dumps(
            {
                "color_order": "RGB",
                "roi": {"x": 160, "y": 80, "width": 320, "height": 320},
                "transfer_model": {
                    "architecture": "resnet18",
                    "image_size": 64,
                    "classes": ["acceptable", "visible_reject"],
                },
            }
        ),
        encoding="utf-8",
    )
    threshold = tmp_path / "operating_threshold.json"
    threshold.write_text(json.dumps({"operating_threshold": 0.5}), encoding="utf-8")
    return probe_dir, labels_csv, model, config, threshold


def test_cli_writes_full_report_with_saliency(tmp_path):
    probe_dir, labels_csv, model, config, threshold = _cli_workspace(tmp_path)
    output = tmp_path / "reports" / "probe_report.json"
    exit_code = main(
        [
            str(probe_dir),
            str(labels_csv),
            "--model",
            str(model),
            "--config",
            str(config),
            "--threshold-artifact",
            str(threshold),
            "--in-domain-successes",
            "55",
            "--in-domain-trials",
            "60",
            "--saliency",
            "1",
            "--output",
            str(output),
        ],
        classifier_factory=_FakeClassifier,
    )
    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["operating_threshold"] == {"value": 0.5, "source": str(threshold)}
    assert report["probe"]["accuracy"] == {
        "successes": 2,
        "trials": 2,
        "rate": 1.0,
        "wilson_95": list(wilson_interval(2, 2)),
    }
    assert [row["bean_id"] for row in report["probe"]["per_image"]] == ["B001", "B002"]
    assert report["background_dependence"]["flag"] is False
    assert len(report["saliency"]["images"]) == 1
    heatmap = tmp_path / "reports" / "probe_report_saliency_B001.png"
    assert heatmap.exists()
    assert report["saliency"]["images"][0]["heatmap"] == str(heatmap)
    assert len(report["model"]["sha256"]) == 64


def test_cli_rejects_bad_image_without_writing_report(tmp_path):
    probe_dir, labels_csv, model, config, threshold = _cli_workspace(tmp_path)
    _write_probe_png(probe_dir / "B999.png", size=(100, 100))
    output = tmp_path / "probe_report.json"
    with pytest.raises(SystemExit):
        main(
            [
                str(probe_dir),
                str(labels_csv),
                "--model",
                str(model),
                "--config",
                str(config),
                "--threshold-artifact",
                str(threshold),
                "--output",
                str(output),
            ],
            classifier_factory=_FakeClassifier,
        )
    assert not output.exists()


def test_cli_refuses_overwrite_and_pairs_in_domain_flags(tmp_path):
    probe_dir, labels_csv, model, config, threshold = _cli_workspace(tmp_path)
    output = tmp_path / "probe_report.json"
    output.write_text("{}", encoding="utf-8")
    base_args = [
        str(probe_dir),
        str(labels_csv),
        "--model",
        str(model),
        "--config",
        str(config),
        "--threshold-artifact",
        str(threshold),
        "--output",
        str(output),
    ]
    with pytest.raises(SystemExit):
        main(base_args, classifier_factory=_FakeClassifier)
    assert output.read_text(encoding="utf-8") == "{}"

    with pytest.raises(SystemExit):
        main(
            base_args + ["--overwrite", "--in-domain-successes", "55"],
            classifier_factory=_FakeClassifier,
        )

    assert main(base_args + ["--overwrite"], classifier_factory=_FakeClassifier) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["background_dependence"]["flag"] is None
