# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Build the local data cache.

    python -m tiefer_lab.data.build_cache --split train|val|test|all [--limit N]
        [--bands used|all] [--shard I/N | --merge N] [--max-rate P]

Reads the chosen bands (the four used bands, or all 13 Level-1C bands) and
the label of each selected patch and writes them into
`$TIEFER_DATA_DIR/<name>/` (layout in `cache.py`). The build is resumable:
progress is saved every few patches, and running the same command again
continues where it stopped. Counts are verified at the end, and the disk
needed is printed before a build starts.

`--shard I/N` builds part I of N of a split in its own folder, so several jobs
can run side by side without writing the same file; `--merge N` joins the N
complete shards. `--max-rate` caps the reads per minute of the whole split and
is shared equally between the shards.

`--synthetic` writes a cache of synthetic scenes instead, for smoke runs and
tests when the dataset is not reachable. A synthetic cache is marked as such
in its index and is refused by training and evaluation unless they are
explicitly run as a smoke run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import cache, http, source
from tiefer_lab.data.transforms import band_statistics
from tiefer_lab.utils import paths

DEFAULT_NAME = "cloudsen12-l1c-high"
SYNTHETIC_NAME = "synthetic"
SAVE_EVERY = 25
DEFAULT_WORKERS = 4


def download_workers(requested: int | None = None) -> int:
    """Parallel readers: --workers, else SLURM_CPUS_PER_TASK, else 4."""
    if requested:
        return requested
    value = os.environ.get("SLURM_CPUS_PER_TASK", "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else DEFAULT_WORKERS


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _base_index(source_name: str, dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": cache.CACHE_FORMAT,
        "source": source_name,
        "dataset": dataset,
        "bands": list(source.USED_BANDS),
        "band_labels": list(source.USED_BAND_LABELS),
        "reflectance": {
            "scale": source.REFLECTANCE_SCALE,
            "offset": source.REFLECTANCE_OFFSET,
        },
        "classes": list(source.CLASS_NAMES),
        "splits": {},
    }


def _open_index(directory: Path, source_name: str, dataset: dict[str, Any]) -> dict[str, Any]:
    if (directory / cache.INDEX_NAME).is_file():
        index = cache.read_index(directory)
        if index.get("source") != source_name:
            raise cache.CacheError(
                f"{paths.portable(directory)} holds a {index.get('source')!r} cache; "
                f"use another --name for {source_name!r} data"
            )
        if (
            source_name != cache.SYNTHETIC_SOURCE
            and index["dataset"].get("taco") != dataset["taco"]
        ):
            raise cache.CacheError(
                "the cache was built from other dataset files; use another --name"
            )
        return index
    return _base_index(source_name, dataset)


def _update_normalisation(directory: Path, index: dict[str, Any]) -> None:
    images = np.load(cache.images_path(directory, "train"), mmap_mode="r", allow_pickle=False)
    mean, std = band_statistics(images)
    index["normalisation"] = {
        "computed_on": "train",
        "patches": int(images.shape[0]),
        "units": "top-of-atmosphere reflectance",
        "mean": [float(v) for v in mean],
        "std": [float(v) for v in std],
    }


# Patches per chunk when counting class pixels: 64 patches of 509 x 509 are
# about 17 MB of labels and 133 MB of int64 counts at most.
COUNT_CHUNK = 64


def class_pixels(labels: np.ndarray, chunk: int = COUNT_CHUNK) -> list[int]:
    """Pixels per class, counted in chunks so a memory-mapped split is never loaded whole."""
    counts = np.zeros(4, dtype=np.int64)
    for start in range(0, labels.shape[0], chunk):
        block = np.asarray(labels[start : start + chunk]).ravel()
        counts += np.bincount(block, minlength=4)[:4]
    return [int(c) for c in counts]


def _finish_split(
    directory: Path,
    index: dict[str, Any],
    split: str,
    patch_ids: list[str],
    metadata: list[dict[str, Any]],
    limit: int | None,
    reference_names: Sequence[str],
    selection: dict[str, Any] | None = None,
    row_keys: list[str] | None = None,
) -> None:
    images = np.load(cache.images_path(directory, split), mmap_mode="r", allow_pickle=False)
    labels = np.load(cache.labels_path(directory, split), mmap_mode="r", allow_pickle=False)
    if images.shape[0] != len(patch_ids) or labels.shape[0] != len(patch_ids):
        raise cache.CacheError(
            f"count check failed for {split}: {len(patch_ids)} IDs, "
            f"{images.shape[0]} images, {labels.shape[0]} labels"
        )
    index["splits"][split] = {
        "complete": True,
        "count": len(patch_ids),
        "height": int(images.shape[2]),
        "width": int(images.shape[3]),
        "limit": limit,
        "build_date": _now(),
        "patch_ids": patch_ids,
        "row_keys": row_keys or [],
        "selection": selection or {},
        "metadata": metadata,
        "reference_masks": list(reference_names),
        "class_pixels": class_pixels(labels),
    }
    if split == "train":
        _update_normalisation(directory, index)
    cache.write_index(directory, index)
    print(f"{split}: {len(patch_ids)} patches verified and indexed", flush=True)


# Real data -----------------------------------------------------------------


def _progress_path(directory: Path, split: str) -> Path:
    return cache.progress_path(directory, split)


def _partial(path: Path) -> Path:
    return path.with_name(path.name.replace(".npy", ".partial.npy"))


@dataclass(frozen=True)
class Target:
    """Where one resumable read writes: final arrays and a progress file."""

    images: Path
    labels: Path
    progress: Path


@dataclass
class Plan:
    """The selected rows of one split, their identities and the band choice."""

    split: str
    table: Any
    rows: list[int]
    ids: list[str]
    roi_ids: list[str]
    counts: dict[str, Any]
    bands: tuple[str, ...]
    extra: bool = False


def bytes_per_patch(bands: int, size: int = source.KEPT_SHAPE) -> int:
    """Disk use of one cached patch: uint16 bands and a uint8 label."""
    return bands * size * size * 2 + size * size


def check_disk(directory: Path, needed: int, what: str) -> None:
    """Print the disk estimate and stop when the file system has less free space.

    The free space of the file system is an upper bound: the project quota on
    /scratch can be lower (hpc/roihu/README.md says how to check it).
    """
    directory.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(directory).free
    gib = 1024**3
    print(
        f"disk estimate for {what}: {needed / gib:.1f} GiB; "
        f"file system free: {free / gib:.1f} GiB (check the project quota too)",
        flush=True,
    )
    if free < needed:
        raise cache.CacheError(
            f"{what} needs about {needed / gib:.1f} GiB but only {free / gib:.1f} GiB are free"
        )


def _read_rows(
    target: Target,
    plan: Plan,
    rows: Sequence[int],
    ids: Sequence[str],
    *,
    reader: Any,
    workers: int,
    restart: bool,
    label: str,
) -> list[dict[str, Any]]:
    """Read `rows` into `target`, resuming from its progress file. Returns the metadata.

    Patches are read in parallel but written in order, so `done` always means
    "patches 0 to done - 1 are in the arrays" and a restart continues there.
    """
    progress: dict[str, Any] = {}
    if target.progress.is_file():
        progress = json.loads(target.progress.read_text(encoding="utf-8"))
        if progress.get("patch_ids") != list(ids):
            if not restart:
                raise cache.CacheError(
                    f"{label}: {paths.portable(target.progress.parent)} holds a build in "
                    f"progress with another selection ({len(progress.get('patch_ids', []))} "
                    f"patches; now {len(ids)}). Use another --name or $TIEFER_DATA_DIR, or "
                    "pass --restart to discard it"
                )
            print(f"{label}: --restart: discarding the build in progress", flush=True)
            progress = {}
    n = len(rows)
    if (
        progress
        and int(progress["done"]) == n
        and target.images.is_file()
        and target.labels.is_file()
        and not _partial(target.images).exists()
    ):
        # Every patch was written and the files were moved into place, but the
        # finishing step did not complete (for example out of memory): finish only.
        print(f"{label}: all {n} patches written; running the finishing step", flush=True)
        metadata: list[dict[str, Any]] = progress["metadata"]
        return metadata

    first: source.Patch | None = None
    if progress:
        height, width = progress["height"], progress["width"]
        done = int(progress["done"])
        metadata = progress["metadata"]
        mode = "r+"
    else:
        first = reader(rows[0])
        height, width = first.label.shape
        done, metadata, mode = 0, [], "w+"
    target.images.parent.mkdir(parents=True, exist_ok=True)
    images = np.lib.format.open_memmap(
        _partial(target.images),
        mode=mode,
        dtype=np.uint16,
        shape=(n, len(plan.bands), height, width),
    )
    labels = np.lib.format.open_memmap(
        _partial(target.labels), mode=mode, dtype=np.uint8, shape=(n, height, width)
    )

    def save_progress() -> None:
        images.flush()
        labels.flush()
        state = {
            "patch_ids": list(ids),
            "done": done,
            "height": height,
            "width": width,
            "bands": list(plan.bands),
            "metadata": metadata,
        }
        tmp = target.progress.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, target.progress)

    if done:
        print(f"{label}: resuming at patch {done} of {n}", flush=True)
    print(f"{label}: reading with {workers} parallel workers", flush=True)
    window = max(1, workers) * 4
    pool = ThreadPoolExecutor(max_workers=max(1, workers))
    pending: dict[int, Future[source.Patch]] = {}
    submitted = done
    try:
        for i in range(done, n):
            while submitted < min(i + window, n):
                if submitted == 0 and first is not None:
                    ready: Future[source.Patch] = Future()
                    ready.set_result(first)
                    pending[submitted] = ready
                else:
                    pending[submitted] = pool.submit(reader, rows[submitted])
                submitted += 1
            patch = pending.pop(i).result()
            if patch.label.shape != (height, width):
                raise cache.CacheError(
                    f"patch {patch.patch_id} is {patch.label.shape}, expected {(height, width)}"
                )
            images[i] = patch.image
            labels[i] = patch.label
            metadata.append(patch.metadata)
            done = i + 1
            if done % SAVE_EVERY == 0 or done == n:
                save_progress()
                print(f"{label}: {done}/{n}", flush=True)
    except BaseException:
        save_progress()
        print(f"{label}: stopped after {done} of {n}; run the same command to continue", flush=True)
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    save_progress()
    os.replace(_partial(target.images), target.images)
    os.replace(_partial(target.labels), target.labels)
    return metadata


