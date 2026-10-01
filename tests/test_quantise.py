# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""INT8 static quantisation on synthetic data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnx
import pytest
import torch

from tiefer_lab.config import EvaluationConfig
from tiefer_lab.data import build_cache, cache
from tiefer_lab.export import onnx_export, quantise
from tiefer_lab.models.cloud_filter import build_model


@pytest.fixture
def synthetic(tiefer_env: dict[str, Path]) -> Path:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "5", "--patch-size", "64"])
    return cache.cache_dir(build_cache.SYNTHETIC_NAME)


def test_int8_model_is_qdq_and_scores(synthetic: Path, tmp_path: Path) -> None:
    torch.manual_seed(0)
    model = build_model((8, 16)).eval()
    fp32 = onnx_export.export_fp32(model, tmp_path / "fp32.onnx", 64, 17)
    index = cache.read_index(synthetic)
    mean, std = cache.normalisation(index)
    train_data = cache.load_split(synthetic, "train")
    reader = quantise.CalibrationReader(train_data, mean, std, 64, count=3)
    assert len(reader.positions) == 3
    int8 = quantise.quantise_int8(fp32, tmp_path / "int8.onnx", reader)
    ops = {node.op_type for node in onnx.load(int8).graph.node}
    assert {"QuantizeLinear", "DequantizeLinear"} <= ops
    settings = EvaluationConfig(bootstrap_resamples=100)
    val = cache.load_split(synthetic, "val")
    fp32_report = quantise.score_onnx(fp32, val, mean, std, 64, settings)
    int8_report = quantise.score_onnx(int8, val, mean, std, 64, settings)
    assert fp32_report["patches"] == int8_report["patches"] == 5
    change = quantise.compare_reports(fp32_report, int8_report)
    assert {"mean_iou_change", "false_discard_rate_change"} <= set(change)


def test_calibration_uses_training_split_only(synthetic: Path) -> None:
    mean, std = cache.normalisation(cache.read_index(synthetic))
    with pytest.raises(ValueError, match="training split"):
        quantise.CalibrationReader(cache.load_split(synthetic, "val"), mean, std, 64, 2)


def test_large_drop_is_reported_with_proposal() -> None:
    fp32 = {"pixel": {"mean_iou": 0.80}, "false_discard_rate": 0.05}
    int8 = {"pixel": {"mean_iou": 0.77}, "false_discard_rate": 0.07}
    change = quantise.compare_reports(fp32, int8)
    assert change["mean_iou_change"] == pytest.approx(-0.03)
    assert "quantisation-aware training" in change["note"]
    small = quantise.compare_reports(
        fp32, {"pixel": {"mean_iou": 0.795}, "false_discard_rate": 0.05}
    )
    assert "note" not in small
    assert np.isclose(small["false_discard_rate_change"], 0.0)
