# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab import bootstrap


def _mean_of(values: np.ndarray) -> bootstrap.Statistic:
    return lambda idx: float(values[idx].mean())


def test_same_seed_gives_same_interval() -> None:
    values = np.random.default_rng(0).normal(size=50)
    a = bootstrap.bootstrap(50, {"mean": _mean_of(values)}, resamples=200, seed=3)
    b = bootstrap.bootstrap(50, {"mean": _mean_of(values)}, resamples=200, seed=3)
    c = bootstrap.bootstrap(50, {"mean": _mean_of(values)}, resamples=200, seed=4)
    assert a == b
    assert a["mean"].low != c["mean"].low


def test_interval_brackets_the_estimate() -> None:
    values = np.random.default_rng(1).normal(loc=2.0, size=200)
    interval = bootstrap.bootstrap(200, {"mean": _mean_of(values)})["mean"]
    assert interval.low is not None and interval.high is not None
    assert interval.low < values.mean() < interval.high
    assert interval.resamples == 1000 and interval.seed == 0 and interval.level == 0.95


def test_constant_data_and_undefined_statistic() -> None:
    values = np.full(10, 0.7)
    out = bootstrap.bootstrap(
        10, {"mean": _mean_of(values), "undefined": lambda idx: float("nan")}, resamples=50
    )
    assert out["mean"].low == pytest.approx(0.7) and out["mean"].high == pytest.approx(0.7)
    assert out["undefined"].low is None and out["undefined"].high is None


def test_empty_sample_is_rejected() -> None:
    with pytest.raises(ValueError):
        bootstrap.resample_indices(0, 10, 0)
