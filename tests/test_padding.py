# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The padding of cached patches, and the read-only check of a cache, on synthetic data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tiefer_lab.data import build_cache, cache, padding

SIZE = 64
REAL = 61  # 3 padded rows and columns, as 509 in a 512 x 512 patch
PATCHES = 6


def padded_cache(sides: tuple[str, str] = ("left", "bottom"), label: int = 0) -> Path:
    """A synthetic val split whose patches are padded by 3 pixels on `sides`.

    The padded image pixels are zero in every band and the padded label
    pixels hold `label`; `real_proj_shape` is written into the metadata.
    """
    build_cache.main(
        ["--split", "val", "--synthetic", "--limit", str(PATCHES), "--patch-size", str(SIZE)]
    )
    directory = cache.cache_dir(build_cache.SYNTHETIC_NAME)
    images = np.load(cache.images_path(directory, "val"))
    labels = np.load(cache.labels_path(directory, "val"))
    images[images == 0] = 1  # no zero pixel outside the padding
    pad = padding.padding_of((SIZE, SIZE), (REAL, REAL), sides)
    invalid = np.zeros((SIZE, SIZE), dtype=bool)
    invalid[: pad.top] = invalid[SIZE - pad.bottom :] = True
    invalid[:, : pad.left] = invalid[:, SIZE - pad.right :] = True
    images[:, :, invalid] = 0
    labels[:, invalid] = label
    np.save(cache.images_path(directory, "val"), images)
    np.save(cache.labels_path(directory, "val"), labels)
    index = cache.read_index(directory)
    for m in index["splits"]["val"]["metadata"]:
        m["real_proj_shape"] = REAL
    cache.write_index(directory, index)
    return directory


def test_padding_follows_the_metadata_and_the_sides() -> None:
    assert padding.padding_of((512, 512), (509, 509)) == padding.Padding(bottom=3, left=3)
    assert padding.padding_of((512, 512), (509, 509), ("top", "right")) == padding.Padding(
        top=3, right=3
    )
    assert not padding.padding_of((512, 512), None)
    assert not padding.padding_of((509, 509), (509, 509))
    assert padding.Padding(bottom=3, left=3).pixels(512, 512) == 3_063
    with pytest.raises(ValueError, match="smaller"):
        padding.padding_of((500, 500), (509, 509))
    with pytest.raises(ValueError, match="no side"):
        padding.padding_of((512, 512), (509, 509), ("left",))
    with pytest.raises(ValueError, match="at most one"):
        padding.padding_of((512, 512), (509, 509), ("left", "right", "bottom"))
    assert padding.real_shape({"real_proj_shape": 509}) == (509, 509)
    assert padding.real_shape({"real_proj_shape": "509.0"}) == (509, 509)
    assert padding.real_shape({}) is None
    assert padding.real_shape({"real_proj_shape": "x"}) is None


def test_check_finds_the_padded_sides(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    padded_cache()
    capsys.readouterr()
    assert cache.main(["padding", build_cache.SYNTHETIC_NAME, "--split", "val"]) == 0
    out = capsys.readouterr().out
    shapes = f"stored images ({PATCHES}, 4, {SIZE}, {SIZE}), labels ({PATCHES}, {SIZE}, {SIZE})"
    assert shapes in out
    assert f"real_proj_shape: {REAL} x {REAL}: {PATCHES}" in out
    strip_pixels = PATCHES * 3 * SIZE
    assert f"| left | 3 | 0: {strip_pixels:,} | {PATCHES} of {PATCHES} |" in out
    assert f"| bottom | 3 | 0: {strip_pixels:,} | {PATCHES} of {PATCHES} |" in out
    assert "| right | 3 |" in out and "| top | 3 |" in out
    assert "zero sides found: left, bottom; this agrees with PADDING_SIDES" in out


def test_check_reports_padding_on_other_sides(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    padded_cache(("top", "right"), label=3)
    capsys.readouterr()
    code = cache.main(["padding", build_cache.SYNTHETIC_NAME, "--split", "val", "--patches", "2"])
    out = capsys.readouterr().out
    assert code == 1
    assert "patches read: 2" in out
    assert f"| top | 3 | 3: {2 * 3 * SIZE:,} | 2 of 2 |" in out
    assert "zero sides found: right, top; this differs from PADDING_SIDES" in out


def test_check_writes_nothing(tiefer_env: dict[str, Path]) -> None:
    directory = padded_cache()
    before = {p.name: p.stat().st_mtime_ns for p in directory.iterdir()}
    cache.main(["padding", build_cache.SYNTHETIC_NAME])
    assert {p.name: p.stat().st_mtime_ns for p in directory.iterdir()} == before


def test_without_real_size_there_is_no_padding(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    build_cache.main(["--split", "val", "--synthetic", "--limit", "2", "--patch-size", "32"])
    assert cache.main(["padding", build_cache.SYNTHETIC_NAME]) in (0, 1)
    out = capsys.readouterr().out
    assert "real_proj_shape: not in the metadata: 2" in out


def test_sample_positions_spread_over_the_split() -> None:
    assert cache.sample_positions(10, 3) == [0, 4, 9]  # 4.5 rounds to the even 4
    assert cache.sample_positions(3, 50) == [0, 1, 2]
    assert cache.sample_positions(0, 5) == []
