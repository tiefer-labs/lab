# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The local data cache: layout, index and reading.

Layout of `$TIEFER_DATA_DIR/<cache-name>/`:

- `<split>_images.npy`: uint16 digital numbers, shape (patches, bands, height, width);
  the stored bands are listed by name in the index (`bands`), and a model's
  band set is selected from them at load time
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

from tiefer_lab.data import padding
from tiefer_lab.tables import Group, markdown_table
from tiefer_lab.utils import paths

CACHE_FORMAT = 1
INDEX_NAME = "index.json"
SPLITS = ("train", "val", "test")
# Scribble and nolabel patches for training only (source.select_extra).
EXTRA_SPLIT = "train_extra"
ALL_SPLITS = (*SPLITS, EXTRA_SPLIT)
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
    # "four_class" or "cloud" per reference mask (build_cache --references).
    reference_kinds: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return int(self.images.shape[0])


def band_positions(index: dict[str, Any], bands: Sequence[str] | None) -> list[int]:
    """Positions of `bands` (names such as "B02") among the bands the cache stores."""
    stored = list(index["bands"])
    if bands is None:
        return list(range(len(stored)))
    missing = [b for b in bands if b not in stored]
    if missing:
        raise CacheError(f"the cache stores bands {stored}; {missing} are not among them")
    return [stored.index(b) for b in bands]


class BandSelection:
    """A memory-mapped image array that shows only some bands, read on access.

    Indexing works like a (patches, selected bands, height, width) array:
    the first index selects patches, the rest applies to the selected bands.
    """

    def __init__(self, base: NDArray[np.uint16], positions: Sequence[int]) -> None:
        self.base = base
        self.positions = list(positions)
        self.shape = (base.shape[0], len(self.positions), *base.shape[2:])
        self.dtype = base.dtype
        self.ndim = base.ndim

    def __len__(self) -> int:
        return int(self.shape[0])

    def __getitem__(self, key: Any) -> NDArray[np.uint16]:
        parts = key if isinstance(key, tuple) else (key,)
        first, rest = parts[0], parts[1:]
        block = np.asarray(self.base[first])
        if isinstance(first, int | np.integer):
            out = block[self.positions]
            return out[rest] if rest else out
        out = block[:, self.positions]
        return out[(slice(None), *rest)] if rest else out

    def __array__(self, dtype: Any = None, copy: Any = None) -> NDArray[np.uint16]:
        out = self[:]
        return out.astype(dtype) if dtype is not None else out


# Patches per chunk when only some bands are read into memory.
SELECT_CHUNK = 64


def load_split(
    directory: Path, split: str, mode: LoadMode = "auto", bands: Sequence[str] | None = None
) -> SplitData:
    """Load one split, checking it against the index.

    `bands` selects bands by name (for example ["B02", "B03", "B04", "B08"]);
    by default every stored band is loaded. One cache with all bands thus
    serves models with any band set.

    `auto` loads the arrays into memory when they fit (see MEMORY_SHARE) and
    memory-maps them otherwise.
    """
    index = read_index(directory)
    positions = band_positions(index, bands)
    all_bands = positions == list(range(len(index["bands"])))
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
        image_bytes = files[0].stat().st_size * len(positions) / len(index["bands"])
        size = image_bytes + sum(f.stat().st_size for f in files[1:])
        available = available_memory_bytes()
        in_memory = available is not None and size <= MEMORY_SHARE * available
    else:
        in_memory = mode == "memory"
    mmap: Literal["r"] | None = None if in_memory else "r"
    stored = np.load(files[0], mmap_mode="r", allow_pickle=False)
    images: Any
    if all_bands:
        images = np.load(files[0], mmap_mode=mmap, allow_pickle=False)
    elif in_memory:
        images = np.empty((stored.shape[0], len(positions), *stored.shape[2:]), stored.dtype)
        for start in range(0, stored.shape[0], SELECT_CHUNK):
            images[start : start + SELECT_CHUNK] = stored[start : start + SELECT_CHUNK][
                :, positions
            ]
    else:
        images = BandSelection(stored, positions)
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
    if stored.ndim != 4 or stored.shape[1] != len(index["bands"]):
        raise CacheError(
            f"images have shape {stored.shape}, expected (N, {len(index['bands'])}, H, W)"
        )
    return SplitData(
        split=split,
        images=images,
        labels=labels,
        patch_ids=list(entry["patch_ids"]),
        metadata=list(entry.get("metadata", [])),
        reference=reference,
        in_memory=in_memory,
        reference_kinds={
            n: str(entry.get("reference_kinds", {}).get(n, "four_class")) for n in names
        },
    )


