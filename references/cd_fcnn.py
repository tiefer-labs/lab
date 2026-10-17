# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""CD-FCNN (IPL-UV, DL-L8S2-UV) in PyTorch, with its published Keras weights.

The network is the one stored in the `model_config` of the published files
`landsatbiomeRGBI6.hdf5` and `landsatbiomeRGBISWIR7.hdf5`
(https://github.com/IPL-UV/DL-L8S2-UV, branch main, read 17 October 2026),
rebuilt layer by layer: a frozen 1 x 1 convolution named `normalization`, a
U-Net of three levels whose blocks are two separable 3 x 3 convolutions with
bias, each followed by batch norm (epsilon 0.001) and ReLU, 2 x 2 max pooling,
2 x 2 transposed convolutions of stride 2 with the skip concatenated after
them, and a 1 x 1 convolution with a sigmoid. The weights are read from the
files as published (`keras_weights`), never trained or changed; they are kept
outside the repository (references/README.md), under the MIT licence of their
repository (maintainer's reading of 16 October 2026).

Use on Sentinel-2, as `dl_l8s2_uv/utils.py` and `satreaders/s2image.py` of
that repository do it: the bands B02, B03, B04, B08 (RGBI) or B02, B03, B04,
B08, B11, B12 (RGBISWIR) as top-of-atmosphere reflectance, the digital
numbers divided by 10,000; the image padded by reflection to a multiple of 8
in each direction and cropped back after the network; cloud where the
probability is at least 0.5. The published tool resamples Sentinel-2 to 30 m
by default (`S2Image(size_def="30")`), each band with rasterio's
`Resampling.cubic_spline` in the band's own data type, and offers 10, 20 and
60 m too. The primary run here is at that 30 m (`resample_30m`): the cached
10 m bands, padded by reflection at the bottom and right to a multiple of 3,
are resampled the same way, and the 30 m mask is brought back to 10 m by
nearest neighbour and cropped to the patch. The run at the caches' own 10 m is
kept as well, under its own label; neither is chosen by its result
(docs/ASSUMPTIONS.md, `A-6.16` and `A-6.17`). `tests/test_reference_runners.py` checks the
rebuild against TensorFlow's output for the same weights.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn

BANDS: dict[str, tuple[str, ...]] = {
    "cd_fcnn_rgbi": ("B02", "B03", "B04", "B08"),
    "cd_fcnn_rgbiswir": ("B02", "B03", "B04", "B08", "B11", "B12"),
}
REFLECTANCE_SCALE = 10000.0
THRESHOLD = 0.5
PAD_DIVISOR = 8
BN_EPSILON = 1e-3
# Ground sampling distance of the caches and of the published default, metres.
CACHE_RESOLUTION = 10
PUBLISHED_RESOLUTION = 30
FACTOR = PUBLISHED_RESOLUTION // CACHE_RESOLUTION


class SeparableConv(nn.Module):
    """Keras SeparableConv2D, 3 x 3, padding same, depth multiplier 1, with bias."""

    def __init__(self, cin: int, cout: int) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(cin, cin, 3, padding=1, groups=cin, bias=False)
        self.pointwise = nn.Conv2d(cin, cout, 1, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pointwise(self.depthwise(x))


class Block(nn.Sequential):
    """Two separable convolutions, each with batch norm and ReLU (`conv_blocks`)."""

    def __init__(self, cin: int, cout: int) -> None:
        super().__init__(
            SeparableConv(cin, cout),
            nn.BatchNorm2d(cout, eps=BN_EPSILON),
            nn.ReLU(),
            SeparableConv(cout, cout),
            nn.BatchNorm2d(cout, eps=BN_EPSILON),
            nn.ReLU(),
        )


class CDFCNN(nn.Module):
    """The U-Net of the published files; outputs the cloud probability."""

    def __init__(self, bands: int) -> None:
        super().__init__()
        self.normalization = nn.Conv2d(bands, bands, 1, bias=True)
        self.input = Block(bands, 32)
        self.pool1 = Block(32, 64)
        self.pool2 = Block(64, 128)
        self.upconv1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.up1 = Block(128, 64)
        self.upconv2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.up2 = Block(64, 32)
        self.linear_model = nn.Conv2d(32, 1, 1, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        c1 = self.input(self.normalization(x))
        c2 = self.pool1(nn.functional.max_pool2d(c1, 2))
        c3 = self.pool2(nn.functional.max_pool2d(c2, 2))
        u1 = self.up1(torch.cat([self.upconv1(c3), c2], dim=1))
        u2 = self.up2(torch.cat([self.upconv2(u1), c1], dim=1))
        return torch.sigmoid(self.linear_model(u2))


BLOCKS = ("input", "pool1", "pool2", "up1", "up2")


def keras_weights(path: Path) -> dict[str, NDArray[np.float32]]:
    """Every array of a Keras weights file, keyed `<layer>/<weight>` (h5py is needed)."""
    import h5py

    out: dict[str, NDArray[np.float32]] = {}
    with h5py.File(path, "r") as f:
        group = f.get("model_weights", f)

        def take(name: str, obj: object) -> None:
            if isinstance(obj, h5py.Dataset):
                layer = name.split("/")[0]
                weight = name.rsplit("/", 1)[-1].split(":")[0]
                out[f"{layer}/{weight}"] = np.asarray(obj, dtype=np.float32)

        group.visititems(take)
    return out


def _set(param: torch.Tensor, value: NDArray[np.float32]) -> None:
    if tuple(param.shape) != value.shape:
        raise ValueError(f"shape {value.shape} does not fit {tuple(param.shape)}")
    with torch.no_grad():
        param.copy_(torch.from_numpy(np.ascontiguousarray(value)))


def load(model: CDFCNN, weights: Mapping[str, NDArray[np.float32]]) -> CDFCNN:
    """Copy Keras weights (height, width, in, out layouts) into the PyTorch layers."""
    used: set[str] = set()

    def get(key: str) -> NDArray[np.float32]:
        used.add(key)
        return weights[key]

    def conv(layer: nn.Conv2d, name: str) -> None:
        _set(layer.weight, get(f"{name}/kernel").transpose(3, 2, 0, 1))
        assert layer.bias is not None
        _set(layer.bias, get(f"{name}/bias"))

    conv(model.normalization, "normalization")
    conv(model.linear_model, "linear_model")
    for name in BLOCKS:
        block = getattr(model, name)
        for i, (sep, bn) in enumerate(((block[0], block[1]), (block[3], block[4])), start=1):
            prefix = f"{name}_conv_{i}"
            # depthwise (3, 3, in, 1) -> (in, 1, 3, 3); pointwise (1, 1, in, out) -> (out, in, 1, 1)
            _set(sep.depthwise.weight, get(f"{prefix}/depthwise_kernel").transpose(2, 3, 0, 1))
            _set(sep.pointwise.weight, get(f"{prefix}/pointwise_kernel").transpose(3, 2, 0, 1))
            _set(sep.pointwise.bias, get(f"{prefix}/bias"))
            bn_name = f"{name}_bn_{i}"
            _set(bn.weight, get(f"{bn_name}/gamma"))
            _set(bn.bias, get(f"{bn_name}/beta"))
            _set(bn.running_mean, get(f"{bn_name}/moving_mean"))
            _set(bn.running_var, get(f"{bn_name}/moving_variance"))
    for name in ("upconv1", "upconv2"):
        layer = getattr(model, name)
        # Conv2DTranspose (h, w, out, in) -> ConvTranspose2d (in, out, h, w)
        _set(layer.weight, get(f"{name}/kernel").transpose(3, 2, 0, 1))
        _set(layer.bias, get(f"{name}/bias"))
    unused = set(weights) - used
    if unused:
        raise ValueError(f"weights not used: {sorted(unused)}")
    return model.eval()


def _pad(size: int) -> tuple[int, int]:
    """`find_padding` of the published utils: to a multiple of 8, split before and after."""
    total = max(PAD_DIVISOR, int(PAD_DIVISOR * np.ceil(size / PAD_DIVISOR))) - size
    return total // 2, total - total // 2


def probability(model: CDFCNN, reflectance: NDArray[np.float32]) -> NDArray[np.float32]:
    """Cloud probability of one image (bands, height, width) of reflectance."""
    _, height, width = reflectance.shape
    top, bottom = _pad(height)
    left, right = _pad(width)
    padded = np.pad(reflectance, ((0, 0), (top, bottom), (left, right)), mode="reflect")
    with torch.no_grad():
        out = model(torch.from_numpy(padded[None].astype(np.float32)))[0, 0].numpy()
    return out[top : top + height, left : left + width]


def resample_30m(digital_numbers: NDArray[np.uint16]) -> NDArray[np.uint16]:
    """The 10 m bands at 30 m, as the published tool resamples them.

    The patch is padded by reflection at the bottom and right to a multiple of
    3, then each band is resampled with rasterio's cubic spline in its own data
    type. Source and target share one grid origin and a placeholder projected
    CRS, so nothing but the pixel size changes.
    """
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    from rasterio.warp import Resampling, reproject

    bands, height, width = digital_numbers.shape
    pad_h, pad_w = -height % FACTOR, -width % FACTOR
    padded = np.pad(digital_numbers, ((0, 0), (0, pad_h), (0, pad_w)), mode="reflect")
    out = np.zeros(
        (bands, padded.shape[1] // FACTOR, padded.shape[2] // FACTOR), dtype=digital_numbers.dtype
    )
    crs = CRS.from_epsg(32633)
    src = Affine(CACHE_RESOLUTION, 0, 0, 0, -CACHE_RESOLUTION, 0)
    dst = Affine(PUBLISHED_RESOLUTION, 0, 0, 0, -PUBLISHED_RESOLUTION, 0)
    for b in range(bands):
        reproject(
            padded[b],
            out[b],
            src_transform=src,
            src_crs=crs,
            dst_transform=dst,
            dst_crs=crs,
            resampling=Resampling.cubic_spline,
        )
    return out


def cloud_mask(
    model: CDFCNN, digital_numbers: NDArray[np.uint16], resolution: int = PUBLISHED_RESOLUTION
) -> NDArray[np.uint8]:
    """1 where cloudy (probability at least 0.5), 0 elsewhere, at the cache's 10 m.

    `resolution` is where the network runs: 30 m, the published default, or
    10 m, the caches' own; the mask is always returned on the 10 m grid.
    """
    if resolution not in (CACHE_RESOLUTION, PUBLISHED_RESOLUTION):
        raise ValueError(f"resolution must be {CACHE_RESOLUTION} or {PUBLISHED_RESOLUTION} m")
    _, height, width = digital_numbers.shape
    numbers = digital_numbers if resolution == CACHE_RESOLUTION else resample_30m(digital_numbers)
    reflectance = numbers.astype(np.float32) / REFLECTANCE_SCALE
    mask = (probability(model, reflectance) >= THRESHOLD).astype(np.uint8)
    if resolution == PUBLISHED_RESOLUTION:
        mask = mask.repeat(FACTOR, axis=0).repeat(FACTOR, axis=1)[:height, :width]
    return mask
