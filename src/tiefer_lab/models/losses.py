# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cross-entropy plus Dice loss, with class weights from the training split."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812
from torch import nn


def class_weights(pixel_counts: Sequence[int]) -> torch.Tensor:
    """Median frequency balancing: weight_c = median(freq) / freq_c.

    Classes with no pixels get weight 0. Counts come from the training split
    (`class_pixels` in the cache index).
    """
    counts = np.asarray(pixel_counts, dtype=np.float64)
    if counts.sum() <= 0:
        raise ValueError("no labelled pixels")
    freq = counts / counts.sum()
    present = freq > 0
    weights = np.zeros_like(freq)
    weights[present] = np.median(freq[present]) / freq[present]
    return torch.tensor(weights, dtype=torch.float32)


class CrossEntropyDice(nn.Module):
    """Weighted cross-entropy plus dice_weight x (1 - mean soft Dice over classes)."""

    def __init__(self, weights: torch.Tensor, dice_weight: float = 1.0, eps: float = 1.0) -> None:
        super().__init__()
        self.register_buffer("weights", weights)
        self.dice_weight = dice_weight
        self.eps = eps

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        logits = logits.float()
        weights: torch.Tensor = self.weights  # type: ignore[assignment]
        ce = F.cross_entropy(logits, target, weight=weights)
        if self.dice_weight == 0:
            return ce
        probs = logits.softmax(dim=1)
        one_hot = F.one_hot(target, num_classes=logits.shape[1]).permute(0, 3, 1, 2).float()
        dims = (0, 2, 3)
        intersection = (probs * one_hot).sum(dims)
        total = probs.sum(dims) + one_hot.sum(dims)
        dice = (2.0 * intersection + self.eps) / (total + self.eps)
        return ce + self.dice_weight * (1.0 - dice.mean())
