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
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLOUD_SHADOW, NUM_CLASSES, THICK_CLOUD, THIN_CLOUD

PAPER_DEFINITION_VERIFIED = False

PROBLEMS: dict[str, tuple[int, ...]] = {
    "cloud": (THICK_CLOUD, THIN_CLOUD),
    "shadow": (CLOUD_SHADOW,),
}
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
    rows = [patch_measures(*binary_counts(cm, PROBLEMS[problem])) for cm in cms]
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
            "positive_classes": list(PROBLEMS[problem]),
            **{
                f"median_{m}": None if math.isnan(median(v)) else median(v)
                for m, v in values.items()
            },
            **{f"patches_defined_{m}": int(np.isfinite(v).sum()) for m, v in values.items()},
        }
    out["definition"] = "this repository (binary_metrics.py); paper definition TODO(verify)"
    out["paper_definition_verified"] = PAPER_DEFINITION_VERIFIED
    return out
