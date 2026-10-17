# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Run a published reference model on a cache split and add its masks to the cache.

    python references/run_reference.py --model <name> --cache <cache> --split val
    python references/run_reference.py --model <name> --cache <cache> --split test \
        --final --reason "<why>"
    python references/run_reference.py --model <name> --data <independent cache> \
        --reason "<why>"

Reference models are third-party models with their own published weights.
They are run here, outside `src/`, exactly as published: never trained
further and never used to choose anything of Tiefer's own models. Tiefer's
models stay trained from random initialisation (NOTICE.md).

Before a model runs, the licences of its code and of its weights are read
from their primary sources, and the maintainer records whether they allow this
use. The record of every model is `REFERENCES` of
src/tiefer_lab/reference_models.py (licences, decision, files); until it is
complete the script stops and says what is missing. A model whose runner is
not written yet stops too; its runner is added in a pull request after its
licence is cleared, with the class mapping of its output recorded in
docs/ASSUMPTIONS.md.

Reading the test split, even only to compute a reference mask, is logged like
every other use: `--final` and `--reason` append an entry to
`reports/test_log.md` before the test images are read.

`--data` runs the model on an independent dataset cache (`build_cache
--source`), the path of `evaluate --data`: it reads that cache only (a
CloudSEN12+ cache, whose test split stays behind `--final`, is refused), needs
`--reason`, logs the use in `reports/test_log.md` before the tiles are read,
and adds the masks to the cache, where `evaluate --data --baselines` scores
them. It never selects, tunes or trains anything.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tiefer_lab.data import cache, independent
from tiefer_lab.data.source import DataSourceError
from tiefer_lab.evaluate import TestGuardError, check_test_guard, log_test_evaluation
from tiefer_lab.reference_models import REFERENCES, Reference
from tiefer_lab.utils import metadata

# The runners (runners.py, cd_fcnn.py) sit next to this script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runners import Runner, RunnerError, runners


def allowed_references() -> list[str]:
    """The references whose licence decision does not refuse them."""
    return sorted(n for n, r in REFERENCES.items() if not r.decision.refused)


class ReferenceError(RuntimeError):
    """A reference model cannot run yet."""


def ready(reference: Reference) -> Runner:
    """The runner of a reference whose licence is cleared, or a clear stop."""
    if reference.decision.refused:
        raise ReferenceError(f"{reference.name} is {reference.decision.describe()}")
    if reference.licence is None:
        raise ReferenceError(
            f"{reference.name}: licence not read yet (TODO(verify)); read it at "
            f"{reference.source} and record it in src/tiefer_lab/reference_models.py and "
            "references/README.md"
        )
    if reference.weights_licence is None:
        raise ReferenceError(
            f"{reference.name}: no licence is stated for its weights; the model stops until "
            "one is read and recorded in src/tiefer_lab/reference_models.py"
        )
    if reference.decision.status != "used":
        raise ReferenceError(
            f"{reference.name}: licence {reference.licence}; the maintainer has not recorded "
            f"whether it allows this use ({reference.note or 'see docs/DATASETS.md'})"
        )
    runner = runners().get(reference.name)
    if runner is None:
        raise ReferenceError(f"{reference.name}: no runner yet; it is added after the licence")
    return runner


def _reference(name: str) -> Reference:
    if name not in REFERENCES:
        raise ReferenceError(f"unknown reference {name!r}; known: {sorted(REFERENCES)}")
    return REFERENCES[name]


def run(
    name: str, cache_name: str, split: str, final: bool = False, reason: str | None = None
) -> list[str]:
    """Compute the reference masks of one CloudSEN12+ split and add them to the cache."""
    reference = _reference(name)
    check_test_guard(split, final, reason)
    runner = ready(reference)
    directory = cache.cache_dir(cache_name)
    if cache.read_index(directory).get("independent"):
        raise ReferenceError(f"{cache_name} is an independent dataset cache: use --data")
    if split == "test":
        commit = metadata.git_commit()["commit"]
        log_test_evaluation(f"reference-{name}", commit, reason or "", "published weights")
    data = cache.load_split(directory, split, bands=runner.bands)
    masks = runner.run(data)
    cache.add_reference_masks(directory, split, {name: masks}, {name: reference.kind})
    return [name]


def run_independent(name: str, data_cache: str, reason: str | None) -> list[str]:
    """Compute the reference masks of an independent dataset cache; the use is logged."""
    reference = _reference(name)
    if not (reason and reason.strip()):
        raise TestGuardError(
            "an independent dataset is a clean check: --data needs --reason, and the run "
            "is logged like a use of the test split"
        )
    runner = ready(reference)
    directory = cache.cache_dir(data_cache)
    index = cache.read_index(directory)
    if not index.get("independent"):
        raise ReferenceError(
            f"{data_cache} is not an independent dataset cache; a CloudSEN12+ split is run "
            "with --cache and --split, and its test split only with --final"
        )
    source = str(index.get("source"))
    independent.require_dataset_allowed(source)
    commit = metadata.git_commit()["commit"]
    log_test_evaluation(
        f"reference-{name}", commit, f"independent dataset {source}: {reason}", "published weights"
    )
    data = cache.load_independent(directory, runner.bands)
    masks = runner.run(data)
    cache.add_reference_masks(
        directory, cache.INDEPENDENT_SPLIT, {name: masks}, {name: reference.kind}
    )
    return [name]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python references/run_reference.py")
    parser.add_argument("--model", required=True, choices=allowed_references())
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--cache", help="a CloudSEN12+ cache, with --split")
    where.add_argument("--data", help="an independent dataset cache, with --reason (logged)")
    parser.add_argument("--split", choices=["val", "test"])
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)
    if args.data and (args.split or args.final):
        parser.error("--data runs the whole independent dataset; leave out --split and --final")
    if args.cache and not args.split:
        parser.error("--cache needs --split")
    try:
        if args.data:
            added = run_independent(args.model, args.data, args.reason)
            where_text = f"{args.data} ({cache.INDEPENDENT_SPLIT})"
        else:
            added = run(args.model, args.cache, args.split, args.final, args.reason)
            where_text = args.split
    except (ReferenceError, RunnerError, TestGuardError, cache.CacheError, DataSourceError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"{where_text}: reference masks {', '.join(added)} added", flush=True)
    return 0


def describe() -> list[dict[str, Any]]:
    """Every reference with its licence state, for the README and the tests."""
    return [
        {
            "name": r.name,
            "licence": r.licence or "not read",
            "decision": r.decision.status,
            "runner": r.name in runners(),
        }
        for r in REFERENCES.values()
    ]


if __name__ == "__main__":
    sys.exit(main())
