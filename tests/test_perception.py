import numpy as np
import pytest

from beansight_vn.models import Label
from beansight_vn.perception import DarkPixelBaseline, Roi


def test_roi_bounds_are_enforced():
    with pytest.raises(ValueError, match="outside"):
        Roi(9, 9, 2, 2).crop(np.ones((10, 10, 3)))


def test_dark_pixel_baseline_has_declared_binary_behavior():
    classifier = DarkPixelBaseline(Roi(0, 0, 10, 10), luminance_threshold=50, reject_fraction=0.2)
    dark = np.zeros((10, 10, 3), dtype=np.uint8)
    bright = np.full((10, 10, 3), 200, dtype=np.uint8)
    assert classifier.classify(dark).label is Label.VISIBLE_REJECT
    assert classifier.classify(bright).label is Label.ACCEPTABLE
