from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .models import Label, PerceptionResult

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


@dataclass(frozen=True, slots=True)
class Roi:
    x: int
    y: int
    width: int
    height: int

    def crop(self, frame: np.ndarray) -> np.ndarray:
        if min(self.x, self.y, self.width, self.height) < 0 or self.width == 0 or self.height == 0:
            raise ValueError("ROI must have non-negative coordinates and positive dimensions")
        if self.x + self.width > frame.shape[1] or self.y + self.height > frame.shape[0]:
            raise ValueError(f"ROI {self} is outside frame shape {frame.shape}")
        return frame[self.y : self.y + self.height, self.x : self.x + self.width]

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


def classifier_image_crop(
    frame: Any,
    roi: Roi,
    *,
    input_color_order: str = "RGB",
) -> np.ndarray:
    """Return the contiguous RGB crop shared by training and runtime inference."""

    image = np.asarray(frame)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError(f"expected H×W×3 image, got shape {image.shape}")
    if input_color_order not in {"RGB", "BGR"}:
        raise ValueError("input_color_order must be RGB or BGR")
    crop = roi.crop(image[..., :3])
    if input_color_order == "BGR":
        crop = crop[..., ::-1]
    # PIL-backed arrays can be read-only. Own a writable, contiguous copy so
    # torch.from_numpy never inherits a non-writable buffer.
    return np.array(crop, copy=True, order="C")


def classifier_tensor(
    frame: Any,
    roi: Roi,
    *,
    image_size: int = 224,
    device: str = "cpu",
    input_color_order: str = "RGB",
) -> Any:
    """Crop, resize, and normalize one classifier frame.

    Torch remains an optional dependency: importing :mod:`beansight_vn.perception`
    does not import it. Both the manifest evaluator and ``TorchScriptClassifier``
    call this function so their deterministic preprocessing cannot drift apart.
    """

    if image_size <= 0:
        raise ValueError("image_size must be positive")
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install the perception extra: pip install -e '.[perception]'") from exc

    image = classifier_image_crop(frame, roi, input_color_order=input_color_order)
    tensor = torch.from_numpy(image).permute(2, 0, 1).float().div(255.0).unsqueeze(0)
    tensor = torch.nn.functional.interpolate(
        tensor, size=(image_size, image_size), mode="bilinear", align_corners=False
    )
    mean = torch.tensor(IMAGENET_MEAN, dtype=tensor.dtype).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD, dtype=tensor.dtype).view(1, 3, 1, 1)
    return ((tensor - mean) / std).to(device)


class DarkPixelBaseline:
    """A deliberately simple, calibrated color baseline for black defects.

    It is not a food-safety detector. The thresholds must be calibrated under
    the fixed BeanSight lamp and inspection nest.
    """

    def __init__(
        self,
        roi: Roi,
        *,
        luminance_threshold: float,
        reject_fraction: float,
    ) -> None:
        if not 0 <= luminance_threshold <= 255:
            raise ValueError("luminance_threshold must be in [0, 255]")
        if not 0 <= reject_fraction <= 1:
            raise ValueError("reject_fraction must be in [0, 1]")
        self.roi = roi
        self.luminance_threshold = luminance_threshold
        self.reject_fraction = reject_fraction

    def classify(
        self,
        frame: Any,
        *,
        frame_id: str | None = None,
        session_id: str | None = None,
    ) -> PerceptionResult:
        image = np.asarray(frame)
        if image.ndim != 3 or image.shape[2] < 3:
            raise ValueError(f"expected H×W×3 image, got shape {image.shape}")
        crop = self.roi.crop(image[..., :3]).astype(np.float32)
        # Channel-order independent approximation; adequate only as the declared baseline.
        luminance = crop.mean(axis=2)
        dark_fraction = float(np.mean(luminance < self.luminance_threshold))
        rejected = dark_fraction >= self.reject_fraction
        distance = abs(dark_fraction - self.reject_fraction)
        scale = max(self.reject_fraction, 1.0 - self.reject_fraction, 1e-6)
        confidence = min(1.0, 0.5 + 0.5 * distance / scale)
        return PerceptionResult(
            label=Label.VISIBLE_REJECT if rejected else Label.ACCEPTABLE,
            confidence=confidence,
            defect_type="black_or_dark" if rejected else None,
            roi=self.roi.as_tuple(),
            frame_id=frame_id,
            session_id=session_id,
        )


class TorchScriptClassifier:
    """Load a binary transfer model without owning or reopening a camera."""

    def __init__(
        self,
        model_path: str | Path,
        roi: Roi,
        *,
        operating_threshold: float,
        image_size: int = 224,
        reject_class_index: int = 1,
        device: str = "cpu",
        input_color_order: str = "RGB",
    ) -> None:
        if image_size <= 0:
            raise ValueError("image_size must be positive")
        if not 0.0 <= operating_threshold <= 1.0:
            raise ValueError("operating_threshold must be in [0, 1]")
        if input_color_order not in {"RGB", "BGR"}:
            raise ValueError("input_color_order must be RGB or BGR")
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install the perception extra: pip install -e '.[perception]'"
            ) from exc
        self.torch = torch
        self.model = torch.jit.load(str(model_path), map_location=device).eval()
        self.roi = roi
        self.image_size = image_size
        self.reject_class_index = reject_class_index
        # This is the validation-frozen classifier decision threshold. The
        # controller's reject_threshold remains a separate motion-confidence
        # gate and can be more conservative.
        self.operating_threshold = operating_threshold
        self.device = device
        self.input_color_order = input_color_order

    def _tensor(self, frame: Any) -> Any:
        return classifier_tensor(
            frame,
            self.roi,
            image_size=self.image_size,
            device=self.device,
            input_color_order=self.input_color_order,
        )

    def classify(
        self,
        frame: Any,
        *,
        frame_id: str | None = None,
        session_id: str | None = None,
    ) -> PerceptionResult:
        torch = self.torch
        with torch.inference_mode():
            logits = self.model(self._tensor(frame))
            probabilities = torch.softmax(logits, dim=1)[0]
        reject_probability = float(probabilities[self.reject_class_index].item())
        rejected = reject_probability >= self.operating_threshold
        return PerceptionResult(
            label=Label.VISIBLE_REJECT if rejected else Label.ACCEPTABLE,
            confidence=reject_probability if rejected else 1.0 - reject_probability,
            defect_type="model_visible_reject" if rejected else None,
            roi=self.roi.as_tuple(),
            frame_id=frame_id,
            session_id=session_id,
        )
