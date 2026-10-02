# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cross-entropy plus Dice loss, with optional class weights and focal term.

Pixels whose label is IGNORE_INDEX (no label: scribble gaps, nolabel patches)
add nothing to either term. `distillation` is the self-distillation term of
the band-flexible models.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812
from torch import nn

from tiefer_lab.data.source import IGNORE_INDEX


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
    """Cross-entropy (weighted, optionally focal) plus dice_weight x (1 - mean soft Dice).

    With focal_gamma > 0 each pixel's cross-entropy is multiplied by
    (1 - p)^gamma, p being the predicted probability of its true class.
    """

    def __init__(
        self,
        weights: torch.Tensor | None,
        dice_weight: float = 1.0,
        eps: float = 1.0,
        focal_gamma: float = 0.0,
    ) -> None:
        super().__init__()
        self.register_buffer("weights", weights)
        self.dice_weight = dice_weight
        self.eps = eps
        self.focal_gamma = focal_gamma

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        logits = logits.float()
        weights: torch.Tensor | None = self.weights  # type: ignore[assignment]
        valid = target != IGNORE_INDEX
        if not bool(valid.any()):
            return logits.sum() * 0.0
        if self.focal_gamma > 0:
            pixel_ce = F.cross_entropy(
                logits, target, weight=weights, ignore_index=IGNORE_INDEX, reduction="none"
            )
            safe = target.where(valid, 0)
            p_true = logits.softmax(dim=1).gather(1, safe[:, None]).squeeze(1)
            focal = (1.0 - p_true).pow(self.focal_gamma) * pixel_ce
            if weights is not None:
                norm = weights[safe][valid].sum()
            else:
                norm = valid.sum().to(logits.dtype)
            ce = focal[valid].sum() / norm
        else:
            ce = F.cross_entropy(logits, target, weight=weights, ignore_index=IGNORE_INDEX)
        if self.dice_weight == 0:
            return ce
        mask = valid[:, None].float()
        probs = logits.softmax(dim=1) * mask
        safe = target.where(valid, 0)
        one_hot = F.one_hot(safe, num_classes=logits.shape[1]).permute(0, 3, 1, 2).float() * mask
        dims = (0, 2, 3)
        intersection = (probs * one_hot).sum(dims)
        total = probs.sum(dims) + one_hot.sum(dims)
        dice = (2.0 * intersection + self.eps) / (total + self.eps)
        return ce + self.dice_weight * (1.0 - dice.mean())


def distillation(student: torch.Tensor, teacher: torch.Tensor) -> torch.Tensor:
    """Mean over pixels of KL(teacher || student) of the class distributions.

    The teacher is the prediction with all bands and carries no gradient.
    """
    log_student = student.float().log_softmax(dim=1)
    log_teacher = teacher.detach().float().log_softmax(dim=1)
    kl = (log_teacher.exp() * (log_teacher - log_student)).sum(dim=1)
    return kl.mean()
