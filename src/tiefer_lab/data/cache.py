# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The local data cache: layout, index and reading.

Layout of `$TIEFER_DATA_DIR/<cache-name>/`:

- `<split>_images.npy`: uint16 digital numbers, shape (patches, 4, height, width)
- `<split>_labels.npy`: uint8 class indexes, shape (patches, height, width)
- `<split>_ref_<name>.npy`: optional reference masks, same shape as labels
- `index.json`: patch IDs, metadata, dataset revision, build dates, counts and
  the normalisation statistics of the training split

Arrays are plain `.npy` files read without pickle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.utils import paths

CACHE_FORMAT = 1
INDEX_NAME = "index.json"
SPLITS = ("train", "val", "test")
SYNTHETIC_SOURCE = "synthetic"

LoadMode = Literal["auto", "memory", "mmap"]

# Load a split into memory only when it uses at most this share of the
# memory that is currently available.
MEMORY_SHARE = 0.5


class CacheError(RuntimeError):
    """The cache is missing, incomplete or inconsistent."""


def cache_dir(name: str) -> Path:
    return paths.data_dir() / name


def images_path(directory: Path, split: str) -> Path:
    return directory / f"{split}_images.npy"


def labels_path(directory: Path, split: str) -> Path:
    return directory / f"{split}_labels.npy"


def reference_path(directory: Path, split: str, name: str) -> Path:
    return directory / f"{split}_ref_{name}.npy"


def progress_path(directory: Path, split: str) -> Path:
    """Progress file of a split whose build is under way or was interrupted."""
    return directory / f"{split}.progress.json"


def read_index(directory: Path) -> dict[str, Any]:
    path = directory / INDEX_NAME
    if not path.is_file():
        raise CacheError(
            f"no cache index at {paths.portable(path)}; build it with "
            "python -m tiefer_lab.data.build_cache"
        )
    index: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if index.get("format") != CACHE_FORMAT:
        raise CacheError(f"cache format {index.get('format')} is not {CACHE_FORMAT}")
    return index


def write_index(directory: Path, index: dict[str, Any]) -> None:
    """Write the index atomically."""
    directory.mkdir(parents=True, exist_ok=True)
    tmp = directory / (INDEX_NAME + ".tmp")
    tmp.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, directory / INDEX_NAME)


def available_memory_bytes() -> int | None:
    """Memory available to new allocations, from /proc/meminfo or sysconf."""
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    try:
        return int(os.sysconf("SC_AVPHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
    except (ValueError, OSError, AttributeError):
        return None


@dataclass
class SplitData:
    """One split of the cache. Arrays are in memory or memory-mapped."""

    split: str
    images: NDArray[np.uint16]
    labels: NDArray[np.uint8]
    patch_ids: list[str]
    metadata: list[dict[str, Any]]
    reference: dict[str, NDArray[np.uint8]] = field(default_factory=dict)
    in_memory: bool = False

    def __len__(self) -> int:
        return int(self.images.shape[0])


def load_split(directory: Path, split: str, mode: LoadMode = "auto") -> SplitData:
    """Load one split, checking it against the index.

    `auto` loads the arrays into memory when they fit (see MEMORY_SHARE) and
    memory-maps them otherwise.
    """
    index = read_index(directory)
    entry = index.get("splits", {}).get(split)
    if not entry or not entry.get("complete"):
        raise CacheError(f"split {split!r} is not complete in {paths.portable(directory)}")
    files = [images_path(directory, split), labels_path(directory, split)]
    names = list(entry.get("reference_masks", []))
    files += [reference_path(directory, split, n) for n in names]
    for f in files:
        if not f.is_file():
            raise CacheError(f"missing cache file {paths.portable(f)}")
    if mode == "auto":
        size = sum(f.stat().st_size for f in files)
        available = available_memory_bytes()
        in_memory = available is not None and size <= MEMORY_SHARE * available
    else:
        in_memory = mode == "memory"
    mmap: Literal["r"] | None = None if in_memory else "r"
    images = np.load(files[0], mmap_mode=mmap, allow_pickle=False)
    labels = np.load(files[1], mmap_mode=mmap, allow_pickle=False)
    reference = {
        n: np.load(reference_path(directory, split, n), mmap_mode=mmap, allow_pickle=False)
        for n in names
    }
    count = int(entry["count"])
    if images.shape[0] != count or labels.shape[0] != count:
        raise CacheError(
            f"split {split!r}: index says {count} patches, arrays have "
            f"{images.shape[0]} images and {labels.shape[0]} labels"
        )
    if images.dtype != np.uint16 or labels.dtype != np.uint8:
        raise CacheError(f"unexpected dtypes {images.dtype}, {labels.dtype}")
    if images.ndim != 4 or images.shape[1] != len(index["bands"]):
        raise CacheError(f"images have shape {images.shape}, expected (N, 4, H, W)")
    return SplitData(
        split=split,
        images=images,
        labels=labels,
        patch_ids=list(entry["patch_ids"]),
        metadata=list(entry.get("metadata", [])),
        reference=reference,
        in_memory=in_memory,
    )


def normalisation(index: dict[str, Any]) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Per-band mean and standard deviation of the training split."""
    stats = index.get("normalisation")
    if not stats:
        raise CacheError("the cache has no normalisation statistics; build the train split first")
    if stats.get("computed_on") != "train":
        raise CacheError("normalisation statistics must come from the training split")
    return (
        np.asarray(stats["mean"], dtype=np.float32),
        np.asarray(stats["std"], dtype=np.float32),
    )


def is_synthetic(index: dict[str, Any]) -> bool:
    return bool(index.get("source") == SYNTHETIC_SOURCE)


def splits_ready(directory: Path, splits: Sequence[str]) -> bool:
    """True when every split is complete in the index and none is being rebuilt.

    The index exists as soon as the first split is finished, so it alone does
    not show that a build (for example data.sbatch) has finished.
    """
    try:
        index = read_index(directory)
    except (CacheError, ValueError):
        return False
    for split in splits:
        entry = index.get("splits", {}).get(split)
        if not entry or not entry.get("complete") or progress_path(directory, split).exists():
            return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.data.cache",
        description="Exit 0 when the named splits of a cache are complete and not being built.",
    )
    parser.add_argument("command", choices=["ready"])
    parser.add_argument("name", help="cache folder name in $TIEFER_DATA_DIR")
    parser.add_argument("splits", nargs="+", choices=SPLITS)
    args = parser.parse_args(argv)
    directory = cache_dir(args.name)
    ready = splits_ready(directory, args.splits)
    state = "ready" if ready else "not ready"
    print(f"cache {paths.portable(directory)}: {', '.join(args.splits)} {state}", flush=True)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
