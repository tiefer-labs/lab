# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""PyTorch datasets over the cache: random crops for training, full patches for evaluation."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import Dataset

from tiefer_lab.data import source, transforms
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


class DeviceTrainBatches:
    """The whole training split, held once per job, with augmentation on the device.

    The cached digital numbers are kept as they are (16 bit) on the GPU when they
    fit in `gpu_share` of its free memory, otherwise in pinned CPU memory (or in
    CPU memory on a machine without CUDA). Each batch is cropped, flipped,
    rotated, changed in brightness and contrast and normalised on the training
    device, with the same distributions as `TrainPatches`. Random draws come
    from a CPU generator seeded per epoch, so runs and resumed runs repeat.
    """

    def __init__(
        self,
        data: SplitData,
        mean: NDArray[np.float32],
        std: NDArray[np.float32],
        crop_size: int,
        photometric: transforms.Photometric,
        device: torch.device,
        batch_size: int,
        seed: int,
        gpu_share: float = 0.6,
    ) -> None:
        images = np.ascontiguousarray(np.asarray(data.images))
        labels = np.ascontiguousarray(np.asarray(data.labels))
        # uint16 is stored bit for bit as int16 and read back with & 0xFFFF.
        stored_images = torch.from_numpy(images.view(np.int16))
        stored_labels = torch.from_numpy(labels)
        nbytes = images.nbytes + labels.nbytes
        self.placement = "cpu"
        if device.type == "cuda":
            free, _ = torch.cuda.mem_get_info(device)
            if nbytes <= gpu_share * free:
                stored_images, stored_labels = stored_images.to(device), stored_labels.to(device)
                self.placement = "gpu"
            else:
                stored_images, stored_labels = (
                    stored_images.pin_memory(),
                    stored_labels.pin_memory(),
                )
                self.placement = "pinned"
        self.images, self.labels = stored_images, stored_labels
        self.nbytes = nbytes
        self.device = device
        self.crop_size = crop_size
        self.photometric = photometric
        self.batch_size = batch_size
        self.seed = seed
        self.mean = torch.as_tensor(mean, dtype=torch.float32, device=device).view(1, -1, 1, 1)
        self.std = torch.as_tensor(std, dtype=torch.float32, device=device).view(1, -1, 1, 1)

    @property
    def patches(self) -> int:
        return int(self.images.shape[0])

    def __len__(self) -> int:
        """Batches per epoch; the last incomplete batch is dropped, as in the loader."""
        return max(1, self.patches // self.batch_size)

    def epoch(self, epoch: int) -> Iterator[tuple[torch.Tensor, torch.Tensor]]:
        generator = torch.Generator().manual_seed(self.seed * 100_003 + epoch)
        order = torch.randperm(self.patches, generator=generator)
        for b in range(len(self)):
            yield self._batch(order[b * self.batch_size : (b + 1) * self.batch_size], generator)

    def _batch(
        self, indexes: torch.Tensor, generator: torch.Generator
    ) -> tuple[torch.Tensor, torch.Tensor]:
        n = int(indexes.numel())
        height, width = int(self.images.shape[2]), int(self.images.shape[3])
        crop_h, crop_w = min(self.crop_size, height), min(self.crop_size, width)
        tops = torch.randint(0, height - crop_h + 1, (n,), generator=generator).tolist()
        lefts = torch.randint(0, width - crop_w + 1, (n,), generator=generator).tolist()
        hflip = torch.rand(n, generator=generator) < 0.5
        vflip = torch.rand(n, generator=generator) < 0.5
        turns = torch.randint(0, 4, (n,), generator=generator)
        b, c = self.photometric.brightness, self.photometric.contrast
        gain = 1.0 + (torch.rand(n, generator=generator) * 2.0 - 1.0) * b
        factor = 1.0 + (torch.rand(n, generator=generator) * 2.0 - 1.0) * c

        rows = indexes.tolist()
        image = torch.stack(
            [
                self.images[i, :, t : t + crop_h, left : left + crop_w]
                for i, t, left in zip(rows, tops, lefts, strict=True)
            ]
        ).to(self.device, non_blocking=True)
        label = torch.stack(
            [
                self.labels[i, t : t + crop_h, left : left + crop_w]
                for i, t, left in zip(rows, tops, lefts, strict=True)
            ]
        ).to(self.device, non_blocking=True)

        dn = (image.to(torch.int32) & 0xFFFF).to(torch.float32)
        refl = dn * source.REFLECTANCE_SCALE + source.REFLECTANCE_OFFSET
        h = hflip.to(self.device)
        v = vflip.to(self.device)
        refl = torch.where(h.view(-1, 1, 1, 1), refl.flip(-1), refl)
        label = torch.where(h.view(-1, 1, 1), label.flip(-1), label)
        refl = torch.where(v.view(-1, 1, 1, 1), refl.flip(-2), refl)
        label = torch.where(v.view(-1, 1, 1), label.flip(-2), label)
        if crop_h == crop_w:
            for k in (1, 2, 3):
                chosen = (turns == k).to(self.device)
                if bool(chosen.any()):
                    refl[chosen] = torch.rot90(refl[chosen], k, dims=(-2, -1))
                    label[chosen] = torch.rot90(label[chosen], k, dims=(-2, -1))
        mean = refl.mean(dim=(2, 3), keepdim=True)
        f = factor.to(self.device).view(-1, 1, 1, 1)
        g = gain.to(self.device).view(-1, 1, 1, 1)
        refl = ((mean + (refl - mean) * f) * g).clamp(0.0, transforms.MAX_REFLECTANCE)
        image_out = (refl - self.mean) / self.std
        return image_out, label.to(torch.int64)
