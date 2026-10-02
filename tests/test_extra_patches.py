# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Scribble and nolabel patches: verification stops, location exclusion, ignored pixels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from tiefer_lab.data import build_cache, cache, source


def _table() -> pd.DataFrame:
    # Locations: L1 and L2 are in val or test; extra patches there must be dropped.
    rows = [
        ("h0", "L0", "high", "train", 509),
        ("h1", "L1", "high", "validation", 509),
        ("h2", "L2", "high", "test", 509),
        ("s0", "L3", "scribble", "train", 509),
        ("s1", "L1", "scribble", "train", 509),  # location in val: dropped
        ("s2", "L4", "scribble", "train", 2000),  # other size: dropped
        ("n0", "L5", "nolabel", "train", 509),
        ("n1", "L2", "nolabel", "train", 509),  # location in test: dropped
        ("s3", "L6", "scribble", "test", 509),  # not the training split: not used
        ("n2", "L6", "nolabel", "train", 509),  # shares L6 with a test-split row: dropped
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            source.ID_FIELD,
            source.PATCH_ID_FIELD,
            source.QUALITY_FIELD,
            source.SPLIT_FIELD,
            source.SHAPE_FIELD,
        ],
    )
    frame["region"] = "x"
    return frame


class _Table:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.iloc = frame.iloc
        self.columns = frame.columns

    def __getitem__(self, key: Any) -> Any:
        return self.frame[key]


def test_extra_patches_wait_for_verified_facts() -> None:
    with pytest.raises(source.DataSourceError, match="LOCATION_FIELD is not verified yet"):
        source.select_extra(_table())


def test_extra_patches_away_from_val_and_test(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(source, "LOCATION_FIELD", source.PATCH_ID_FIELD)
    chosen = source.select_extra(_table())
    frame = _table()
    assert [frame.iloc[i][source.ID_FIELD] for i in chosen.positions] == ["n0", "s0"]
    counts = chosen.counts()
    assert counts["high_quality"] == 6  # extra patches of the training split
    assert counts["dropped_other_shape"] == 1
    assert counts["dropped_location_in_val_or_test"] == 3


def test_unlabelled_scribble_pixels_are_ignored() -> None:
    raw = np.array([[0, 1, 99], [2, 3, 99]])
    with pytest.raises(source.DataSourceError, match="99"):
        source.map_labels(raw)
    mapped = source.map_labels(raw, unlabelled_code=99)
    assert mapped.tolist() == [[0, 1, source.IGNORE_INDEX], [2, 3, source.IGNORE_INDEX]]


def test_read_extra_patch_by_label_type(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _table()
    image = np.ones((13, 4, 4), np.uint16)
    scribble = np.array([[0, 99, 99, 3]] * 4, np.uint8)

    class Sample:
        def read(self, k: int) -> str:
            return f"item{k}"

    class Table(_Table):
        def read(self, _: int) -> Sample:
            return Sample()

    def fake_bands(path: str, indexes: Any, expected: int) -> np.ndarray:
        return image[[i - 1 for i in indexes]] if path == "item0" else scribble[None]

    monkeypatch.setattr(source, "_read_bands", fake_bands)
    table = Table(frame)
    with pytest.raises(source.DataSourceError, match="SCRIBBLE_UNLABELLED_CODE"):
        source.read_extra_patch(table, 3)
    monkeypatch.setattr(source, "SCRIBBLE_UNLABELLED_CODE", 99)
    patch = source.read_extra_patch(table, 3)
    assert (patch.label == source.IGNORE_INDEX).sum() == 8 and patch.image.shape == (4, 4, 4)
    nolabel = source.read_extra_patch(table, 6, bands=source.L1C_BAND_NAMES)
    assert (nolabel.label == source.IGNORE_INDEX).all() and nolabel.image.shape == (13, 4, 4)


def test_built_index_proves_no_training_patch_shares_a_location_with_val_or_test(
    tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = _table()
    table = _Table(frame)
    monkeypatch.setattr(source, "LOCATION_FIELD", source.PATCH_ID_FIELD)
    monkeypatch.setattr(source, "open_table", lambda _: table)

    def fake_read(_: Any, position: int, bands: Any = source.USED_BANDS) -> source.Patch:
        kind = frame.iloc[position][source.QUALITY_FIELD]
        label = np.full((8, 8), position % 4, np.uint8)
        if kind != "high":
            label[:, :4] = source.IGNORE_INDEX
        return source.Patch(
            patch_id=str(frame.iloc[position][source.PATCH_ID_FIELD]),
            image=np.random.default_rng(position).integers(1, 5000, (len(bands), 8, 8), np.uint16),
            label=label,
            metadata=source.row_metadata(frame.iloc[position]),
        )

    monkeypatch.setattr(source, "read_patch", fake_read)
    monkeypatch.setattr(source, "read_extra_patch", fake_read)
    base = ["--revision", "r", "--taco", "local.taco"]
    for split in ("train", "val", "test", cache.EXTRA_SPLIT):
        assert build_cache.main(["--split", split, *base]) == 0
    directory = cache.cache_dir(build_cache.DEFAULT_NAME)
    index = cache.read_index(directory)
    assert index["splits"][cache.EXTRA_SPLIT]["patch_ids"] == ["L5", "L3"]
    # Ignored pixels are not counted as any class.
    assert sum(index["splits"][cache.EXTRA_SPLIT]["class_pixels"]) == 2 * 8 * 4
    assert cache.location_overlap(index, source.PATCH_ID_FIELD) == {"train": 0, "train_extra": 0}
    assert cache.main(["overlap", build_cache.DEFAULT_NAME, source.PATCH_ID_FIELD]) == 0

    # The check catches an overlap, and a missing field never passes.
    index["splits"]["train"]["metadata"][0][source.PATCH_ID_FIELD] = "L2"
    cache.write_index(directory, index)
    assert cache.location_overlap(index, source.PATCH_ID_FIELD)["train"] == 1
    assert cache.main(["overlap", build_cache.DEFAULT_NAME, source.PATCH_ID_FIELD]) == 1
    assert cache.location_overlap(index, "no_such_field") == {"train": 1, "train_extra": 2}
