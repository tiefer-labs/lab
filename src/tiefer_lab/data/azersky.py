# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Azersky (SPOT 7, operated by Azercosmos): a candidate dataset with no data yet.

Status: candidate, no data, no licence decision. Its terms will come from a
data agreement with Azercosmos that the maintainer records in `DECISION`;
until then nothing of it is read, and nothing is ever downloaded: this module
holds no file record and no URL to fetch.

Every fact the reader needs is None until it is verified from a primary
source, and the reader stops on the first one that is not, naming the source
that resolves it (`FACTS`). Nothing is guessed: not the product format, the
band list and order, the scaling to top-of-atmosphere reflectance, the ground
sampling distance or whether labels exist.

Decisions recorded in docs/ASSUMPTIONS.md:

- `A-2.10`: the resolution difference is handled by the existing path of the
  independent datasets: a scene is resampled from its verified ground
  sampling to 10 m (`tiefer_lab.data.independent.resample`), and the native
  resolution is evaluated only as the `rescale` perturbation;
- `A-2.11`: labels are made by Tiefer from scratch, not by correcting the
  output of any model, in the class scheme of CloudSEN12 (clear, thick cloud,
  thin cloud, cloud shadow).

Use: evaluation on the CPU only, conditional on data arriving
(hpc/roihu/plan.md, section 3.9); it could serve as the third sensor of
`IND-01`.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from tiefer_lab.data.independent import Scene
from tiefer_lab.data.source import (
    CLEAR,
    CLOUD_SHADOW,
    THICK_CLOUD,
    THIN_CLOUD,
    DataSourceError,
    LicenceDecision,
    require_allowed,
)

NAME = "azersky"
SENSOR = "SPOT 7"
OPERATOR = "Azercosmos"
STATUS = "candidate, no data, no licence decision"
# No decision: the terms come from a data agreement with Azercosmos that the
# maintainer records here, with its date. Until then the source is not read.
DECISION = LicenceDecision("no decision", reason="terms from a data agreement with Azercosmos")
# The class scheme of the labels Tiefer will make (A-2.11): CloudSEN12's.
LABEL_CLASSES = {
    "clear": CLEAR,
    "thick cloud": THICK_CLOUD,
    "thin cloud": THIN_CLOUD,
    "cloud shadow": CLOUD_SHADOW,
}


@dataclass(frozen=True)
class Fact:
    """One fact the reader needs: its value once verified, and what verifies it."""

    value: object | None
    resolves: str
    # What is said about it before verification; never used as a value.
    unverified: str = ""


FACTS: dict[str, Fact] = {
    "product_format": Fact(
        None,
        "the product documentation that comes with the data from Azercosmos, or the SPOT 6/7 "
        "user guide of Airbus",
        "Airbus SPOT 6/7 products are said to be JPEG 2000 with DIMAP metadata; not verified",
    ),
    "bands": Fact(
        None,
        "the DIMAP metadata of a delivered product: band names, wavelengths and their order "
        "in the file",
    ),
    "toa_scaling": Fact(
        None,
        "the DIMAP metadata of a delivered product: gain, bias and solar irradiance per band, "
        "and the formula of the product documentation",
    ),
    "gsd_m": Fact(
        None,
        "the DIMAP metadata of a delivered product (ground sampling of the multispectral bands)",
        "6 m multispectral is the stated value; not verified",
    ),
    "labels": Fact(
        None,
        "the data agreement with Azercosmos and the delivery: whether any labels come with "
        "it; Tiefer's own labels are made from scratch (A-2.11)",
    ),
}


def require_fact(name: str) -> object:
    """Stop on a fact that is not verified, naming the source that resolves it."""
    fact = FACTS[name]
    if fact.value is None:
        said = f" ({fact.unverified})" if fact.unverified else ""
        raise DataSourceError(
            f"{NAME}: {name} is not verified yet (TODO(verify)){said}; it is resolved by "
            f"{fact.resolves}, then recorded in FACTS of src/tiefer_lab/data/azersky.py"
        )
    return fact.value


def read_azersky(root: Path, bands: Sequence[str]) -> Iterator[Scene]:
    """Azersky scenes; stops until the decision is recorded and every fact is verified."""
    require_allowed(NAME, DECISION)
    for name in FACTS:
        require_fact(name)
    raise DataSourceError(f"{NAME} reader: write the scene read with the verified facts")
