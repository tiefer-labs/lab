# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Percentile bootstrap confidence intervals over patches.

All statistics of one evaluation are computed on the same resamples, drawn
from a generator with a fixed seed, so intervals are reproducible.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

DEFAULT_RESAMPLES = 1000
DEFAULT_SEED = 0
DEFAULT_LEVEL = 0.95

Statistic = Callable[[NDArray[np.intp]], float]


@dataclass(frozen=True)
class Interval:
    low: float | None
    high: float | None
    level: float
    resamples: int
    seed: int

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "low": self.low,
            "high": self.high,
            "level": self.level,
            "resamples": self.resamples,
            "seed": self.seed,
        }


def resample_indices(n: int, resamples: int, seed: int) -> NDArray[np.intp]:
    """Index sets of shape (resamples, n), drawn with replacement."""
    if n < 1:
        raise ValueError("cannot bootstrap an empty sample")
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(resamples, n), dtype=np.intp)


def bootstrap(
    n: int,
    statistics: Mapping[str, Statistic],
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
    level: float = DEFAULT_LEVEL,
) -> dict[str, Interval]:
    """Percentile intervals for several statistics of the same n patches.

    Each statistic takes an array of patch indexes and returns a number. NaN
    values of a resample are left out; if every resample is NaN the interval
    is (None, None).
    """
    if not 0.0 < level < 1.0:
        raise ValueError("level must be in (0, 1)")
    indices = resample_indices(n, resamples, seed)
    values = {name: np.empty(resamples, dtype=np.float64) for name in statistics}
    for r in range(resamples):
        for name, stat in statistics.items():
            values[name][r] = stat(indices[r])
    tail = (1.0 - level) / 2.0 * 100.0
    out = {}
    for name, v in values.items():
        finite = v[np.isfinite(v)]
        if finite.size == 0:
            out[name] = Interval(None, None, level, resamples, seed)
        else:
            low, high = np.percentile(finite, [tail, 100.0 - tail])
            out[name] = Interval(float(low), float(high), level, resamples, seed)
    return out
