# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The cloud filter: a compact U-Net style network with depthwise separable convolutions.

Input: 4 bands (blue, green, red, near infrared), normalised reflectance.
Output: logits for 4 classes (clear, thick cloud, thin cloud, cloud shadow).

Only operators that TensorRT handles well in INT8 are used: convolution,
batch norm (folded at export), ReLU6, max pooling, bilinear upsampling and
concatenation. There is no attention and there are no custom operators.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterator, Sequence
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn
from torch.nn.utils.fusion import fuse_conv_bn_eval
from torch.utils.data import DataLoader

from tiefer_lab.data.source import NUM_CLASSES
from tiefer_lab.data.transforms import crop_back
from tiefer_lab.utils.devices import Precision, autocast

IN_CHANNELS = 4
PARAMETER_BUDGET = 1_000_000
REFERENCE_INPUT = (1, IN_CHANNELS, 512, 512)


class ConvBNAct(nn.Sequential):
    """Convolution, batch norm and ReLU6 (activation optional)."""

    def __init__(
        self, cin: int, cout: int, kernel: int, groups: int = 1, activation: bool = True
    ) -> None:
        layers: list[nn.Module] = [
            nn.Conv2d(cin, cout, kernel, padding=kernel // 2, groups=groups, bias=False),
            nn.BatchNorm2d(cout),
        ]
        if activation:
            layers.append(nn.ReLU6(inplace=True))
        super().__init__(*layers)


class SeparableConv(nn.Sequential):
    """Depthwise 3 x 3 convolution followed by a pointwise 1 x 1 convolution."""

    def __init__(self, cin: int, cout: int) -> None:
        super().__init__(ConvBNAct(cin, cin, 3, groups=cin), ConvBNAct(cin, cout, 1))


class Block(nn.Sequential):
    def __init__(self, cin: int, cout: int) -> None:
        super().__init__(SeparableConv(cin, cout), SeparableConv(cout, cout))


class CloudFilterNet(nn.Module):
    """Encoder with max pooling, decoder with bilinear upsampling and skip connections.

    The input height and width must be multiples of 2 ** (len(widths) - 1).
    """

    def __init__(
        self, widths: Sequence[int] = (16, 32, 64, 128, 256), in_channels: int = IN_CHANNELS
    ) -> None:
        super().__init__()
        self.widths = tuple(widths)
        self.in_channels = in_channels
        self.stem = ConvBNAct(in_channels, widths[0], 3)
        self.encoder = nn.ModuleList([Block(widths[0], widths[0])])
        for cin, cout in itertools.pairwise(widths):
            self.encoder.append(Block(cin, cout))
        self.pool = nn.MaxPool2d(2)
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.decoder = nn.ModuleList(
            Block(widths[i + 1] + widths[i], widths[i]) for i in reversed(range(len(widths) - 1))
        )
        self.head = nn.Conv2d(widths[0], NUM_CLASSES, 1)

    @property
    def downsampling(self) -> int:
        return int(2 ** (len(self.widths) - 1))

    @property
    def input_bands(self) -> int:
        return self.in_channels

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skips = []
        x = self.encoder[0](self.stem(x))
        for stage in self.encoder[1:]:
            skips.append(x)
            x = stage(self.pool(x))
        for stage in self.decoder:
            x = stage(torch.cat([self.up(x), skips.pop()], dim=1))
        out: torch.Tensor = self.head(x)
        return out


def build_model(widths: Sequence[int], in_channels: int = IN_CHANNELS) -> CloudFilterNet:
    return CloudFilterNet(widths, in_channels)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def count_macs(model: nn.Module, input_shape: tuple[int, ...] | None = None) -> int:
    """Multiply-accumulate operations of convolutions for one forward pass.

    Counts every Conv2d (out_elements x in_channels / groups x kernel area).
    Batch norm, activations, pooling and upsampling are not counted; batch
    norm disappears when folded at export. The default input is one 512 x 512
    tile with the model's input bands.
    """
    if input_shape is None:
        input_shape = (1, int(getattr(model, "input_bands", IN_CHANNELS)), 512, 512)
    total = 0

    def hook(module: nn.Module, _inputs: Any, output: torch.Tensor) -> None:
        nonlocal total
        assert isinstance(module, nn.Conv2d)
        kh, kw = module.kernel_size
        total += output.numel() * (module.in_channels // module.groups) * kh * kw

    handles = [m.register_forward_hook(hook) for m in model.modules() if isinstance(m, nn.Conv2d)]
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            model(torch.zeros(input_shape))
    finally:
        for h in handles:
            h.remove()
        model.train(was_training)
    return total


def fold_batch_norm[M: nn.Module](model: M) -> M:
    """A copy in eval mode with every batch norm folded into its convolution."""
    folded = copy.deepcopy(model).eval()
    for module in folded.modules():
        if isinstance(module, ConvBNAct):
            conv, bn = module[0], module[1]
            assert isinstance(conv, nn.Conv2d) and isinstance(bn, nn.BatchNorm2d)
            module[0] = fuse_conv_bn_eval(conv, bn)
            del module[1]
    return folded


def predict_masks(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, int]],
    device: torch.device,
    precision: Precision,
) -> Iterator[tuple[int, NDArray[np.uint8], NDArray[np.int64]]]:
    """Predicted masks for an EvalPatches loader, cropped back to the label size.

    Yields (patch position, predicted mask, reference label).
    """
    model.eval()
    channels_last = device.type == "cuda"
    with torch.no_grad():
        for images, labels, indexes in loader:
            images = images.to(device, non_blocking=True)
            if channels_last:
                images = images.contiguous(memory_format=torch.channels_last)
            with autocast(device, precision):
                logits = model(images)
            preds = logits.argmax(dim=1).to(torch.uint8).cpu().numpy()
            for pred, label, index in zip(preds, labels.numpy(), indexes.tolist(), strict=True):
                yield int(index), crop_back(pred, label.shape), label.astype(np.int64)
