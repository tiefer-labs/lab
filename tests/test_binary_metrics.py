# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Binary accuracy measures, checked by hand."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tiefer_lab import binary_metrics as bm
from tiefer_lab import metrics
from tiefer_lab.config import EvaluationConfig
from tiefer_lab.data.source import IGNORE_INDEX
from tiefer_lab.evaluate import Scores

# Reference rows, predicted columns: clear, thick cloud, thin cloud, cloud shadow.
CM = np.array(
    [
        [5, 1, 0, 0],  # 6 clear pixels: 5 right, 1 called thick cloud
        [1, 3, 0, 0],  # 4 thick cloud pixels: 1 called clear
        [0, 1, 1, 0],  # 2 thin cloud pixels: 1 called thick cloud (still cloud)
        [1, 0, 0, 1],  # 2 shadow pixels: 1 called clear
    ]
)


def test_cloud_problem_by_hand() -> None:
    # Cloud = thick + thin. TP 3 + 0 + 1 + 1 = 5, FN 1, FP 1, TN 5 + 0 + 1 + 1 = 7.
    assert bm.binary_counts(CM, bm.PROBLEMS["cloud"]) == (5, 1, 1, 7)
    m = bm.patch_measures(5, 1, 1, 7)
    assert m["pa"] == pytest.approx(5 / 6)
    assert m["ua"] == pytest.approx(5 / 6)
    assert m["oa"] == pytest.approx(12 / 14)
    assert m["boa"] == pytest.approx((5 / 6 + 7 / 8) / 2)


def test_shadow_problem_by_hand() -> None:
    assert bm.binary_counts(CM, bm.PROBLEMS["shadow"]) == (1, 1, 0, 12)
    m = bm.patch_measures(1, 1, 0, 12)
    assert (m["pa"], m["ua"], m["boa"]) == (0.5, 1.0, 0.75)


def test_undefined_values_are_left_out_of_the_median() -> None:
    no_cloud = np.diag([10, 0, 0, 0])  # a clear patch: cloud PA and BOA are undefined
    m = bm.patch_measures(*bm.binary_counts(no_cloud, bm.PROBLEMS["cloud"]))
    assert math.isnan(m["pa"]) and math.isnan(m["boa"]) and math.isnan(m["ua"])
    assert m["oa"] == 1.0
    out = bm.summary(np.stack([CM, no_cloud, CM]))
    assert out["cloud"]["median_boa"] == pytest.approx((5 / 6 + 7 / 8) / 2)
    assert out["cloud"]["patches_defined_boa"] == 2
    assert out["cloud"]["patches_defined_oa"] == 3
    assert out["paper_definition_verified"] is False
    assert math.isnan(bm.median(np.array([math.nan])))


def test_producers_and_users_accuracy_per_class() -> None:
    np.testing.assert_allclose(metrics.producers_accuracy(CM), [5 / 6, 3 / 4, 1 / 2, 1 / 2])
    np.testing.assert_allclose(metrics.users_accuracy(CM), [5 / 7, 3 / 5, 1 / 1, 1 / 1])


def test_scores_leave_ignored_pixels_out_and_report_intervals() -> None:
    reference = np.array([[0, 1], [2, IGNORE_INDEX]], np.uint8)
    prediction = np.array([[0, 1], [IGNORE_INDEX, 3]], np.uint8)
    scores = Scores()
    scores.add(prediction, reference)
    scores.add(np.array([[1, 1], [0, 0]], np.uint8), np.array([[1, 2], [0, 3]], np.uint8))
    settings = EvaluationConfig(bootstrap_resamples=100)
    report = scores.report(settings)
    assert report["ignored_pixels"] == 2
    assert report["pixel"]["pixels"] == 2 + 4
    cloud = report["binary"]["cloud"]
    assert cloud["median_boa"] == pytest.approx(1.0)
    assert set(cloud["intervals"]) == {"median_boa", "median_pa", "median_ua", "median_oa"}


def test_binary_only_scores_report_the_cloud_problem_only() -> None:
    scores = Scores(binary_only=True)
    scores.add(np.array([[1, 0]], np.uint8), np.array([[2, 3]], np.uint8))
    report = scores.report(EvaluationConfig(bootstrap_resamples=100))
    assert set(report) == {"patches", "ignored_pixels", "binary"}
    assert set(report["binary"]) == {"cloud", "definition", "paper_definition_verified"}
    assert report["binary"]["cloud"]["median_boa"] == 1.0


