# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Where the dataset padded each cached patch, and how the padding is masked.

The CloudSEN12+ card says that the 509 x 509 patches are padded to 512 x 512
with zeros on the left and bottom sides (docs/DATA.md, section 4). The cache
keeps the arrays as they are stored, so the padded pixels are in every cached
patch. The width of the padding is not taken from the card: it is the
stored size minus the original size, `real_proj_shape`, of each patch. Only
the sides come from the card, in PADDING_SIDES.

`python -m tiefer_lab.data.cache padding <cache-name>` reads a sample of
patches of a real cache and reports what the strips on each side hold; it
exits with 1 when the zero strips are not on PADDING_SIDES.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from tiefer_lab.data.source import SHAPE_FIELD

# The sides of each patch that hold the padding. From the dataset card;
# TODO(verify) with `python -m tiefer_lab.data.cache padding` on the caches on
# CSC Roihu (docs/DATA.md, section 13). One side per axis.
PADDING_SIDES: tuple[str, ...] = ("left", "bottom")
# Width of the padding on each padded side by the card: 512 - 509. Used by the
# check only when a patch has no `real_proj_shape`.
CARD_WIDTH = 3
SIDES = ("left", "bottom", "right", "top")
VERTICAL = ("top", "bottom")
HORIZONTAL = ("left", "right")


@dataclass(frozen=True)
class Padding:
    """Padded rows and columns on each side of one patch."""

    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0

    def __bool__(self) -> bool:
        return bool(self.top or self.bottom or self.left or self.right)

    def pixels(self, height: int, width: int) -> int:
        """Number of padded pixels of a height x width patch."""
        real = (height - self.top - self.bottom) * (width - self.left - self.right)
        return height * width - real

    def as_dict(self) -> dict[str, int]:
        return {"top": self.top, "bottom": self.bottom, "left": self.left, "right": self.right}


NO_PADDING = Padding()


def check_sides(sides: Sequence[str]) -> None:
    unknown = [s for s in sides if s not in SIDES]
    if unknown:
        raise ValueError(f"unknown padding sides {unknown}; choose from {SIDES}")
    for axis in (VERTICAL, HORIZONTAL):
        if sum(s in axis for s in sides) > 1:
            raise ValueError(f"at most one of {axis} can hold the padding, got {list(sides)}")


def real_shape(metadata: Mapping[str, Any]) -> tuple[int, int] | None:
    """The original (height, width) of a patch from `real_proj_shape`, or None.

    The card gives one number, the side of a square patch (509 or 2000).
    """
    value = metadata.get(SHAPE_FIELD)
    if value is None:
        return None
    try:
        side = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(side) or side <= 0 or side != int(side):
        return None
    return int(side), int(side)


def padding_of(
    stored: tuple[int, int],
    real: tuple[int, int] | None,
    sides: Sequence[str] = PADDING_SIDES,
) -> Padding:
    """The padding of a patch stored at `stored` whose original size is `real`.

    The width per axis is the stored size minus the real size; it lies on the
    side of `sides` for that axis. Without a real size there is no padding.
    """
    check_sides(sides)
    if real is None:
        return NO_PADDING
    extra_h, extra_w = stored[0] - real[0], stored[1] - real[1]
    if extra_h < 0 or extra_w < 0:
        raise ValueError(f"stored size {stored} is smaller than the real size {real}")
    widths: dict[str, int] = {}
    for extra, axis in ((extra_h, VERTICAL), (extra_w, HORIZONTAL)):
        chosen = [s for s in sides if s in axis]
        if extra and not chosen:
            raise ValueError(f"{extra} padded pixels on {axis}, but no side of {axis} is listed")
        if chosen:
            widths[chosen[0]] = extra
    return Padding(**widths)


def paddings(
    metadata: Sequence[Mapping[str, Any]], count: int, stored: tuple[int, int]
) -> list[Padding]:
    """The padding of each of `count` patches; none when the metadata has no real size."""
    if len(metadata) != count:
        return [NO_PADDING] * count
    return [padding_of(stored, real_shape(m)) for m in metadata]


# The check -----------------------------------------------------------------


@dataclass
class SideReport:
    """What one strip of the sampled patches holds."""

    side: str
    width: int
    label_counts: dict[int, int]
    patches_all_zero: int
    patches: int

    @property
    def all_zero(self) -> bool:
        return self.patches > 0 and self.patches_all_zero == self.patches


def strip(array: Any, side: str, width: int) -> Any:
    """The strip of `width` rows or columns on `side` of the last two axes."""
    if side == "left":
        return array[..., :width]
    if side == "right":
        return array[..., array.shape[-1] - width :]
    if side == "top":
        return array[..., :width, :]
    return array[..., array.shape[-2] - width :, :]


def inspect(
    images: Any,
    labels: Any,
    metadata: Sequence[Mapping[str, Any]],
    positions: Sequence[int],
    default_width: int,
) -> tuple[list[SideReport], dict[str, int]]:
    """Label values and zero images in the strips of every side, over `positions`.

    The strip width per axis is the stored size minus `real_proj_shape` when
    the metadata has it, otherwise `default_width`. Returns the side reports
    and the counts of the real sizes found.
    """
    height, width = int(labels.shape[-2]), int(labels.shape[-1])
    reals: dict[str, int] = {}
    reports = {
        s: SideReport(side=s, width=0, label_counts={}, patches_all_zero=0, patches=0)
        for s in SIDES
    }
    for p in positions:
        real = real_shape(metadata[p]) if p < len(metadata) else None
        key = "not in the metadata" if real is None else f"{real[0]} x {real[1]}"
        reals[key] = reals.get(key, 0) + 1
        widths = {
            "top": height - real[0] if real else default_width,
            "bottom": height - real[0] if real else default_width,
            "left": width - real[1] if real else default_width,
            "right": width - real[1] if real else default_width,
        }
        label = np.asarray(labels[p])
        image = np.asarray(images[p])
        for side in SIDES:
            w = widths[side]
            report = reports[side]
            report.width = max(report.width, w)
            report.patches += 1
            if w <= 0:
                continue
            values, counts = np.unique(strip(label, side, w), return_counts=True)
            for v, c in zip(values.tolist(), counts.tolist(), strict=True):
                report.label_counts[int(v)] = report.label_counts.get(int(v), 0) + int(c)
            if not np.any(strip(image, side, w)):
                report.patches_all_zero += 1
    return [reports[s] for s in SIDES], reals


def zero_sides(reports: Sequence[SideReport]) -> tuple[str, ...]:
    """The sides whose strips are zero in every band of every sampled patch."""
    return tuple(r.side for r in reports if r.width > 0 and r.all_zero)
