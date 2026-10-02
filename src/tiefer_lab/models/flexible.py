# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Band-flexible models: one network for any subset of the 13 Level-1C bands.

The input is all 13 normalised bands plus one availability flag per band.
An unavailable band must not look like a dark pixel, so its values are
replaced before the network sees them, and the flags are given as 13 more
input channels. Two simple designs are compared on validation:

- "placeholder": an unavailable band is replaced by a learned value per band;
- "zero": an unavailable band is replaced by 0 (the training mean after
  normalisation), and only the flag tells it apart.

The band set of a forward pass is a (batch, 13) tensor of 0 and 1, or the
model's default set (`set_band_set`), which evaluation and export use.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch
from torch import nn

from tiefer_lab.data.source import L1C_BAND_NAMES
from tiefer_lab.models.cloud_filter import CloudFilterNet
from tiefer_lab.models.convnext_unet import ConvNeXtUNet

DESIGNS = ("placeholder", "zero")
ARCHITECTURES = ("separable_unet", "convnext_unet")


def availability(bands: Sequence[str], names: Sequence[str] = L1C_BAND_NAMES) -> torch.Tensor:
    """A (len(names),) tensor with 1 for every band in `bands`, 0 otherwise."""
    unknown = [b for b in bands if b not in names]
    if unknown:
        raise ValueError(f"unknown bands {unknown}; known bands are {list(names)}")
    return torch.tensor([1.0 if n in bands else 0.0 for n in names])


class BandInput(nn.Module):
    """(batch, bands, H, W) values and (batch, bands) flags to (batch, 2 x bands, H, W)."""

    def __init__(self, bands: int, design: str) -> None:
        super().__init__()
        if design not in DESIGNS:
            raise ValueError(f"design must be one of {DESIGNS}, got {design!r}")
        self.design = design
        self.placeholder = nn.Parameter(torch.zeros(bands)) if design == "placeholder" else None

    def forward(self, x: torch.Tensor, available: torch.Tensor) -> torch.Tensor:
        flags = available[:, :, None, None].to(x.dtype)
        filled = x * flags
        if self.placeholder is not None:
            filled = filled + (1 - flags) * self.placeholder[None, :, None, None].to(x.dtype)
        return torch.cat([filled, flags.expand_as(x)], dim=1)


Backbone = CloudFilterNet | ConvNeXtUNet


class FlexibleModel(nn.Module):
    def __init__(self, backbone: Backbone, bands: int, design: str) -> None:
        super().__init__()
        self.band_input = BandInput(bands, design)
        self.backbone = backbone
        self.bands = bands
        self.register_buffer("default_availability", torch.ones(bands))

    @property
    def downsampling(self) -> int:
        return int(self.backbone.downsampling)

    @property
    def input_bands(self) -> int:
        return self.bands

    def set_band_set(self, bands: Sequence[str]) -> None:
        """The band set used when forward is called without availability."""
        mask = availability(bands)
        if mask.numel() != self.bands:
            raise ValueError(f"the model takes {self.bands} bands")
        self.default_availability.copy_(mask)  # type: ignore[operator]

    def forward(self, x: torch.Tensor, available: torch.Tensor | None = None) -> torch.Tensor:
        if available is None:
            default: torch.Tensor = self.default_availability  # type: ignore[assignment]
            available = default.to(x.device).expand(x.shape[0], -1)
        out: torch.Tensor = self.backbone(self.band_input(x, available))
        return out


def backbone(architecture: str, widths: Sequence[int], in_channels: int) -> Backbone:
    if architecture == "separable_unet":
        return CloudFilterNet(widths, in_channels)
    if architecture == "convnext_unet":
        return ConvNeXtUNet(widths, in_channels)
    raise ValueError(f"architecture must be one of {ARCHITECTURES}, got {architecture!r}")


class BandSetModel(nn.Module):
    """A band-flexible model fixed to one band set, taking only those bands.

    Input: (batch, k, H, W), the k bands of the set in the order given.
    Everything that depends only on the band set is precomputed as one
    constant: the value of each unavailable band (its learned placeholder, or
    0) and the 13 availability flags. The network sees exactly what the
    flexible model would see for this band set, and the exported model takes
    only the sensor's bands; its flags cannot be changed after export.
    """

    def __init__(self, model: FlexibleModel, bands: Sequence[str]) -> None:
        super().__init__()
        mask = availability(bands)
        self.backbone = model.backbone
        self.bands = tuple(bands)
        position = {b: i for i, b in enumerate(bands)}
        self.layout = [position.get(name, -1) for name in L1C_BAND_NAMES]
        placeholder = model.band_input.placeholder
        fill = (
            placeholder.detach().clone() * (1 - mask)
            if placeholder is not None
            else torch.zeros_like(mask)
        )
        self.register_buffer("constants", torch.cat([fill, mask]))

    @property
    def downsampling(self) -> int:
        return int(self.backbone.downsampling)

    @property
    def input_bands(self) -> int:
        return len(self.bands)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        constants: torch.Tensor = self.constants  # type: ignore[assignment]
        count = len(self.layout)
        maps = (
            constants[None, :, None, None]
            .to(x.dtype)
            .expand(x.shape[0], -1, x.shape[2], x.shape[3])
        )
        parts = [
            x[:, j : j + 1] if j >= 0 else maps[:, b : b + 1] for b, j in enumerate(self.layout)
        ]
        parts.append(maps[:, count:])
        out: torch.Tensor = self.backbone(torch.cat(parts, dim=1))
        return out


Model = FlexibleModel | CloudFilterNet | ConvNeXtUNet


def build(model_config: Any, bands: Sequence[str]) -> Model:
    """The model of a configuration: fixed bands, or band-flexible over `bands`."""
    if model_config.input == "flexible":
        if tuple(bands) != tuple(L1C_BAND_NAMES):
            raise ValueError("a band-flexible model takes all 13 Level-1C bands in order")
        net = backbone(model_config.architecture, model_config.widths, 2 * len(bands))
        return FlexibleModel(net, len(bands), model_config.flexible_design)
    return backbone(model_config.architecture, model_config.widths, len(bands))
