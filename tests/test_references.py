# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Reference masks from the extra table: verification stops, encodings, coverage, resume."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from tiefer_lab.data import build_cache, cache, source

N = 6
SIZE = 8


class _Table:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.iloc = frame.iloc
        self.columns = frame.columns

    def __getitem__(self, key: Any) -> Any:
        return self.frame[key]


class _Sample:
    def __init__(self, row: int) -> None:
        self.row = row

    def __getitem__(self, key: str) -> list[str]:
        assert key == "tortilla:id"
        return ["mask_a", "mask_b"]

    def read(self, k: int) -> str:
        return f"{self.row}:{k}"


class _Extra(_Table):
    def read(self, position: int) -> _Sample:
        return _Sample(position)


def _l1c() -> _Table:
    frame = pd.DataFrame(
        {
            source.ID_FIELD: [f"p{i}" for i in range(N)],
            source.PATCH_ID_FIELD: [f"ROI_{i}" for i in range(N)],
            source.SPLIT_FIELD: ["test"] * N,
            source.QUALITY_FIELD: ["high"] * N,
            source.SHAPE_FIELD: [509] * N,
        }
    )
    return _Table(frame)


def _extra() -> _Extra:
    # ROI_4 has no row in the extra table; rows come in another order.
    return _Extra(
        pd.DataFrame({source.PATCH_ID_FIELD: ["ROI_3", "ROI_0", "ROI_1", "ROI_2", "ROI_5"]})
    )


@pytest.fixture
def built(tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> Path:
    table = _l1c()
    monkeypatch.setattr(source, "open_table", lambda _: table)

    def fake_read(_: Any, position: int, bands: Any = source.USED_BANDS) -> source.Patch:
        return source.Patch(
            patch_id=f"ROI_{position}",
            image=np.random.default_rng(position).integers(1, 9, (4, SIZE, SIZE), np.uint16),
            label=np.zeros((SIZE, SIZE), np.uint8),
            metadata=source.row_metadata(table.iloc[position]),
        )

    monkeypatch.setattr(source, "read_patch", fake_read)
    assert build_cache.main(["--split", "test", "--revision", "r", "--taco", "x"]) == 0
    return cache.cache_dir(build_cache.DEFAULT_NAME)


def _verified(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test encodings only: mask_a is a binary cloud mask with codes 0 and 1 and
    # no-data 9; mask_b uses our four classes, coded 10 to 13.
    monkeypatch.setattr(source, "REFERENCE_LINK_FIELD", source.PATCH_ID_FIELD)
    monkeypatch.setattr(source, "REFERENCE_MASK_ITEMS", {"qa": "mask_a", "four": "mask_b"})
    monkeypatch.setattr(
        source,
        "REFERENCE_ENCODINGS",
        {
            "qa": source.MaskEncoding("cloud", {0: 0, 1: 1, 9: source.IGNORE_INDEX}),
            "four": source.MaskEncoding("four_class", {10: 0, 11: 1, 12: 2, 13: 3}),
        },
    )


def _raw(path: str, indexes: Any, expected: int) -> np.ndarray:
    row, item = (int(v) for v in path.split(":"))
    if item == 0:
        values = np.full((SIZE, SIZE), row % 2, np.uint8)
        values[0, 0] = 9
    else:
        values = np.full((SIZE, SIZE), 10 + row % 4, np.uint8)
    return values[None]


def test_references_wait_for_verified_facts(built: Path) -> None:
    with pytest.raises(source.DataSourceError, match="REFERENCE_LINK_FIELD is not verified yet"):
        build_cache.main(["--split", "test", "--references"])


def test_unknown_raw_values_stop_the_encoding() -> None:
    encoding = source.MaskEncoding("cloud", {0: 0, 1: 1})
    with pytest.raises(source.DataSourceError, match=r"raw values \[7\]"):
        source.encode_mask(np.array([0, 1, 7]), encoding, "x")
    with pytest.raises(ValueError):
        source.MaskEncoding("binary", {})


def test_references_are_linked_encoded_and_resumable(
    built: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _verified(monkeypatch)
    extra = _extra()
    monkeypatch.setattr(source, "open_extra_table", lambda taco=None: extra)
    monkeypatch.setattr(source, "_read_bands", _raw)
    real = source.read_references
    calls = {"n": 0}

    def flaky(table: Any, position: int, names: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 3:
            raise ConnectionError("simulated network failure")
        return real(table, position, names)

    monkeypatch.setattr(source, "read_references", flaky)
    args = ["--split", "test", "--references", "--workers", "1"]
    monkeypatch.setattr(source, "REFERENCE_MASK_NAMES", ("qa", "four"))
    with pytest.raises(ConnectionError):
        build_cache.main(args)
    assert build_cache.main(args) == 0

    index = cache.read_index(built)
    entry = index["splits"]["test"]
    assert entry["reference_masks"] == ["qa", "four"]
    assert entry["reference_kinds"] == {"qa": "cloud", "four": "four_class"}
    assert entry["reference_missing"] == 1
    data = cache.load_split(built, "test")
    # Patch i is linked to its extra row by roi_id, whatever the row order.
    extra_row = {f"ROI_{i}": r for r, i in enumerate([3, 0, 1, 2, 5])}
    for i in range(N):
        qa, four = data.reference["qa"][i], data.reference["four"][i]
        if i == 4:
            assert (qa == source.IGNORE_INDEX).all() and (four == source.IGNORE_INDEX).all()
            continue
        row = extra_row[f"ROI_{i}"]
        assert qa[0, 0] == source.IGNORE_INDEX and qa[1, 1] == row % 2
        assert (four == row % 4).all()
    assert not (built / "test.references.json").exists()
