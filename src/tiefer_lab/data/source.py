# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""CloudSEN12+ access with tacoreader.

Every dataset fact the code depends on is defined in this module, once, and
documented with its source in docs/DATA.md. Facts marked TODO(verify) could
not be checked against the dataset card when this module was written; the
reader checks them against the data at run time and stops with a clear
message when they do not hold.

The reader uses the tacoreader 0.5 API (`tacoreader.load`, `TortillaDataFrame.read`),
which reads the dataset's `.taco` files over HTTPS and returns GDAL virtual
file paths that rasterio opens. Only the requested bands and the label are
read; nothing else is downloaded.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

# Dataset identity.
DATASET_REPO = "tacofoundation/cloudsen12"
DATASET_CARD_URL = "https://huggingface.co/datasets/tacofoundation/cloudsen12"
DATASET_API_URL = "https://huggingface.co/api/datasets/tacofoundation/cloudsen12"
DATASET_LICENCE = "CC0-1.0"

# TODO(verify): name of the Level-1C variant in the TACO Foundation catalogue
# (https://huggingface.co/datasets/tacofoundation/cloudsen12).
TACO_NAME_L1C = "tacofoundation:cloudsen12-l1c"

# TODO(verify): band order of the Level-1C image item. Sentinel-2 Level-1C has
# these 13 bands; the card states the order in which the dataset stores them.
L1C_BAND_NAMES: tuple[str, ...] = (
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B09",
    "B10",
    "B11",
    "B12",
)

# The four bands Tiefer uses: blue, green, red, near infrared (docs/ASSUMPTIONS.md).
USED_BANDS: tuple[str, ...] = ("B02", "B03", "B04", "B08")
USED_BAND_LABELS: tuple[str, ...] = ("blue", "green", "red", "near infrared")
# 1-based band indexes for rasterio, derived from the order above.
USED_BAND_INDEXES: tuple[int, ...] = tuple(L1C_BAND_NAMES.index(b) + 1 for b in USED_BANDS)

# TODO(verify): digital number to top-of-atmosphere reflectance,
# reflectance = DN * REFLECTANCE_SCALE + REFLECTANCE_OFFSET.
REFLECTANCE_SCALE = 1.0e-4
REFLECTANCE_OFFSET = 0.0

# Class indexes used by every model and metric in this repository.
CLASS_NAMES: tuple[str, ...] = ("clear", "thick cloud", "thin cloud", "cloud shadow")
CLEAR, THICK_CLOUD, THIN_CLOUD, CLOUD_SHADOW = 0, 1, 2, 3
NUM_CLASSES = len(CLASS_NAMES)

# TODO(verify): label codes in the dataset's label item, mapped to the class
# indexes above.
LABEL_CODES: Mapping[int, int] = {0: CLEAR, 1: THICK_CLOUD, 2: THIN_CLOUD, 3: CLOUD_SHADOW}

# TODO(verify): metadata fields for the split, the label quality and the patch ID,
# and their values.
SPLIT_FIELD = "tortilla:data_split"
SPLIT_VALUES: Mapping[str, str] = {"train": "train", "val": "validation", "test": "test"}
QUALITY_FIELD = "label_type"
QUALITY_HIGH = "high"
ID_FIELD = "tortilla:id"

# TODO(verify): position of the image and label items inside one sample.
IMAGE_ITEM = 0
LABEL_ITEM = 1

# TODO(verify): reference masks from established algorithms shipped with the
# dataset, as {name: item position}. Empty until the card confirms which exist.
REFERENCE_MASK_ITEMS: Mapping[str, int] = {}

# Metadata columns that describe file layout rather than the scene.
_LAYOUT_PREFIXES = ("internal:", "tortilla:offset", "tortilla:length", "tortilla:file_format")


class DataSourceError(RuntimeError):
    """The dataset does not match the facts this module depends on."""


@dataclass
class Patch:
    """One patch: four-band image as stored digital numbers, and class labels."""

    patch_id: str
    image: NDArray[np.uint16]
    label: NDArray[np.uint8]
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)
    reference: dict[str, NDArray[np.uint8]] = field(default_factory=dict)


def map_labels(raw: NDArray[np.integer[Any]]) -> NDArray[np.uint8]:
    """Map dataset label codes to class indexes; unknown codes are an error."""
    values = np.unique(raw)
    unknown = sorted(int(v) for v in values if int(v) not in LABEL_CODES)
    if unknown:
        raise DataSourceError(
            f"label item contains codes {unknown} that are not in LABEL_CODES "
            f"{dict(LABEL_CODES)}; check the dataset card ({DATASET_CARD_URL})"
        )
    lookup = np.zeros(max(LABEL_CODES) + 1, dtype=np.uint8)
    for code, cls in LABEL_CODES.items():
        lookup[code] = cls
    return lookup[raw.astype(np.int64)]


