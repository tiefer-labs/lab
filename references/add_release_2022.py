# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Add the masks of the CloudSEN12 release of 2022 to a CloudSEN12+ cache split.

    python references/add_release_2022.py --root <release folder> --cache <cache> \
        --split val [--mask kappamask_l1c ...]
    python references/add_release_2022.py ... --split test --final --reason "<why>"

The release holds the masks of six of the paper's algorithms on the 2022
patches (Fmask, KappaMask L1C and L2A, CD-FCNN-RGBI and RGBISWIR, and the
Sen2Cor, QA60 and s2cloudless masks also shipped with CloudSEN12+). They are
added under the names `2022_<mask>`, so a report scores them as
`reference_2022_<mask>`, always against the CloudSEN12+ labels of the same
pixels (src/tiefer_lab/data/cloudsen12_2022.py).

The script stops until the release's licence decision (CC BY-NC 4.0), its
file layout, the link fields and the encodings are verified. Reading the test
split is logged like every other use.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tiefer_lab.data import cache, cloudsen12_2022
from tiefer_lab.data.source import DataSourceError
from tiefer_lab.evaluate import TestGuardError, check_test_guard, log_test_evaluation
from tiefer_lab.utils import metadata

PREFIX = "2022_"


def add(
    root: Path,
    cache_name: str,
    split: str,
    masks: Sequence[str],
    final: bool = False,
    reason: str | None = None,
) -> list[str]:
    check_test_guard(split, final, reason)
    cloudsen12_2022.check_ready(masks)
    if split == "test":
        commit = metadata.git_commit()["commit"]
        log_test_evaluation("release-2022-masks", commit, reason or "", "published masks")
    cache.read_index(cache.cache_dir(cache_name))
    raise DataSourceError(
        f"{root}: facts recorded; write the read of {', '.join(masks)} in the pull request "
        "that records them (cloudsen12_2022.MASK_FILES)"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python references/add_release_2022.py")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--split", required=True, choices=["val", "test"])
    parser.add_argument("--mask", action="append", choices=cloudsen12_2022.MASKS)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)
    try:
        added = add(
            args.root,
            args.cache,
            args.split,
            args.mask or cloudsen12_2022.MASKS,
            args.final,
            args.reason,
        )
    except (DataSourceError, TestGuardError, cache.CacheError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"{args.split}: masks {', '.join(PREFIX + m for m in added)} added", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
