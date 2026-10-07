# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""INT8 static post-training quantisation with ONNX Runtime, and its evaluation.

Calibration uses patches from the training split only. The quantised model
uses the QDQ format with symmetric INT8 activations and per-channel
symmetric INT8 weights, which TensorRT reads as explicit quantisation.
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from onnxruntime import quantization as ortq

from tiefer_lab.config import EvaluationConfig
from tiefer_lab.data import cache
from tiefer_lab.data.dataset import normalised_patch
from tiefer_lab.data.transforms import crop_back, pad_to_shape
from tiefer_lab.evaluate import Scores
from tiefer_lab.export.onnx_export import INPUT_NAME
from tiefer_lab.export.verify import padded_patches, session

# A drop of mean IoU larger than this (one point) is reported, with
# quantisation-aware training proposed as future work.
MAX_MEAN_IOU_DROP = 0.01


class CalibrationReader(ortq.CalibrationDataReader):  # type: ignore[misc]
    """Feeds normalised, padded training patches to the calibrator."""

    def __init__(
        self,
        data: cache.SplitData,
        mean: NDArray[np.float32],
        std: NDArray[np.float32],
        input_size: int,
        count: int,
        seed: int = 0,
    ) -> None:
        if data.split != "train":
            raise ValueError("calibration uses the training split only")
        n = min(count, len(data))
        rng = np.random.default_rng(seed)
        self.positions = sorted(int(i) for i in rng.choice(len(data), size=n, replace=False))
        self.data, self.mean, self.std, self.input_size = data, mean, std, input_size
        self._iter: Iterator[dict[str, NDArray[np.float32]]] | None = None

    def _batches(self) -> Iterator[dict[str, NDArray[np.float32]]]:
        for i in self.positions:
            image = normalised_patch(self.data, i, self.mean, self.std)
            yield {INPUT_NAME: pad_to_shape(image, (self.input_size, self.input_size))[None]}

    def get_next(self) -> dict[str, NDArray[np.float32]] | None:
        if self._iter is None:
            self._iter = self._batches()
        return next(self._iter, None)

    def rewind(self) -> None:
        self._iter = None


def quantise_int8(fp32_path: Path, out_path: Path, reader: CalibrationReader) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        prepared = Path(tmp) / "prepared.onnx"
        ortq.quant_pre_process(fp32_path, prepared, skip_symbolic_shape=True)
        ortq.quantize_static(
            prepared,
            out_path,
            reader,
            quant_format=ortq.QuantFormat.QDQ,
            per_channel=True,
            activation_type=ortq.QuantType.QInt8,
            weight_type=ortq.QuantType.QInt8,
            calibrate_method=ortq.CalibrationMethod.MinMax,
            extra_options={"ActivationSymmetric": True, "WeightSymmetric": True},
        )
    return out_path


def score_onnx(
    onnx_path: Path,
    data: cache.SplitData,
    mean: NDArray[np.float32],
    std: NDArray[np.float32],
    input_size: int,
    settings: EvaluationConfig,
) -> dict[str, Any]:
    """Pixel and frame metrics of an ONNX model on a whole split."""
    sess = session(onnx_path)
    input_type = sess.get_inputs()[0].type
    dtype = np.float16 if "float16" in input_type else np.float32
    scores = Scores()
    for batch, size, i, _ in padded_patches(data, mean, std, input_size):
        logits = sess.run(None, {INPUT_NAME: batch.astype(dtype)})[0]
        pred = crop_back(np.asarray(logits).argmax(axis=1)[0].astype(np.uint8), size)
        scores.add(pred, np.asarray(data.labels[i]))
    return scores.report(settings)


def compare_reports(fp32: dict[str, Any], int8: dict[str, Any]) -> dict[str, Any]:
    """Change in mean IoU, cloud and shadow BOA and false discard rate from FP32 to INT8."""

    def delta(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else b - a

    def boa(report: dict[str, Any], problem: str) -> float | None:
        value = report.get("binary", {}).get(problem, {}).get("median_boa")
        return None if value is None else float(value)

    miou_change = delta(fp32["pixel"]["mean_iou"], int8["pixel"]["mean_iou"])
    out: dict[str, Any] = {
        "mean_iou_fp32": fp32["pixel"]["mean_iou"],
        "mean_iou_int8": int8["pixel"]["mean_iou"],
        "mean_iou_change": miou_change,
        "false_discard_rate_fp32": fp32["false_discard_rate"],
        "false_discard_rate_int8": int8["false_discard_rate"],
        "false_discard_rate_change": delta(fp32["false_discard_rate"], int8["false_discard_rate"]),
        "max_mean_iou_drop": MAX_MEAN_IOU_DROP,
        "cloud_boa_change": delta(boa(fp32, "cloud"), boa(int8, "cloud")),
        "shadow_boa_change": delta(boa(fp32, "shadow"), boa(int8, "shadow")),
    }
    if miou_change is not None and -miou_change > MAX_MEAN_IOU_DROP:
        out["note"] = (
            "INT8 lowers mean IoU by more than one point; quantisation-aware training is "
            "proposed as future work"
        )
    return out
