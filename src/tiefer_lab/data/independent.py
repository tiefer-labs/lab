# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Independent test datasets: facts, readers, harmonisation and tiling.

Four datasets of the CloudSEN12 paper's Table 1 are used as independent
tests, never for training, selection, calibration or thresholds:

- `landsat8_biome`: L8 Biome cloud validation masks (USGS, 2016);
- `landsat8_sparcs`: L8 SPARCS cloud validation masks (USGS, 2016);
- `s2_cloud_catalogue`: Sentinel-2 Cloud Mask Catalogue (Zenodo, 2020);
- `kappaset`: KappaSet, Sentinel-2 KappaZeta cloud and cloud shadow masks
  (Zenodo, 2022).

Every fact below is read from the primary source named next to it, with the
date it was read; the data card is docs/INDEPENDENT.md. A fact that is not
verified is None and stops the build with `require_verified`, naming what
resolves it. Nothing is guessed: no label code, scale, offset, field name or
file name.

Pipeline of `build_cache --source <dataset> --root <download folder>`:
read a scene, convert to top-of-atmosphere reflectance, harmonise the labels
to clear 0, thick cloud 1, thin cloud 2, cloud shadow 3 and unlabelled 255
(docs/DATASETS.md, section 3), resample to 10 m like
`tiefer_lab.onboard.predict_frame` (or keep the native resolution, a
perturbation), cut non-overlapping 509 x 509 tiles from the top left and drop
tiles with more than `max_nodata` unlabelled pixels. The patch definition is
a protocol decision (docs/INDEPENDENT.md, section 4).
"""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import (
    CLEAR,
    CLOUD_SHADOW,
    IGNORE_INDEX,
    L1C_BAND_NAMES,
    THICK_CLOUD,
    THIN_CLOUD,
    DataSourceError,
    require_verified,
)

LANDSAT8 = "Landsat 8 OLI"
SENTINEL2 = "Sentinel-2 MSI"
TILE = 509
TRAINING_GSD_M = 10.0
# Default largest share of unlabelled pixels in a kept tile (a protocol decision).
MAX_NODATA_SHARE = 0.1


@dataclass(frozen=True)
class Dataset:
    """What is known about one independent dataset, each item from its source."""

    name: str
    sensor: str
    version: str
    url: str
    licence: str | None
    licence_source: str
    gsd_m: float
    # Raw label code to class index; None until verified.
    label_codes: Mapping[int, int] | None
    has_thin: bool
    has_shadow: bool
    # Name of the reference mask in reports that is the dataset's operational mask.
    operational_mask: str | None
    # Metadata fields that are biomes or surface classes (IND-04).
    strata_fields: tuple[str, ...]
    note: str = ""


# Landsat 8 OLI band number to the Sentinel-2 band of the closest centre wavelength
# and width: a decision recorded in docs/ASSUMPTIONS.md (A-1.8) and docs/DATASETS.md,
# section 3. Band 5 (865 nm, narrow) matches B8A, not B08; band 9 (cirrus) matches B10.
LANDSAT8_TO_S2: Mapping[int, str] = {
    1: "B01",
    2: "B02",
    3: "B03",
    4: "B04",
    5: "B8A",
    6: "B11",
    7: "B12",
    9: "B10",
}
# The four-band models need B08; on Landsat 8 the band 5 stands in for it. This is a
# substitution, recorded as such in every report and reported apart.
SUBSTITUTIONS: Mapping[str, Mapping[str, str]] = {LANDSAT8: {"B08": "B8A"}}

DATASETS: dict[str, Dataset] = {
    "landsat8_biome": Dataset(
        name="landsat8_biome",
        sensor=LANDSAT8,
        version="USGS data release 2016, doi:10.5066/F7251GDH; 96 pre-collection Level-1T scenes",
        url="https://www.usgs.gov/landsat-missions/landsat-8-cloud-cover-assessment-validation-data",
        licence="U.S. Public Domain",
        licence_source="https://www.usgs.gov/information-policies-and-instructions/"
        "copyrights-and-credits, read 14 October 2026: USGS-authored or produced data are "
        "in the U.S. Public Domain; credit requested",
        gsd_m=30.0,
        # TODO(verify): mask values from the data release files or Foga et al. 2017,
        # https://doi.org/10.1016/j.rse.2017.03.026.
        label_codes=None,
        has_thin=True,
        has_shadow=True,
        operational_mask="reference_landsat_qa",
        strata_fields=("biome",),
        note="shadow is labelled in part of the scenes only",
    ),
    "landsat8_sparcs": Dataset(
        name="landsat8_sparcs",
        sensor=LANDSAT8,
        version="USGS data release 2016, doi:10.5066/F7FB5146; 80 subsets of 1000 x 1000 "
        "pixels of pre-collection scenes",
        url="https://www.usgs.gov/landsat-missions/"
        "spatial-procedures-automated-removal-cloud-and-shadow-sparcs-validation-data",
        licence="U.S. Public Domain",
        licence_source="https://www.usgs.gov/information-policies-and-instructions/"
        "copyrights-and-credits, read 14 October 2026",
        gsd_m=30.0,
        # From the dataset page, read 14 October 2026: 0 shadow, 1 shadow over water,
        # 2 water, 3 snow, 4 land, 5 cloud, 6 flooded. Snow, water and flooded are clear.
        # No thin cloud class: cloud is scored on the cloud problem only. The page's
        # prose lists the classes in another order; the value table is used, and the
        # build stops on any other value (a no-data value is not listed).
        label_codes={
            0: CLOUD_SHADOW,
            1: CLOUD_SHADOW,
            2: CLEAR,
            3: CLEAR,
            4: CLEAR,
            5: THICK_CLOUD,
            6: CLEAR,
        },
        has_thin=False,
        has_shadow=True,
        operational_mask="reference_landsat_qa",
        strata_fields=(),
    ),
    "s2_cloud_catalogue": Dataset(
        name="s2_cloud_catalogue",
        sensor=SENTINEL2,
        version="Zenodo record 4172871, published 1 November 2020, doi:10.5281/zenodo.4172871",
        url="https://zenodo.org/records/4172871",
        licence="CC-BY-4.0",
        licence_source="Zenodo record 4172871, read 14 October 2026",
        gsd_m=20.0,
        # README.pdf of the record, read 14 October 2026: one-hot masks with the class
        # order CLEAR, CLOUD, CLOUD_SHADOW; stored here as channel index 0, 1, 2.
        label_codes={0: CLEAR, 1: THICK_CLOUD, 2: CLOUD_SHADOW},
        has_thin=False,
        has_shadow=True,
        operational_mask=None,
        strata_fields=(
            "forest/jungle",
            "snow/ice",
            "agricultural",
            "urban/developed",
            "coastal",
            "hills/mountains",
            "desert/barren",
            "shrublands/plains",
            "wetland/bog/marsh",
            "open_water",
            "enclosed_water",
        ),
        note="shadow is scored only on subscenes with shadows_marked = 1",
    ),
    "kappaset": Dataset(
        name="kappaset",
        sensor=SENTINEL2,
        version="Zenodo record 7100327, version 1, published 21 September 2022, "
        "doi:10.5281/zenodo.7100327",
        url="https://zenodo.org/records/7100327",
        licence="CC-BY-4.0",
        licence_source="Zenodo record 7100327, read 14 October 2026",
        gsd_m=10.0,
        # README.pdf of the record, read 14 October 2026: 0 undefined, 1 clear,
        # 2 cloud shadow, 3 semi-transparent cloud, 4 cloud, 5 missing.
        label_codes={
            0: IGNORE_INDEX,
            1: CLEAR,
            2: CLOUD_SHADOW,
            3: THIN_CLOUD,
            4: THICK_CLOUD,
            5: IGNORE_INDEX,
        },
        has_thin=True,
        has_shadow=True,
        operational_mask=None,
        strata_fields=(),
        note="the test folder also holds Sen2Cor (SCL), Fmask (FMC) and s2cloudless (SS2C) "
        "maps on the same pixels",
    ),
}


# Facts still open, by dataset. Each is None until set from its source; the build
# stops on the first one it needs (docs/INDEPENDENT.md, section 6).
OPEN_FACTS: dict[str, dict[str, Any]] = {
    "landsat8_biome": {
        "scene_layout": None,  # file names of bands, BQA, MTL and mask in a scene folder
        "biome_of_scene": None,  # where the biome of each scene is given
        "qa_bit_layout": None,  # pre-collection BQA bits, from the USGS product guide
    },
    "landsat8_sparcs": {
        "scene_layout": None,  # file names of the band stack, QA, MTL and mask
        "band_stack_order": None,  # band order of the band-interleaved file
        "qa_bit_layout": None,
    },
    "s2_cloud_catalogue": {
        # The README names the product ID in the `scene` column; the processing
        # baseline of each product is read from it by the ESA naming convention.
        "product_naming": None,
    },
    "kappaset": {
        "band_scale": None,  # whether the NetCDF bands are digital numbers or reflectance
        "product_id": None,  # where the Sentinel-2 product ID of a sub-tile is given
        "scl_codes": None,  # Sen2Cor scene classification codes, from its user manual
        "netcdf_driver": None,  # that GDAL in the locked rasterio reads the NetCDF files
    },
}

# Raw codes of the operational and comparison masks, once verified.
COMPARISON_CODES: dict[str, Mapping[int, int] | None] = {
    "reference_landsat_qa": None,
    "reference_sen2cor": None,
}


def dataset(name: str) -> Dataset:
    if name not in DATASETS:
        raise DataSourceError(f"unknown independent dataset {name!r}; known: {sorted(DATASETS)}")
    return DATASETS[name]


def require_fact(name: str, fact: str) -> Any:
    """The value of an open fact of a dataset, or a clear stop."""
    return require_verified(f"independent.OPEN_FACTS[{name!r}][{fact!r}]", OPEN_FACTS[name][fact])


# Reflectance -----------------------------------------------------------------


def landsat_toa_reflectance(
    dn: NDArray[np.integer[Any]], mult: float, add: float, sun_elevation_deg: float
) -> NDArray[np.float32]:
    """Landsat top-of-atmosphere reflectance with the sun angle correction.

    rho = (REFLECTANCE_MULT_BAND_x x DN + REFLECTANCE_ADD_BAND_x) / sin(SUN_ELEVATION),
    from "Using the USGS Landsat Level-1 Data Product", USGS,
    https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product,
    read 14 October 2026. It matches the sun-angle corrected reflectance of
    Sentinel-2 Level-1C. DN 0 is fill and gives NaN.
    """
    if not 0 < sun_elevation_deg <= 90:
        raise DataSourceError(f"sun elevation {sun_elevation_deg} is not in (0, 90] degrees")
    values = (mult * dn.astype(np.float64) + add) / math.sin(math.radians(sun_elevation_deg))
    out = values.astype(np.float32)
    out[dn == 0] = np.nan
    return out


MTL_LINE = re.compile(r"^\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$")


def parse_mtl(text: str) -> dict[str, str]:
    """KEY = VALUE pairs of a Landsat MTL file; quotes are removed."""
    out = {}
    for line in text.splitlines():
        match = MTL_LINE.match(line)
        if match and match.group(1) not in ("GROUP", "END_GROUP"):
            out[match.group(1)] = match.group(2).strip('"')
    return out


def landsat_scale(mtl: Mapping[str, str], band: int) -> tuple[float, float, float]:
    """(REFLECTANCE_MULT_BAND_x, REFLECTANCE_ADD_BAND_x, SUN_ELEVATION) of one band.

    The field names are those of the USGS page above; a file without them stops.
    """
    keys = (f"REFLECTANCE_MULT_BAND_{band}", f"REFLECTANCE_ADD_BAND_{band}", "SUN_ELEVATION")
    missing = [k for k in keys if k not in mtl]
    if missing:
        raise DataSourceError(
            f"MTL file lacks {missing}; check the product guide of its collection"
        )
    mult, add, sun = (float(mtl[k]) for k in keys)
    return mult, add, sun


# Sentinel-2 processing baseline from the product ID, by the ESA naming convention
# (for example ..._N0206_... is baseline 02.06). TODO(verify): the convention page.
PRODUCT_BASELINE = re.compile(r"_N(\d{2})(\d{2})_")
# From processing baseline 04.00 (products from 25 January 2022) Level-1C digital
# numbers carry a radiometric offset (-1000) given in the product metadata.
OFFSET_BASELINE = (4, 0)


def s2_baseline(product_id: str) -> tuple[int, int]:
    """The processing baseline (major, minor) written in a Sentinel-2 product ID."""
    require_fact("s2_cloud_catalogue", "product_naming")
    match = PRODUCT_BASELINE.search(product_id)
    if not match:
        raise DataSourceError(f"no processing baseline in product ID {product_id!r}")
    return int(match.group(1)), int(match.group(2))


def s2_needs_offset(product_id: str) -> bool:
    """Whether the product's digital numbers carry the radiometric offset (baseline 04.00+)."""
    return s2_baseline(product_id) >= OFFSET_BASELINE


