# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The onboard decision for one frame: fail-safe, with tiled inference for large frames.

A frame is kept on board only when the model ran on valid input and found its
cloud fraction at or above the threshold. Everything else ends in "send" with
a flag that says why: input with the wrong number of bands, non-finite
values, too many saturated, empty or out-of-range pixels, a ground sampling
distance outside the design domain, a model file whose SHA-256 differs from
the expected one, or any error during inference. A doubtful frame thus costs
downlink, never a lost frame (docs/ASSUMPTIONS.md, section 3: a false discard
is the most costly error).

Large frames are resampled to the training resolution (10 m), run in tiles
of `tile` pixels that overlap by `overlap` pixels (logits are averaged where
tiles overlap), and the mask is resampled back to the frame's size.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812
from numpy.typing import NDArray
from torch import nn

from tiefer_lab import decisions
from tiefer_lab.data.transforms import MAX_REFLECTANCE

TRAINING_GSD_M = 10.0


class ModelIntegrityError(RuntimeError):
    """The model file is not the expected one."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_model_file(path: Path, expected_sha256: str) -> None:
    """Stop with a clear status unless the file's SHA-256 is the expected one."""
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ModelIntegrityError(
            f"model file {path.name}: SHA-256 {actual} differs from the expected {expected_sha256}"
        )


@dataclass(frozen=True)
class Domain:
    """Inputs the filter is designed for; outside it, a frame is sent and flagged."""

    bands: int
    min_gsd_m: float = 0.5
    max_gsd_m: float = 20.0
    max_reflectance: float = MAX_REFLECTANCE
    saturated_dn: int = 65535
    # Share of pixels that may be saturated, empty (all bands 0) or out of range.
    max_invalid_share: float = 0.01
    min_size: int = 32


def input_flags(frame: NDArray[Any], gsd_m: float, domain: Domain, scale: float) -> list[str]:
    """Reasons why a frame is outside the design domain (empty when it is inside)."""
    flags: list[str] = []
    if frame.ndim != 3 or frame.shape[0] != domain.bands:
        return [f"expected ({domain.bands}, height, width), got shape {frame.shape}"]
    if min(frame.shape[1:]) < domain.min_size:
        flags.append(f"frame smaller than {domain.min_size} pixels")
    if not domain.min_gsd_m <= gsd_m <= domain.max_gsd_m:
        flags.append(
            f"ground sampling distance {gsd_m} m outside {domain.min_gsd_m} to {domain.max_gsd_m} m"
        )
    values = frame.astype(np.float64)
    if not np.isfinite(values).all():
        return [*flags, "non-finite values"]
    saturated = (
        (frame >= domain.saturated_dn).any(axis=0)
        if np.issubdtype(frame.dtype, np.integer)
        else np.zeros(frame.shape[1:], bool)
    )
    empty = (values == 0).all(axis=0)
    reflectance = values * scale
    out_of_range = ((reflectance < 0) | (reflectance > domain.max_reflectance)).any(axis=0)
    for name, mask in (("saturated", saturated), ("empty", empty), ("out-of-range", out_of_range)):
        share = float(mask.mean())
        if share > domain.max_invalid_share:
            flags.append(f"{share:.3f} of the pixels are {name}")
    return flags


def predict_frame(
    model: nn.Module,
    reflectance: NDArray[np.float32],
    mean: NDArray[np.float32],
    std: NDArray[np.float32],
    gsd_m: float,
    *,
    tile: int = 512,
    overlap: int = 64,
    training_gsd_m: float = TRAINING_GSD_M,
) -> NDArray[np.uint8]:
    """Class mask of a frame of any size, at the frame's own size.

    The frame is resampled to the training resolution (area averaging when it
    is finer), cut into tiles of `tile` pixels overlapping by `overlap`, the
    logits are averaged where tiles overlap, and the mask is resampled back
    with nearest neighbour.
    """
    if not 0 <= overlap < tile:
        raise ValueError("overlap must be in [0, tile)")
    x = torch.from_numpy(np.ascontiguousarray(reflectance, dtype=np.float32))[None]
    height, width = x.shape[-2:]
    factor = gsd_m / training_gsd_m
    size = (max(1, round(height * factor)), max(1, round(width * factor)))
    if size != (height, width):
        x = F.interpolate(x, size=size, mode="area" if factor < 1 else "bilinear")
    x = (x - torch.from_numpy(mean)[None, :, None, None]) / torch.from_numpy(std)[
        None, :, None, None
    ]
    h, w = size
    stride = tile - overlap
    rows = max(1, math.ceil((h - overlap) / stride)) if h > tile else 1
    cols = max(1, math.ceil((w - overlap) / stride)) if w > tile else 1
    padded_h, padded_w = (rows - 1) * stride + tile, (cols - 1) * stride + tile
    x = F.pad(
        x, (0, padded_w - w, 0, padded_h - h), mode="reflect" if min(h, w) > 1 else "replicate"
    )
    logits = torch.zeros(1, 4, padded_h, padded_w)
    weight = torch.zeros(1, 1, padded_h, padded_w)
    model.eval()
    with torch.no_grad():
        for r in range(rows):
            for c in range(cols):
                top, left = r * stride, c * stride
                out = model(x[..., top : top + tile, left : left + tile]).float()
                logits[..., top : top + tile, left : left + tile] += out
                weight[..., top : top + tile, left : left + tile] += 1
    mask = (logits / weight)[..., :h, :w].argmax(dim=1, keepdim=True).float()
    if (h, w) != (height, width):
        mask = F.interpolate(mask, size=(height, width), mode="nearest")
    return mask[0, 0].to(torch.uint8).numpy()


