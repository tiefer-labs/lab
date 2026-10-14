# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Per-patch accuracy of binary problems, summarised by the median over patches.

Two binary problems are scored on every patch, from its four-class confusion
matrix (reference rows, predicted columns):

- cloud: thick cloud and thin cloud against clear and cloud shadow;
- shadow: cloud shadow against everything else.

For each problem and patch, with TP, FN, FP, TN counted over valid pixels:

- producer's accuracy (PA) = TP / (TP + FN), the share of reference positives found;
- user's accuracy (UA) = TP / (TP + FP), the share of predicted positives that are right;
- overall accuracy (OA) = (TP + TN) / (TP + FN + FP + TN);
- balanced overall accuracy (BOA) = (TP / (TP + FN) + TN / (TN + FP)) / 2.

A ratio whose denominator is zero is undefined for that patch (for example
PA and BOA on a patch with no reference cloud); undefined values are left out
of the median, and their number is reported next to it.

These are the definitions of this repository. The dataset paper
(https://doi.org/10.1038/s41597-022-01878-2, Technical Validation, read on
7 October 2026 in its Europe PMC full text) defines PA = TP / (TP + FN),
UA = TP / (TP + FP) and BOA = 0.5 (PA + TN / (TN + FP)) per patch, with cloud
as thick plus thin cloud, and sets PA and UA of cloudless patches to NaN. It
reports the median of BOA over patches, but summarises PA and UA as the share
of patches below 0.1, between 0.1 and 0.9 and above 0.9, not as a median.
`PAPER_DEFINITION_VERIFIED` stays False because of that difference. Published
values are placed only in docs/LANDSCAPE.md, never next to these measurements
in docs/RESULTS.md.

