# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab import baselines, decisions, metrics
from tiefer_lab.data import build_cache, transforms


def _pixels(values: list[tuple[float, float, float, float]]) -> np.ndarray:
    """A 1 x n image from (blue, green, red, nir) reflectance tuples."""
    return np.array(values, dtype=np.float32).T.reshape(4, 1, len(values))


def test_always_send_sends_every_frame() -> None:
    mask = baselines.always_send((3, 8, 8))
    assert mask.shape == (3, 8, 8) and mask.max() == 0
    fractions = decisions.cloud_fractions(mask)
    assert all(decisions.decide(f, 0.3) == "send" for f in fractions)


def test_brightness_and_whiteness_by_hand() -> None:
    image = _pixels([(0.5, 0.5, 0.5, 0.4), (0.1, 0.2, 0.3, 0.4)])
    np.testing.assert_allclose(baselines.visible_brightness(image)[0], [0.5, 0.2], rtol=1e-6)
    # Second pixel: |0.1-0.2| + |0.2-0.2| + |0.3-0.2| = 0.2, divided by 0.2 = 1.0.
    np.testing.assert_allclose(baselines.whiteness(image)[0], [0.0, 1.0], rtol=1e-5)


def test_threshold_rule_predicts_by_hand() -> None:
    rule = baselines.ThresholdRule(thick_brightness=0.4, thin_brightness=0.2, max_whiteness=0.5)
    image = _pixels(
        [
            (0.5, 0.5, 0.5, 0.5),  # bright and white: thick cloud
            (0.25, 0.25, 0.25, 0.3),  # medium and white: thin cloud
            (0.1, 0.4, 0.7, 0.5),  # bright but coloured: clear
            (0.05, 0.05, 0.05, 0.2),  # dark: clear
        ]
    )
    np.testing.assert_array_equal(rule.predict(image)[0], [1, 2, 0, 0])
    with pytest.raises(ValueError):
        baselines.ThresholdRule(0.2, 0.3, 0.5)


def test_histogram_confusion_matches_pixel_rule() -> None:
    rng = np.random.default_rng(0)
    image = rng.uniform(0.0, 1.1, size=(4, 40, 40)).astype(np.float32)
    label = rng.integers(0, 4, size=(40, 40)).astype(np.uint8)
    hist = baselines.RuleHistogram()
    hist.add(image, label)
    for rule in [
        baselines.ThresholdRule(0.45, 0.2, 0.5),
        baselines.ThresholdRule(0.6, 0.38, 1.0),
        baselines.ThresholdRule(0.25, 0.08, 0.1),
    ]:
        expected = metrics.confusion_matrix(rule.predict(image), label)
        np.testing.assert_array_equal(hist.confusion(rule), expected)


def test_tuning_recovers_a_separable_rule() -> None:
    hist = baselines.RuleHistogram()
    for image_dn, label in build_cache.synthetic_patches(6, 48, seed=11):
        hist.add(transforms.to_reflectance(image_dn), label)
    rule, score = baselines.tune_threshold_rule(hist)
    untuned = metrics.mean_iou(hist.confusion(baselines.ThresholdRule(0.6, 0.4, 0.1)))
    assert score >= untuned
    assert rule.thin_brightness < rule.thick_brightness
    again, again_score = baselines.tune_threshold_rule(hist)
    assert again == rule and again_score == score


def test_dark_pixels_bin_without_an_invalid_cast_and_match_the_rule() -> None:
    import warnings

    # Digital number 0 in the visible bands: brightness 0 and whiteness +inf.
    image = _pixels([(0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.3), (0.5, 0.5, 0.5, 0.5)])
    label = np.array([[0, 1, 1]], dtype=np.uint8)
    assert np.isinf(baselines.whiteness(image)[0, :2]).all()
    histogram = baselines.RuleHistogram()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        histogram.add(image, label)
    # The two dark pixels are in the last whiteness bin, never called white.
    assert histogram.counts[:, 0, baselines.WHITENESS_BINS].sum() == 2
    assert histogram.counts[:, 0, 0].sum() == 0, "dark pixels are not in the whitest bin"
    rule = baselines.ThresholdRule(thick_brightness=0.4, thin_brightness=0.2, max_whiteness=1.0)
    expected = metrics.confusion_matrix(rule.predict(image)[None], label[None])
    np.testing.assert_array_equal(histogram.confusion(rule), expected)


def test_nan_reflectance_is_an_error_in_the_histogram() -> None:
    image = _pixels([(np.nan, 0.1, 0.1, 0.1)])
    with pytest.raises(ValueError, match="NaN"):
        baselines.RuleHistogram().add(image, np.zeros((1, 1), dtype=np.uint8))