@dataclass(frozen=True)
class FrameResult:
    decision: decisions.Decision
    cloud_fraction: float | None
    shadow_fraction: float | None
    status: str
    flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class OnboardFilter:
    """Decision per frame for one model and one band set; fail-safe by construction.

    `model` takes the bands of `domain` (a specialist, or a band-flexible
    model fixed to a band set). With `model_path` and `expected_sha256`, the
    file is checked once, before any inference; a mismatch stops inference
    and every frame is sent with the status "model_hash_mismatch".
    """

    model: nn.Module
    mean: NDArray[np.float32]
    std: NDArray[np.float32]
    domain: Domain
    threshold: float = decisions.DEFAULT_THRESHOLD
    reflectance_scale: float = 1.0e-4
    model_path: Path | None = None
    expected_sha256: str | None = None
    tile: int = 512
    overlap: int = 64
    status: str = "ok"
    problem: str = ""

    def __post_init__(self) -> None:
        if self.model_path is not None or self.expected_sha256 is not None:
            try:
                if self.model_path is None or self.expected_sha256 is None:
                    raise ModelIntegrityError("both model_path and expected_sha256 are needed")
                verify_model_file(self.model_path, self.expected_sha256)
            except (ModelIntegrityError, OSError) as err:
                self.status = "model_hash_mismatch"
                self.problem = str(err)

    def _send(self, status: str, flags: Sequence[str]) -> FrameResult:
        return FrameResult("send", None, None, status, tuple(flags))

    def process(self, frame: NDArray[Any], gsd_m: float = TRAINING_GSD_M) -> FrameResult:
        if self.status != "ok":
            return self._send(self.status, [self.problem])
        try:
            flags = input_flags(frame, gsd_m, self.domain, self.reflectance_scale)
            if flags:
                return self._send("outside_domain", flags)
            reflectance = (frame.astype(np.float32) * self.reflectance_scale).clip(
                0.0, self.domain.max_reflectance
            )
            mask = predict_frame(
                self.model,
                reflectance,
                self.mean,
                self.std,
                gsd_m,
                tile=self.tile,
                overlap=self.overlap,
            )
            cloud = decisions.cloud_fraction(mask)
            shadow = decisions.shadow_fraction(mask)
            if not (math.isfinite(cloud) and math.isfinite(shadow)):
                return self._send("error", ["non-finite cloud fraction"])
            return FrameResult(decisions.decide(cloud, self.threshold), cloud, shadow, "ok")
        except Exception as err:  # fail-safe: any error sends the frame
            return self._send("error", [f"{type(err).__name__}: {err}"])


def failsafe_check() -> dict[str, Any]:
    """Run invalid, missing, saturated and out-of-domain frames through the filter.

    Uses a fixed pixel-wise model that would call every bright pixel thick
    cloud, and frames that are bright (cloudy) where they are valid, so a
    frame is only sent because the fail-safe rules sent it. Returns the
    number of cases and how many of them ended in a discarded frame ("keep").
    """
    conv = nn.Conv2d(2, 4, 1)
    bias = torch.zeros(4)
    bias[1] = -5.0
    weight = torch.zeros(4, 2, 1, 1)
    weight[1, 0] = 10.0
    conv.weight = nn.Parameter(weight)
    conv.bias = nn.Parameter(bias)
    zero, one = np.zeros(2, np.float32), np.ones(2, np.float32)
    domain = Domain(bands=2)
    cloudy = np.full((2, 200, 200), 8000, np.uint16)
    nan = cloudy.astype(np.float32)
    nan[0, 0, 0] = np.nan
    saturated = cloudy.copy()
    saturated[:, :80] = 65535
    empty = cloudy.copy()
    empty[:, :40] = 0
    out_of_range = cloudy.copy()
    out_of_range[0, :40] = 30000
    cases: dict[str, tuple[NDArray[Any], float]] = {
        "wrong band count": (cloudy[:1], TRAINING_GSD_M),
        "extra band": (np.concatenate([cloudy, cloudy[:1]]), TRAINING_GSD_M),
        "non-finite": (nan, TRAINING_GSD_M),
        "saturated": (saturated, TRAINING_GSD_M),
        "empty": (empty, TRAINING_GSD_M),
        "out of range": (out_of_range, TRAINING_GSD_M),
        "too small": (cloudy[:, :10, :10], TRAINING_GSD_M),
        "resolution outside the domain": (cloudy, 100.0),
    }
    results = {
        name: OnboardFilter(conv, zero, one, domain, tile=128, overlap=16).process(frame, gsd)
        for name, (frame, gsd) in cases.items()
    }

    class Broken(nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            raise RuntimeError("simulated failure")

    results["error during inference"] = OnboardFilter(Broken(), zero, one, domain).process(cloudy)
    valid = OnboardFilter(conv, zero, one, domain, tile=128, overlap=16).process(cloudy)
    return {
        "cases": len(results),
        "discarded": sum(r.decision == "keep" for r in results.values()),
        "control_valid_cloudy_frame": valid.decision,
        "results": {
            name: {"decision": r.decision, "status": r.status} for name, r in results.items()
        },
    }