def open_table(taco: str | Sequence[str] = TACO_NAME_L1C) -> Any:
    """Load the dataset's metadata table (a pandas data frame) with tacoreader."""
    import tacoreader

    table = tacoreader.load(taco if isinstance(taco, str) else list(taco))
    missing = [c for c in (SPLIT_FIELD, QUALITY_FIELD, ID_FIELD) if c not in table.columns]
    if missing:
        raise DataSourceError(
            f"metadata columns {missing} not found; available columns: "
            f"{sorted(map(str, table.columns))}. Check the dataset card ({DATASET_CARD_URL})"
        )
    return table


def select_rows(table: Any, split: str, limit: int | None = None, seed: int = 0) -> list[int]:
    """Row positions of high quality patches in one split, sorted by patch ID.

    With `limit`, a fixed-seed random subset of that size is taken, so a small
    cache is spread over the split rather than taken from its start.
    """
    if split not in SPLIT_VALUES:
        raise ValueError(f"split must be one of {sorted(SPLIT_VALUES)}, got {split!r}")
    split_values = set(map(str, table[SPLIT_FIELD].unique()))
    if SPLIT_VALUES[split] not in split_values:
        raise DataSourceError(
            f"split value {SPLIT_VALUES[split]!r} not found in {SPLIT_FIELD}; "
            f"values present: {sorted(split_values)}"
        )
    quality_values = set(map(str, table[QUALITY_FIELD].unique()))
    if QUALITY_HIGH not in quality_values:
        raise DataSourceError(
            f"quality value {QUALITY_HIGH!r} not found in {QUALITY_FIELD}; "
            f"values present: {sorted(quality_values)}"
        )
    mask = (table[SPLIT_FIELD] == SPLIT_VALUES[split]) & (table[QUALITY_FIELD] == QUALITY_HIGH)
    positions = [int(i) for i in np.flatnonzero(np.asarray(mask))]
    positions.sort(key=lambda i: str(table.iloc[i][ID_FIELD]))
    if limit is not None and limit < len(positions):
        rng = np.random.default_rng(seed)
        chosen = rng.choice(len(positions), size=limit, replace=False)
        positions = [positions[i] for i in sorted(int(c) for c in chosen)]
    return positions


def row_metadata(row: Mapping[str, Any]) -> dict[str, str | int | float | bool]:
    """Scalar metadata of one row, without file layout columns."""
    out: dict[str, str | int | float | bool] = {}
    for key, value in row.items():
        name = str(key)
        if name.startswith(_LAYOUT_PREFIXES):
            continue
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, bool | int | float | str):
            out[name] = value
    return out


def _read_bands(path: str, indexes: Sequence[int], expected_count: int) -> NDArray[np.generic]:
    import rasterio

    with rasterio.open(path) as src:
        if src.count != expected_count:
            raise DataSourceError(
                f"expected {expected_count} bands, found {src.count} in {path}; "
                f"check the band order on the dataset card ({DATASET_CARD_URL})"
            )
        descriptions = [d for d in src.descriptions if d]
        if expected_count == len(L1C_BAND_NAMES) and len(descriptions) == expected_count:
            found = tuple(d.upper() for d in descriptions)
            if found != L1C_BAND_NAMES:
                raise DataSourceError(f"band descriptions {found} differ from {L1C_BAND_NAMES}")
        data: NDArray[np.generic] = src.read(list(indexes))
    return data


def read_patch(table: Any, position: int) -> Patch:
    """Read the four used bands and the label of the patch at `position`."""
    row = table.iloc[position]
    sample = table.read(position)
    image_path = sample.read(IMAGE_ITEM)
    label_path = sample.read(LABEL_ITEM)
    image = _read_bands(image_path, USED_BAND_INDEXES, len(L1C_BAND_NAMES))
    if image.dtype != np.uint16:
        raise DataSourceError(f"expected uint16 digital numbers, found {image.dtype}")
    raw_label = _read_bands(label_path, (1,), 1)[0]
    label = map_labels(raw_label.astype(np.int64))
    if label.shape != image.shape[1:]:
        raise DataSourceError(f"label shape {label.shape} differs from image {image.shape[1:]}")
    reference = {
        name: map_labels(_read_bands(sample.read(item), (1,), 1)[0].astype(np.int64))
        for name, item in REFERENCE_MASK_ITEMS.items()
    }
    return Patch(
        patch_id=str(row[ID_FIELD]),
        image=image.astype(np.uint16),
        label=label,
        metadata=row_metadata(row),
        reference=reference,
    )


def dataset_revision(timeout: float = 20.0) -> str | None:
    """Current commit of the dataset repository on Hugging Face, or None.

    TODO(verify): the response field (`sha`) of the Hugging Face dataset API.
    """
    try:
        with urllib.request.urlopen(DATASET_API_URL, timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, ValueError):
        return None
    sha = payload.get("sha") if isinstance(payload, dict) else None
    return str(sha) if sha else None
