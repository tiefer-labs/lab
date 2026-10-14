# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""A re-implementation of CloudScout (ESA Phi-sat-1), trained by Tiefer Lab.

This is a re-implementation trained by Tiefer Lab from random initialisation,
not the flown model. It follows the paper: CloudScout: A Deep Neural Network
for On-Board Cloud Detection on Hyperspectral Images, Remote Sensing 12(14),
2205, 2020, https://doi.org/10.3390/rs12142205, section 3.4.2 and Figure 7,
read on 14 October 2026:

- input: three bands (the text names Sentinel-2 bands 1, 2 and 8; Figure 7
  writes "Bands: 0, 1, 8", which is TODO(verify) against the authors);
- feature extraction: a convolutional size reduction layer (Figure 7: 5 x 5,
  stride 1, batch norm, ReLU, max pooling), then groups of 3 x 3, 1 x 1 and
  3 x 3 convolutions (the text says four groups; Figure 7 shows two 3 x 3
  blocks and a 1 x 1 block), and a global max pooling;
- decision: fully connected layers and a two-class softmax, cloudy or not;
- loss: binary cross-entropy with the penalty of a false positive (a
  not-cloudy frame called cloudy) doubled, Equation (2).

The paper does not give the number of filters of any layer; the widths of
the config are a design choice of this repository (docs/ASSUMPTIONS.md,
section 6). The fully connected layers are written as 1 x 1 convolutions and
the global max pooling as a max pooling over the whole map, so the exported
graph uses only the operators of docs/SPEC.md, section 4.

For the evaluation of this repository, the two frame logits become a
four-class map of the input's size: clear and thick cloud carry the two
logits, thin cloud and shadow a fixed large negative value, so every pixel of
a frame gets the frame's class and the predicted cloud fraction is 0 or 1.
Pixel metrics of this model are therefore not meaningful; its frame metrics
are.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence

import torch
import torch.nn.functional as F  # noqa: N812
from torch import nn

from tiefer_lab.data.source import NUM_CLASSES
from tiefer_lab.models.cloud_filter import ConvBNAct

# Logit of the classes the frame classifier never predicts.
NEVER = -1.0e4


class _Group(nn.Sequential):
    """3 x 3, 1 x 1 and 3 x 3 convolutions with batch norm and ReLU, then 2 x 2 max pooling."""

    def __init__(self, cin: int, cout: int) -> None:
        super().__init__(
            ConvBNAct(cin, cout, 3),
            ConvBNAct(cout, cout, 1),
            ConvBNAct(cout, cout, 3),
            nn.MaxPool2d(2),
        )


class CloudScoutNet(nn.Module):
    """Frame classifier; `forward` gives a four-class map, `frame_logits` the two logits.

    widths: the width of the size reduction layer, then one width per group.
    The input height and width must be multiples of `downsampling`.
    """

    def __init__(self, widths: Sequence[int], in_channels: int, hidden: int = 64) -> None:
        super().__init__()
        if len(widths) < 2:
            raise ValueError("cloudscout needs a stem width and at least one group width")
        self.widths = tuple(widths)
        self.in_channels = in_channels
        self.stem = nn.Sequential(ConvBNAct(in_channels, widths[0], 5), nn.MaxPool2d(2))
        self.groups = nn.Sequential(
            *[_Group(cin, cout) for cin, cout in itertools.pairwise(widths)]
        )
        self.decision = nn.Sequential(
            nn.Conv2d(widths[-1], hidden, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, 2, 1),
        )
        # Fixed map from the two frame logits to the four classes of this repository.
        self.to_classes = nn.Conv2d(2, NUM_CLASSES, 1)
        with torch.no_grad():
            self.to_classes.weight.zero_()
            self.to_classes.weight[0, 0] = 1.0
            self.to_classes.weight[1, 1] = 1.0
            bias = self.to_classes.bias
            assert bias is not None
            bias.copy_(torch.tensor([0.0, 0.0, NEVER, NEVER]))
        for p in self.to_classes.parameters():
            p.requires_grad_(False)

    @property
    def downsampling(self) -> int:
        return int(2 ** len(self.widths))

    @property
    def input_bands(self) -> int:
        return self.in_channels

    def _pooled(self, x: torch.Tensor) -> torch.Tensor:
        features = self.groups(self.stem(x))
        # Global max pooling as a max pooling over the whole map (an ONNX MaxPool).
        size = (int(features.shape[-2]), int(features.shape[-1]))
        return F.max_pool2d(features, kernel_size=size)

    def frame_logits(self, x: torch.Tensor) -> torch.Tensor:
        """(batch, 2) logits: not cloudy, cloudy."""
        out: torch.Tensor = self.decision(self._pooled(x))[:, :, 0, 0]
        return out

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.to_classes(self.decision(self._pooled(x)))
        # The pooled map is 1 x 1; a scale factor equal to the input size keeps the
        # exported graph to one Resize with constant scales (no Shape or Slice nodes).
        scale = (float(x.shape[-2]), float(x.shape[-1]))
        out: torch.Tensor = F.interpolate(logits, scale_factor=scale, mode="nearest")
        return out


def frame_loss(
    logits: torch.Tensor, cloudy: torch.Tensor, false_positive_weight: float = 2.0
) -> torch.Tensor:
    """Equation (2) of the paper: -(y log p + w (1 - y) log(1 - p)), mean over frames.

    `logits` are the (batch, 2) frame logits, `cloudy` is 1.0 for a cloudy frame
    and 0.0 otherwise, and p is the softmax probability of "cloudy". The paper
    uses w = 2, so that a false positive costs twice a false negative.
    """
    log_p = logits.float().log_softmax(dim=1)
    y = cloudy.float()
    per_frame = -(y * log_p[:, 1] + false_positive_weight * (1 - y) * log_p[:, 0])
    return per_frame.mean()
