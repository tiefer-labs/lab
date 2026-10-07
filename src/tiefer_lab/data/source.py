# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""CloudSEN12+ access with tacoreader.

Every dataset fact the code depends on is defined in this module, once, and
documented with its source in docs/DATA.md. The facts come from the dataset
card (https://huggingface.co/datasets/tacofoundation/cloudsen12, version
1.1.2). The one fact the card does not state, the name of the split field,
is checked against the data on the first real build: the reader prints the
metadata columns and stops with a clear message when the field is missing.

The reader uses the tacoreader 0.5 API (`tacoreader.load`, `TortillaDataFrame.read`),
which reads the dataset's `.taco` files over HTTPS and returns GDAL virtual
file paths that rasterio opens. The card example uses tacoreader 0.5.3; this
repository pins 0.5.6, which works on CSC Roihu. Only the requested bands and
the label are read; nothing else is downloaded.
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
DATASET_CARD_VERSION = "1.1.2"
DATASET_LICENCE = "CC0-1.0"

# Level-1C variant in the TACO Foundation catalogue (card). The reference masks
# of established algorithms are in a separate variant (card).
TACO_NAME_L1C = "tacofoundation:cloudsen12-l1c"
TACO_NAME_EXTRA = "tacofoundation:cloudsen12-extra"

# Band order of the Level-1C image item (card).
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
# Descriptive names of the used bands; other bands are named by their band name.
BAND_LABELS: Mapping[str, str] = dict(zip(USED_BANDS, USED_BAND_LABELS, strict=True))
# 1-based band indexes for rasterio, derived from the order above.
USED_BAND_INDEXES: tuple[int, ...] = tuple(L1C_BAND_NAMES.index(b) + 1 for b in USED_BANDS)

# Digital number to top-of-atmosphere reflectance (card: scale 0.0001, no offset),
# reflectance = DN * REFLECTANCE_SCALE + REFLECTANCE_OFFSET.
REFLECTANCE_SCALE = 1.0e-4
REFLECTANCE_OFFSET = 0.0

# Class indexes used by every model and metric in this repository.
CLASS_NAMES: tuple[str, ...] = ("clear", "thick cloud", "thin cloud", "cloud shadow")
CLEAR, THICK_CLOUD, THIN_CLOUD, CLOUD_SHADOW = 0, 1, 2, 3
NUM_CLASSES = len(CLASS_NAMES)

# Label codes of the label item (card: 0 clear, 1 thick cloud, 2 thin cloud,
# 3 cloud shadow), mapped to the class indexes above.
LABEL_CODES: Mapping[int, int] = {0: CLEAR, 1: THICK_CLOUD, 2: THIN_CLOUD, 3: CLOUD_SHADOW}

# Metadata fields. From the card: label quality `label_type` (high, scribble,
# nolabel), patch identifier `roi_id` (also `old_roi_id`) and patch size
# `real_proj_shape` (509 or 2000). The split field is not named on the card;
# the cache builds of 2 October 2026 on CSC Roihu found it with these values
# (docs/DATA.md, section 9). The reader stops if it is missing.
SPLIT_FIELD = "tortilla:data_split"
SPLIT_VALUES: Mapping[str, str] = {"train": "train", "val": "validation", "test": "test"}
QUALITY_FIELD = "label_type"
QUALITY_HIGH = "high"
PATCH_ID_FIELD = "roi_id"
SHAPE_FIELD = "real_proj_shape"
# Only 509 x 509 patches are kept: 2000 x 2000 patches would bloat the cache
# and do not fit the fixed 512 x 512 export input.
KEPT_SHAPE = 509
# Extra training patches with partial or no labels (card: label_type values
# scribble and nolabel). They are used for training only, never for
# evaluation, and only when their location is not in the val or test split.
EXTRA_LABEL_TYPES: tuple[str, ...] = ("scribble", "nolabel")
# The field that identifies where a patch is. TODO(verify) from the survey
# (reports/data/survey.json, "overlap_with_val_test"; roi_id and stac:centroid
# are candidates). Until it is set, extra patches are not built.
LOCATION_FIELD: str | None = None
# The code of unlabelled pixels in scribble labels. TODO(verify) from the
# survey (label histograms of the scribble samples). Until it is set, scribble
# patches are not built.
SCRIBBLE_UNLABELLED_CODE: int | None = None
# Class index of pixels without a label; the loss ignores them.
IGNORE_INDEX = 255

# Row key of the TACO table; patches are sorted by it, reports use PATCH_ID_FIELD.
ID_FIELD = "tortilla:id"

# Position of the image and label items inside one sample (card: read(0), read(1)).
IMAGE_ITEM = 0
LABEL_ITEM = 1

