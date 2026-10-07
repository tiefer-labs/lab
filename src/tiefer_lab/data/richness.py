# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""How varied a built cache is: classes, cloud cover and verified metadata.

    python -m tiefer_lab.data.richness <cache-name>

Writes `$TIEFER_REPORTS_DIR/data/richness_<cache-name>.json`. Per split:
patch count, pixel share of each class, the number of patches in each cloud
cover bin (thick plus thin cloud), the number of patches that contain shadow,
and distinct values of the metadata fields whose meaning was checked against
the dataset card (`VERIFIED_FIELDS`). Other metadata fields are only listed
by name: their meaning is not verified, so nothing is concluded from them,
for example about geography or season.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from tiefer_lab.data import cache, padding, source
from tiefer_lab.utils import paths

# Fields of docs/DATA.md, section 9, checked against the dataset card 1.1.2.
VERIFIED_FIELDS = ("roi_id", "label_type", "real_proj_shape")
COVER_BINS = (0.0, 0.1, 0.3, 0.7, 0.9, 1.0)
CHUNK = 64
MAX_LISTED = 20


def cover_bin_names() -> list[str]:
    names = [f"[{lo:g}, {hi:g})" for lo, hi in itertools.pairwise(COVER_BINS[:-1])]
    return [*names, f"[{COVER_BINS[-2]:g}, {COVER_BINS[-1]:g}]"]


def patch_statistics(labels: Any) -> tuple[list[int], int]:
    """Patches per cloud cover bin and patches with shadow, in chunks."""
    bins = np.zeros(len(COVER_BINS) - 1, dtype=np.int64)
    shadow = 0
    for start in range(0, labels.shape[0], CHUNK):
        block = np.asarray(labels[start : start + CHUNK])
        valid = (block != source.IGNORE_INDEX).sum(axis=(1, 2))
        cloud = np.isin(block, (1, 2)).sum(axis=(1, 2))
        cover = np.divide(cloud, valid, out=np.zeros(len(block)), where=valid > 0)
        index = np.clip(np.searchsorted(COVER_BINS, cover, side="right") - 1, 0, len(bins) - 1)
        bins += np.bincount(index, minlength=len(bins))
        shadow += int((block == 3).any(axis=(1, 2)).sum())
    return [int(b) for b in bins], shadow


def field_summary(metadata: Sequence[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in VERIFIED_FIELDS:
        values = [str(m[name]) for m in metadata if name in m]
        if not values:
            out[name] = "not in the metadata"
            continue
        counts = Counter(values)
        out[name] = {
            "patches_with_field": len(values),
            "distinct": len(counts),
            "most_common": dict(counts.most_common(MAX_LISTED)),
        }
    return out


def split_report(directory: Path, split: str, entry: dict[str, Any]) -> dict[str, Any]:
    stored = np.load(cache.labels_path(directory, split), mmap_mode="r", allow_pickle=False)
    metadata = list(entry.get("metadata", []))
    # The dataset's padding is left out, as in training and evaluation (data/padding.py).
    pads = padding.paddings(metadata, int(stored.shape[0]), tuple(stored.shape[1:3]))
    labels: Any = padding.MaskedLabels(stored, pads) if any(pads) else stored
    bins, shadow = patch_statistics(labels)
    if any(pads):
        pixels = cache.count_class_pixels(labels)
    else:
        pixels = [int(p) for p in entry.get("class_pixels", [])]
    total = sum(pixels)
    names = sorted({k for m in metadata for k in m} - set(VERIFIED_FIELDS))
    return {
        "patches": int(entry["count"]),
        "class_pixel_share": {
            name: (p / total if total else None)
            for name, p in zip(source.CLASS_NAMES, pixels, strict=False)
        },
        "patches_per_cloud_cover": dict(zip(cover_bin_names(), bins, strict=True)),
        "patches_with_shadow": shadow,
        "verified_fields": field_summary(metadata),
        "other_fields_not_interpreted": names,
    }


def report(name: str) -> dict[str, Any]:
    directory = cache.cache_dir(name)
    index = cache.read_index(directory)
    splits = {
        split: split_report(directory, split, entry)
        for split, entry in index.get("splits", {}).items()
        if entry.get("complete")
    }
    if not splits:
        raise cache.CacheError(f"cache {name!r} has no complete split")
    return {
        "cache": name,
        "synthetic": cache.is_synthetic(index),
        "dataset": index.get("dataset", {}),
        "cloud_cover": "share of labelled pixels that are thick or thin cloud",
        "splits": splits,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.data.richness", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("name", help="cache folder name in $TIEFER_DATA_DIR")
    args = parser.parse_args(argv)
    try:
        out_report = report(args.name)
    except (cache.CacheError, FileNotFoundError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    out = paths.reports_dir() / "data" / f"richness_{args.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for split, part in out_report["splits"].items():
        print(
            f"{split}: {part['patches']} patches, cloud cover {part['patches_per_cloud_cover']}, "
            f"with shadow {part['patches_with_shadow']}",
            flush=True,
        )
    print(f"richness: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
