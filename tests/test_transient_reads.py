# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""A read that fails part way, as when the server answers with an error page.

GDAL then reports the file as "not recognized as being in a supported file
format" and rasterio raises RasterioIOError("Read failed.") from inside
`src.read(...)`, after the open succeeded. These tests use a fake rasterio
dataset; nothing is downloaded.
"""

from __future__ import annotations

import random
import urllib.error
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import rasterio
import rasterio.errors

from tiefer_lab.data import build_cache, cache, http, source

SIZE = 4


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class _Dataset:
    """A fake rasterio dataset; `failures` read calls raise before data comes back."""

    def __init__(self, count: int, data: np.ndarray, failures: list[int]) -> None:
        self.count = count
        self.descriptions = (None,) * count
        self._data = data
        self._failures = failures

    def __enter__(self) -> _Dataset:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, indexes: list[int]) -> np.ndarray:
        if self._failures[0] > 0:
            self._failures[0] -= 1
            raise rasterio.errors.RasterioIOError("Read failed.")
        return self._data[[i - 1 for i in indexes]]


class _Sample:
    def read(self, item: int) -> str:
        return {source.IMAGE_ITEM: "image.tif", source.LABEL_ITEM: "label.tif"}[item]


class _Table:
    def __init__(self) -> None:
        self.iloc = [{source.PATCH_ID_FIELD: "ROI_00042", "label_type": "high"}]

    def read(self, position: int) -> _Sample:
        return _Sample()


def _fake_rasterio(
    monkeypatch: pytest.MonkeyPatch,
    *,
    image_failures: int = 0,
    image_bands: int = len(source.L1C_BAND_NAMES),
    label_size: int = SIZE,
) -> list[int]:
    failures = [image_failures]
    image = np.ones((image_bands, SIZE, SIZE), dtype=np.uint16)
    label = np.zeros((1, label_size, label_size), dtype=np.uint8)

    def fake_open(path: str) -> _Dataset:
        if path == "image.tif":
            return _Dataset(image_bands, image, failures)
        return _Dataset(1, label, [0])

    monkeypatch.setattr(rasterio, "open", fake_open)
    return failures


def _reader(clock: _Clock, attempts: int = http.MAX_ATTEMPTS) -> Any:
    backoff = http.Backoff(
        sleep=clock.sleep, clock=clock.time, rng=random.Random(0), attempts=attempts
    )
    plan = SimpleNamespace(bands=source.USED_BANDS, extra=False, table=_Table())
    return build_cache._reader(plan, backoff, None)  # type: ignore[arg-type]


def test_a_read_that_fails_twice_part_way_pauses_and_is_read_again(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    left = _fake_rasterio(monkeypatch, image_failures=2)
    clock = _Clock()
    patch = _reader(clock)(0)
    assert patch.patch_id == "ROI_00042"
    assert patch.image.shape == (len(source.USED_BANDS), SIZE, SIZE)
    assert left == [0] and len(clock.sleeps) == 2, "two pauses, then the third read succeeds"
    out = capsys.readouterr().out
    assert out.count("read failed (RasterioIOError: Read failed.); all readers pause") == 2


def test_the_job_stops_after_the_last_attempt_and_names_the_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_rasterio(monkeypatch, image_failures=100)
    clock = _Clock()
    with pytest.raises(cache.CacheError) as caught:
        _reader(clock, attempts=3)(0)
    message = str(caught.value)
    assert "patch ROI_00042 (row 0) could not be read after 3 attempts" in message
    assert "Read failed." in message and "The build is resumable" in message
    assert isinstance(caught.value.__cause__, rasterio.errors.RasterioIOError)
    assert len(clock.sleeps) == 2


@pytest.mark.parametrize(
    "fault, expected",
    [
        ({"image_bands": 12}, "expected 13 bands, found 12"),
        ({"label_size": SIZE + 1}, "differs from image"),
    ],
)
def test_errors_a_retry_cannot_fix_are_raised_at_once(
    monkeypatch: pytest.MonkeyPatch, fault: dict[str, int], expected: str
) -> None:
    _fake_rasterio(monkeypatch, **fault)
    clock = _Clock()
    with pytest.raises(source.DataSourceError, match=expected):
        _reader(clock)(0)
    assert clock.sleeps == []


@pytest.mark.parametrize(
    "error, transient",
    [
        (rasterio.errors.RasterioIOError("Read failed."), True),
        (rasterio.errors.RasterioIOError("HTTP response code: 429"), True),
        (urllib.error.HTTPError("https://example.invalid", 429, "x", None, None), True),  # type: ignore[arg-type]
        (urllib.error.HTTPError("https://example.invalid", 503, "x", None, None), True),  # type: ignore[arg-type]
        (urllib.error.HTTPError("https://example.invalid", 404, "x", None, None), False),  # type: ignore[arg-type]
        (source.DataSourceError("expected 13 bands, found 12"), False),
        (ValueError("bad band"), False),
        (OSError("disk full"), False),
    ],
)
def test_which_errors_are_transient(error: BaseException, transient: bool) -> None:
    assert http.is_transient(error) is transient
