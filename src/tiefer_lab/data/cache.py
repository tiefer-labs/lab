# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The local data cache: layout, index and reading.

Layout of `$TIEFER_DATA_DIR/<cache-name>/`:

- `<split>_images.npy`: uint16 digital numbers, shape (patches, bands, height, width);
  the stored bands are listed by name in the index (`bands`), and a model's
  band set is selected from them at load time
- `<split>_labels.npy`: uint8 class indexes, shape (patches, height, width);
  `load_split` sets the dataset's padding of each patch to IGNORE_INDEX
  (data/padding.py), the file itself is never changed
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
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import padding
from tiefer_lab.data.source import NUM_CLASSES
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
# memory that is currently available, divided by the runs that share the node.
MEMORY_SHARE = 0.5
# Set by the packed training job (hpc/roihu/train_packed.sbatch): how many runs
# share one reserved GPU, its cores and its memory.
RUNS_PER_GPU_ENV = "TIEFER_RUNS_PER_GPU"


def runs_per_gpu() -> int:
    """Runs sharing this job's GPU, cores and memory: TIEFER_RUNS_PER_GPU, else 1."""
    value = os.environ.get(RUNS_PER_GPU_ENV, "").strip()
    if not value:
        return 1
    if not value.isdigit() or int(value) < 1:
        raise CacheError(f"{RUNS_PER_GPU_ENV} must be a whole number of at least 1, got {value!r}")
    return int(value)


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
    tmp = directory / f"{INDEX_NAME}.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, directory / INDEX_NAME)


def cgroup_memory_bytes(root: Path = Path("/sys/fs/cgroup")) -> int | None:
    """Memory left under this process's cgroup v2 limits (Slurm's --mem), or None."""
    try:
        line = Path("/proc/self/cgroup").read_text().splitlines()[0]
    except (OSError, IndexError):
        return None
    folder, left = root / line.split("::", 1)[-1].lstrip("/"), None
    while folder != root.parent and root in (folder, *folder.parents):
        try:
            limit = (folder / "memory.max").read_text().strip()
            used = int((folder / "memory.current").read_text())
        except (OSError, ValueError):
            limit = "max"
        if limit != "max":
            left = int(limit) - used if left is None else min(left, int(limit) - used)
        folder = folder.parent
    return left


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
    # The dataset's padding of each patch, masked in `labels` (data/padding.py);
    # empty when no patch is padded.
    padding: list[padding.Padding] = field(default_factory=list)

    def __len__(self) -> int:
        return int(self.images.shape[0])

    def valid_area(self, index: int) -> NDArray[np.bool_]:
        """True on the real image pixels of patch `index`, False on its padding."""
        height, width = int(self.labels.shape[-2]), int(self.labels.shape[-1])
        pad = self.padding[index] if self.padding else padding.NO_PADDING
        return padding.valid_area(height, width, pad)

    def padded_pixels(self) -> int:
        """Padded pixels over the whole split, all masked in `labels`."""
        height, width = int(self.labels.shape[-2]), int(self.labels.shape[-1])
        return sum(p.pixels(height, width) for p in self.padding)


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


def require_independent_allowed(index: dict[str, Any]) -> None:
    """Stop on a cache of an independent dataset that its licence decision does not allow.

    Every reader of a cache split goes through `load_split`, so `evaluate` with or
    without `--data`, `calibrate`, `diagnose` and `references/run_reference.py`
    cannot read a cache built before a decision changed.
    """
    if not index.get("independent"):
        return
    from tiefer_lab.data import independent

    source = str(index.get("source"))
    if source not in independent.DATASETS:
        raise CacheError(f"independent cache of unknown dataset {source!r}")
    independent.require_dataset_allowed(source)


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
    require_independent_allowed(index)
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
        slurm = os.environ.get("SLURM_MEM_PER_NODE", "")
        job = int(slurm) * 2**20 if slurm.isdigit() else None
        limits = (available_memory_bytes(), cgroup_memory_bytes(), job)
        free = [m for m in limits if m is not None]
        available = min(free) if free else None
        in_memory = available is not None and size <= MEMORY_SHARE * available / runs_per_gpu()
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
    labels: Any = np.load(files[1], mmap_mode=mmap, allow_pickle=False)
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
    metadata = list(entry.get("metadata", []))
    pads = padding.paddings(metadata, count, (int(labels.shape[1]), int(labels.shape[2])))
    if not any(pads):
        pads = []
    elif in_memory:
        padding.mask_labels(labels, pads)
    else:
        labels = padding.MaskedLabels(labels, pads)
    return SplitData(
        split=split,
        images=images,
        labels=labels,
        patch_ids=list(entry["patch_ids"]),
        metadata=metadata,
        reference=reference,
        in_memory=in_memory,
        reference_kinds={
            n: str(entry.get("reference_kinds", {}).get(n, "four_class")) for n in names
        },
        padding=pads,
    )