def normalisation(
    index: dict[str, Any], bands: Sequence[str] | None = None
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Per-band mean and standard deviation of the training split, for `bands`."""
    stats = index.get("normalisation")
    if not stats:
        raise CacheError("the cache has no normalisation statistics; build the train split first")
    if stats.get("computed_on") != "train":
        raise CacheError("normalisation statistics must come from the training split")
    positions = band_positions(index, bands)
    return (
        np.asarray(stats["mean"], dtype=np.float32)[positions],
        np.asarray(stats["std"], dtype=np.float32)[positions],
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


def location_overlap(
    index: dict[str, Any],
    field: str,
    training: Sequence[str] = ("train", EXTRA_SPLIT),
    held_out: Sequence[str] = ("val", "test"),
) -> dict[str, int]:
    """Patches of each training split whose location also appears in val or test.

    Reads the metadata stored in the index. A training patch without the
    field counts as overlapping, so a missing field can never pass the check.
    """
    splits = index.get("splits", {})
    held = {
        str(m[field]) for s in held_out for m in splits.get(s, {}).get("metadata", []) if field in m
    }
    out: dict[str, int] = {}
    for split in training:
        if split not in splits:
            continue
        metadata = splits[split].get("metadata", [])
        out[split] = sum(1 for m in metadata if field not in m or str(m[field]) in held)
    return out


# Patches read by the padding check unless --patches says otherwise.
PADDING_SAMPLE = 50


def sample_positions(count: int, patches: int) -> list[int]:
    """Up to `patches` positions spread evenly over `count` patches, first and last included."""
    if count <= 0 or patches <= 0:
        return []
    n = min(patches, count)
    return sorted(set(np.rint(np.linspace(0, count - 1, n)).astype(int).tolist()))


def padding_check(directory: Path, split: str, patches: int = PADDING_SAMPLE) -> int:
    """Print what the strips on each side of a sample of patches hold; write nothing.

    Reads the stored arrays as they are (memory-mapped), not the masked
    labels of `load_split`. Exit code 0 when the sides whose image strips are
    zero in every band of every sampled patch are padding.PADDING_SIDES, or when the
    patches have no padding; 1 otherwise.
    """
    index = read_index(directory)
    entry = index.get("splits", {}).get(split)
    if not entry or not entry.get("complete"):
        raise CacheError(f"split {split!r} is not complete in {paths.portable(directory)}")
    images = np.load(images_path(directory, split), mmap_mode="r", allow_pickle=False)
    labels = np.load(labels_path(directory, split), mmap_mode="r", allow_pickle=False)
    metadata = list(entry.get("metadata", []))
    positions = sample_positions(int(labels.shape[0]), patches)
    reports, reals = padding.inspect(images, labels, metadata, positions, padding.CARD_WIDTH)
    print(f"cache {paths.portable(directory)}, split {split}", flush=True)
    print(f"stored images {tuple(images.shape)}, labels {tuple(labels.shape)}", flush=True)
    real_text = ", ".join(f"{k}: {v}" for k, v in sorted(reals.items()))
    print(f"patches read: {len(positions)}; real_proj_shape: {real_text}", flush=True)
    rows = [
        [
            r.side,
            str(r.width),
            ", ".join(f"{v}: {c:,}" for v, c in sorted(r.label_counts.items())) or "n/a",
            f"{r.patches_all_zero} of {r.patches}",
        ]
        for r in reports
    ]
    headers = ["Side", "Width", "Label values: pixels", "Patches with every band zero"]
    print(markdown_table(headers, [Group("", rows)]).rstrip("\n"), flush=True)
    found = padding.zero_sides(reports)
    if all(r.width == 0 for r in reports):
        print("no padding: the stored size equals real_proj_shape", flush=True)
        return 0
    expected = tuple(padding.PADDING_SIDES)
    agree = set(found) == set(expected)
    verdict = "agrees with" if agree else "differs from"
    print(
        f"zero sides found: {', '.join(found) or 'none'}; this {verdict} PADDING_SIDES "
        f"({', '.join(expected)})",
        flush=True,
    )
    return 0 if agree else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.data.cache",
        description=(
            "ready: exit 0 when the named splits are complete and not being built. "
            "overlap: exit 0 when no training patch shares its location with val or test. "
            "padding: report the label values and zero images on each side of a sample of "
            "patches; read-only; exit 0 when the zero sides are PADDING_SIDES."
        ),
    )
    parser.add_argument("command", choices=["ready", "overlap", "padding"])
    parser.add_argument("name", help="cache folder name in $TIEFER_DATA_DIR")
    parser.add_argument("args", nargs="*", help="splits (ready) or the location field (overlap)")
    parser.add_argument("--split", default="val", choices=ALL_SPLITS, help="padding: the split")
    parser.add_argument(
        "--patches", type=int, default=PADDING_SAMPLE, help="padding: patches to read"
    )
    args = parser.parse_args(argv)
    directory = cache_dir(args.name)
    if args.command == "padding":
        return padding_check(directory, args.split, args.patches)
    if not args.args:
        parser.error(f"{args.command} needs splits (ready) or the location field (overlap)")
    if args.command == "overlap":
        overlap = location_overlap(read_index(directory), args.args[0])
        where = paths.portable(directory)
        print(f"cache {where}: patches sharing a location with val or test: {overlap}")
        return 0 if not any(overlap.values()) else 1
    args.splits = args.args
    unknown = [s for s in args.splits if s not in ALL_SPLITS]
    if unknown:
        parser.error(f"unknown splits {unknown}; choose from {ALL_SPLITS}")
    ready = splits_ready(directory, args.splits)
    state = "ready" if ready else "not ready"
    print(f"cache {paths.portable(directory)}: {', '.join(args.splits)} {state}", flush=True)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
