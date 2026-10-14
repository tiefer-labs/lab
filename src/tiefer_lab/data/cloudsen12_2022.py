# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Reference masks of the CloudSEN12 release of 2022, linked to CloudSEN12+ patches.

The 2022 release (Science Data Bank, https://doi.org/10.57760/sciencedb.06669)
holds, per image patch, a `labels/` folder with the masks of fmask, QA60,
s2cloudless, sen2cor, CD-FCNN-RGBI, CD-FCNN-RGBISWIR, kappamask_L1C and
kappamask_L2A next to the manual labels (CloudSEN12, Scientific Data 9, 782,
2022, Table 2, read on 14 October 2026). Fmask, KappaMask and the CD-FCNN
models are not in the extra table of CloudSEN12+, so this release is the
only way to score them on the same pixels without running them.

Before any mask is read, four facts must be verified, each with its source:

1. the licence allows the use: the record page gives CC BY-NC 4.0 (read on
   14 October 2026), a non-commercial licence; Tiefer is a company, so the
   maintainer decides (`LICENCE_DECISION`);
2. the file layout and the item name of every mask (`MASK_FILES`);
3. the link of a 2022 patch to a CloudSEN12+ patch (`LINK_FIELDS`, for
   example `old_roi_id` and the Sentinel-2 product ID); patches that do not
   link one to one are dropped and counted;
4. the encoding of every mask (`ENCODINGS`), from the paper's Table 5 read in
   the PDF and the value histograms of a survey of the files; codes Table 5
   does not list (for example Sen2Cor no data, saturated, unclassified) are
   decisions recorded in docs/ASSUMPTIONS.md before use.

The labels of CloudSEN12+ were refined in version 1.1.0, so a 2022 mask is
scored against the CloudSEN12+ labels of the same pixels, never against the
2022 labels; every report says so.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data.source import DataSourceError, MaskEncoding, encode_mask, require_verified

RELEASE_DOI = "https://doi.org/10.57760/sciencedb.06669"
# Licence on the record page, read on 14 October 2026.
RELEASE_LICENCE = "CC-BY-NC-4.0"
# The maintainer's decision whether the non-commercial licence allows this use.
# TODO(verify): None until the maintainer records it in docs/DATASETS.md.
LICENCE_DECISION: str | None = None

# Masks of the labels/ folder (paper, Table 2), by the name used in reports.
MASKS: tuple[str, ...] = (
    "fmask",
    "qa60",
    "s2cloudless",
    "sen2cor",
    "cd_fcnn_rgbi",
    "cd_fcnn_rgbiswir",
    "kappamask_l1c",
    "kappamask_l2a",
)
# {report name: file or item name in the release}. TODO(verify) from the release files.
MASK_FILES: Mapping[str, str] = {}
# Fields that link a 2022 patch to one CloudSEN12+ patch. TODO(verify) from both
# metadata tables; CloudSEN12+ keeps the previous identifier as `old_roi_id`.
LINK_FIELDS: tuple[str, ...] | None = None
# {report name: encoding}. TODO(verify) from Table 5 of the paper (PDF) and the survey.
ENCODINGS: Mapping[str, MaskEncoding] = {}

LABEL_NOTE = (
    "mask of the CloudSEN12 release of 2022, scored against the CloudSEN12+ labels of the "
    "same pixels; the labels were refined in CloudSEN12+ 1.1.0"
)


def check_ready(names: Sequence[str] = MASKS) -> None:
    """Stop with a clear message unless every fact needed for `names` is verified."""
    require_verified("cloudsen12_2022.LICENCE_DECISION", LICENCE_DECISION)
    require_verified("cloudsen12_2022.LINK_FIELDS", LINK_FIELDS)
    for name in names:
        if name not in MASKS:
            raise DataSourceError(f"{name!r} is not a mask of the 2022 release {MASKS}")
        require_verified(f"cloudsen12_2022.MASK_FILES[{name!r}]", MASK_FILES.get(name))
        require_verified(f"cloudsen12_2022.ENCODINGS[{name!r}]", ENCODINGS.get(name))


def link(
    old: Sequence[Mapping[str, Any]], new: Sequence[Mapping[str, Any]]
) -> tuple[dict[int, int], dict[str, int]]:
    """{position in `new`: position in `old`} for patches that link one to one.

    A key of the link fields that appears more than once on either side, or on
    one side only, is dropped and counted; nothing is matched by guess.
    """
    fields = require_verified("cloudsen12_2022.LINK_FIELDS", LINK_FIELDS)

    def keys(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, ...], list[int]]:
        out: dict[tuple[str, ...], list[int]] = {}
        for i, row in enumerate(rows):
            out.setdefault(tuple(str(row.get(f)) for f in fields), []).append(i)
        return out

    old_keys, new_keys = keys(old), keys(new)
    pairs = {
        n[0]: o[0]
        for k, n in new_keys.items()
        if len(n) == 1 and (o := old_keys.get(k)) is not None and len(o) == 1
    }
    counts = {
        "linked": len(pairs),
        "new_without_old": sum(len(v) for k, v in new_keys.items() if k not in old_keys),
        "ambiguous": sum(
            len(v) for k, v in new_keys.items() if len(v) > 1 or len(old_keys.get(k, [])) > 1
        ),
    }
    return pairs, counts


def encode(name: str, raw: NDArray[np.integer[Any]]) -> NDArray[np.uint8]:
    """Encode a raw mask of the release with its verified encoding."""
    check_ready((name,))
    return encode_mask(raw, ENCODINGS[name], f"2022 {name}")
