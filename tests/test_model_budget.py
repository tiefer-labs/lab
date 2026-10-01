# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Parameter budget and the operator set seen by TensorRT."""

from __future__ import annotations

import io
import warnings
from pathlib import Path

import onnx
import pytest
import torch

from tiefer_lab.config import load_config
from tiefer_lab.models import cloud_filter
from tiefer_lab.models.losses import CrossEntropyDice, class_weights

# Operators TensorRT handles well in INT8, as ONNX node types. ReLU6 exports
# as Clip, bilinear upsampling as Resize; Constant nodes hold Resize scales.
ALLOWED_OPS = {
    "Conv",
    "ConvTranspose",
    "BatchNormalization",
    "Relu",
    "Clip",
    "MaxPool",
    "AveragePool",
    "Resize",
    "Concat",
    "Add",
    "Constant",
}


@pytest.mark.parametrize("name", ["l1_base.toml", "smoke.toml"])
def test_parameter_budget(repo_root: Path, name: str) -> None:
    config = load_config(repo_root / "configs" / name)
    model = cloud_filter.build_model(config.model.widths)
    assert cloud_filter.count_parameters(model) <= cloud_filter.PARAMETER_BUDGET


def _onnx_ops(model: torch.nn.Module, size: int = 64) -> list[str]:
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        torch.onnx.export(
            model, (torch.zeros(1, 4, size, size),), buffer, opset_version=17, dynamo=False
        )
    graph = onnx.load_from_string(buffer.getvalue()).graph
    constants = {init.name for init in graph.initializer}
    # The exporter de-duplicates identical initialisers through Identity nodes
    # (aliases of constants, no computation); the export step removes them.
    return [
        node.op_type
        for node in graph.node
        if not (node.op_type == "Identity" and set(node.input) <= constants)
    ]


def test_onnx_operators_are_allowed_and_batch_norm_is_folded() -> None:
    model = cloud_filter.build_model((16, 32, 64, 128, 256))
    folded = cloud_filter.fold_batch_norm(model)
    ops = _onnx_ops(folded)
    assert set(ops) <= ALLOWED_OPS, f"unexpected operators: {set(ops) - ALLOWED_OPS}"
    assert "BatchNormalization" not in ops
    assert "Conv" in ops and "Resize" in ops


def test_folding_keeps_outputs() -> None:
    torch.manual_seed(0)
    model = cloud_filter.build_model((8, 16, 32))
    # Give batch norm non-trivial statistics.
    model.train()
    with torch.no_grad():
        model(torch.randn(4, 4, 32, 32))
    model.eval()
    x = torch.randn(2, 4, 32, 32)
    with torch.no_grad():
        torch.testing.assert_close(
            cloud_filter.fold_batch_norm(model)(x), model(x), atol=1e-4, rtol=1e-4
        )


def test_macs_are_counted_for_reference_input() -> None:
    model = cloud_filter.build_model((8, 16))
    # Stem 4->8 3x3 at 32x32, then counted by hand for a 32 x 32 input.
    macs = cloud_filter.count_macs(model, (1, 4, 32, 32))
    stem = 32 * 32 * 8 * 4 * 9
    assert macs > stem
    assert cloud_filter.count_macs(model, (1, 4, 64, 64)) == 4 * macs


def test_loss_and_class_weights() -> None:
    weights = class_weights([600, 300, 100, 0])
    # Median of the present frequencies (0.6, 0.3, 0.1) is 0.3.
    torch.testing.assert_close(weights, torch.tensor([0.5, 1.0, 3.0, 0.0]))
    loss = CrossEntropyDice(weights, dice_weight=1.0)
    target = torch.randint(0, 3, (2, 8, 8))
    perfect = torch.nn.functional.one_hot(target, 4).permute(0, 3, 1, 2).float() * 20.0
    assert loss(perfect, target) < loss(torch.zeros(2, 4, 8, 8), target)
