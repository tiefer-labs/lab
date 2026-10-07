# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Per-frame cloud fraction, shadow fraction and the send or keep decision.

A frame is sent when its cloud fraction (thick plus thin cloud) is strictly
below the operator's threshold, and kept on board otherwise. Cloud shadow is
reported separately and does not count towards the cloud fraction
(docs/ASSUMPTIONS.md, section 3).

Fractions are taken over labelled pixels only: IGNORE_INDEX (no label, or
the dataset's padding of a cached patch, data/padding.py) is left out of the
numerator and the denominator. `frame_fractions` gives the reference and the
predicted fractions of one frame over the same pixels. A prediction never
holds IGNORE_INDEX, so on real frames on board (onboard.py) every pixel counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLOUD_SHADOW, IGNORE_INDEX, THICK_CLOUD, THIN_CLOUD

Decision = Literal["send", "keep"]
CLOUD_CLASSES = (THICK_CLOUD, THIN_CLOUD)
DEFAULT_THRESHOLD = 0.5


def _check_threshold(threshold: float) -> None:
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")


def _labelled(mask: NDArray[np.integer[Any]]) -> NDArray[np.bool_]:
    if mask.size == 0:
        raise ValueError("empty mask")
    labelled = np.asarray(mask != IGNORE_INDEX)
    if not labelled.any():
        raise ValueError("no labelled pixels")
    return labelled


def cloud_fraction(mask: NDArray[np.integer[Any]]) -> float:
    """Share of labelled pixels that are thick or thin cloud."""
    labelled = _labelled(mask)
    return float(np.isin(mask, CLOUD_CLASSES).sum() / labelled.sum())


def shadow_fraction(mask: NDArray[np.integer[Any]]) -> float:
    """Share of labelled pixels that are cloud shadow."""
    labelled = _labelled(mask)
    return float((mask == CLOUD_SHADOW).sum() / labelled.sum())


def cloud_fractions(masks: NDArray[np.integer[Any]]) -> NDArray[np.float64]:
    """Cloud fraction of each frame in a stack of shape (frames, height, width).

    Over the labelled pixels of each frame; a frame without any is NaN.
    """
    if masks.ndim != 3:
        raise ValueError(f"expected (frames, height, width), got {masks.shape}")
    labelled = (masks != IGNORE_INDEX).sum(axis=(1, 2))
    cloud = np.isin(masks, CLOUD_CLASSES).sum(axis=(1, 2))
    out = np.full(masks.shape[0], np.nan, dtype=np.float64)
    np.divide(cloud, labelled, out=out, where=labelled > 0)
    return out


@dataclass(frozen=True)
class FrameFractions:
    """Reference and predicted fractions of one frame over the same pixels."""

    true_cloud: float
    predicted_cloud: float
    predicted_shadow: float
    pixels: int


def frame_fractions(
    prediction: NDArray[np.integer[Any]], reference: NDArray[np.integer[Any]]
) -> FrameFractions:
    """Fractions of one frame over the pixels labelled in both masks.

    The predicted fraction uses the same pixels as the reference, the real
    image area of a patch, so both describe the same region.
    """
    if prediction.shape != reference.shape:
        raise ValueError(f"shape mismatch: {prediction.shape} vs {reference.shape}")
    valid = (reference != IGNORE_INDEX) & (prediction != IGNORE_INDEX)
    pixels = int(valid.sum())
    if pixels == 0:
        raise ValueError("no labelled pixels")
    true_mask, pred_mask = reference[valid], prediction[valid]
    return FrameFractions(
        true_cloud=float(np.isin(true_mask, CLOUD_CLASSES).sum() / pixels),
        predicted_cloud=float(np.isin(pred_mask, CLOUD_CLASSES).sum() / pixels),
        predicted_shadow=float((pred_mask == CLOUD_SHADOW).sum() / pixels),
        pixels=pixels,
    )


def decide(fraction: float, threshold: float = DEFAULT_THRESHOLD) -> Decision:
    """Send when the cloud fraction is below the threshold, keep otherwise."""
    _check_threshold(threshold)
    return "send" if fraction < threshold else "keep"


def send_mask(fractions: NDArray[np.floating[Any]], threshold: float) -> NDArray[np.bool_]:
    """Vectorised `decide`: True where a frame is sent."""
    _check_threshold(threshold)
    return np.asarray(fractions < threshold)


@dataclass(frozen=True)
class FrameSummary:
    cloud_fraction: float
    shadow_fraction: float
    threshold: float
    decision: Decision


def summarise(mask: NDArray[np.integer[Any]], threshold: float = DEFAULT_THRESHOLD) -> FrameSummary:
    """Everything the onboard filter reports about one frame."""
    cf = cloud_fraction(mask)
    return FrameSummary(
        cloud_fraction=cf,
        shadow_fraction=shadow_fraction(mask),
        threshold=threshold,
        decision=decide(cf, threshold),
    )