def _dataset(taco: Sequence[str], revision: str | None) -> dict[str, Any]:
    return {
        "repo": source.DATASET_REPO,
        "card": source.DATASET_CARD_URL,
        "licence": source.DATASET_LICENCE,
        "taco": list(taco),
        "revision": revision or "unknown",
    }


def _open_real_index(
    directory: Path, taco: Sequence[str], revision: str | None, bands: Sequence[str]
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    index = _open_index(directory, "cloudsen12", _dataset(taco, revision))
    if index["splits"] and list(index["bands"]) != list(bands):
        raise cache.CacheError(
            f"{paths.portable(directory)} stores bands {index['bands']}; this build asks for "
            f"{list(bands)}. Use another --name"
        )
    index["bands"] = list(bands)
    index["band_labels"] = [source.BAND_LABELS.get(b, b) for b in bands]
    if revision:
        index["dataset"]["revision"] = revision
    return index


def plan_split(
    split: str,
    limit: int | None,
    taco: Sequence[str],
    bands: Sequence[str],
    backoff: http.Backoff,
) -> Plan:
    table = backoff.call(source.open_table, taco[0] if len(taco) == 1 else list(taco))
    extra = split == cache.EXTRA_SPLIT
    chosen = source.select_extra(table, limit) if extra else source.select(table, split, limit)
    counts = chosen.counts()
    kind = "scribble and nolabel training" if extra else "high quality"
    print(
        f"{split}: {counts['high_quality']} {kind} patches, "
        f"{counts['kept_509']} kept ({source.KEPT_SHAPE} x {source.KEPT_SHAPE}), "
        f"{counts['dropped_other_shape']} dropped (other sizes), "
        f"{counts['dropped_location_in_val_or_test']} dropped (location in val or test), "
        f"{counts['selected']} selected",
        flush=True,
    )
    if not chosen.positions:
        raise cache.CacheError(
            f"no high quality {source.KEPT_SHAPE} x {source.KEPT_SHAPE} patches for {split!r}"
        )
    # The row key identifies a row of the TACO table (resume); roi_id identifies
    # the patch in reports.
    rows = chosen.positions
    return Plan(
        split=split,
        table=table,
        rows=rows,
        ids=[str(table.iloc[r][source.ID_FIELD]) for r in rows],
        roi_ids=[str(table.iloc[r][source.PATCH_ID_FIELD]) for r in rows],
        counts=counts,
        bands=tuple(bands),
        extra=extra,
    )


def _reader(plan: Plan, backoff: http.Backoff, limiter: http.RateLimiter | None) -> Any:
    bands = None if plan.bands == source.USED_BANDS else plan.bands

    def read(position: int) -> source.Patch:
        def once() -> source.Patch:
            if limiter is not None:
                limiter.acquire()
            if plan.extra:
                return source.read_extra_patch(plan.table, position, bands=plan.bands)
            if bands is None:
                return source.read_patch(plan.table, position)
            return source.read_patch(plan.table, position, bands=bands)

        return backoff.call(once)

    return read


def build_real_split(
    directory: Path,
    split: str,
    limit: int | None,
    taco: Sequence[str],
    revision: str | None,
    workers: int = 4,
    restart: bool = False,
    bands: Sequence[str] = source.USED_BANDS,
    max_rate: float | None = None,
) -> None:
    """Build one split of the real cache, resuming an interrupted build.

    A split that is already complete with the same selection is left as it
    is. A complete or partly built split with another selection (for example
    a `--limit` build pointed at the full cache) is never replaced unless
    `restart` is set, so a small build can never reset a large one.
    """
    index = _open_real_index(directory, taco, revision, bands)
    backoff = http.Backoff()
    plan = plan_split(split, limit, taco, bands, backoff)
    where = paths.portable(directory)
    existing = index["splits"].get(split)
    if existing and existing.get("complete") and not restart:
        if existing.get("row_keys") == plan.ids:
            print(f"{split}: already complete in {where} ({len(plan.ids)} patches)", flush=True)
            return
        raise cache.CacheError(
            f"{split}: {where} already holds a complete split with another selection "
            f"({existing.get('count')} patches, limit {existing.get('limit')}; now "
            f"{len(plan.ids)} patches, limit {limit}). Use another --name or $TIEFER_DATA_DIR, "
            "or pass --restart to replace it"
        )
    target = Target(
        cache.images_path(directory, split),
        cache.labels_path(directory, split),
        _progress_path(directory, split),
    )
    if not target.progress.is_file():
        check_disk(directory, len(plan.rows) * bytes_per_patch(len(bands)), f"split {split}")
    limiter = http.RateLimiter(max_rate) if max_rate else None
    metadata = _read_rows(
        target,
        plan,
        plan.rows,
        plan.ids,
        reader=_reader(plan, backoff, limiter),
        workers=workers,
        restart=restart,
        label=split,
    )
    _finish_split(
        directory, index, split, plan.roi_ids, metadata, limit, [], plan.counts, row_keys=plan.ids
    )
    target.progress.unlink()


# Reference masks -------------------------------------------------------------


def build_references(
    directory: Path,
    split: str,
    names: Sequence[str] | None = None,
    workers: int = 4,
    max_rate: float | None = None,
) -> None:
    """Add the reference masks of established algorithms to a complete split.

    Reads them from the extra table, row by row in the split's order, so every
    reference algorithm is scored by our code on our patches. Stops with a
    clear message until the link field, the item names and the encodings are
    verified (source.reference_encoding). A patch without a row in the extra
    table gets IGNORE_INDEX everywhere; the count is recorded in the index.
    Resumable through `<split>.references.json`.
    """
    index = cache.read_index(directory)
    entry = index["splits"].get(split)
    if not entry or not entry.get("complete"):
        raise cache.CacheError(f"split {split!r} is not complete; build it before its references")
    names = list(names or source.REFERENCE_MASK_NAMES)
    encodings = {name: source.reference_encoding(name) for name in names}
    field = source.require_verified("REFERENCE_LINK_FIELD", source.REFERENCE_LINK_FIELD)
    keys = []
    for m in entry["metadata"]:
        if field not in m:
            raise cache.CacheError(f"the {split} metadata has no {field!r}; it cannot be linked")
        keys.append(str(m[field]))
    backoff = http.Backoff()
    extra = backoff.call(source.open_extra_table)
    lookup: dict[str, int] = {}
    for position, value in enumerate(extra[field]):
        if str(value) in lookup:
            raise cache.CacheError(f"{field!r} is not unique in the extra table: {value!r}")
        lookup[str(value)] = position
    rows = [lookup.get(k) for k in keys]
    missing = sum(r is None for r in rows)
    print(f"{split}: {len(rows) - missing} of {len(rows)} patches have reference masks", flush=True)
    labels = np.load(cache.labels_path(directory, split), mmap_mode="r")
    n, height, width = labels.shape
    progress_file = directory / f"{split}.references.json"
    done = 0
    if progress_file.is_file():
        state = json.loads(progress_file.read_text(encoding="utf-8"))
        if state.get("names") == names:
            done = int(state["done"])
    mode: Literal["r+", "w+"] = "r+" if done else "w+"
    arrays = {
        name: np.lib.format.open_memmap(
            _partial(cache.reference_path(directory, split, name)),
            mode=mode,
            dtype=np.uint8,
            shape=(n, height, width),
        )
        for name in names
    }

    def save() -> None:
        for a in arrays.values():
            a.flush()
        progress_file.write_text(json.dumps({"names": names, "done": done}))

    limiter = http.RateLimiter(max_rate) if max_rate else None

    def read(row: int | None) -> dict[str, NDArray[np.uint8]]:
        if row is None:
            return {name: np.full((height, width), source.IGNORE_INDEX, np.uint8) for name in names}

        def once() -> dict[str, NDArray[np.uint8]]:
            if limiter is not None:
                limiter.acquire()
            return source.read_references(extra, row, names)

        return backoff.call(once)

    pool = ThreadPoolExecutor(max_workers=max(1, workers))
    pending: dict[int, Future[dict[str, NDArray[np.uint8]]]] = {}
    submitted = done
    try:
        for i in range(done, n):
            while submitted < min(i + max(1, workers) * 4, n):
                pending[submitted] = pool.submit(read, rows[submitted])
                submitted += 1
            masks = pending.pop(i).result()
            for name in names:
                if masks[name].shape != (height, width):
                    raise cache.CacheError(f"{name} of patch {i} is {masks[name].shape}")
                arrays[name][i] = masks[name]
            done = i + 1
            if done % SAVE_EVERY == 0 or done == n:
                save()
                print(f"{split} references: {done}/{n}", flush=True)
    except BaseException:
        save()
        print(f"{split} references: stopped after {done} of {n}; run again to continue", flush=True)
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    arrays.clear()  # release the memory maps before the files are moved
    for name in names:
        path = cache.reference_path(directory, split, name)
        os.replace(_partial(path), path)
    entry["reference_masks"] = names
    entry["reference_kinds"] = {name: encodings[name].kind for name in names}
    entry["reference_missing"] = missing
    entry["reference_link_field"] = field
    cache.write_index(directory, index)
    progress_file.unlink()
    print(f"{split}: reference masks {', '.join(names)} added", flush=True)


# Shards ----------------------------------------------------------------------
#
# Several CPU jobs can build one split side by side: shard i of n reads its
# own contiguous part of the selected rows into its own folder, so no two jobs
# ever write the same file. `--merge` then copies the shards in order into the
# split's arrays, deleting each shard after it is copied, and writes the index.


def shard_dir(directory: Path, split: str, shard: int, shards: int) -> Path:
    return directory / "shards" / split / f"{shard}-of-{shards}"


def shard_bounds(n: int, shard: int, shards: int) -> tuple[int, int]:
    """Rows [start, stop) of shard `shard` of `shards`; sizes differ by at most one."""
    if not 0 <= shard < shards:
        raise ValueError(f"shard {shard} is not in 0 to {shards - 1}")
    return n * shard // shards, n * (shard + 1) // shards


def _fingerprint(ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode()).hexdigest()


def build_shard(
    directory: Path,
    split: str,
    shard: int,
    shards: int,
    limit: int | None,
    taco: Sequence[str],
    revision: str | None,
    workers: int = 4,
    restart: bool = False,
    bands: Sequence[str] = source.USED_BANDS,
    max_rate: float | None = None,
) -> None:
    index = _open_real_index(directory, taco, revision, bands)
    if index["splits"].get(split, {}).get("complete") and not restart:
        raise cache.CacheError(
            f"{split} is already complete in {paths.portable(directory)}; nothing to build"
        )
    backoff = http.Backoff()
    plan = plan_split(split, limit, taco, bands, backoff)
    start, stop = shard_bounds(len(plan.rows), shard, shards)
    folder = shard_dir(directory, split, shard, shards)
    done_file = folder / "shard.json"
    label = f"{split} shard {shard} of {shards}"
    if done_file.is_file() and not restart:
        print(f"{label}: already complete", flush=True)
        return
    target = Target(folder / "images.npy", folder / "labels.npy", folder / "progress.json")
    if not target.progress.is_file():
        check_disk(folder, (stop - start) * bytes_per_patch(len(bands)), label)
    # A global rate cap is shared equally between the shards.
    limiter = http.RateLimiter(max_rate / shards) if max_rate else None
    metadata = _read_rows(
        target,
        plan,
        plan.rows[start:stop],
        plan.ids[start:stop],
        reader=_reader(plan, backoff, limiter),
        workers=workers,
        restart=restart,
        label=label,
    )
    state = {
        "split": split,
        "shard": shard,
        "shards": shards,
        "start": start,
        "stop": stop,
        "selection": _fingerprint(plan.ids),
        "patches": len(plan.ids),
        "limit": limit,
        "bands": list(bands),
        "row_keys": plan.ids[start:stop],
        "roi_ids": plan.roi_ids[start:stop],
        "metadata": metadata,
        "counts": plan.counts,
    }
    tmp = done_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, done_file)
    target.progress.unlink()
    print(f"{label}: complete ({stop - start} patches)", flush=True)


