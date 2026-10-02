# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The metadata survey, on a synthetic table with real GeoTIFF items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from tiefer_lab.data import source, survey


def _tif(path: Path, data: np.ndarray, description: str | None = None) -> str:
    import rasterio

    bands = data if data.ndim == 3 else data[None]
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=bands.shape[2],
        height=bands.shape[1],
        count=bands.shape[0],
        dtype=bands.dtype,
    ) as dst:
        dst.write(bands)
        if description:
            dst.set_band_description(1, description)
    return str(path)


class _Sample(pd.DataFrame):
    def read(self, k: int) -> str:
        return str(self.iloc[k]["path"])


class _Table(pd.DataFrame):
    items: ClassVar[dict[int, list[tuple[str, str]]]] = {}

    def read(self, position: int) -> _Sample:
        rows = self.items[position]
        return _Sample({"tortilla:id": [n for n, _ in rows], "path": [p for _, p in rows]})


@pytest.fixture
def table(tmp_path: Path) -> _Table:
    image = _tif(tmp_path / "image.tif", np.ones((13, 4, 4), np.uint16))
    high_label = _tif(tmp_path / "high.tif", np.array([[0, 1], [2, 3]], np.uint8))
    scribble = _tif(tmp_path / "scribble.tif", np.array([[0, 99], [99, 3]], np.uint8), "label")
    frame = _Table(
        {
            source.ID_FIELD: [f"r{i}" for i in range(6)],
            source.PATCH_ID_FIELD: ["A", "B", "C", "C", "D", "A"],
            source.QUALITY_FIELD: ["high", "high", "high", "scribble", "nolabel", "scribble"],
            source.SHAPE_FIELD: [509, 509, 509, 509, 509, 2000],
            source.SPLIT_FIELD: ["train", "validation", "test", "train", "train", "train"],
            "stac:centroid": ["P0", "P1", "P2", "P2", "P4", "P0"],
        }
    )
    _Table.items = {
        0: [("image", image), ("label", high_label)],
        3: [("image", image), ("label", scribble)],
        4: [("image", image)],
    }
    return frame


def test_survey_reports_counts_locations_overlap_and_encodings(table: _Table) -> None:
    report = survey.run(per_type=1, with_extra=False, open_table=lambda _: table)
    l1c = report["l1c"]
    assert l1c["rows"] == 6
    assert {
        "label_type": "scribble",
        "real_proj_shape": 509,
        "tortilla:data_split": "train",
        "patches": 1,
    } in l1c["counts"]
    assert l1c["label_types"]["scribble"]["distinct_roi_id"] == 2
    assert l1c["location_fields"] == ["roi_id", "stac:centroid"]
    # The scribble patch at location C (P2) shares it with the high quality test patch.
    overlap = l1c["overlap_with_val_test"]["fields"]
    assert overlap["roi_id"]["scribble"] == {"patches": 2, "location_in_val_or_test": 1}
    assert overlap["stac:centroid"]["nolabel"] == {"patches": 1, "location_in_val_or_test": 0}
    scribble_items = l1c["samples"]["scribble"][0]["items"]
    assert [i["name"] for i in scribble_items] == ["image", "label"]
    assert scribble_items[0]["bands"] == 13 and scribble_items[0]["dtype"] == "uint16"
    label = scribble_items[1]
    assert label["descriptions"] == ["label"]
    assert label["histogram"][0]["values"] == {"0": 1, "3": 1, "99": 2}
    assert [i["name"] for i in l1c["samples"]["nolabel"][0]["items"]] == ["image"]


def test_survey_writes_its_report(
    table: _Table, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = survey.run
    monkeypatch.setattr(survey, "run", lambda *_: original(1, False, open_table=lambda _: table))
    assert survey.main(["--no-extra"]) == 0
    report = json.loads((tiefer_env["TIEFER_REPORTS_DIR"] / "data" / "survey.json").read_text())
    assert report["l1c"]["rows"] == 6 and report["card_version"] == source.DATASET_CARD_VERSION


def test_link_counts_extra_rows_found_in_the_level_1c_table(table: _Table) -> None:
    extra = pd.DataFrame(
        {source.ID_FIELD: ["r0", "r1", "zz"], source.PATCH_ID_FIELD: ["A", "B", "Q"]}
    )
    out = survey.link(table, extra)
    assert out["shared_columns"] == [source.PATCH_ID_FIELD, source.ID_FIELD]
    assert out["matches"][source.ID_FIELD] == {"extra_rows": 3, "found_in_l1c": 2}


def test_overlap_needs_the_split_field(table: _Table) -> None:
    out = survey.overlap(pd.DataFrame(table.drop(columns=[source.SPLIT_FIELD])), ["roi_id"])
    assert out["computed"] is False
