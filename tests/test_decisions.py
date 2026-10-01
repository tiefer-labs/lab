# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab import decisions


def _mask() -> np.ndarray:
    # 16 pixels: 4 thick cloud, 2 thin cloud, 3 cloud shadow, 7 clear.
    flat = [1, 1, 1, 1, 2, 2, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0]
    return np.array(flat, dtype=np.uint8).reshape(4, 4)


def test_fractions_by_hand() -> None:
    mask = _mask()
    assert decisions.cloud_fraction(mask) == pytest.approx(6 / 16)
    assert decisions.shadow_fraction(mask) == pytest.approx(3 / 16)
    stack = np.stack([mask, np.zeros_like(mask), np.ones_like(mask)])
    np.testing.assert_allclose(decisions.cloud_fractions(stack), [6 / 16, 0.0, 1.0])


def test_decision_is_send_only_strictly_below_threshold() -> None:
    assert decisions.decide(0.375, 0.5) == "send"
    assert decisions.decide(0.375, 0.3) == "keep"
    assert decisions.decide(0.5, 0.5) == "keep"
    assert decisions.decide(0.0, 0.3) == "send"
    np.testing.assert_array_equal(
        decisions.send_mask(np.array([0.1, 0.5, 0.7]), 0.5), [True, False, False]
    )
    with pytest.raises(ValueError):
        decisions.decide(0.1, 0.0)
    with pytest.raises(ValueError):
        decisions.decide(0.1, 1.5)


def test_summary_reports_all_fields() -> None:
    summary = decisions.summarise(_mask(), threshold=0.3)
    assert summary.cloud_fraction == pytest.approx(0.375)
    assert summary.shadow_fraction == pytest.approx(0.1875)
    assert summary.decision == "keep"
    assert summary.threshold == 0.3
