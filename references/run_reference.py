# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Run a published reference model on a cache split and add its masks to the cache.

    python references/run_reference.py --model <name> --cache <cache> --split val
    python references/run_reference.py --model <name> --cache <cache> --split test \
        --final --reason "<why>"

Reference models are third-party models with their own published weights.
They are run here, outside `src/`, exactly as published: never trained
further and never used to choose anything of Tiefer's own models. Tiefer's
models stay trained from random initialisation (NOTICE.md).

Before a model runs, its licence is read from its primary source and the
maintainer records whether it allows this use (`decision` below, and
docs/DATASETS.md for the record). Until then the script stops and says what
is missing. A model whose runner is not written yet stops too; its runner is
added in a pull request after its licence is cleared, with the class mapping
of its output recorded in docs/ASSUMPTIONS.md.

Reading the test split, even only to compute a reference mask, is logged like
every other use: `--final` and `--reason` append an entry to
`reports/test_log.md` before the test images are read.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import cache
from tiefer_lab.evaluate import TestGuardError, check_test_guard, log_test_evaluation
from tiefer_lab.utils import metadata

Runner = Callable[[cache.SplitData], NDArray[np.uint8]]


@dataclass(frozen=True)
class Reference:
    """A published reference model and what is known about using it."""

    name: str
    source: str
    licence: str | None  # as read on the primary source, or None: TODO(verify)
    decision: str | None  # the maintainer's decision for this use, or None
    kind: str  # "four_class", "cloud" or "probability", the output as stored
    runner: Runner | None = None
    note: str = ""


REFERENCES: dict[str, Reference] = {
    "unetmobv2": Reference(
        "unetmobv2",
        "UNetMobV2 of the CloudSEN12 paper; primary page of the weights TODO(verify)",
        None,
        None,
        "four_class",
        note="CloudSEN12+ ships its mask (cloudmask_unetmobv2_v1); this runner is for the "
        "independent datasets",
    ),
    "s2cloudless": Reference(
        "s2cloudless",
        "s2cloudless, Sentinel Hub; primary page TODO(verify)",
        None,
        None,
        "probability",
        note="CloudSEN12+ ships its probability; this runner is for the independent datasets",
    ),
    "dtacs4bands": Reference(
        "dtacs4bands",
        "https://huggingface.co/isp-uv-es/cloudsen12_models",
        "CC-BY-NC-4.0",
        None,
        "four_class",
        note="non-commercial licence: the maintainer decides before any use",
    ),
    "kappamask_l1c": Reference(
        "kappamask_l1c",
        "KappaMask, KappaZeta; primary page TODO(verify)",
        None,
        None,
        "four_class",
        note="first try the masks of the CloudSEN12 release of 2022 (data/cloudsen12_2022.py)",
    ),
    "kappamask_l2a": Reference(
        "kappamask_l2a",
        "KappaMask, KappaZeta; primary page TODO(verify)",
        None,
        None,
        "four_class",
        note="needs Level-2A input; first try the 2022 release masks",
    ),
    "cd_fcnn_rgbi": Reference(
        "cd_fcnn_rgbi",
        "CD-FCNN, primary page TODO(verify)",
        None,
        None,
        "cloud",
        note="first try the 2022 release masks",
    ),
    "cd_fcnn_rgbiswir": Reference(
        "cd_fcnn_rgbiswir",
        "CD-FCNN, primary page TODO(verify)",
        None,
        None,
        "cloud",
        note="first try the 2022 release masks",
    ),
    "fmask4": Reference(
        "fmask4",
        "Fmask 4, primary page TODO(verify)",
        None,
        None,
        "four_class",
        note="needs product metadata (sun and view angles) that 509 x 509 patches may not have; "
        "may stay not measured",
    ),
}


class ReferenceError(RuntimeError):
    """A reference model cannot run yet."""


def ready(reference: Reference) -> Runner:
    """The runner of a reference whose licence is cleared, or a clear stop."""
    if reference.licence is None:
        raise ReferenceError(
            f"{reference.name}: licence not read yet (TODO(verify)); read it at "
            f"{reference.source} and record it in references/run_reference.py and docs/DATASETS.md"
        )
    if reference.decision is None:
        raise ReferenceError(
            f"{reference.name}: licence {reference.licence}; the maintainer has not recorded "
            f"whether it allows this use ({reference.note or 'see docs/DATASETS.md'})"
        )
    if reference.runner is None:
        raise ReferenceError(f"{reference.name}: no runner yet; it is added after the licence")
    return reference.runner


def run(
    name: str, cache_name: str, split: str, final: bool = False, reason: str | None = None
) -> list[str]:
    """Compute the reference masks of one split and add them to the cache."""
    if name not in REFERENCES:
        raise ReferenceError(f"unknown reference {name!r}; known: {sorted(REFERENCES)}")
    check_test_guard(split, final, reason)
    reference = REFERENCES[name]
    runner = ready(reference)
    directory = cache.cache_dir(cache_name)
    if split == "test":
        commit = metadata.git_commit()["commit"]
        log_test_evaluation(f"reference-{name}", commit, reason or "", "published weights")
    data = cache.load_split(directory, split)
    masks = runner(data)
    cache.add_reference_masks(directory, split, {name: masks}, {name: reference.kind})
    return [name]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python references/run_reference.py")
    parser.add_argument("--model", required=True, choices=sorted(REFERENCES))
    parser.add_argument("--cache", required=True)
    parser.add_argument("--split", required=True, choices=["val", "test"])
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)
    try:
        added = run(args.model, args.cache, args.split, args.final, args.reason)
    except (ReferenceError, TestGuardError, cache.CacheError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"{args.split}: reference masks {', '.join(added)} added", flush=True)
    return 0


def describe() -> list[dict[str, Any]]:
    """Every reference with its licence state, for the README and the tests."""
    return [
        {
            "name": r.name,
            "licence": r.licence or "not read",
            "decision": r.decision or "none",
            "runner": r.runner is not None,
        }
        for r in REFERENCES.values()
    ]


if __name__ == "__main__":
    sys.exit(main())
