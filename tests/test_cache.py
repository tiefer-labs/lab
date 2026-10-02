# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Cache building, resuming and reading, with synthetic data only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from tiefer_lab.data import build_cache, cache, source


def test_synthetic_cache_round_trip(tiefer_env: dict[str, Path]) -> None:
    assert (
        build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
        == 0
    )
    directory = cache.cache_dir(build_cache.SYNTHETIC_NAME)
    index = cache.read_index(directory)
    assert cache.is_synthetic(index)
    assert index["bands"] == list(source.USED_BANDS)
    mean, std = cache.normalisation(index)
    assert mean.shape == (4,) and np.all(std > 0)
    for mode in ("memory", "mmap"):
        data = cache.load_split(directory, "val", mode=mode)  # type: ignore[arg-type]
        assert len(data) == 6
        assert data.images.shape == (6, 4, 64, 64) and data.images.dtype == np.uint16
        assert data.labels.shape == (6, 64, 64) and data.labels.max() < source.NUM_CLASSES
        assert data.in_memory == (mode == "memory")
    assert sum(index["splits"]["train"]["class_pixels"]) == 6 * 64 * 64


def test_synthetic_data_is_reproducible(tiefer_env: dict[str, Path]) -> None:
    first = list(build_cache.synthetic_patches(3, 32, seed=7))
    second = list(build_cache.synthetic_patches(3, 32, seed=7))
    for (a_img, a_lab), (b_img, b_lab) in zip(first, second, strict=True):
        np.testing.assert_array_equal(a_img, b_img)
        np.testing.assert_array_equal(a_lab, b_lab)


def test_missing_or_incomplete_split_is_an_error(tiefer_env: dict[str, Path]) -> None:
    directory = cache.cache_dir("absent")
    with pytest.raises(cache.CacheError, match="no cache index"):
        cache.load_split(directory, "train")
    build_cache.main(["--split", "val", "--synthetic", "--limit", "2", "--patch-size", "32"])
    with pytest.raises(cache.CacheError, match="not complete"):
        cache.load_split(cache.cache_dir(build_cache.SYNTHETIC_NAME), "train")


class _FakeTable:
    def __init__(self, n: int, large: int = 0) -> None:
        total = n + large
        self.frame = pd.DataFrame(
            {
                source.ID_FIELD: [f"p{i:03d}" for i in range(total)],
                source.PATCH_ID_FIELD: [f"ROI_{i:05d}" for i in range(total)],
                source.SPLIT_FIELD: [source.SPLIT_VALUES["train"]] * total,
                source.QUALITY_FIELD: [source.QUALITY_HIGH] * total,
                source.SHAPE_FIELD: [509] * n + [2000] * large,
                "region": ["north" if i % 2 else "south" for i in range(total)],
            }
        )
        self.iloc = self.frame.iloc
        self.columns = self.frame.columns

    def __getitem__(self, key: Any) -> Any:
        return self.frame[key]


def test_real_builder_resumes_after_interruption(
    tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    table = _FakeTable(60, large=5)
    reads: list[int] = []
    fail_at = {"position": 30}

    def fake_read(_: Any, position: int) -> source.Patch:
        if position == fail_at["position"]:
            raise ConnectionError("simulated network failure")
        reads.append(position)
        rng = np.random.default_rng(position)
        return source.Patch(
            patch_id=f"ROI_{position:05d}",
            image=rng.integers(0, 5000, size=(4, 16, 16), dtype=np.uint16),
            label=np.full((16, 16), position % 4, dtype=np.uint8),
            metadata=source.row_metadata(table.iloc[position]),
        )

    monkeypatch.setattr(source, "open_table", lambda _: table)
    monkeypatch.setattr(source, "read_patch", fake_read)
    args = ["--split", "train", "--revision", "test-revision", "--taco", "local.taco"]
    with pytest.raises(ConnectionError):
        build_cache.main(args)
    directory = cache.cache_dir(build_cache.DEFAULT_NAME)
    assert (directory / "train.progress.json").is_file()
    # Progress is saved when a read fails, so nothing before the failure is read again.
    saved = 30

    fail_at["position"] = -1
    reads.clear()
    assert build_cache.main(args) == 0
    assert min(reads) == saved, "the second run continues where the first one stopped"
    data = cache.load_split(directory, "train")
    assert len(data) == 60
    assert data.patch_ids == [f"ROI_{i:05d}" for i in range(60)]
    np.testing.assert_array_equal(data.labels[:, 0, 0], np.arange(60) % 4)
    assert data.metadata[1]["region"] == "north"
    index = cache.read_index(directory)
    assert index["dataset"]["revision"] == "test-revision"
    entry = index["splits"]["train"]
    assert entry["row_keys"] == [f"p{i:03d}" for i in range(60)]
    assert entry["selection"]["kept_509"] == 60
    assert entry["selection"]["dropped_other_shape"] == 5
    assert not list(directory.glob("*.partial.npy"))
    assert not (directory / "train.progress.json").exists()


def test_download_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLURM_CPUS_PER_TASK", raising=False)
    assert build_cache.download_workers() == 4
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "16")
    assert build_cache.download_workers() == 16
    assert build_cache.download_workers(2) == 2


