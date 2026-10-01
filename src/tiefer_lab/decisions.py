# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Per-frame cloud fraction, shadow fraction and the send or keep decision.

A frame is sent when its cloud fraction (thick plus thin cloud) is strictly
below the operator's threshold, and kept on board otherwise. Cloud shadow is
reported separately and does not count towards the cloud fraction
(docs/ASSUMPTIONS.md, section 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLOUD_SHADOW, THICK_CLOUD, THIN_CLOUD

Decision = Literal["send", "keep"]
CLOUD_CLASSES = (THICK_CLOUD, THIN_CLOUD)
DEFAULT_THRESHOLD = 0.5


def _check_threshold(threshold: float) -> None:
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")


def cloud_fraction(mask: NDArray[np.integer[Any]]) -> float:
    """Share of pixels that are thick or thin cloud."""
    if mask.size == 0:
        raise ValueError("empty mask")
    return float(np.isin(mask, CLOUD_CLASSES).mean())


def shadow_fraction(mask: NDArray[np.integer[Any]]) -> float:
    """Share of pixels that are cloud shadow."""
    if mask.size == 0:
        raise ValueError("empty mask")
    return float((mask == CLOUD_SHADOW).mean())


def cloud_fractions(masks: NDArray[np.integer[Any]]) -> NDArray[np.float64]:
    """Cloud fraction of each frame in a stack of shape (frames, height, width)."""
    if masks.ndim != 3:
        raise ValueError(f"expected (frames, height, width), got {masks.shape}")
    return np.asarray(np.isin(masks, CLOUD_CLASSES).mean(axis=(1, 2)), dtype=np.float64)


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
