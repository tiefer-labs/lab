# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Sensor robustness: augmentations in training and fixed perturbations in evaluation.

Target sensors differ from Sentinel-2 in resolution, radiometric calibration,
noise and sharpness. Each effect has one augmentation, switched on in its own
training run, and one fixed perturbation, applied at evaluation to measure
its cost on Sentinel-2 validation:

- rescale: a resolution change by a factor s (s < 1 is coarser), image
  bilinear with antialiasing, label nearest neighbour;
- gain and offset: per band, reflectance x (1 + g) + o;
- noise: additive Gaussian noise in reflectance;
- blur: a Gaussian blur of the image with standard deviation sigma pixels.

All values are top-of-atmosphere reflectance; the result is clamped to
[0, MAX_REFLECTANCE] like the photometric jitter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F  # noqa: N812

from tiefer_lab.data.transforms import MAX_REFLECTANCE

PERTURBATIONS = ("rescale", "gain", "offset", "noise", "blur")


@dataclass(frozen=True)
class Robustness:
    """Training augmentations; every one is off at its default."""

    rescale_min: float = 1.0
    rescale_max: float = 1.0
    gain_jitter: float = 0.0
    offset_jitter: float = 0.0
    noise_std: float = 0.0
    blur_sigma: float = 0.0

    @property
    def rescales(self) -> bool:
        return self.rescale_min != 1.0 or self.rescale_max != 1.0


def draw_scale(robustness: Robustness, generator: torch.Generator) -> float:
    """A rescale factor, log-uniform in [rescale_min, rescale_max]."""
    if not robustness.rescales:
        return 1.0
    low, high = math.log(robustness.rescale_min), math.log(robustness.rescale_max)
    return math.exp(low + (high - low) * float(torch.rand(1, generator=generator)))


def resize(
    image: torch.Tensor, label: torch.Tensor, size: tuple[int, int]
) -> tuple[torch.Tensor, torch.Tensor]:
    """(B, C, H, W) reflectance and (B, H, W) labels to `size`."""
    if tuple(image.shape[-2:]) == tuple(size):
        return image, label
    shrink = size[0] < image.shape[-2]
    image = F.interpolate(image, size=size, mode="bilinear", align_corners=False, antialias=shrink)
    label = F.interpolate(label[:, None].float(), size=size, mode="nearest")[:, 0].to(label.dtype)
    return image, label


def gaussian_blur(image: torch.Tensor, sigma: float) -> torch.Tensor:
    """Separable Gaussian blur of every band, reflect padding, radius 3 sigma."""
    if sigma <= 0:
        return image
    radius = max(1, math.ceil(3 * sigma))
    x = torch.arange(-radius, radius + 1, dtype=image.dtype, device=image.device)
    kernel = torch.exp(-(x**2) / (2 * sigma**2))
    kernel = kernel / kernel.sum()
    channels = image.shape[1]
    padded = F.pad(image, (radius, radius, radius, radius), mode="reflect")
    out = F.conv2d(padded, kernel.view(1, 1, 1, -1).repeat(channels, 1, 1, 1), groups=channels)
    return F.conv2d(out, kernel.view(1, 1, -1, 1).repeat(channels, 1, 1, 1), groups=channels)


def augment(
    image: torch.Tensor, robustness: Robustness, generator: torch.Generator
) -> torch.Tensor:
    """Gain, offset, noise and blur on a (B, C, H, W) reflectance batch."""
    b, c = image.shape[:2]
    device = image.device
    if robustness.gain_jitter > 0:
        g = (torch.rand(b, c, 1, 1, generator=generator) * 2 - 1) * robustness.gain_jitter
        image = image * (1 + g.to(device))
    if robustness.offset_jitter > 0:
        o = (torch.rand(b, c, 1, 1, generator=generator) * 2 - 1) * robustness.offset_jitter
        image = image + o.to(device)
    if robustness.noise_std > 0:
        std = torch.rand(b, 1, 1, 1, generator=generator) * robustness.noise_std
        noise = torch.randn(image.shape, generator=generator) * std
        image = image + noise.to(device)
    if robustness.blur_sigma > 0:
        image = gaussian_blur(
            image, float(torch.rand(1, generator=generator)) * robustness.blur_sigma
        )
    return image.clamp(0.0, MAX_REFLECTANCE)


@dataclass(frozen=True)
class Perturbation:
    """One fixed perturbation for evaluation, for example rescale=0.5 or noise=0.01."""

    kind: str
    value: float

    @classmethod
    def parse(cls, text: str) -> Perturbation:
        kind, _, value = text.partition("=")
        if kind not in PERTURBATIONS or not value:
            raise ValueError(
                f"perturbation must be one of {PERTURBATIONS} as kind=value, got {text!r}"
            )
        number = float(value)
        if kind == "rescale" and not 0.1 <= number <= 4.0:
            raise ValueError("rescale must be in [0.1, 4]")
        if kind in ("noise", "blur") and number < 0:
            raise ValueError(f"{kind} must be >= 0")
        return cls(kind, number)

    @property
    def name(self) -> str:
        return f"{self.kind}={self.value:g}"

    def apply(
        self, image: torch.Tensor, label: torch.Tensor, seed: int
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Perturb one (C, H, W) reflectance image and its (H, W) label."""
        x, y = image[None], label[None]
        if self.kind == "rescale":
            size = (
                max(8, round(x.shape[-2] * self.value)),
                max(8, round(x.shape[-1] * self.value)),
            )
            x, y = resize(x, y, size)
        elif self.kind == "gain":
            x = x * self.value
        elif self.kind == "offset":
            x = x + self.value
        elif self.kind == "noise":
            generator = torch.Generator().manual_seed(seed)
            x = x + torch.randn(x.shape, generator=generator) * self.value
        elif self.kind == "blur":
            x = gaussian_blur(x, self.value)
        return x[0].clamp(0.0, MAX_REFLECTANCE), y[0]
