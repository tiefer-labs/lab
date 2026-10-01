# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""ONNX export round trip on a tiny untrained model, and the export command."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pytest
import torch

from tests.test_model_budget import ALLOWED_OPS
from tiefer_lab import train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache, cache
from tiefer_lab.export import __main__ as export_cli
from tiefer_lab.export import onnx_export, verify
from tiefer_lab.models.cloud_filter import build_model


def _tiny_model() -> torch.nn.Module:
    torch.manual_seed(0)
    model = build_model((8, 16, 32))
    model.train()
    with torch.no_grad():
        model(torch.randn(4, 4, 64, 64))  # non-trivial batch norm statistics
    return model.eval()


def test_fp32_round_trip_matches_pytorch(tmp_path: Path) -> None:
    model = _tiny_model()
    path = onnx_export.export_fp32(model, tmp_path / "m.onnx", input_size=64, opset=17)
    ops = set(onnx_export.operator_types(path))
    assert ops <= ALLOWED_OPS and "BatchNormalization" not in ops and "Identity" not in ops
    x = np.random.default_rng(1).normal(size=(1, 4, 64, 64)).astype(np.float32)
    batches = [(x, (64, 64), 0)]
    agreement = verify.compare(path, model, batches)
    assert agreement.argmax_agreement == 1.0
    assert agreement.max_abs_logit_difference < 1e-4
    verify.check(agreement, max_difference=1e-3, min_agreement=0.999)


def test_dynamic_batch_and_fp16(tmp_path: Path) -> None:
    model = _tiny_model()
    dynamic = onnx_export.export_fp32(model, tmp_path / "d.onnx", 64, 17, dynamic_batch=True)
    x = np.random.default_rng(2).normal(size=(3, 4, 64, 64)).astype(np.float32)
    out = ort.InferenceSession(str(dynamic)).run(None, {onnx_export.INPUT_NAME: x})[0]
    assert out.shape == (3, 4, 64, 64)
    fixed = onnx_export.export_fp32(model, tmp_path / "f.onnx", 64, 17)
    half = onnx_export.export_fp16(fixed, tmp_path / "h.onnx")
    agreement = verify.compare(half, model, [(x[:1], (64, 64), 0)])
    assert agreement.argmax_agreement > 0.99


def test_verification_fails_loudly_on_mismatch(tmp_path: Path) -> None:
    path = onnx_export.export_fp32(_tiny_model(), tmp_path / "m.onnx", 64, 17)
    torch.manual_seed(99)
    other = build_model((8, 16, 32)).eval()
    x = np.random.default_rng(3).normal(size=(1, 4, 64, 64)).astype(np.float32)
    agreement = verify.compare(path, other, [(x, (64, 64), 0)])
    with pytest.raises(verify.VerificationError):
        verify.check(agreement, max_difference=1e-3, min_agreement=0.999)


def test_export_command_writes_files_and_report(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    config = config_from_dict(
        {
            "name": "tiny",
            "data": {"cache_name": "synthetic", "crop_size": 32, "batch_size": 4, "num_workers": 0},
            "model": {"widths": [8, 16]},
            "train": {"epochs": 1, "max_steps_per_epoch": 2},
            "evaluation": {"bootstrap_resamples": 100},
            "export": {"input_size": 64, "calibration_patches": 4},
        }
    )
    run = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-export"
    train.train(config, run, device_name="cpu", allow_synthetic=True)
    assert export_cli.main(["--run", str(run), "--allow-synthetic"]) == 0
    for name in export_cli.FILES.values():
        assert (run / "export" / name).is_file()
    text = (tiefer_env["TIEFER_REPORTS_DIR"] / "export" / "tiny-export.json").read_text()
    report = json.loads(text)
    assert report["smoke"] is True
    assert report["verification"]["fp32"]["argmax_agreement"] >= 0.999
    assert len(report["files"]["fp32"]["sha256"]) == 64
    assert report["files"]["int8"]["path"].startswith("$TIEFER_RUNS_DIR/")
    assert "change" in report["quantisation"]["val"]
    assert "test" not in report["quantisation"]
    assert str(tiefer_env["TIEFER_RUNS_DIR"]) not in text
    assert not cache.is_synthetic({"source": "cloudsen12"})
