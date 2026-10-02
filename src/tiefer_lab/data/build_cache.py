# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Build the local data cache.

    python -m tiefer_lab.data.build_cache --split train|val|test|all [--limit N]

Reads only the four used bands and the label of each selected patch and
writes them into `$TIEFER_DATA_DIR/<name>/` (layout in `cache.py`). The build
is resumable: progress is saved every few patches, and running the same
command again continues where it stopped. Counts are verified at the end.

`--synthetic` writes a cache of synthetic scenes instead, for smoke runs and
tests when the dataset is not reachable. A synthetic cache is marked as such
in its index and is refused by training and evaluation unless they are
explicitly run as a smoke run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections.abc import Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import cache, source
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
        "class_pixels": [int(c) for c in np.bincount(np.asarray(labels).ravel(), minlength=4)],
    }
    if split == "train":
        _update_normalisation(directory, index)
    cache.write_index(directory, index)
    print(f"{split}: {len(patch_ids)} patches verified and indexed", flush=True)


# Real data -----------------------------------------------------------------


def _progress_path(directory: Path, split: str) -> Path:
    return directory / f"{split}.progress.json"


def _partial(path: Path) -> Path:
    return path.with_name(path.name.replace(".npy", ".partial.npy"))


def build_real_split(
    directory: Path,
    split: str,
    limit: int | None,
    taco: Sequence[str],
    revision: str | None,
    workers: int = 4,
    restart: bool = False,
) -> None:
    """Build one split of the real cache, resuming an interrupted build.

    A split that is already complete with the same selection is left as it
    is. A complete or partly built split with another selection (for example
    a `--limit` build pointed at the full cache) is never replaced unless
    `restart` is set, so a small build can never reset a large one.
    """
    dataset = {
        "repo": source.DATASET_REPO,
        "card": source.DATASET_CARD_URL,
        "licence": source.DATASET_LICENCE,
        "taco": list(taco),
        "revision": revision or "unknown",
    }
    directory.mkdir(parents=True, exist_ok=True)
    index = _open_index(directory, "cloudsen12", dataset)
    if revision:
        index["dataset"]["revision"] = revision
    table = source.open_table(taco[0] if len(taco) == 1 else list(taco))
    chosen = source.select(table, split, limit)
    rows = chosen.positions
    counts = chosen.counts()
    print(
        f"{split}: {counts['high_quality']} high quality patches, "
        f"{counts['kept_509']} kept ({source.KEPT_SHAPE} x {source.KEPT_SHAPE}), "
        f"{counts['dropped_other_shape']} dropped (other sizes), {counts['selected']} selected",
        flush=True,
    )
    if not rows:
        raise cache.CacheError(
            f"no high quality {source.KEPT_SHAPE} x {source.KEPT_SHAPE} patches for {split!r}"
        )
    # The row key identifies a row of the TACO table (resume); roi_id identifies
    # the patch in reports.
    ids = [str(table.iloc[r][source.ID_FIELD]) for r in rows]
    roi_ids = [str(table.iloc[r][source.PATCH_ID_FIELD]) for r in rows]

    where = paths.portable(directory)
    existing = index["splits"].get(split)
    if existing and existing.get("complete") and not restart:
        if existing.get("row_keys") == ids:
            print(f"{split}: already complete in {where} ({len(ids)} patches)", flush=True)
            return
        raise cache.CacheError(
            f"{split}: {where} already holds a complete split with another selection "
            f"({existing.get('count')} patches, limit {existing.get('limit')}; now "
            f"{len(ids)} patches, limit {limit}). Use another --name or $TIEFER_DATA_DIR, "
            "or pass --restart to replace it"
        )

    progress_file = _progress_path(directory, split)
    progress: dict[str, Any] = {}
    if progress_file.is_file():
        progress = json.loads(progress_file.read_text(encoding="utf-8"))
        if progress.get("patch_ids") != ids:
            if not restart:
                raise cache.CacheError(
                    f"{split}: {where} holds a build in progress with another selection "
                    f"({len(progress.get('patch_ids', []))} patches; now {len(ids)}). "
                    "Use another --name or $TIEFER_DATA_DIR, or pass --restart to "
                    "discard it"
                )
            print(f"{split}: --restart: discarding the build in progress", flush=True)
            progress = {}

    ref_names = list(source.REFERENCE_MASK_ITEMS)
    first: source.Patch | None = None
    if progress:
        height, width = progress["height"], progress["width"]
        done = int(progress["done"])
        metadata: list[dict[str, Any]] = progress["metadata"]
        mode = "r+"
    else:
        first = source.read_patch(table, rows[0])
        height, width = first.label.shape
        done, metadata, mode = 0, [], "w+"
    n = len(rows)
    images = np.lib.format.open_memmap(
        _partial(cache.images_path(directory, split)),
        mode=mode,
        dtype=np.uint16,
        shape=(n, len(source.USED_BANDS), height, width),
    )
    labels = np.lib.format.open_memmap(
        _partial(cache.labels_path(directory, split)),
        mode=mode,
        dtype=np.uint8,
        shape=(n, height, width),
    )
    refs = {
        name: np.lib.format.open_memmap(
            _partial(cache.reference_path(directory, split, name)),
            mode=mode,
            dtype=np.uint8,
            shape=(n, height, width),
        )
        for name in ref_names
    }

    def save_progress() -> None:
        images.flush()
        labels.flush()
        for r in refs.values():
            r.flush()
        state = {
            "patch_ids": ids,
            "done": done,
            "height": height,
            "width": width,
            "metadata": metadata,
        }
        tmp = progress_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, progress_file)

    if done:
        print(f"{split}: resuming at patch {done} of {n}", flush=True)
    print(f"{split}: reading with {workers} parallel workers", flush=True)
    # Patches are read in parallel but written in order, so `done` always means
    # "patches 0 to done - 1 are in the arrays" and a restart continues there.
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
                    pending[submitted] = pool.submit(source.read_patch, table, rows[submitted])
                submitted += 1
            patch = pending.pop(i).result()
            if patch.label.shape != (height, width):
                raise cache.CacheError(
                    f"patch {patch.patch_id} is {patch.label.shape}, expected {(height, width)}"
                )
            images[i] = patch.image
            labels[i] = patch.label
            for name, arr in refs.items():
                arr[i] = patch.reference[name]
            metadata.append(patch.metadata)
            done = i + 1
            if done % SAVE_EVERY == 0 or done == n:
                save_progress()
                print(f"{split}: {done}/{n}", flush=True)
    except BaseException:
        save_progress()
        print(f"{split}: stopped after {done} of {n}; run the same command to continue", flush=True)
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    save_progress()
    os.replace(_partial(cache.images_path(directory, split)), cache.images_path(directory, split))
    os.replace(_partial(cache.labels_path(directory, split)), cache.labels_path(directory, split))
    for name in ref_names:
        p = cache.reference_path(directory, split, name)
        os.replace(_partial(p), p)
    _finish_split(
        directory, index, split, roi_ids, metadata, limit, ref_names, counts, row_keys=ids
    )
    progress_file.unlink()


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
    parser.add_argument("--split", required=True, choices=[*cache.SPLITS, "all"])
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
        taco = args.taco or [source.TACO_NAME_L1C]
        workers = download_workers(args.workers)
        for split in splits:
            build_real_split(
                directory, split, args.limit, taco, revision, workers, restart=args.restart
            )
    print(f"cache: {paths.portable(directory)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
