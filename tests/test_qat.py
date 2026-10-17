# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Quantisation-aware fine-tuning: off by default, trains, exports QDQ with allowed operators."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import pytest
import torch
from onnx import numpy_helper

from tests.test_model_budget import ALLOWED_OPS
from tiefer_lab import train
from tiefer_lab.config import ConfigError, TrainConfig, config_from_dict, load_config
from tiefer_lab.data import build_cache
from tiefer_lab.export import __main__ as export_cli
from tiefer_lab.export import onnx_export
from tiefer_lab.models import qat
from tiefer_lab.models.cloud_filter import build_model

QDQ = {"QuantizeLinear", "DequantizeLinear"}


def _tiny_model() -> torch.nn.Module:
    torch.manual_seed(0)
    model = build_model((8, 16, 32))
    model.train()
    with torch.no_grad():
        model(torch.randn(4, 4, 64, 64))
    return model.eval()


def test_off_by_default(repo_root: Path) -> None:
    assert TrainConfig().qat is False
    assert load_config(repo_root / "configs" / "sieb.toml").train.qat is False
    config = load_config(repo_root / "configs" / "sieb_qat.toml")
    assert config.train.qat and config.train.init_checkpoint == "sieb-seed0"


@pytest.mark.parametrize(
    "train_values, model_values, message",
    [
        ({"qat": True}, {}, "init_checkpoint"),
        (
            {"qat": True, "init_checkpoint": "x"},
            {"architecture": "convnext_unet"},
            "separable_unet",
        ),
    ],
)
def test_qat_needs_a_start_and_the_separable_unet(
    train_values: dict[str, object], model_values: dict[str, object], message: str
) -> None:
    raw: dict[str, object] = {
        "name": "q",
        "data": {"cache_name": "c"},
        "model": {"widths": [8, 16], **model_values},
        "train": train_values,
    }
    with pytest.raises(ConfigError, match=message):
        config_from_dict(raw)


def test_fake_quantisation_follows_the_float_model_and_learns_its_scales() -> None:
    model = _tiny_model()
    prepared = qat.prepare(model)
    convs = [m for m in prepared.modules() if isinstance(m, qat.QatConv2d)]
    assert convs and not any(isinstance(m, torch.nn.BatchNorm2d) for m in prepared.modules())
    x = torch.randn(2, 4, 64, 64)
    prepared.train()
    prepared(x)
    assert all(float(m.input_amax) > 0 for m in convs)
    prepared.eval()
    with torch.no_grad():
        float_out = model(x)
        quant_out = prepared(x)
        stripped = qat.float_copy(prepared)(x)
    assert torch.allclose(stripped, float_out, atol=1e-4)
    # INT8 rounding moves the logits a little, not the classes of most pixels.
    agreement = (quant_out.argmax(1) == float_out.argmax(1)).float().mean()
    assert agreement > 0.9 and not torch.equal(quant_out, float_out)


def test_qdq_export_has_allowed_operators_and_matches_pytorch(tmp_path: Path) -> None:
    prepared = qat.prepare(_tiny_model())
    prepared.train()
    prepared(torch.randn(2, 4, 64, 64))
    frozen = qat.frozen(prepared)
    path = onnx_export.export_fp32(frozen, tmp_path / "int8.onnx", 64, 17)
    ops = set(onnx_export.operator_types(path))
    assert ops >= QDQ and ops <= ALLOWED_OPS | QDQ
    model = onnx.load(path)
    constants = {i.name: numpy_helper.to_array(i) for i in model.graph.initializer}
    for node in model.graph.node:
        if node.op_type == "Constant":
            constants[node.output[0]] = numpy_helper.to_array(node.attribute[0].t)
    for node in model.graph.node:
        if node.op_type == "QuantizeLinear":
            # Symmetric INT8, zero point 0: the explicit quantisation TensorRT reads.
            zero = constants[node.input[2]]
            assert zero.dtype == np.int8 and not zero.any()
    x = np.random.default_rng(4).normal(size=(1, 4, 64, 64)).astype(np.float32)
    onnx_out = ort.InferenceSession(str(path)).run(None, {onnx_export.INPUT_NAME: x})[0]
    with torch.no_grad():
        torch_out = frozen(torch.from_numpy(x)).numpy()
    assert (onnx_out.argmax(1) == torch_out.argmax(1)).mean() > 0.99
    plain = onnx_export.export_fp32(qat.float_copy(prepared), tmp_path / "fp32.onnx", 64, 17)
    assert set(onnx_export.operator_types(plain)) <= ALLOWED_OPS


def test_a_qat_run_fine_tunes_and_exports_its_own_int8_file(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    raw: dict[str, object] = {
        "name": "tiny",
        "data": {"cache_name": "synthetic", "crop_size": 32, "batch_size": 4, "num_workers": 0},
        "model": {"widths": [8, 16]},
        "train": {"epochs": 1, "max_steps_per_epoch": 2},
        "evaluation": {"bootstrap_resamples": 100},
        "export": {"input_size": 64, "calibration_patches": 4},
    }
    runs = tiefer_env["TIEFER_RUNS_DIR"]
    train.train(
        config_from_dict(raw), runs / "tiny-seed0-a", device_name="cpu", allow_synthetic=True
    )
    raw["name"] = "tiny_qat"
    raw["train"] = {
        "epochs": 1,
        "max_steps_per_epoch": 2,
        "qat": True,
        "init_checkpoint": "tiny-seed0",
    }
    run = runs / "tiny_qat-seed0-a"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    assert export_cli.main(["--run", str(run), "--allow-synthetic"]) == 0
    report = json.loads(
        (tiefer_env["TIEFER_REPORTS_DIR"] / "export" / "tiny_qat-seed0-a.json").read_text()
    )
    assert report["calibration"]["method"] == "quantisation-aware fine-tuning"
    assert QDQ <= set(report["operators"]["int8"]) <= ALLOWED_OPS | QDQ
    assert set(report["operators"]["fp32"]) <= ALLOWED_OPS
