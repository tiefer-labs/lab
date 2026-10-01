# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""PyTorch datasets over the cache: random crops for training, full patches for evaluation."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import Dataset

from tiefer_lab.data import transforms
from tiefer_lab.data.cache import SplitData


class TrainPatches(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Augmented random crops of training patches.

    Randomness comes from `torch.initial_seed()`, which the DataLoader sets
    per worker from its seeded generator, and from the epoch set with
    `set_epoch`, so runs and resumed runs repeat exactly.
    """

    def __init__(
        self,
        data: SplitData,
        mean: NDArray[np.float32],
        std: NDArray[np.float32],
        crop_size: int,
        photometric: transforms.Photometric,
    ) -> None:
        self.data = data
        self.mean = mean
        self.std = std
        self.crop_size = crop_size
        self.photometric = photometric
        self.epoch = 0
        self._rng: np.random.Generator | None = None
        self._rng_key: tuple[int, int] | None = None

    def __len__(self) -> int:
        return len(self.data)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def _generator(self) -> np.random.Generator:
        key = (torch.initial_seed() % 2**63, self.epoch)
        if self._rng is None or self._rng_key != key:
            self._rng = np.random.default_rng(list(key))
            self._rng_key = key
        return self._rng

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        rng = self._generator()
        dn = np.asarray(self.data.images[index])
        label = np.asarray(self.data.labels[index])
        dn, label = transforms.random_crop(dn, label, self.crop_size, rng)
        refl = transforms.to_reflectance(np.ascontiguousarray(dn))
        refl, label = transforms.random_flip_rotate(refl, label, rng)
        refl = transforms.brightness_contrast(refl, rng, self.photometric)
        image = transforms.normalise(refl, self.mean, self.std)
        return torch.from_numpy(image), torch.from_numpy(label.astype(np.int64))


class EvalPatches(Dataset[tuple[torch.Tensor, torch.Tensor, int]]):
    """Full patches, reflect-padded to a multiple of `multiple`; no augmentation.

    Returns the padded image, the unpadded label and the patch position. Use
    `transforms.crop_back` on predictions with the label's size.
    """

    def __init__(
        self,
        data: SplitData,
        mean: NDArray[np.float32],
        std: NDArray[np.float32],
        multiple: int = 32,
    ) -> None:
        self.data = data
        self.mean = mean
        self.std = std
        self.multiple = multiple

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, int]:
        refl = transforms.to_reflectance(np.asarray(self.data.images[index]))
        image = transforms.normalise(refl, self.mean, self.std)
        padded, _ = transforms.pad_to_multiple(image, self.multiple)
        label = np.asarray(self.data.labels[index]).astype(np.int64)
        return torch.from_numpy(np.ascontiguousarray(padded)), torch.from_numpy(label), index


def normalised_patch(
    data: SplitData, index: int, mean: NDArray[np.float32], std: NDArray[np.float32]
) -> NDArray[np.float32]:
    """One full patch as normalised reflectance, without padding."""
    refl = transforms.to_reflectance(np.asarray(data.images[index]))
    return transforms.normalise(refl, mean, std)