# Labels, resampling and tiles -------------------------------------------------


def harmonise(
    raw: NDArray[np.integer[Any]], codes: Mapping[int, int], name: str
) -> NDArray[np.uint8]:
    """Map raw label codes to the four classes and 255; any other code stops the build."""
    values = raw.astype(np.int64)
    unknown = sorted(int(v) for v in np.unique(values) if int(v) not in codes)
    if unknown:
        raise DataSourceError(f"{name}: label codes {unknown} are not in its verified map")
    lookup = np.full(max(codes) + 1, IGNORE_INDEX, dtype=np.uint8)
    for code, cls in codes.items():
        lookup[code] = cls
    return lookup[values]


def resample(
    image: NDArray[np.float32],
    label: NDArray[np.uint8],
    gsd_m: float,
    target_gsd_m: float = TRAINING_GSD_M,
    masks: Mapping[str, NDArray[np.uint8]] | None = None,
) -> tuple[NDArray[np.float32], NDArray[np.uint8], dict[str, NDArray[np.uint8]]]:
    """Resample to `target_gsd_m` as `onboard.predict_frame` does for images
    (area averaging when finer, bilinear when coarser); labels and masks nearest.

    NaN (no data) pixels of the image become unlabelled in the label. Torch is
    imported here only, so the CPU jobs that import this module run without it.
    """
    import torch
    import torch.nn.functional as F  # noqa: N812

    factor = gsd_m / target_gsd_m
    height, width = label.shape
    size = (max(1, round(height * factor)), max(1, round(width * factor)))
    nodata = ~np.isfinite(image).all(axis=0)
    label = label.copy()
    label[nodata] = IGNORE_INDEX
    if size == (height, width):
        return np.nan_to_num(image), label, dict(masks or {})
    x = torch.from_numpy(np.nan_to_num(image).astype(np.float32))[None]
    x = F.interpolate(x, size=size, mode="area" if factor < 1 else "bilinear", align_corners=None)

    def nearest(a: NDArray[np.uint8]) -> NDArray[np.uint8]:
        t = torch.from_numpy(a.astype(np.float32))[None, None]
        return F.interpolate(t, size=size, mode="nearest")[0, 0].numpy().astype(np.uint8)

    return (
        x[0].numpy(),
        nearest(label),
        {k: nearest(v) for k, v in (masks or {}).items()},
    )


