# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""A U-Net whose encoder uses ConvNeXt-style blocks, for the largest size of the ladder.

Encoder block: depthwise 7 x 7 convolution, batch norm, a 1 x 1 expansion
to four times the width, ReLU6, a 1 x 1 projection back, and a residual
connection. Batch norm and ReLU6 replace the layer norm and GELU of the
ConvNeXt paper, so the operators stay those of the separable U-Net
(convolution, batch norm, ReLU6, upsampling, concatenation); downsampling is
a 2 x 2 convolution with stride 2. The decoder is that of the separable
U-Net. No pretrained weights are used; every model is trained from scratch.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence

import torch
from torch import nn

from tiefer_lab.data.source import NUM_CLASSES
from tiefer_lab.models.cloud_filter import Block, ConvBNAct

BLOCKS_PER_STAGE = 2
EXPANSION = 4


class NeXtBlock(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.body = nn.Sequential(
            nn.Conv2d(width, width, 7, padding=3, groups=width, bias=False),
            nn.BatchNorm2d(width),
            nn.Conv2d(width, width * EXPANSION, 1),
            nn.ReLU6(inplace=True),
            nn.Conv2d(width * EXPANSION, width, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out: torch.Tensor = x + self.body(x)
        return out


def _stage(width: int) -> nn.Sequential:
    return nn.Sequential(*[NeXtBlock(width) for _ in range(BLOCKS_PER_STAGE)])


class ConvNeXtUNet(nn.Module):
    """The input height and width must be multiples of 2 ** (len(widths) - 1)."""

    def __init__(self, widths: Sequence[int], in_channels: int) -> None:
        super().__init__()
        self.widths = tuple(widths)
        self.in_channels = in_channels
        self.stem = ConvBNAct(in_channels, widths[0], 3)
        self.stages = nn.ModuleList([_stage(widths[0])])
        self.downs = nn.ModuleList()
        for cin, cout in itertools.pairwise(widths):
            self.downs.append(
                nn.Sequential(nn.Conv2d(cin, cout, 2, stride=2, bias=False), nn.BatchNorm2d(cout))
            )
            self.stages.append(_stage(cout))
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
        x = self.stages[0](self.stem(x))
        skips = []
        for down, stage in zip(self.downs, self.stages[1:], strict=True):
            skips.append(x)
            x = stage(down(x))
        for block in self.decoder:
            x = block(torch.cat([self.up(x), skips.pop()], dim=1))
        out: torch.Tensor = self.head(x)
        return out
