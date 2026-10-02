# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Band selection and label mapping, against small synthetic GeoTIFF files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
import rasterio

from tiefer_lab.data import source


def test_exactly_four_bands_in_order() -> None:
    assert source.USED_BANDS == ("B02", "B03", "B04", "B08")
    assert source.USED_BAND_LABELS == ("blue", "green", "red", "near infrared")
    assert len(source.USED_BAND_INDEXES) == 4
    for name, index in zip(source.USED_BANDS, source.USED_BAND_INDEXES, strict=True):
        assert source.L1C_BAND_NAMES[index - 1] == name


def test_class_order_and_label_mapping() -> None:
    assert source.CLASS_NAMES == ("clear", "thick cloud", "thin cloud", "cloud shadow")
    assert source.NUM_CLASSES == 4
    raw = np.array([[0, 1], [2, 3]], dtype=np.uint8)
    mapped = source.map_labels(raw)
    expected = [source.LABEL_CODES[v] for v in (0, 1, 2, 3)]
    np.testing.assert_array_equal(mapped.ravel(), expected)
    assert mapped.dtype == np.uint8


def test_unknown_label_code_is_an_error() -> None:
    with pytest.raises(source.DataSourceError, match="LABEL_CODES"):
        source.map_labels(np.array([[0, 9]], dtype=np.uint8))


def _write_tif(path: Path, data: np.ndarray) -> None:
    profile = {
        "driver": "GTiff",
        "height": data.shape[1],
        "width": data.shape[2],
        "count": data.shape[0],
        "dtype": data.dtype.name,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)


class _Sample:
    def __init__(self, paths: list[str]) -> None:
        self._paths = paths

    def read(self, item: int) -> str:
        return self._paths[item]


class _FakeTable:
    """The two methods of tacoreader's table that the reader uses."""

    def __init__(self, frame: pd.DataFrame, samples: list[_Sample]) -> None:
        self.iloc = frame.iloc
        self._samples = samples

    def read(self, position: int) -> Any:
        return self._samples[position]


def test_read_patch_selects_used_bands_from_synthetic_file(tmp_path: Path) -> None:
    height, width = 8, 6
    # Band k of the synthetic 13-band file holds the value 100 * k everywhere.
    bands = np.stack([np.full((height, width), 100 * (k + 1), dtype=np.uint16) for k in range(13)])
    label = np.zeros((1, height, width), dtype=np.uint8)
    label[0, :2] = 1
    label[0, 2:4] = 2
    label[0, 4:5] = 3
    _write_tif(tmp_path / "image.tif", bands)
    _write_tif(tmp_path / "label.tif", label)
    frame = pd.DataFrame(
        {
            source.ID_FIELD: ["synthetic-0"],
            source.PATCH_ID_FIELD: ["ROI_00001"],
            source.SPLIT_FIELD: [source.SPLIT_VALUES["train"]],
            source.QUALITY_FIELD: [source.QUALITY_HIGH],
            "internal:subfile": ["ignored"],
        }
    )
    table = _FakeTable(frame, [_Sample([str(tmp_path / "image.tif"), str(tmp_path / "label.tif")])])
    patch = source.read_patch(table, 0)
    assert patch.patch_id == "ROI_00001", "reports identify patches by roi_id"
    assert patch.image.shape == (4, height, width)
    assert [int(patch.image[i, 0, 0]) for i in range(4)] == [
        100 * i for i in source.USED_BAND_INDEXES
    ]
    np.testing.assert_array_equal(patch.label, source.map_labels(label[0]))
    assert "internal:subfile" not in patch.metadata
    assert patch.metadata[source.ID_FIELD] == "synthetic-0"


def test_read_patch_rejects_wrong_band_count(tmp_path: Path) -> None:
    _write_tif(tmp_path / "image.tif", np.zeros((4, 4, 4), dtype=np.uint16))
    _write_tif(tmp_path / "label.tif", np.zeros((1, 4, 4), dtype=np.uint8))
    frame = pd.DataFrame({source.ID_FIELD: ["x"], source.PATCH_ID_FIELD: ["ROI_x"]})
    table = _FakeTable(frame, [_Sample([str(tmp_path / "image.tif"), str(tmp_path / "label.tif")])])
    with pytest.raises(source.DataSourceError, match="expected 13 bands"):
        source.read_patch(table, 0)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            source.ID_FIELD: ["c", "a", "b", "d", "e", "f"],
            source.PATCH_ID_FIELD: ["r3", "r1", "r2", "r4", "r5", "r6"],
            source.SPLIT_FIELD: ["train", "train", "validation", "train", "test", "train"],
            source.QUALITY_FIELD: ["high", "high", "high", "scribble", "high", "high"],
            source.SHAPE_FIELD: [509, 509, 509, 509, 509, 2000],
        }
    )


def test_select_keeps_high_quality_509_patches_and_counts_dropped() -> None:
    frame = _frame()
    assert source.select_rows(frame, "train") == [1, 0]
    assert source.select_rows(frame, "val") == [2]
    assert len(source.select_rows(frame, "train", limit=1)) == 1
    counts = source.select(frame, "train").counts()
    assert counts == {
        "high_quality": 3,
        "kept_509": 2,
        "dropped_other_shape": 1,
        "dropped_location_in_val_or_test": 0,
        "limit": None,
        "selected": 2,
    }
    with pytest.raises(ValueError):
        source.select_rows(frame, "holdout")


def test_missing_split_field_stops_with_a_clear_message() -> None:
    frame = _frame().drop(columns=[source.SPLIT_FIELD])
    with pytest.raises(source.DataSourceError, match="does not name the split field"):
        source.select(frame, "train")
    with pytest.raises(source.DataSourceError, match="real_proj_shape"):
        source.check_columns(
            [source.SPLIT_FIELD, source.QUALITY_FIELD, source.PATCH_ID_FIELD, source.ID_FIELD]
        )