def test_expected_calibration_error_by_hand() -> None:
    calibration = metrics.Calibration(bins=10)
    # Bin [0.9, 1.0): 4 pixels at 0.95, 3 right: accuracy 0.75, confidence 0.95.
    # Bin [0.6, 0.7): 2 pixels at 0.65, both right: accuracy 1.0, confidence 0.65.
    confidence = np.array([0.95, 0.95, 0.95, 0.95, 0.65, 0.65, 0.5])
    prediction = np.array([1, 1, 1, 1, 2, 2, 0])
    reference = np.array([1, 1, 1, 0, 2, 2, IGNORE_INDEX])
    calibration.add(confidence, prediction, reference)
    expected = 4 / 6 * abs(0.75 - 0.95) + 2 / 6 * abs(1.0 - 0.65)
    assert calibration.ece() == pytest.approx(expected)
    assert calibration.report()["pixels"] == 6
    assert metrics.Calibration().ece() is None


def test_worst_stratum_is_named() -> None:
    from tiefer_lab.evaluate import worst_stratum

    strata = {
        "season": {
            "winter": {"patches": 40, "cloud_boa": 0.71},
            "summer": {"patches": 60, "cloud_boa": 0.93},
        },
        "region": {"north": {"patches": 5, "cloud_boa": 0.20}},  # too few patches
    }
    worst = worst_stratum(strata)
    assert worst is not None and (worst["field"], worst["value"]) == ("season", "winter")
    assert worst_stratum({}) is None


def test_int8_comparison_reports_the_boa_change() -> None:
    from tiefer_lab.export.quantise import compare_reports

    def report(miou: float, boa: float) -> dict:
        return {
            "pixel": {"mean_iou": miou},
            "false_discard_rate": 0.1,
            "binary": {"cloud": {"median_boa": boa}, "shadow": {"median_boa": None}},
        }

    out = compare_reports(report(0.7, 0.90), report(0.69, 0.885))
    assert out["cloud_boa_change"] == pytest.approx(-0.015)
    assert out["shadow_boa_change"] is None


def test_paper_shares_by_hand() -> None:
    # Values 0.05 (low), 0.1 and 0.9 (middle, bounds included), 0.95 (high), NaN (left out).
    values = np.array([0.05, 0.1, 0.9, 0.95, math.nan])
    out = bm.shares(values)
    assert out == {"low": 0.25, "middle": 0.5, "high": 0.25, "patches_defined": 4}
    assert bm.shares(np.array([math.nan]))["low"] is None


def test_valid_problem_and_paper_summary_by_hand() -> None:
    # Valid against invalid: positives thick, thin and shadow (rows and columns 1 to 3).
    # TP 3 + 2 + 1 = 6, FN 1 + 0 + 1 = 2 (called clear), FP 1 (clear called thick), TN 5.
    assert bm.binary_counts(CM, bm.ALL_PROBLEMS["valid"]) == (6, 2, 1, 5)
    no_cloud = np.diag([10, 0, 0, 0])
    out = bm.paper_summary(np.stack([CM, no_cloud]))
    assert set(out) >= {"cloud", "shadow", "valid", "verified"}
    # The clear patch has no cloud: PA undefined, so one defined patch.
    assert out["cloud"]["pa_shares"]["patches_defined"] == 1
    assert out["cloud"]["pa_shares"]["middle"] == 1.0  # 5 / 6
    # A cloudless patch with a false cloud pixel: its UA (0) is NaN, as in the paper.
    false_cloud = np.array([[9, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    out2 = bm.paper_summary(np.stack([CM, false_cloud]), ("cloud",))
    assert out2["cloud"]["ua_shares"]["patches_defined"] == 1
    assert out["verified"] == {"median_boa": True, "share_summary": False}
    assert out["valid"]["median_boa"] == pytest.approx((6 / 8 + 5 / 6) / 2)


def test_default_report_is_unchanged_and_full_adds_the_paper_summary() -> None:
    scores = Scores()
    scores.add(np.array([[1, 0], [0, 3]], np.uint8), np.array([[1, 1], [0, 3]], np.uint8))
    scores.add(np.array([[0, 0], [0, 0]], np.uint8), np.array([[0, 0], [0, 1]], np.uint8))
    settings = EvaluationConfig(bootstrap_resamples=100)
    plain = scores.report(settings)
    assert "paper" not in plain and "frame_sweep" not in plain
    assert "valid" not in plain["binary"]
    full = scores.report(settings, full=True)
    assert {k: v for k, v in full.items() if k not in ("paper", "frame_sweep")} == plain
    assert "valid" in full["paper"]
    assert len(full["frame_sweep"]["points"]) == 19