# Reference masks of established algorithms (card). They are in TACO_NAME_EXTRA,
# not in the Level-1C samples, and are read by `build_cache --references`.
REFERENCE_MASK_NAMES: tuple[str, ...] = (
    "cloudmask_qa60",
    "cloudmask_sen2cor",
    "cloudmask_s2cloudless",
    "cloudmask_cloudscore_cs_v1",
    "cloudmask_cloudscore_cs_cdf_v1",
    "cloudmask_unetmobv2_v1",
    "cloudmask_unetmobv2_v2",
    "cloudmask_sensei_v2",
)
# Item name of each mask in a sample of the extra table: {mask name: item name}.
# TODO(verify) from the survey (extra.samples[*].items[*].name). Empty until then.
REFERENCE_MASK_ITEMS: Mapping[str, str] = {}
# Metadata field shared by a Level-1C row and its row in the extra table.
# TODO(verify) from the survey (extra.link_to_l1c). None until then.
REFERENCE_LINK_FIELD: str | None = None


@dataclass(frozen=True)
class MaskEncoding:
    """How one reference mask is encoded, read from the survey.

    `kind` is "four_class" when the mask has our four classes, or "cloud"
    when it only separates cloud from non-cloud. `codes` maps every raw value
    to a class index (four_class), to 1 for cloud and 0 for non-cloud (cloud),
    or to IGNORE_INDEX for no data. Any other raw value is an error.
    """

    kind: str
    codes: Mapping[int, int]

    def __post_init__(self) -> None:
        if self.kind not in ("four_class", "cloud"):
            raise ValueError(f"kind must be four_class or cloud, got {self.kind!r}")


# {mask name: encoding}. TODO(verify) from the survey (value histograms and
# band descriptions of every mask item) and the card. Empty until then.
REFERENCE_ENCODINGS: Mapping[str, MaskEncoding] = {}


def reference_encoding(name: str) -> MaskEncoding:
    """The verified encoding of a reference mask, or a clear stop."""
    require_verified("REFERENCE_LINK_FIELD", REFERENCE_LINK_FIELD)
    require_verified(f"REFERENCE_MASK_ITEMS[{name!r}]", REFERENCE_MASK_ITEMS.get(name))
    return require_verified(f"REFERENCE_ENCODINGS[{name!r}]", REFERENCE_ENCODINGS.get(name))


def encode_mask(
    raw: NDArray[np.integer[Any]], encoding: MaskEncoding, name: str
) -> NDArray[np.uint8]:
    """Apply a verified encoding; a raw value it does not list is an error."""
    unknown = sorted(int(v) for v in np.unique(raw) if int(v) not in encoding.codes)
    if unknown:
        raise DataSourceError(f"{name}: raw values {unknown} are not in its verified encoding")
    lookup = np.zeros(max(encoding.codes) + 1, dtype=np.uint8)
    for code, value in encoding.codes.items():
        lookup[code] = value
    return lookup[raw.astype(np.int64)]


def open_extra_table(taco: str = TACO_NAME_EXTRA) -> Any:
    """The extra table (reference masks); its columns are printed, not checked."""
    import tacoreader

    table = tacoreader.load(taco)
    print(f"extra metadata columns: {', '.join(sorted(map(str, table.columns)))}", flush=True)
    return table


def read_references(
    extra: Any, position: int, names: Sequence[str]
) -> dict[str, NDArray[np.uint8]]:
    """Read and encode the named masks of row `position` of the extra table."""
    sample = extra.read(position)
    items = [str(n) for n in sample["tortilla:id"]]
    out = {}
    for name in names:
        item = REFERENCE_MASK_ITEMS[name]
        if item not in items:
            raise DataSourceError(f"item {item!r} for {name} is not in the extra sample: {items}")
        raw = _read_bands(sample.read(items.index(item)), (1,), 1)[0]
        out[name] = encode_mask(raw, reference_encoding(name), name)
    return out


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


def map_labels(
    raw: NDArray[np.integer[Any]], unlabelled_code: int | None = None
) -> NDArray[np.uint8]:
    """Map dataset label codes to class indexes; unknown codes are an error.

    With `unlabelled_code`, pixels with that code become IGNORE_INDEX.
    """
    codes = dict(LABEL_CODES)
    if unlabelled_code is not None:
        codes[unlabelled_code] = IGNORE_INDEX
    values = np.unique(raw)
    unknown = sorted(int(v) for v in values if int(v) not in codes)
    if unknown:
        raise DataSourceError(
            f"label item contains codes {unknown} that are not in LABEL_CODES "
            f"{dict(LABEL_CODES)}; check the dataset card ({DATASET_CARD_URL})"
        )
    lookup = np.zeros(max(codes) + 1, dtype=np.uint8)
    for code, cls in codes.items():
        lookup[code] = cls
    return lookup[raw.astype(np.int64)]