def _fake_reads(
    table: _FakeTable, reads: list[int], fail_at: dict[str, int]
) -> Any:  # a source.read_patch stand-in
    def fake_read(_: Any, position: int) -> source.Patch:
        if position == fail_at["position"]:
            raise ConnectionError("simulated network failure")
        reads.append(position)
        return source.Patch(
            patch_id=f"ROI_{position:05d}",
            image=np.full((4, 16, 16), position, dtype=np.uint16),
            label=np.full((16, 16), position % 4, dtype=np.uint8),
            metadata=source.row_metadata(table.iloc[position]),
        )

    return fake_read


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir()) if p.is_file()}


def test_a_limited_build_never_resets_or_replaces_the_full_cache(
    tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    table = _FakeTable(60)
    reads: list[int] = []
    fail_at = {"position": 40}
    monkeypatch.setattr(source, "open_table", lambda _: table)
    monkeypatch.setattr(source, "read_patch", _fake_reads(table, reads, fail_at))
    full = ["--split", "train", "--revision", "r", "--taco", "local.taco"]
    tiny = [*full, "--limit", "32"]
    directory = cache.cache_dir(build_cache.DEFAULT_NAME)

    # A full build in progress (as while data.sbatch runs): a tiny build stops.
    with pytest.raises(ConnectionError):
        build_cache.main(full)
    before = _snapshot(directory)
    with pytest.raises(cache.CacheError, match="build in progress with another selection"):
        build_cache.main(tiny)
    assert _snapshot(directory) == before, "the build in progress is untouched"

    # The full build continues where it stopped, then a tiny build still stops.
    fail_at["position"] = -1
    reads.clear()
    assert build_cache.main(full) == 0
    assert min(reads) == 40
    before = _snapshot(directory)
    with pytest.raises(cache.CacheError, match="complete split with another selection"):
        build_cache.main(tiny)
    assert _snapshot(directory) == before, "the complete split is untouched"

    # The same full build again reads nothing; --restart is the only way to replace it.
    reads.clear()
    assert build_cache.main(full) == 0
    assert reads == [] and _snapshot(directory) == before
    assert build_cache.main([*tiny, "--restart"]) == 0
    assert len(cache.load_split(directory, "train")) == 32


def test_class_pixels_are_counted_in_chunks_without_loading_the_split(tmp_path: Path) -> None:
    import tracemalloc

    labels = np.lib.format.open_memmap(
        tmp_path / "labels.npy", mode="w+", dtype=np.uint8, shape=(200, 256, 256)
    )
    labels[:] = np.arange(256, dtype=np.uint8)[None, None, :] % 4
    labels.flush()
    labels = np.load(tmp_path / "labels.npy", mmap_mode="r")
    tracemalloc.start()
    counts = build_cache.class_pixels(labels, chunk=16)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert counts == [200 * 256 * 64] * 4
    # Counting the whole split at once would allocate 8 bytes per pixel.
    assert peak < labels.nbytes, f"peak {peak} bytes for {labels.nbytes} bytes of labels"


def test_band_statistics_are_chunked(tmp_path: Path) -> None:
    import tracemalloc

    from tiefer_lab.data import transforms

    images = np.lib.format.open_memmap(
        tmp_path / "images.npy", mode="w+", dtype=np.uint16, shape=(256, 13, 128, 128)
    )
    images[:] = np.arange(256 * 13, dtype=np.uint16).reshape(256, 13, 1, 1) + 1
    images.flush()
    images = np.load(tmp_path / "images.npy", mmap_mode="r")
    tracemalloc.start()
    transforms.band_statistics(images)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # float64 of the whole split would be 4 times its uint16 size; chunks keep
    # the peak at a few chunks, independent of the number of patches.
    assert peak < images.nbytes / 2


def test_finishing_step_resumes_after_it_failed(
    tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    table = _FakeTable(20)
    reads: list[int] = []
    monkeypatch.setattr(source, "open_table", lambda _: table)
    monkeypatch.setattr(source, "read_patch", _fake_reads(table, reads, {"position": -1}))
    real_finish = build_cache._finish_split

    def out_of_memory(*_: Any, **__: Any) -> None:
        raise MemoryError("simulated out of memory in the finishing step")

    monkeypatch.setattr(build_cache, "_finish_split", out_of_memory)
    args = ["--split", "train", "--revision", "r", "--taco", "local.taco"]
    with pytest.raises(MemoryError):
        build_cache.main(args)
    directory = cache.cache_dir(build_cache.DEFAULT_NAME)
    # The state that failed on Roihu: final files in place, no partial files, progress at the end.
    assert (directory / "train_images.npy").is_file()
    assert not (directory / "train_images.partial.npy").exists()
    assert json.loads((directory / "train.progress.json").read_text())["done"] == 20

    monkeypatch.setattr(build_cache, "_finish_split", real_finish)
    reads.clear()
    assert build_cache.main(args) == 0
    assert reads == [], "no patch is read again"
    data = cache.load_split(directory, "train")
    assert len(data) == 20 and not (directory / "train.progress.json").exists()
    assert sum(cache.read_index(directory)["splits"]["train"]["class_pixels"]) == 20 * 16 * 16
