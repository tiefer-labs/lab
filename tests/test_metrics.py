# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Metrics against examples computed by hand."""

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab import metrics

PRED = np.array([0, 0, 1, 1, 2, 3])
REF = np.array([0, 1, 1, 1, 2, 2])


def test_confusion_matrix_by_hand() -> None:
    cm = metrics.confusion_matrix(PRED, REF)
    expected = [[1, 0, 0, 0], [1, 2, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]
    np.testing.assert_array_equal(cm, expected)


def test_iou_f1_accuracy_by_hand() -> None:
    cm = metrics.confusion_matrix(PRED, REF)
    np.testing.assert_allclose(metrics.per_class_iou(cm), [1 / 2, 2 / 3, 1 / 2, 0.0])
    np.testing.assert_allclose(metrics.per_class_f1(cm), [2 / 3, 4 / 5, 2 / 3, 0.0])
    assert metrics.mean_iou(cm) == pytest.approx((1 / 2 + 2 / 3 + 1 / 2 + 0) / 4)
    assert metrics.overall_accuracy(cm) == pytest.approx(4 / 6)


def test_undefined_class_is_left_out_of_mean_iou() -> None:
    cm = metrics.confusion_matrix(np.array([0, 1]), np.array([0, 1]))
    iou = metrics.per_class_iou(cm)
    assert np.isnan(iou[2]) and np.isnan(iou[3])
    assert metrics.mean_iou(cm) == pytest.approx(1.0)
    report = metrics.pixel_metrics(cm)
    assert report["iou"][2] is None and report["mean_iou"] == 1.0


def test_out_of_range_class_is_rejected() -> None:
    with pytest.raises(ValueError):
        metrics.confusion_matrix(np.array([4]), np.array([0]))


def test_frame_metrics_by_hand() -> None:
    true = np.array([0.1, 0.4, 0.6, 0.9])
    pred = np.array([0.2, 0.6, 0.5, 0.8])
    report = metrics.frame_metrics(true, pred)
    assert report["cloud_fraction_mae"] == pytest.approx(0.125)
    at50 = report["thresholds"]["0.50"]
    # Useful frames at 0.5: frames 0 and 1. Frame 1 is predicted at 0.6 and kept.
    assert at50["false_discard_rate"] == pytest.approx(1 / 2)
    # Cloudy frames: 2 (0.6) and 3 (0.9); both predicted at or above 0.5, none sent.
    assert at50["false_send_rate"] == pytest.approx(0.0)
    assert at50["decision_accuracy"] == pytest.approx(3 / 4)
    assert at50["useful_frames"] == 2 and at50["frames"] == 4
    assert report["thresholds"]["0.30"]["false_discard_rate"] == pytest.approx(0.0)
    assert report["thresholds"]["0.70"]["decision_accuracy"] == pytest.approx(1.0)


def test_false_discard_rate_undefined_without_useful_frames() -> None:
    true = np.array([0.8, 0.9])
    assert np.isnan(metrics.false_discard_rate(true, true, 0.5))
    assert metrics.frame_metrics(true, true)["thresholds"]["0.50"]["false_discard_rate"] is None