def require_verified[T](name: str, value: T | None) -> T:
    """Stop with a clear message when a fact the code needs is not verified yet."""
    if value is None:
        raise DataSourceError(
            f"{name} is not verified yet (TODO(verify)); run the survey "
            "(hpc/roihu/survey.sbatch), read it from reports/data/survey.json and set "
            f"{name} in src/tiefer_lab/data/source.py"
        )
    return value


def open_table(taco: str | Sequence[str] = TACO_NAME_L1C) -> Any:
    """Load the dataset's metadata table (a pandas data frame) with tacoreader.

    Prints the metadata columns once, and stops with a clear message when a
    field the reader depends on is missing.
    """
    import tacoreader

    table = tacoreader.load(taco if isinstance(taco, str) else list(taco))
    columns = sorted(map(str, table.columns))
    print(f"metadata columns ({len(columns)}): {', '.join(columns)}", flush=True)
    check_columns(columns)
    return table


def check_columns(columns: Sequence[str]) -> None:
    if SPLIT_FIELD not in columns:
        raise DataSourceError(
            f"the split field {SPLIT_FIELD!r} is not in the metadata. The dataset card does "
            "not name the split field; find it in the columns printed above and set "
            "SPLIT_FIELD and SPLIT_VALUES in src/tiefer_lab/data/source.py"
        )
    missing = [
        c for c in (QUALITY_FIELD, PATCH_ID_FIELD, SHAPE_FIELD, ID_FIELD) if c not in columns
    ]
    if missing:
        raise DataSourceError(
            f"metadata columns {missing} not found; available columns: {list(columns)}. "
            f"Check the dataset card ({DATASET_CARD_URL})"
        )


@dataclass(frozen=True)
class Selection:
    """Row positions of one split and how many patches were kept and dropped."""

    positions: list[int]
    high_quality: int
    kept: int
    dropped_other_shape: int
    limit: int | None
    dropped_location: int = 0

    def counts(self) -> dict[str, int | None]:
        return {
            "high_quality": self.high_quality,
            "kept_509": self.kept,
            "dropped_other_shape": self.dropped_other_shape,
            "limit": self.limit,
            "selected": len(self.positions),
            "dropped_location_in_val_or_test": self.dropped_location,
        }


def select(table: Any, split: str, limit: int | None = None, seed: int = 0) -> Selection:
    """High quality 509 x 509 patches of one split, sorted by the row key.

    Patches of any other size are dropped and counted. With `limit`, a
    fixed-seed random subset of that size is taken, so a small cache is
    spread over the split rather than taken from its start.
    """
    if split not in SPLIT_VALUES:
        raise ValueError(f"split must be one of {sorted(SPLIT_VALUES)}, got {split!r}")
    check_columns([str(c) for c in table.columns])
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
    in_split = np.asarray(
        (table[SPLIT_FIELD] == SPLIT_VALUES[split]) & (table[QUALITY_FIELD] == QUALITY_HIGH)
    )
    shapes = np.asarray([_as_number(v) for v in table[SHAPE_FIELD]])
    kept_mask = in_split & (shapes == KEPT_SHAPE)
    positions = [int(i) for i in np.flatnonzero(kept_mask)]
    positions.sort(key=lambda i: str(table.iloc[i][ID_FIELD]))
    kept = len(positions)
    if limit is not None and limit < len(positions):
        rng = np.random.default_rng(seed)
        chosen = rng.choice(len(positions), size=limit, replace=False)
        positions = [positions[i] for i in sorted(int(c) for c in chosen)]
    return Selection(
        positions=positions,
        high_quality=int(in_split.sum()),
        kept=kept,
        dropped_other_shape=int(in_split.sum()) - kept,
        limit=limit,
    )