The paper's own summary (`paper_summary`, evaluated only with
`python -m tiefer_lab.evaluate --full-metrics`, a protocol option whose
default leaves every report unchanged): per patch PA and UA, both NaN on a
patch without reference positives ("Since the PA and UA values are always
zero in cloudless IPs, they were replaced by NaN"), and UA also NaN where
nothing is predicted positive (0 / 0); then
the share of patches with the value below 0.1 (low), from 0.1 to 0.9
(middle) and above 0.9 (high). Source: CloudSEN12, Scientific Data 9, 782,
2022, https://doi.org/10.1038/s41597-022-01878-2, Technical Validation, Eq. 1
and the paragraph after it, and the notes of Table 6 ("percentage of IPs";
the BOA is "the median BOA across all IPs"), read on 14 October 2026 in the
Europe PMC full text (PMC9789947). The denominator of the shares is TODO(verify): the text says
"percentage of IPs" and "of total IPs" and sets PA and UA of cloudless
patches to NaN, but does not say whether those NaN patches are in the
denominator; this code divides by the patches where the value is defined,
which the rows of Table 6 summing to 100 supports. `PAPER_VERIFIED` records
what matches the paper: the median BOA does; the share summary waits for the
denominator. The paper's third experiment, valid against invalid, has thick
cloud, thin cloud and cloud shadow as positives (`PAPER_PROBLEMS`).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLOUD_SHADOW, NUM_CLASSES, THICK_CLOUD, THIN_CLOUD

PAPER_DEFINITION_VERIFIED = False
# What matches the paper, by summary (see the module docstring).
PAPER_VERIFIED: dict[str, bool] = {"median_boa": True, "share_summary": False}
# Bounds of the paper's low, middle and high groups.
SHARE_LOW, SHARE_HIGH = 0.1, 0.9

PROBLEMS: dict[str, tuple[int, ...]] = {
    "cloud": (THICK_CLOUD, THIN_CLOUD),
    "shadow": (CLOUD_SHADOW,),
}
# The paper's third experiment; scored only with the full metric set.
PAPER_PROBLEMS: dict[str, tuple[int, ...]] = {
    "valid": (THICK_CLOUD, THIN_CLOUD, CLOUD_SHADOW),
}
ALL_PROBLEMS: dict[str, tuple[int, ...]] = {**PROBLEMS, **PAPER_PROBLEMS}
MEASURES = ("boa", "pa", "ua", "oa")


def binary_counts(
    cm: NDArray[np.integer[Any]], positive: Sequence[int]
) -> tuple[int, int, int, int]:
    """(TP, FN, FP, TN) of `positive` classes against the rest, from a confusion matrix."""
    pos = np.zeros(cm.shape[0], dtype=bool)
    pos[list(positive)] = True
    tp = int(cm[np.ix_(pos, pos)].sum())
    fn = int(cm[np.ix_(pos, ~pos)].sum())
    fp = int(cm[np.ix_(~pos, pos)].sum())
    tn = int(cm[np.ix_(~pos, ~pos)].sum())
    return tp, fn, fp, tn


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else math.nan


def patch_measures(tp: int, fn: int, fp: int, tn: int) -> dict[str, float]:
    tpr = _ratio(tp, tp + fn)
    tnr = _ratio(tn, tn + fp)
    return {
        "boa": (tpr + tnr) / 2 if not (math.isnan(tpr) or math.isnan(tnr)) else math.nan,
        "pa": tpr,
        "ua": _ratio(tp, tp + fp),
        "oa": _ratio(tp + tn, tp + fn + fp + tn),
    }


def per_patch(cms: NDArray[np.integer[Any]], problem: str) -> dict[str, NDArray[np.float64]]:
    """Each measure for every patch (NaN where undefined), from (patches, 4, 4) matrices."""
    if cms.ndim != 3 or cms.shape[1:] != (NUM_CLASSES, NUM_CLASSES):
        raise ValueError(f"expected (patches, {NUM_CLASSES}, {NUM_CLASSES}), got {cms.shape}")
    rows = [patch_measures(*binary_counts(cm, ALL_PROBLEMS[problem])) for cm in cms]
    return {m: np.asarray([r[m] for r in rows], dtype=np.float64) for m in MEASURES}


def median(values: NDArray[np.float64]) -> float:
    """Median over patches where the value is defined; NaN when none is."""
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if finite.size else math.nan


def summary(
    cms: NDArray[np.integer[Any]], problems: Sequence[str] = tuple(PROBLEMS)
) -> dict[str, Any]:
    """Median of every measure per problem, with the number of patches it is defined on."""
    out: dict[str, Any] = {}
    for problem in problems:
        values = per_patch(cms, problem)
        out[problem] = {
            "positive_classes": list(ALL_PROBLEMS[problem]),
            **{
                f"median_{m}": None if math.isnan(median(v)) else median(v)
                for m, v in values.items()
            },
            **{f"patches_defined_{m}": int(np.isfinite(v).sum()) for m, v in values.items()},
        }
    out["definition"] = "this repository (binary_metrics.py); paper definition TODO(verify)"
    out["paper_definition_verified"] = PAPER_DEFINITION_VERIFIED
    return out


def shares(values: NDArray[np.float64]) -> dict[str, float | int | None]:
    """The paper's low, middle and high shares over the patches where the value is defined.

    low: below 0.1; middle: from 0.1 to 0.9, both included; high: above 0.9.
    The shares are None when no patch has a defined value.
    """
    finite = values[np.isfinite(values)]
    n = int(finite.size)
    if n == 0:
        return {"low": None, "middle": None, "high": None, "patches_defined": 0}
    low = int((finite < SHARE_LOW).sum())
    high = int((finite > SHARE_HIGH).sum())
    return {
        "low": low / n,
        "middle": (n - low - high) / n,
        "high": high / n,
        "patches_defined": n,
    }


def paper_summary(
    cms: NDArray[np.integer[Any]], problems: Sequence[str] = tuple(ALL_PROBLEMS)
) -> dict[str, Any]:
    """Median BOA and the low, middle and high shares of PA and UA, per problem."""
    out: dict[str, Any] = {}
    for problem in problems:
        values = per_patch(cms, problem)
        # The paper sets UA to NaN on patches without reference positives, like PA.
        ua = np.where(np.isnan(values["pa"]), np.nan, values["ua"])
        out[problem] = {
            "positive_classes": list(ALL_PROBLEMS[problem]),
            "median_boa": None if math.isnan(median(values["boa"])) else median(values["boa"]),
            "pa_shares": shares(values["pa"]),
            "ua_shares": shares(ua),
        }
    out["verified"] = dict(PAPER_VERIFIED)
    out["share_denominator"] = "patches where the value is defined (TODO(verify))"
    return out
