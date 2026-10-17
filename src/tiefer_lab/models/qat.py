# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Quantisation-aware fine-tuning (`train.qat`), off by default.

A run with `qat = true` starts from the best.pt of another run of this
repository (`init_checkpoint`), folds every batch norm into its convolution
and then fine-tunes with every convolution quantised on the fly, in the form
that the INT8 export of `tiefer_lab.export.quantise` writes for TensorRT:

- weights: symmetric INT8 per output channel, zero point 0, scale the largest
  absolute weight of the channel / 127;
- the input of each convolution: symmetric INT8 per tensor, zero point 0,
  scale a running largest absolute value / 127, updated in training (an
  exponential average with weight ACTIVATION_MOMENTUM for each new batch).

Rounding passes the gradient straight through (PyTorch's fake quantisation).
Bias and activations other than convolution inputs stay in floating point,
as in the post-training INT8 files. For the export the scales are frozen into
constants (`freeze`), so the ONNX graph holds QuantizeLinear and
DequantizeLinear pairs around the allowed operators of docs/SPEC.md,
section 4, and nothing else (`tests/test_qat.py`).
"""

from __future__ import annotations

import copy

import torch
from torch import nn
from torch.nn import functional

from tiefer_lab.models.cloud_filter import fold_batch_norm

QMIN, QMAX = -128, 127
# The scale of a quantised value is the largest absolute value / 127, so the
# grid is symmetric around zero.
LEVELS = 127.0
ACTIVATION_MOMENTUM = 0.01
EPS = 1e-8


class QatConv2d(nn.Module):
    """A convolution whose input and weight are quantised to INT8 on the fly."""

    input_amax: torch.Tensor
    frozen_input_scale: torch.Tensor
    frozen_weight_scale: torch.Tensor
    frozen_input_zero: torch.Tensor
    frozen_weight_zero: torch.Tensor

    def __init__(self, conv: nn.Conv2d) -> None:
        super().__init__()
        self.conv = conv
        # 0 until the first training batch; a run's checkpoint stores it.
        self.register_buffer("input_amax", torch.zeros(()))
        self.frozen = False

    def _zero(self, like: torch.Tensor) -> torch.Tensor:
        return torch.zeros_like(like, dtype=torch.int32)

    def input_scale(self) -> torch.Tensor:
        return (self.input_amax / LEVELS).clamp(min=EPS)

    def weight_scale(self) -> torch.Tensor:
        amax = self.conv.weight.detach().abs().amax(dim=(1, 2, 3))
        return (amax / LEVELS).clamp(min=EPS)

    def freeze(self) -> None:
        """Store the scales and zero points as constants, so the export has no casts."""
        in_scale, w_scale = self.input_scale().float(), self.weight_scale().float()
        self.register_buffer("frozen_input_scale", in_scale.clone())
        self.register_buffer("frozen_weight_scale", w_scale.clone())
        self.register_buffer("frozen_input_zero", self._zero(in_scale))
        self.register_buffer("frozen_weight_zero", self._zero(w_scale))
        self.frozen = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.training:
            with torch.no_grad():
                amax = x.detach().abs().amax().float()
                if float(self.input_amax) == 0.0:
                    self.input_amax.copy_(amax)
                else:
                    self.input_amax.lerp_(amax, ACTIVATION_MOMENTUM)
        if self.frozen:
            in_scale, w_scale = self.frozen_input_scale, self.frozen_weight_scale
            in_zero, w_zero = self.frozen_input_zero, self.frozen_weight_zero
        else:
            in_scale, w_scale = self.input_scale().float(), self.weight_scale().float()
            in_zero, w_zero = self._zero(in_scale), self._zero(w_scale)
        x = torch.fake_quantize_per_tensor_affine(x, in_scale, in_zero, QMIN, QMAX)
        conv = self.conv
        weight = torch.fake_quantize_per_channel_affine(conv.weight, w_scale, w_zero, 0, QMIN, QMAX)
        return functional.conv2d(
            x, weight, conv.bias, conv.stride, conv.padding, conv.dilation, conv.groups
        )


def _replace_convolutions(module: nn.Module) -> None:
    for name, child in module.named_children():
        if isinstance(child, nn.Conv2d):
            setattr(module, name, QatConv2d(child))
        else:
            _replace_convolutions(child)


def prepare[M: nn.Module](model: M) -> M:
    """A copy with batch norm folded and every Conv2d quantised on the fly."""
    folded = fold_batch_norm(model)
    for conv in folded.modules():
        if isinstance(conv, nn.Conv2d) and conv.bias is None:
            conv.bias = nn.Parameter(torch.zeros(conv.out_channels))
    _replace_convolutions(folded)
    return folded


def frozen[M: nn.Module](model: M) -> M:
    """An eval copy with every scale stored as a constant, for the INT8 export."""
    out = copy.deepcopy(model).eval()
    for module in out.modules():
        if isinstance(module, QatConv2d):
            module.freeze()
    return out


def float_copy[M: nn.Module](model: M) -> M:
    """An eval copy with the quantisation removed, for the FP32 and FP16 exports."""
    out = copy.deepcopy(model).eval()

    def strip(module: nn.Module) -> None:
        for name, child in module.named_children():
            if isinstance(child, QatConv2d):
                setattr(module, name, child.conv)
            else:
                strip(child)

    strip(out)
    return out