def merge_shards(
    directory: Path, split: str, shards: int, taco: Sequence[str], revision: str | None
) -> None:
    """Copy complete shards into the split's arrays, in order, and write the index.

    Resumable: copied shards are recorded in `<split>.merge.json`. A shard's
    files are deleted only after its rows are written and flushed, so the disk
    peak is the split plus one shard.
    """
    states = []
    for shard in range(shards):
        done_file = shard_dir(directory, split, shard, shards) / "shard.json"
        if not done_file.is_file():
            raise cache.CacheError(
                f"{split} shard {shard} of {shards} is not complete; merge later"
            )
        states.append(json.loads(done_file.read_text(encoding="utf-8")))
    selection = {s["selection"] for s in states}
    bands = {tuple(s["bands"]) for s in states}
    if len(selection) != 1 or len(bands) != 1:
        raise cache.CacheError(f"the {split} shards come from different selections or band sets")
    n = int(states[0]["patches"])
    if [s["start"] for s in states] != [shard_bounds(n, i, shards)[0] for i in range(shards)]:
        raise cache.CacheError(f"the {split} shards do not cover the selection in order")
    index = _open_real_index(directory, taco, revision, list(next(iter(bands))))
    merge_file = directory / f"{split}.merge.json"
    copied: list[int] = []
    if merge_file.is_file():
        copied = json.loads(merge_file.read_text(encoding="utf-8"))["copied"]
    final_images = cache.images_path(directory, split)
    final_labels = cache.labels_path(directory, split)
    if copied:
        saved = json.loads(merge_file.read_text(encoding="utf-8"))
        height, width = int(saved["height"]), int(saved["width"])
    else:
        shapes = {
            np.load(shard_dir(directory, split, i, shards) / "labels.npy", mmap_mode="r").shape[1:]
            for i in range(shards)
        }
        if len(shapes) != 1:
            raise cache.CacheError(f"the {split} shards have different patch sizes: {shapes}")
        height, width = (int(v) for v in shapes.pop())
        merge_file.write_text(json.dumps({"copied": [], "height": height, "width": width}))
    remaining = [s for s in states if s["shard"] not in copied]
    if remaining:
        mode: Literal["r+", "w+"] = "r+" if copied else "w+"
        images = np.lib.format.open_memmap(
            _partial(final_images),
            mode=mode,
            dtype=np.uint16,
            shape=(n, len(states[0]["bands"]), height, width),
        )
        labels = np.lib.format.open_memmap(
            _partial(final_labels), mode=mode, dtype=np.uint8, shape=(n, height, width)
        )
        for s in remaining:
            folder = shard_dir(directory, split, s["shard"], shards)
            s_images = np.load(folder / "images.npy", mmap_mode="r")
            s_labels = np.load(folder / "labels.npy", mmap_mode="r")
            for offset in range(0, s_images.shape[0], COUNT_CHUNK):
                rows = slice(s["start"] + offset, min(s["start"] + offset + COUNT_CHUNK, s["stop"]))
                images[rows] = s_images[offset : offset + COUNT_CHUNK]
                labels[rows] = s_labels[offset : offset + COUNT_CHUNK]
            images.flush()
            labels.flush()
            copied.append(s["shard"])
            merge_file.write_text(json.dumps({"copied": copied, "height": height, "width": width}))
            (folder / "images.npy").unlink()
            (folder / "labels.npy").unlink()
            print(f"{split}: merged shard {s['shard']} of {shards}", flush=True)
        del images, labels
    if _partial(final_images).exists():
        os.replace(_partial(final_images), final_images)
        os.replace(_partial(final_labels), final_labels)
    else:
        print(f"{split}: all shards merged; running the finishing step", flush=True)
    _finish_split(
        directory,
        index,
        split,
        [r for s in states for r in s["roi_ids"]],
        [m for s in states for m in s["metadata"]],
        states[0]["limit"],
        [],
        states[0]["counts"],
        row_keys=[k for s in states for k in s["row_keys"]],
    )
    shutil.rmtree(directory / "shards" / split)
    if not any((directory / "shards").iterdir()):
        (directory / "shards").rmdir()
    merge_file.unlink()


