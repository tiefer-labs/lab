# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Baselines, evaluated with the same code and splits as the model.

1. Always send: every pixel is predicted clear, so every frame is sent.
2. Threshold rule: brightness and whiteness of the visible bands, with
   thresholds tuned on the validation split only.
3. Reference masks: masks from established algorithms shipped with the
   dataset, when the cache holds them. They use more spectral bands than the
   four used here, so the comparison favours them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLEAR, IGNORE_INDEX, NUM_CLASSES, THICK_CLOUD, THIN_CLOUD
from tiefer_lab.metrics import mean_iou

FloatArray = NDArray[np.float32]
Mask = NDArray[np.uint8]

# Visible bands in the cache order (blue, green, red, near infrared).
VISIBLE = (0, 1, 2)

# Histogram bins for tuning. Thresholds are taken on bin edges, so a rule
# evaluated from the histogram gives exactly the same confusion matrix as the
# rule applied pixel by pixel.
BRIGHTNESS_STEP = 0.01
BRIGHTNESS_BINS = 100  # [0, 1) in steps of 0.01, plus one bin for >= 1.0
WHITENESS_STEP = 0.05
WHITENESS_BINS = 20  # [0, 1) in steps of 0.05, plus one bin for >= 1.0

THICK_GRID = tuple(round(0.15 + 0.05 * i, 2) for i in range(10))  # 0.15 to 0.60
THIN_GRID = tuple(round(0.08 + 0.02 * i, 2) for i in range(17))  # 0.08 to 0.40
WHITENESS_GRID = tuple(round(0.1 * i, 1) for i in range(1, 11))  # 0.1 to 1.0


def always_send(shape: tuple[int, ...]) -> Mask:
    """Every pixel clear: the cloud fraction is zero and every frame is sent."""
    return np.full(shape, CLEAR, dtype=np.uint8)


def visible_brightness(reflectance: FloatArray) -> FloatArray:
    """Mean top-of-atmosphere reflectance of blue, green and red."""
    return np.asarray(reflectance[list(VISIBLE)].mean(axis=0), dtype=np.float32)


def whiteness(reflectance: FloatArray) -> FloatArray:
    """Spread of the visible bands relative to their mean (low for white surfaces).

    whiteness = sum over visible bands of |band - mean| / mean. Pixels with a
    non-positive mean get a large value, so they are never called cloud.
    """
    mean = visible_brightness(reflectance)
    spread = np.abs(reflectance[list(VISIBLE)] - mean[None]).sum(axis=0)
    out = np.full(mean.shape, np.float32(np.inf))
    np.divide(spread, mean, out=out, where=mean > 0)
    return out.astype(np.float32)


@dataclass(frozen=True)
class ThresholdRule:
    """Thick cloud: brightness >= thick and whiteness < max_whiteness.
    Thin cloud: thin <= brightness < thick and whiteness < max_whiteness.
    Everything else is clear; the rule never predicts cloud shadow.
    """

    thick_brightness: float
    thin_brightness: float
    max_whiteness: float

    def __post_init__(self) -> None:
        if not 0.0 < self.thin_brightness < self.thick_brightness:
            raise ValueError("thresholds must satisfy 0 < thin < thick")
        if self.max_whiteness <= 0.0:
            raise ValueError("max_whiteness must be positive")

    def predict(self, reflectance: FloatArray) -> Mask:
        bright = visible_brightness(reflectance)
        white = whiteness(reflectance) < self.max_whiteness
        mask = np.full(bright.shape, CLEAR, dtype=np.uint8)
        mask[white & (bright >= self.thin_brightness)] = THIN_CLOUD
        mask[white & (bright >= self.thick_brightness)] = THICK_CLOUD
        return mask

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def _bin(values: FloatArray, step: float, bins: int) -> NDArray[np.int64]:
    """Histogram bin of each value: [0, step) is bin 0, and >= bins * step is bin `bins`.

    `whiteness` is +inf where the visible mean is not positive (for example
    pixels with digital number 0); such pixels go to the last bin, which no
    rule calls white, exactly as `ThresholdRule.predict` treats them. Casting
    infinity to an integer is undefined, so values are clipped to the bin
    range before the cast. NaN has no bin and is an error.
    """
    scaled = values.astype(np.float64) / step + 1e-9
    if np.isnan(scaled).any():
        raise ValueError(f"{int(np.isnan(scaled).sum())} NaN values cannot be binned")
    scaled = np.clip(scaled, 0.0, float(bins))
    return np.floor(scaled).astype(np.int64)


class RuleHistogram:
    """Pixel counts by reference class, brightness bin and whiteness bin."""

    def __init__(self) -> None:
        self.counts = np.zeros(
            (NUM_CLASSES, BRIGHTNESS_BINS + 1, WHITENESS_BINS + 1), dtype=np.int64
        )

    def add(self, reflectance: FloatArray, label: NDArray[np.integer[Any]]) -> None:
        """Add the labelled pixels; IGNORE_INDEX (no label, or padding) is left out."""
        valid = label != IGNORE_INDEX
        b = _bin(visible_brightness(reflectance), BRIGHTNESS_STEP, BRIGHTNESS_BINS)[valid]
        w = _bin(whiteness(reflectance), WHITENESS_STEP, WHITENESS_BINS)[valid]
        classes = label[valid].astype(np.int64)
        flat = (classes * (BRIGHTNESS_BINS + 1) + b) * (WHITENESS_BINS + 1) + w
        self.counts += np.bincount(flat.ravel(), minlength=self.counts.size).reshape(
            self.counts.shape
        )

    def confusion(self, rule: ThresholdRule) -> NDArray[np.int64]:
        """Confusion matrix of `rule` over the added pixels (thresholds on bin edges)."""
        b_edges = np.arange(BRIGHTNESS_BINS + 1) * BRIGHTNESS_STEP
        w_upper = (np.arange(WHITENESS_BINS + 1) + 1) * WHITENESS_STEP
        w_upper[-1] = np.inf
        white = w_upper[None, :] <= rule.max_whiteness + 1e-9
        pred = np.full((BRIGHTNESS_BINS + 1, WHITENESS_BINS + 1), CLEAR, dtype=np.int64)
        pred[(b_edges[:, None] >= rule.thin_brightness - 1e-9) & white] = THIN_CLOUD
        pred[(b_edges[:, None] >= rule.thick_brightness - 1e-9) & white] = THICK_CLOUD
        cm = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=np.int64)
        for predicted in (CLEAR, THICK_CLOUD, THIN_CLOUD):
            cm[:, predicted] = self.counts[:, pred == predicted].sum(axis=1)
        return cm


def tune_threshold_rule(
    histogram: RuleHistogram,
    thick_grid: tuple[float, ...] = THICK_GRID,
    thin_grid: tuple[float, ...] = THIN_GRID,
    whiteness_grid: tuple[float, ...] = WHITENESS_GRID,
) -> tuple[ThresholdRule, float]:
    """Grid search for the rule with the highest mean IoU on the given pixels.

    Call it with a histogram of the validation split only. Ties keep the first
    rule in grid order, so the result is deterministic.
    """
    best: tuple[ThresholdRule, float] | None = None
    for thick in thick_grid:
        for thin in thin_grid:
            if thin >= thick:
                continue
            for white in whiteness_grid:
                rule = ThresholdRule(thick, thin, white)
                score = mean_iou(histogram.confusion(rule))
                if np.isfinite(score) and (best is None or score > best[1]):
                    best = (rule, score)
    if best is None:
        raise ValueError("no valid rule in the grid")
    return best
