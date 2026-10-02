# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Pixel and frame metrics.

Confusion matrices have the reference class in rows and the predicted class
in columns. A metric that is undefined (for example IoU of a class that
appears in neither reference nor prediction) is NaN, written as null in JSON.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import CLASS_NAMES, NUM_CLASSES
from tiefer_lab.decisions import send_mask

FloatArray = NDArray[np.float64]
DECISION_THRESHOLDS = (0.3, 0.5, 0.7)


def confusion_matrix(
    prediction: NDArray[np.integer[Any]],
    reference: NDArray[np.integer[Any]],
    num_classes: int = NUM_CLASSES,
) -> NDArray[np.int64]:
    """Counts of (reference, predicted) class pairs over all pixels."""
    if prediction.shape != reference.shape:
        raise ValueError(f"shape mismatch: {prediction.shape} vs {reference.shape}")
    p = prediction.astype(np.int64).ravel()
    r = reference.astype(np.int64).ravel()
    if p.size and (p.min() < 0 or p.max() >= num_classes or r.min() < 0 or r.max() >= num_classes):
        raise ValueError("class index out of range")
    counts = np.bincount(r * num_classes + p, minlength=num_classes * num_classes)
    return counts.reshape(num_classes, num_classes).astype(np.int64)


def _safe_divide(numerator: FloatArray, denominator: FloatArray) -> FloatArray:
    out = np.full(numerator.shape, np.nan, dtype=np.float64)
    np.divide(numerator, denominator, out=out, where=denominator > 0)
    return out


def per_class_iou(cm: NDArray[np.integer[Any]]) -> FloatArray:
    tp = np.diag(cm).astype(np.float64)
    union = cm.sum(axis=0) + cm.sum(axis=1) - np.diag(cm)
    return _safe_divide(tp, union.astype(np.float64))


def per_class_f1(cm: NDArray[np.integer[Any]]) -> FloatArray:
    tp = np.diag(cm).astype(np.float64)
    denominator = (cm.sum(axis=0) + cm.sum(axis=1)).astype(np.float64)
    return _safe_divide(2.0 * tp, denominator)


def mean_iou(cm: NDArray[np.integer[Any]]) -> float:
    """Mean of the defined per-class IoU values."""
    iou = per_class_iou(cm)
    return float(np.nanmean(iou)) if np.any(~np.isnan(iou)) else float("nan")


def overall_accuracy(cm: NDArray[np.integer[Any]]) -> float:
    total = cm.sum()
    return float(np.trace(cm) / total) if total else float("nan")


def producers_accuracy(cm: NDArray[np.integer[Any]]) -> FloatArray:
    """Per class: correct pixels over reference pixels of the class (recall)."""
    return _safe_divide(np.diag(cm).astype(np.float64), cm.sum(axis=1).astype(np.float64))


def users_accuracy(cm: NDArray[np.integer[Any]]) -> FloatArray:
    """Per class: correct pixels over pixels predicted as the class (precision)."""
    return _safe_divide(np.diag(cm).astype(np.float64), cm.sum(axis=0).astype(np.float64))


def pixel_metrics(cm: NDArray[np.integer[Any]]) -> dict[str, Any]:
    iou = per_class_iou(cm)
    f1 = per_class_f1(cm)
    return {
        "classes": list(CLASS_NAMES[: cm.shape[0]]),
        "iou": [_json_float(v) for v in iou],
        "f1": [_json_float(v) for v in f1],
        "producers_accuracy": [_json_float(v) for v in producers_accuracy(cm)],
        "users_accuracy": [_json_float(v) for v in users_accuracy(cm)],
        "mean_iou": _json_float(mean_iou(cm)),
        "overall_accuracy": _json_float(overall_accuracy(cm)),
        "confusion_matrix": cm.astype(int).tolist(),
        "pixels": int(cm.sum()),
    }


def false_discard_rate(
    true_fraction: FloatArray, predicted_fraction: FloatArray, threshold: float
) -> float:
    """Share of useful frames (true cloud fraction below threshold) that would be kept."""
    useful = send_mask(true_fraction, threshold)
    if not useful.any():
        return float("nan")
    kept = ~send_mask(predicted_fraction, threshold)
    return float((kept & useful).sum() / useful.sum())


def false_send_rate(
    true_fraction: FloatArray, predicted_fraction: FloatArray, threshold: float
) -> float:
    """Share of cloudy frames (true cloud fraction at or above threshold) that would be sent."""
    cloudy = ~send_mask(true_fraction, threshold)
    if not cloudy.any():
        return float("nan")
    sent = send_mask(predicted_fraction, threshold)
    return float((sent & cloudy).sum() / cloudy.sum())


def decision_accuracy(
    true_fraction: FloatArray, predicted_fraction: FloatArray, threshold: float
) -> float:
    if true_fraction.size == 0:
        return float("nan")
    same = send_mask(true_fraction, threshold) == send_mask(predicted_fraction, threshold)
    return float(same.mean())


def frame_metrics(
    true_fraction: FloatArray,
    predicted_fraction: FloatArray,
    thresholds: Sequence[float] = DECISION_THRESHOLDS,
) -> dict[str, Any]:
    if true_fraction.shape != predicted_fraction.shape:
        raise ValueError("fraction arrays must have the same shape")
    per_threshold = {}
    for t in thresholds:
        per_threshold[f"{t:.2f}"] = {
            "threshold": t,
            "false_discard_rate": _json_float(
                false_discard_rate(true_fraction, predicted_fraction, t)
            ),
            "false_send_rate": _json_float(false_send_rate(true_fraction, predicted_fraction, t)),
            "decision_accuracy": _json_float(
                decision_accuracy(true_fraction, predicted_fraction, t)
            ),
            "useful_frames": int(send_mask(true_fraction, t).sum()),
            "frames": int(true_fraction.size),
        }
    mae = float(np.abs(true_fraction - predicted_fraction).mean()) if true_fraction.size else None
    return {"cloud_fraction_mae": _json_float(mae), "thresholds": per_threshold}


def _json_float(value: float | None) -> float | None:
    """NaN and None become None (null in JSON)."""
    if value is None or not np.isfinite(value):
        return None
    return float(value)