# Synthetic data ------------------------------------------------------------


def _blobs(
    rng: np.random.Generator, size: int, count: int, radius: tuple[float, float]
) -> NDArray[np.bool_]:
    yy, xx = np.mgrid[0:size, 0:size]
    mask = np.zeros((size, size), dtype=bool)
    for _ in range(count):
        cy, cx = rng.uniform(0, size, 2)
        ry, rx = rng.uniform(radius[0], radius[1], 2) * size
        mask |= ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0
    return mask


def _smooth_field(rng: np.random.Generator, size: int, cells: int = 4) -> NDArray[np.float64]:
    coarse = rng.uniform(0.0, 1.0, (cells, cells))
    reps = -(-size // cells)
    field = np.kron(coarse, np.ones((reps, reps)))[:size, :size]
    return np.asarray(field, dtype=np.float64)


def synthetic_patches(
    count: int, size: int, seed: int
) -> Iterator[tuple[NDArray[np.uint16], NDArray[np.uint8]]]:
    """Synthetic four-band scenes with thick and thin clouds and shadows.

    Synthetic: for smoke runs and tests only. The values only roughly resemble
    top-of-atmosphere reflectance and carry no information about real scenes.
    """
    rng = np.random.default_rng(seed)
    land = np.array([0.08, 0.10, 0.11, 0.28])
    for _ in range(count):
        base = _smooth_field(rng, size)
        refl = land[:, None, None] * (0.7 + 0.6 * base[None])
        label = np.zeros((size, size), dtype=np.uint8)
        thick = _blobs(rng, size, int(rng.integers(0, 4)), (0.08, 0.25))
        thin = _blobs(rng, size, int(rng.integers(0, 3)), (0.10, 0.30)) & ~thick
        shift = (int(rng.integers(3, size // 8 + 4)), int(rng.integers(3, size // 8 + 4)))
        shadow = np.roll(thick, shift, axis=(0, 1)) & ~thick & ~thin
        refl[:, shadow] *= 0.45
        alpha = rng.uniform(0.3, 0.5)
        refl[:, thin] = refl[:, thin] * (1 - alpha) + 0.35 * alpha
        refl[:, thick] = rng.uniform(0.45, 0.8) + rng.normal(0.0, 0.02, size=(4, int(thick.sum())))
        refl += rng.normal(0.0, 0.005, size=refl.shape)
        label[thin] = source.THIN_CLOUD
        label[shadow] = source.CLOUD_SHADOW
        label[thick] = source.THICK_CLOUD
        scaled = (refl - source.REFLECTANCE_OFFSET) / source.REFLECTANCE_SCALE
        yield np.clip(np.rint(scaled), 0, 65535).astype(np.uint16), label


def build_synthetic_split(directory: Path, split: str, count: int, size: int, seed: int) -> None:
    dataset = {"name": "synthetic", "note": "synthetic scenes for smoke runs and tests only"}
    directory.mkdir(parents=True, exist_ok=True)
    index = _open_index(directory, cache.SYNTHETIC_SOURCE, dataset)
    split_seed = seed + cache.SPLITS.index(split) * 1000
    images = np.empty((count, len(source.USED_BANDS), size, size), dtype=np.uint16)
    labels = np.empty((count, size, size), dtype=np.uint8)
    for i, (img, lab) in enumerate(synthetic_patches(count, size, split_seed)):
        images[i], labels[i] = img, lab
    np.save(cache.images_path(directory, split), images, allow_pickle=False)
    np.save(cache.labels_path(directory, split), labels, allow_pickle=False)
    ids = [f"synthetic-{split}-{i:05d}" for i in range(count)]
    metadata: list[dict[str, Any]] = [{"synthetic_group": f"group-{i % 2}"} for i in range(count)]
    _finish_split(directory, index, split, ids, metadata, count, [])


# Command line --------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.data.build_cache", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("--split", required=True, choices=[*cache.ALL_SPLITS, "all"])
    parser.add_argument("--limit", type=int, default=None, help="build only N patches per split")
    parser.add_argument("--name", default=None, help="cache folder name in $TIEFER_DATA_DIR")
    parser.add_argument(
        "--taco",
        action="append",
        default=None,
        help=f"dataset file, URL or catalogue name (default {source.TACO_NAME_L1C}); repeatable",
    )
    parser.add_argument("--revision", default=None, help="record this dataset revision")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="parallel readers (default: SLURM_CPUS_PER_TASK, else 4)",
    )
    parser.add_argument(
        "--bands",
        choices=["used", "all"],
        default="used",
        help="store the four used bands (default) or all 13 Level-1C bands",
    )
    parser.add_argument(
        "--shard",
        default=None,
        help="build part I of N of the split, for example 0/4, in its own folder",
    )
    parser.add_argument(
        "--merge",
        type=int,
        default=None,
        metavar="N",
        help="merge the N complete shards of the split into the cache",
    )
    parser.add_argument(
        "--references",
        action="store_true",
        help="add the reference masks of the extra table to a complete split",
    )
    parser.add_argument(
        "--max-rate",
        type=float,
        default=None,
        help="patches per minute for the whole split, shared between shards",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="replace a split built or being built with another selection",
    )
    parser.add_argument("--synthetic", action="store_true", help="write synthetic scenes")
    parser.add_argument("--patch-size", type=int, default=128, help="synthetic patch size")
    parser.add_argument("--seed", type=int, default=0, help="synthetic data seed")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.synthetic and args.limit is None:
        parser.error("--synthetic needs --limit (patches per split)")
    if args.shard is not None:
        try:
            shard, shards = (int(v) for v in args.shard.split("/"))
        except ValueError:
            parser.error("--shard takes I/N, for example 0/4")
        if not 0 <= shard < shards:
            parser.error("--shard I/N needs 0 <= I < N")
        args.shard = (shard, shards)
    if (args.shard or args.merge) and args.split == "all":
        parser.error("--shard and --merge work on one split at a time")
    if args.shard and args.merge:
        parser.error("--shard and --merge are separate steps")
    if args.max_rate is not None and args.max_rate <= 0:
        parser.error("--max-rate must be positive")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    splits = list(cache.SPLITS) if args.split == "all" else [args.split]
    if args.synthetic:
        directory = cache.cache_dir(args.name or SYNTHETIC_NAME)
        for split in splits:
            build_synthetic_split(directory, split, args.limit, args.patch_size, args.seed)
    else:
        directory = cache.cache_dir(args.name or DEFAULT_NAME)
        revision = args.revision or source.dataset_revision()
        if revision is None:
            print("warning: dataset revision could not be read; recorded as unknown", flush=True)
        token = (
            "set"
            if http.configure_token()
            else f"not set (set {http.TOKEN_ENV} to raise the limit)"
        )
        print(f"Hugging Face token: {token}", flush=True)
        taco = args.taco or [source.TACO_NAME_L1C]
        workers = download_workers(args.workers)
        bands = source.L1C_BAND_NAMES if args.bands == "all" else source.USED_BANDS
        for split in splits:
            if args.references:
                build_references(directory, split, workers=workers, max_rate=args.max_rate)
            elif args.merge:
                merge_shards(directory, split, args.merge, taco, revision)
            elif args.shard:
                shard, shards = args.shard
                build_shard(
                    directory,
                    split,
                    shard,
                    shards,
                    args.limit,
                    taco,
                    revision,
                    workers,
                    restart=args.restart,
                    bands=bands,
                    max_rate=args.max_rate,
                )
            else:
                build_real_split(
                    directory,
                    split,
                    args.limit,
                    taco,
                    revision,
                    workers,
                    restart=args.restart,
                    bands=bands,
                    max_rate=args.max_rate,
                )
    print(f"cache: {paths.portable(directory)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