# Patches per chunk when pixels are counted.
COUNT_CHUNK = 64


def count_class_pixels(labels: Any, chunk: int = COUNT_CHUNK) -> list[int]:
    """Pixels per class in chunks; IGNORE_INDEX and the masked padding are left out."""
    counts = np.zeros(NUM_CLASSES, dtype=np.int64)
    for start in range(0, labels.shape[0], chunk):
        block = np.asarray(labels[start : start + chunk]).ravel()
        counts += np.bincount(block, minlength=NUM_CLASSES)[:NUM_CLASSES]
    return [int(c) for c in counts]


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


def add_reference_masks(
    directory: Path, split: str, masks: dict[str, NDArray[np.uint8]], kinds: dict[str, str]
) -> None:
    """Add reference masks to a complete split, next to the ones it already holds.

    Used for masks made outside `build_cache --references`: the 2022 release
    masks and the reference models run from `references/`. Every array must
    have the split's patch count and label size; a name that the split already
    holds is an error, so nothing is replaced.
    """
    index = read_index(directory)
    entry = index.get("splits", {}).get(split)
    if not entry or not entry.get("complete"):
        raise CacheError(f"split {split!r} is not complete in {paths.portable(directory)}")
    labels = np.load(labels_path(directory, split), mmap_mode="r", allow_pickle=False)
    present = list(entry.get("reference_masks", []))
    for name, array in masks.items():
        if name in present:
            raise CacheError(f"split {split!r} already holds the reference mask {name!r}")
        if array.shape != labels.shape or array.dtype != np.uint8:
            raise CacheError(
                f"{name}: expected uint8 {labels.shape}, got {array.dtype} {array.shape}"
            )
        if kinds.get(name) not in ("four_class", "cloud", "probability"):
            raise CacheError(f"{name}: kind must be four_class, cloud or probability")
    for name, array in masks.items():
        np.save(reference_path(directory, split, name), array, allow_pickle=False)
    entry["reference_masks"] = [*present, *masks]
    entry["reference_kinds"] = {**entry.get("reference_kinds", {}), **kinds}
    write_index(directory, index)


INDEPENDENT_SPLIT = "test"


class ComposedBands:
    """Images of an independent dataset in the band order a model reads.

    A band the cache does not store is all zeros (a band-flexible model marks
    it unavailable, so it never sees the zeros as data); a substituted band is
    read from the stored band that stands in for it, for example B08 from B8A
    on Landsat 8 (data/independent.py, SUBSTITUTIONS).
    """

    def __init__(
        self,
        base: NDArray[np.uint16],
        stored: Sequence[str],
        wanted: Sequence[str],
        substitution: dict[str, str] | None = None,
    ) -> None:
        substitution = substitution or {}
        self.base = base
        self.sources: list[int | None] = []
        for band in wanted:
            name = substitution.get(band, band)
            self.sources.append(list(stored).index(name) if name in stored else None)
        self.shape = (base.shape[0], len(self.sources), *base.shape[2:])
        self.dtype = base.dtype
        self.ndim = base.ndim

    def __len__(self) -> int:
        return int(self.shape[0])

    def __getitem__(self, key: Any) -> NDArray[np.uint16]:
        if not isinstance(key, int | np.integer):
            raise TypeError("ComposedBands is indexed by one patch at a time")
        block = np.asarray(self.base[key])
        out = np.zeros((len(self.sources), *block.shape[1:]), dtype=block.dtype)
        for i, s in enumerate(self.sources):
            if s is not None:
                out[i] = block[s]
        return out


def load_independent(
    directory: Path, wanted: Sequence[str], substitution: dict[str, str] | None = None
) -> SplitData:
    """The tiles of an independent dataset cache, with the images in the model's band order."""
    index = read_index(directory)
    if index.get("source") in (None, "cloudsen12", SYNTHETIC_SOURCE) or not index.get(
        "independent"
    ):
        raise CacheError(f"{paths.portable(directory)} is not an independent dataset cache")
    data = load_split(directory, INDEPENDENT_SPLIT, "mmap")
    images: Any = ComposedBands(data.images, index["bands"], wanted, substitution)
    return replace(data, images=images)
