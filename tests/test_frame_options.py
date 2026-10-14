# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cloud bias, soft fraction and the INT8 options: by hand and on synthetic data."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import pytest
import torch

from tiefer_lab import calibrate, compare, evaluate, train
from tiefer_lab.config import config_from_dict, dump_toml
from tiefer_lab.data import build_cache
from tiefer_lab.export import __main__ as export
from tiefer_lab.models.cloud_filter import CloudBias, build_model, fold_cloud_bias


def test_folded_bias_equals_the_wrapper() -> None:
    torch.manual_seed(0)
    model = build_model((8, 16)).eval()
    x = torch.randn(1, 4, 32, 32)
    with torch.no_grad():
        wrapped = CloudBias(model, -0.7)(x)
        folded = fold_cloud_bias(model, -0.7)(x)
        plain = model(x)
    torch.testing.assert_close(wrapped, folded)
    torch.testing.assert_close(folded[:, 1] - plain[:, 1], torch.full_like(plain[:, 1], -0.7))
    torch.testing.assert_close(folded[:, 0], plain[:, 0])


def test_bias_rule_by_hand() -> None:
    # Two patches, every labelled pixel has margin +0.5 (cloud) in patch 0 and +0.12 in patch 1.
    logits = np.zeros((4, 2, 2), np.float32)
    logits[1] = 0.5
    hist0 = calibrate.margin_histogram(logits, np.zeros((2, 2), np.int64))
    logits[1] = 0.12
    hist1 = calibrate.margin_histogram(logits, np.zeros((2, 2), np.int64))
    assert calibrate.fraction_after_bias(hist0, 0.0) == 1.0
    assert calibrate.fraction_after_bias(hist1, -0.15) == 0.0
    assert calibrate.fraction_after_bias(hist0, -0.15) == 1.0
    # Patch 0 is truly cloudy (0.9), patch 1 is useful (0.1) but predicted cloudy at 0:
    # the smallest bias that sends patch 1 and keeps patch 0 is -0.15.
    out = calibrate.choose_bias([hist0, hist1], np.array([0.9, 0.1]), 0.5)
    assert out["at_zero"]["false_discard_rate"] == 1.0
    assert out["bias"] == -0.15
    assert out["chosen"]["detected"] == 1.0


def test_temperature_by_hand() -> None:
    # Over-confident logits on pixels that are right half of the time: T above 1 fits.
    logits = np.array([[10.0, 0, 0, 0], [10.0, 0, 0, 0]], np.float32)
    labels = np.array([0, 1])
    out = calibrate.fit_temperature(logits, labels)
    assert out["temperature"] > 1.0


@pytest.fixture
def run(tiefer_env: dict[str, Path]) -> Path:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    raw = {
        "name": "tiny",
        "data": {
            "cache_name": "synthetic",
            "crop_size": 32,
            "batch_size": 4,
            "eval_batch_size": 2,
            "num_workers": 0,
        },
        "model": {"widths": [8, 16]},
        "train": {"epochs": 1, "max_steps_per_epoch": 1, "log_every": 1},
        "evaluation": {"bootstrap_resamples": 100},
        "export": {"calibration_patches": 4},
    }
    out = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-seed0-x"
    train.train(config_from_dict(raw), out, device_name="cpu", allow_synthetic=True)
    return out


def test_options_change_nothing_unless_asked(run: Path, tiefer_env: dict[str, Path]) -> None:
    plain = json.loads(evaluate.evaluate_run(run, "val", allow_synthetic=True).read_text())
    assert "options" not in plain
    with pytest.raises(train.TrainingError, match="calibrate"):
        evaluate.evaluate_run(run, "val", allow_synthetic=True, cloud_bias="auto")
    assert calibrate.main(["--run", str(run), "--device", "cpu"]) == 0
    zero = json.loads(
        evaluate.evaluate_run(run, "val", allow_synthetic=True, cloud_bias="0").read_text()
    )
    assert zero["options"] == {"cloud_bias": 0.0}
    assert zero["model"]["pixel"] == plain["model"]["pixel"]
    soft_path = evaluate.evaluate_run(run, "val", allow_synthetic=True, fraction="soft")
    soft = json.loads(soft_path.read_text())
    assert soft_path.name.endswith("_soft.json")
    assert soft["options"]["fraction"] == "soft" and soft["options"]["temperature"] > 0
    # The temperature never changes the argmax, so the pixel metrics stay.
    assert soft["model"]["pixel"]["confusion_matrix"] == plain["model"]["pixel"]["confusion_matrix"]


def test_export_options_keep_allowed_operators(
    run: Path, tiefer_env: dict[str, Path], tmp_path: Path
) -> None:
    config = config_from_dict(
        {
            "name": "tiny_int8options",
            "model": {"widths": [8, 16]},
            "export": {
                "input_size": 64,
                "calibration_patches": 4,
                "calibrate_method": "percentile",
                "calibration_stratified": True,
                "keep_fp_first_last": True,
                "input_clip_percentile": 0.5,
            },
        }
    )
    path = tmp_path / "tiny_int8options.toml"
    path.write_text(dump_toml(config), encoding="utf-8")
    args = [
        "--run",
        str(run),
        "--allow-synthetic",
        "--settings-from",
        str(path),
        "--cloud-bias",
        "-0.5",
    ]
    assert export.main(args) == 0
    report_path = tiefer_env["TIEFER_REPORTS_DIR"] / "export"
    report = json.loads(next(report_path.glob("*_cloudbias_tiny_int8options.json")).read_text())
    assert report["options"]["cloud_bias"] == -0.5
    assert report["options"]["export_config"] == "tiny_int8options"
    assert report["options"]["input_clip"]["low"] < report["options"]["input_clip"]["high"]
    assert report["calibration"]["method"] == "percentile"
    assert compare.operators_allowed(report)
    int8 = onnx.load(
        str(run / "export" / "cloudbias" / "tiny_int8options" / "cloud_filter_int8.onnx")
    )
    convs = [n for n in int8.graph.node if n.op_type == "Conv"]
    inputs = {n.output[0]: n.op_type for n in int8.graph.node}
    # The first convolution reads floating-point input, not a DequantizeLinear output.
    assert inputs.get(convs[0].input[1]) != "DequantizeLinear"