@dataclass
class Tile:
    """One 509 x 509 tile of a scene."""

    tile_id: str
    image: NDArray[np.float32]
    label: NDArray[np.uint8]
    metadata: dict[str, Any]
    masks: dict[str, NDArray[np.uint8]] = field(default_factory=dict)


def tiles(
    scene_id: str,
    image: NDArray[np.float32],
    label: NDArray[np.uint8],
    metadata: Mapping[str, Any],
    masks: Mapping[str, NDArray[np.uint8]] | None = None,
    size: int = TILE,
    max_nodata: float = MAX_NODATA_SHARE,
) -> tuple[list[Tile], dict[str, int]]:
    """Non-overlapping tiles from the top left; the remainder strips are left out.

    A tile with more than `max_nodata` unlabelled pixels is dropped and counted.
    """
    height, width = label.shape
    kept: list[Tile] = []
    dropped = 0
    for r in range(height // size):
        for c in range(width // size):
            window = (slice(r * size, (r + 1) * size), slice(c * size, (c + 1) * size))
            lab = label[window]
            if float((lab == IGNORE_INDEX).mean()) > max_nodata:
                dropped += 1
                continue
            kept.append(
                Tile(
                    f"{scene_id}_r{r}c{c}",
                    image[(slice(None), *window)],
                    lab,
                    {**metadata, "scene": scene_id, "tile_row": r, "tile_col": c},
                    {k: v[window] for k, v in (masks or {}).items()},
                )
            )
    return kept, {
        "kept": len(kept),
        "dropped_nodata": dropped,
        "remainder_pixels": height * width - (height // size) * (width // size) * size * size,
    }


def to_cache_dn(reflectance: NDArray[np.float32]) -> NDArray[np.uint16]:
    """Reflectance stored as the cache stores Sentinel-2 Level-1C: DN = reflectance x 10000."""
    return np.clip(np.rint(np.nan_to_num(reflectance) * 10000.0), 0, 65535).astype(np.uint16)


# Readers -----------------------------------------------------------------------


@dataclass
class Scene:
    """One scene or subscene of a dataset, at its native resolution."""

    scene_id: str
    # Reflectance per Sentinel-2 band name (a Landsat band under its matched name).
    bands: dict[str, NDArray[np.float32]]
    label: NDArray[np.uint8]  # harmonised
    metadata: dict[str, Any]
    masks: dict[str, NDArray[np.uint8]] = field(default_factory=dict)


def read_catalogue(root: Path, bands: Sequence[str]) -> Iterator[Scene]:
    """Sentinel-2 Cloud Mask Catalogue, from the layout of its README (14 October 2026).

    subscenes/<product ID>.npy: 1022 x 1022 x 13 float32 top-of-atmosphere
    reflectance in numerical band order with B8A after B08, already divided by
    10,000; masks/<product ID>.npy: 1022 x 1022 x 3 boolean one-hot CLEAR, CLOUD,
    CLOUD_SHADOW; classification_tags.csv: one row per product with `scene`,
    `difficulty`, `shadows_marked` and the boolean tags. Before a product is
    used, its processing baseline is read from its ID: the README's division by
    10,000 is right only before baseline 04.00, so a later product stops.
    """
    info = dataset("s2_cloud_catalogue")
    codes = info.label_codes
    assert codes is not None
    with (root / "classification_tags.csv").open(newline="", encoding="utf-8") as fh:
        rows = {row["scene"]: row for row in csv.DictReader(fh)}
    positions = [L1C_BAND_NAMES.index(b) for b in bands]
    for scene_id in sorted(rows):
        if s2_needs_offset(scene_id):
            raise DataSourceError(
                f"{scene_id}: processing baseline 04.00 or later; the radiometric offset of "
                "its metadata must be applied before it is used"
            )
        cube = np.load(root / "subscenes" / f"{scene_id}.npy", allow_pickle=False)
        onehot = np.load(root / "masks" / f"{scene_id}.npy", allow_pickle=False)
        if cube.shape[-1] != len(L1C_BAND_NAMES) or onehot.shape[-1] != 3:
            raise DataSourceError(f"{scene_id}: shapes {cube.shape}, {onehot.shape}")
        if not bool((onehot.sum(axis=-1) == 1).all()):
            raise DataSourceError(f"{scene_id}: a mask pixel is not one-hot")
        label = harmonise(onehot.argmax(axis=-1), codes, info.name)
        row = rows[scene_id]
        metadata: dict[str, Any] = {
            "difficulty": row.get("difficulty"),
            "shadows_marked": row.get("shadows_marked"),
            **{tag: row.get(tag) for tag in info.strata_fields},
        }
        yield Scene(
            scene_id,
            {b: cube[..., p].astype(np.float32) for b, p in zip(bands, positions, strict=True)},
            label,
            metadata,
        )


def read_kappaset(root: Path, bands: Sequence[str]) -> Iterator[Scene]:
    """KappaSet sub-tiles of the `test` folder, which also hold the Sen2Cor map (SCL).

    Layout from the README (14 October 2026): kappaset/<month>/ and test/ with
    <tile_x_y.nc> NetCDF files holding the bands B01 to B12 and Label at 10 m,
    and in test also SCL, FMC, SS2C, IDPX and MAJAC. Stops until the band scale,
    the product ID of a sub-tile, the SCL codes and the NetCDF driver are verified.
    """
    require_fact("kappaset", "netcdf_driver")
    scale = require_fact("kappaset", "band_scale")
    require_fact("kappaset", "product_id")
    scl_codes = require_verified(
        "independent.COMPARISON_CODES['reference_sen2cor']", COMPARISON_CODES["reference_sen2cor"]
    )
    raise DataSourceError(
        f"kappaset reader: facts recorded (scale {scale}, SCL {len(scl_codes)} codes); "
        "write the NetCDF read in the pull request that records them"
    )


def read_biome(root: Path, bands: Sequence[str]) -> Iterator[Scene]:
    """L8 Biome scenes: band TIFs, BQA TIF, MTL.txt and the ENVI mask (USGS page)."""
    require_verified(
        "DATASETS['landsat8_biome'].label_codes", DATASETS["landsat8_biome"].label_codes
    )
    require_fact("landsat8_biome", "scene_layout")
    require_fact("landsat8_biome", "biome_of_scene")
    require_fact("landsat8_biome", "qa_bit_layout")
    raise DataSourceError("landsat8_biome reader: write the scene read with the verified layout")


def read_sparcs(root: Path, bands: Sequence[str]) -> Iterator[Scene]:
    """L8 SPARCS subsets: band stack, QA band, MTL.txt and the PNG mask (USGS page)."""
    require_fact("landsat8_sparcs", "scene_layout")
    require_fact("landsat8_sparcs", "band_stack_order")
    require_fact("landsat8_sparcs", "qa_bit_layout")
    raise DataSourceError("landsat8_sparcs reader: write the scene read with the verified layout")


READERS = {
    "s2_cloud_catalogue": read_catalogue,
    "kappaset": read_kappaset,
    "landsat8_biome": read_biome,
    "landsat8_sparcs": read_sparcs,
}


def stored_bands(name: str, requested: Sequence[str]) -> list[str]:
    """The Sentinel-2 band names a dataset can provide, among `requested`."""
    info = dataset(name)
    available = set(LANDSAT8_TO_S2.values()) if info.sensor == LANDSAT8 else set(L1C_BAND_NAMES)
    return [b for b in requested if b in available]


# Independence --------------------------------------------------------------------

# Field of the CloudSEN12+ metadata that holds the Sentinel-2 product ID of a patch.
# TODO(verify) from the survey (reports/data/survey.json, metadata columns).
CLOUDSEN12_PRODUCT_FIELD: str | None = None
# Tile and sensing date in a product ID: ..._YYYYMMDDTHHMMSS_..._T<tile>_...
PRODUCT_TILE_DATE = re.compile(r"_(\d{8})T\d{6}_.*_T(\d{2}[A-Z]{3})_")


def tile_and_date(product_id: str) -> tuple[str, str] | None:
    """(MGRS tile, sensing date) of a Sentinel-2 product ID, or None."""
    require_fact("s2_cloud_catalogue", "product_naming")
    match = PRODUCT_TILE_DATE.search(product_id)
    return (match.group(2), match.group(1)) if match else None


def overlap(
    product_ids: Sequence[str], cloudsen12_metadata: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Products of an independent Sentinel-2 dataset that CloudSEN12+ also uses.

    A product overlaps when its product ID, or its MGRS tile and sensing date,
    appears in any CloudSEN12+ patch of any split. Overlapping products are
    dropped before the build and counted.
    """
    product_field = require_verified(
        "independent.CLOUDSEN12_PRODUCT_FIELD", CLOUDSEN12_PRODUCT_FIELD
    )
    used = {str(m.get(product_field)) for m in cloudsen12_metadata}
    used_tiles = {td for p in used if (td := tile_and_date(p))}
    same_id = sorted(p for p in product_ids if p in used)
    same_tile = sorted(
        p for p in product_ids if p not in used and (td := tile_and_date(p)) and td in used_tiles
    )
    return {
        "products": len(product_ids),
        "same_product": same_id,
        "same_tile_and_date": same_tile,
        "kept": len(product_ids) - len(same_id) - len(same_tile),
    }


def independent_block(name: str, substitution: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The `independent` block of an evaluation report on this dataset."""
    info = dataset(name)
    return {
        "dataset": info.name,
        "sensor": info.sensor,
        "version": info.version,
        "licence": info.licence,
        "has_thin": info.has_thin,
        "has_shadow": info.has_shadow,
        "operational_mask": info.operational_mask,
        "strata_fields": list(info.strata_fields),
        "four_band_equivalent": True,
        "substitution": dict(substitution or {}),
    }