def select_extra(
    table: Any, limit: int | None = None, seed: int = 0, location_field: str | None = None
) -> Selection:
    """Scribble and nolabel 509 x 509 patches for training, away from val and test.

    A patch is used only when its split (if the table has one) is the training
    split and its location (LOCATION_FIELD) appears in no row of the
    validation or test split, of any label type. Dropped patches are counted.
    """
    field = require_verified("LOCATION_FIELD", location_field or LOCATION_FIELD)
    check_columns([str(c) for c in table.columns])
    if field not in table.columns:
        raise DataSourceError(f"location field {field!r} is not in the metadata")
    types = table[QUALITY_FIELD].astype(str)
    extra = np.asarray(types.isin(EXTRA_LABEL_TYPES))
    in_train = np.asarray(table[SPLIT_FIELD] == SPLIT_VALUES["train"])
    held_out = np.asarray(table[SPLIT_FIELD].isin([SPLIT_VALUES["val"], SPLIT_VALUES["test"]]))
    held_locations = set(map(str, table[field][held_out]))
    shapes = np.asarray([_as_number(v) for v in table[SHAPE_FIELD]])
    candidates = extra & in_train
    sized = candidates & (shapes == KEPT_SHAPE)
    away = np.asarray([str(v) not in held_locations for v in table[field]])
    positions = [int(i) for i in np.flatnonzero(sized & away)]
    positions.sort(key=lambda i: str(table.iloc[i][ID_FIELD]))
    kept = len(positions)
    if limit is not None and limit < len(positions):
        rng = np.random.default_rng(seed)
        chosen = rng.choice(len(positions), size=limit, replace=False)
        positions = [positions[i] for i in sorted(int(c) for c in chosen)]
    return Selection(
        positions=positions,
        high_quality=int(candidates.sum()),
        kept=int(sized.sum()),
        dropped_other_shape=int(candidates.sum() - sized.sum()),
        limit=limit,
        dropped_location=int(sized.sum()) - kept,
    )


def read_extra_patch(table: Any, position: int, bands: Sequence[str] = USED_BANDS) -> Patch:
    """Read a scribble or nolabel patch: unlabelled pixels get IGNORE_INDEX.

    Nolabel patches have no label to read: every pixel is IGNORE_INDEX.
    """
    row = table.iloc[position]
    label_type = str(row[QUALITY_FIELD])
    sample = table.read(position)
    image = _read_bands(sample.read(IMAGE_ITEM), band_indexes(bands), len(L1C_BAND_NAMES))
    if image.dtype != np.uint16:
        raise DataSourceError(f"expected uint16 digital numbers, found {image.dtype}")
    if label_type == "nolabel":
        label = np.full(image.shape[1:], IGNORE_INDEX, dtype=np.uint8)
    elif label_type == "scribble":
        code = require_verified("SCRIBBLE_UNLABELLED_CODE", SCRIBBLE_UNLABELLED_CODE)
        raw = _read_bands(sample.read(LABEL_ITEM), (1,), 1)[0]
        label = map_labels(raw.astype(np.int64), unlabelled_code=int(code))
    else:
        raise DataSourceError(f"{label_type!r} is not an extra label type {EXTRA_LABEL_TYPES}")
    if label.shape != image.shape[1:]:
        raise DataSourceError(f"label shape {label.shape} differs from image {image.shape[1:]}")
    return Patch(
        patch_id=str(row[PATCH_ID_FIELD]),
        image=image.astype(np.uint16),
        label=label,
        metadata=row_metadata(row),
    )


def select_rows(table: Any, split: str, limit: int | None = None, seed: int = 0) -> list[int]:
    """Row positions of `select`."""
    return select(table, split, limit, seed).positions


def _as_number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


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


def band_indexes(bands: Sequence[str]) -> tuple[int, ...]:
    """1-based rasterio indexes of Level-1C bands given by name."""
    unknown = [b for b in bands if b not in L1C_BAND_NAMES]
    if unknown:
        raise DataSourceError(f"unknown bands {unknown}; Level-1C bands are {L1C_BAND_NAMES}")
    return tuple(L1C_BAND_NAMES.index(b) + 1 for b in bands)


def read_patch(table: Any, position: int, bands: Sequence[str] = USED_BANDS) -> Patch:
    """Read the given bands (by default the four used bands) and the label at `position`."""
    row = table.iloc[position]
    sample = table.read(position)
    image_path = sample.read(IMAGE_ITEM)
    label_path = sample.read(LABEL_ITEM)
    image = _read_bands(image_path, band_indexes(bands), len(L1C_BAND_NAMES))
    if image.dtype != np.uint16:
        raise DataSourceError(f"expected uint16 digital numbers, found {image.dtype}")
    raw_label = _read_bands(label_path, (1,), 1)[0]
    label = map_labels(raw_label.astype(np.int64))
    if label.shape != image.shape[1:]:
        raise DataSourceError(f"label shape {label.shape} differs from image {image.shape[1:]}")
    return Patch(
        patch_id=str(row[PATCH_ID_FIELD]),
        image=image.astype(np.uint16),
        label=label,
        metadata=row_metadata(row),
    )


def dataset_revision(timeout: float = 20.0) -> str | None:
    """Current commit of the dataset repository on Hugging Face (`sha` field), or None."""
    try:
        from tiefer_lab.data import http

        request = urllib.request.Request(DATASET_API_URL, headers=http.auth_headers())
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (fixed https URL)
            payload = json.load(response)
    except (OSError, ValueError):
        return None
    sha = payload.get("sha") if isinstance(payload, dict) else None
    return str(sha) if sha else None
