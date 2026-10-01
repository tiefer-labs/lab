# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Reflectance, normalisation, augmentation and padding.

Images are channel-first arrays (bands, height, width); labels are
(height, width). Geometric operations are applied to both together.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import source

FloatArray = NDArray[np.float32]
LabelArray = NDArray[np.uint8]

# Upper bound used when clipping augmented reflectance. Bright clouds and snow
# can exceed 1.0 top-of-atmosphere reflectance; 2.0 leaves room for that.
MAX_REFLECTANCE = 2.0


def to_reflectance(
    digital_numbers: NDArray[np.uint16],
    scale: float = source.REFLECTANCE_SCALE,
    offset: float = source.REFLECTANCE_OFFSET,
) -> FloatArray:
    """Top-of-atmosphere reflectance from stored digital numbers."""
    return (digital_numbers.astype(np.float32) * np.float32(scale) + np.float32(offset)).astype(
        np.float32
    )


def band_statistics(
    images: NDArray[np.uint16], chunk: int = 32
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Per-band mean and standard deviation of reflectance over all pixels.

    `images` has shape (patches, bands, height, width) and may be memory-mapped;
    it is read in chunks of patches.
    """
    if images.ndim != 4:
        raise ValueError(f"expected (patches, bands, height, width), got shape {images.shape}")
    bands = images.shape[1]
    total = np.zeros(bands, dtype=np.float64)
    total_sq = np.zeros(bands, dtype=np.float64)
    count = 0
    for start in range(0, images.shape[0], chunk):
        refl = to_reflectance(np.asarray(images[start : start + chunk])).astype(np.float64)
        total += refl.sum(axis=(0, 2, 3))
        total_sq += np.square(refl).sum(axis=(0, 2, 3))
        count += refl.shape[0] * refl.shape[2] * refl.shape[3]
    if count == 0:
        raise ValueError("cannot compute statistics of an empty split")
    mean = total / count
    var = np.maximum(total_sq / count - np.square(mean), 0.0)
    std = np.sqrt(var)
    if np.any(std <= 0):
        raise ValueError(f"a band has zero variance: std={std.tolist()}")
    return mean, std


def normalise(
    reflectance: FloatArray, mean: NDArray[np.floating], std: NDArray[np.floating]
) -> FloatArray:
    """Per-band standardisation with statistics from the training split."""
    m = np.asarray(mean, dtype=np.float32).reshape(-1, 1, 1)
    s = np.asarray(std, dtype=np.float32).reshape(-1, 1, 1)
    return ((reflectance - m) / s).astype(np.float32)


def random_crop[ImageT: np.generic, LabelT: np.generic](
    image: NDArray[ImageT], label: NDArray[LabelT], size: int, rng: np.random.Generator
) -> tuple[NDArray[ImageT], NDArray[LabelT]]:
    """A random square crop of `size` pixels; the full patch if it is not larger."""
    height, width = label.shape
    if size >= height and size >= width:
        return image, label
    size_h, size_w = min(size, height), min(size, width)
    top = int(rng.integers(0, height - size_h + 1))
    left = int(rng.integers(0, width - size_w + 1))
    return (
        image[:, top : top + size_h, left : left + size_w],
        label[top : top + size_h, left : left + size_w],
    )


def random_flip_rotate[ImageT: np.generic, LabelT: np.generic](
    image: NDArray[ImageT], label: NDArray[LabelT], rng: np.random.Generator
) -> tuple[NDArray[ImageT], NDArray[LabelT]]:
    """Random horizontal and vertical flips and a rotation by a multiple of 90 degrees."""
    if rng.random() < 0.5:
        image, label = image[:, :, ::-1], label[:, ::-1]
    if rng.random() < 0.5:
        image, label = image[:, ::-1, :], label[::-1, :]
    k = int(rng.integers(0, 4))
    if k:
        image, label = np.rot90(image, k, axes=(1, 2)), np.rot90(label, k, axes=(0, 1))
    return np.ascontiguousarray(image), np.ascontiguousarray(label)


@dataclass(frozen=True)
class Photometric:
    """Small brightness and contrast changes.

    brightness: maximum relative change of a gain applied to all bands, as a
        change in illumination would (0.1 means a gain in [0.9, 1.1]).
    contrast: maximum relative change of the spread around the patch mean.
    """

    brightness: float = 0.1
    contrast: float = 0.1

    def __post_init__(self) -> None:
        if not 0.0 <= self.brightness < 0.5 or not 0.0 <= self.contrast < 0.5:
            raise ValueError("brightness and contrast changes must be in [0, 0.5)")


def brightness_contrast(
    reflectance: FloatArray, rng: np.random.Generator, change: Photometric
) -> FloatArray:
    """Apply a random gain and contrast change; the result stays in [0, MAX_REFLECTANCE]."""
    gain = 1.0 + rng.uniform(-change.brightness, change.brightness)
    factor = 1.0 + rng.uniform(-change.contrast, change.contrast)
    mean = reflectance.mean(axis=(1, 2), keepdims=True)
    out = (mean + (reflectance - mean) * factor) * gain
    return np.clip(out, 0.0, MAX_REFLECTANCE).astype(np.float32)


def pad_to_multiple(image: FloatArray, multiple: int = 32) -> tuple[FloatArray, tuple[int, int]]:
    """Reflect-pad the bottom and right edges to a multiple of `multiple`.

    Returns the padded image and the original (height, width) for `crop_back`.
    """
    height, width = image.shape[-2:]
    target = (-(-height // multiple) * multiple, -(-width // multiple) * multiple)
    return pad_to_shape(image, target), (height, width)


def pad_to_shape(image: FloatArray, shape: tuple[int, int]) -> FloatArray:
    """Reflect-pad the bottom and right edges to exactly `shape`."""
    height, width = image.shape[-2:]
    pad_h, pad_w = shape[0] - height, shape[1] - width
    if pad_h < 0 or pad_w < 0:
        raise ValueError(f"image {height}x{width} is larger than target {shape[0]}x{shape[1]}")
    if pad_h >= height or pad_w >= width:
        raise ValueError("reflect padding needs the pad to be smaller than the image")
    if pad_h == 0 and pad_w == 0:
        return image
    widths = [(0, 0)] * (image.ndim - 2) + [(0, pad_h), (0, pad_w)]
    return np.pad(image, widths, mode="reflect")


def crop_back[T: np.generic](array: NDArray[T], size: tuple[int, int]) -> NDArray[T]:
    """Undo `pad_to_multiple` on the last two axes."""
    return array[..., : size[0], : size[1]]
