from contextlib import nullcontext

import numpy as np
import pytest

from beansight_vn.models import Label
from beansight_vn.perception import (
    DarkPixelBaseline,
    Roi,
    TorchScriptClassifier,
    classifier_image_crop,
)


def test_roi_bounds_are_enforced():
    with pytest.raises(ValueError, match="outside"):
        Roi(9, 9, 2, 2).crop(np.ones((10, 10, 3)))


def test_dark_pixel_baseline_has_declared_binary_behavior():
    classifier = DarkPixelBaseline(Roi(0, 0, 10, 10), luminance_threshold=50, reject_fraction=0.2)
    dark = np.zeros((10, 10, 3), dtype=np.uint8)
    bright = np.full((10, 10, 3), 200, dtype=np.uint8)
    assert classifier.classify(dark).label is Label.VISIBLE_REJECT
    assert classifier.classify(bright).label is Label.ACCEPTABLE


def test_classifier_crop_is_shared_rgb_byte_contract():
    frame = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)
    roi = Roi(1, 1, 3, 2)

    rgb = classifier_image_crop(frame, roi)
    bgr = classifier_image_crop(frame[..., ::-1], roi, input_color_order="BGR")

    expected = np.ascontiguousarray(frame[1:3, 1:4, :3])
    assert rgb.flags.c_contiguous
    assert rgb.tobytes() == expected.tobytes()
    assert bgr.tobytes() == expected.tobytes()


class _FakeScalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class _FakeTorch:
    @staticmethod
    def inference_mode():
        return nullcontext()

    @staticmethod
    def softmax(_logits, *, dim):
        assert dim == 1
        return [[_FakeScalar(0.35), _FakeScalar(0.65)]]


def test_torchscript_classifier_uses_frozen_operating_threshold():
    classifier = object.__new__(TorchScriptClassifier)
    classifier.torch = _FakeTorch()
    classifier.model = lambda _tensor: object()
    classifier.roi = Roi(0, 0, 1, 1)
    classifier.reject_class_index = 1
    classifier._tensor = lambda _frame: object()

    classifier.operating_threshold = 0.7
    assert classifier.classify(object()).label is Label.ACCEPTABLE

    classifier.operating_threshold = 0.6
    result = classifier.classify(object())
    assert result.label is Label.VISIBLE_REJECT
    assert result.confidence == pytest.approx(0.65)


def test_torchscript_classifier_requires_frozen_operating_threshold():
    with pytest.raises(TypeError, match="operating_threshold"):
        TorchScriptClassifier("model.ts", Roi(0, 0, 1, 1))
