# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Every model of the CloudSEN12 paper against every dataset of its Table 1.

    python -m tiefer_lab.paper_models [--models l1_full,l2_flex_1m]

Writes `reports/coverage.md`: one row per model (this repository's own models
and the nine algorithms of the paper's Table 6) and one column per dataset
(CloudSEN12+ and the nine datasets of the paper's Table 1). Each cell says
whether an evaluation report holds that model on that dataset (`measured`)
and, when not, how it is to be measured or why it cannot be:

- `shipped`: the dataset ships the algorithm's mask on the same pixels;
- `release 2022`: the mask of the CloudSEN12 release of 2022, scored on the
  CloudSEN12+ labels of the same pixels (data/cloudsen12_2022.py);
- `run`: the published model is run by `references/run_reference.py` on the
  dataset's cache (with the Landsat 8 band substitution where noted);
- `needs product`: the algorithm needs the full Level-1 product, which the
  dataset does not ship; a download decision of the maintainer;
- `open`: a fact it depends on is not verified yet (`TODO(verify)`);
- `n/a`: it cannot be measured on this dataset, with the reason.

Nothing here is a measured value: the page is built from the report files
and the facts below, and it never reads the data. The algorithms' input
bands are facts of their primary sources, None until read.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tiefer_lab.data import independent
from tiefer_lab.reports import Reports, load_reports
from tiefer_lab.tables import Group, header_block, markdown_table
from tiefer_lab.utils import paths

REPORT = "coverage.md"
CLOUDSEN12 = "cloudsen12"

# The paper's Table 1, in its order: paper name to the registry key of
# data/independent.py. CloudSEN12 itself is the training dataset.
PAPER_DATASETS: Mapping[str, str] = {
    "L8-SPARCS": "landsat8_sparcs",
    "S2-Hollstein": "s2_hollstein",
    "L8-Biome8": "landsat8_biome",
    "L8-38Cloud": "landsat8_38cloud",
    "S2-CESBIO": "s2_cesbio",
    "L8-95Cloud": "landsat8_95cloud",
    "S2-cloudCatalog": "s2_cloud_catalogue",
    "WHUS2-CD": "whus2_cd",
    "KappaZeta": "kappaset",
}
DATASET_COLUMNS: tuple[str, ...] = (CLOUDSEN12, *PAPER_DATASETS.values())

# The paper's Table 6, in its order. Human level is a published agreement of
# annotators, not a model; it stays in docs/LANDSCAPE.md.
PAPER_MODELS: tuple[str, ...] = (
    "unetmobv2",
    "kappamask_l2a",
    "kappamask_l1c",
    "fmask",
    "s2cloudless",
    "sen2cor",
    "qa60",
    "cd_fcnn_rgbi",
    "cd_fcnn_rgbiswir",
)
# This repository's models that every dataset is evaluated with.
OWN_MODELS: tuple[str, ...] = ("l1_full", "l2_flex_1m")


@dataclass(frozen=True)
class Algorithm:
    """What decides where a paper algorithm can be measured."""

    name: str
    # "learned" (a published network or classifier run on the patches),
    # "processor" (needs the full product: Sen2Cor, Fmask) or "product band" (QA60).
    kind: str
    sensors: tuple[str, ...]
    # Sentinel-2 band names the model reads, from its primary source; None: TODO(verify).
    inputs: tuple[str, ...] | None
    # Name of its entry in references/run_reference.py, when it is run there.
    reference: str | None
    level: str = "L1C"
    note: str = ""


S2 = independent.SENTINEL2
L8 = independent.LANDSAT8

ALGORITHMS: Mapping[str, Algorithm] = {
    "unetmobv2": Algorithm("unetmobv2", "learned", (S2,), None, "unetmobv2"),
    "kappamask_l2a": Algorithm(
        "kappamask_l2a", "learned", (S2,), None, "kappamask_l2a", level="L2A"
    ),
    "kappamask_l1c": Algorithm("kappamask_l1c", "learned", (S2,), None, "kappamask_l1c"),
    "fmask": Algorithm(
        "fmask",
        "processor",
        (S2, L8),
        None,
        "fmask4",
        note="needs the product metadata (angles, MTL) and every band",
    ),
    "s2cloudless": Algorithm("s2cloudless", "learned", (S2,), None, "s2cloudless"),
    "sen2cor": Algorithm("sen2cor", "processor", (S2,), None, None),
    "qa60": Algorithm("qa60", "product band", (S2,), None, None),
    "cd_fcnn_rgbi": Algorithm("cd_fcnn_rgbi", "learned", (S2,), None, "cd_fcnn_rgbi"),
    "cd_fcnn_rgbiswir": Algorithm("cd_fcnn_rgbiswir", "learned", (S2,), None, "cd_fcnn_rgbiswir"),
}

# Report names of the masks CloudSEN12+ ships (data/source.py, REFERENCE_MASK_NAMES)
# and of the 2022 release masks (data/cloudsen12_2022.py, MASKS).
CLOUDSEN12_SHIPPED: Mapping[str, str] = {
    "unetmobv2": "reference_cloudmask_unetmobv2_v1",
    "s2cloudless": "reference_cloudmask_s2cloudless",
    "sen2cor": "reference_cloudmask_sen2cor",
    "qa60": "reference_cloudmask_qa60",
}
RELEASE_2022_PREFIX = "reference_2022_"


@dataclass(frozen=True)
class Route:
    """How one algorithm is measured on one dataset."""

    kind: str  # shipped, release 2022, run, needs product, open, n/a
    report_name: str | None  # the key under `baselines` of an evaluation report
    reason: str


def _dataset_bands(name: str) -> tuple[str, ...] | None:
    """Sentinel-2 band names a dataset provides (Landsat bands under their matched names)."""
    info = independent.dataset(name)
    return info.bands


def route(model: str, dataset: str) -> Route:
    """The route of a paper algorithm on a dataset, from the facts of both."""
    algo = ALGORITHMS[model]
    if dataset == CLOUDSEN12:
        if model in CLOUDSEN12_SHIPPED:
            return Route("shipped", CLOUDSEN12_SHIPPED[model], "mask shipped with CloudSEN12+")
        return Route(
            "release 2022",
            RELEASE_2022_PREFIX + model,
            "mask of the 2022 release on the same pixels (references/add_release_2022.py)",
        )
    info = independent.dataset(dataset)
    shipped = independent.SHIPPED_MASKS.get(dataset, {})
    if model in shipped:
        return Route("shipped", f"reference_{model}", f"the dataset ships it ({shipped[model]})")
    if info.sensor not in algo.sensors and algo.kind != "learned":
        counterpart = (
            "; the Landsat quality band is the operational counterpart (reference_landsat_qa)"
            if model == "qa60"
            else ""
        )
        return Route("n/a", None, f"a {', '.join(algo.sensors)} algorithm{counterpart}")
    if algo.kind == "product band":
        return Route(
            "needs product",
            None,
            "the QA60 band of the Level-1C product; the dataset does not ship it",
        )
    if algo.kind == "processor":
        if dataset in independent.FULL_PRODUCT:
            return Route(
                "run",
                f"reference_{algo.reference}",
                f"{algo.note}; the dataset ships them",
            )
        return Route(
            "needs product",
            None,
            f"{algo.note or 'needs the full Level-1C product'}; the dataset does not ship them",
        )
    if algo.level != "L1C":
        return Route("n/a", None, f"needs {algo.level} input; the dataset is Level-1C")
    bands = _dataset_bands(dataset)
    if algo.inputs is None or bands is None:
        missing = [
            what
            for what, value in (("its input bands", algo.inputs), ("the dataset's bands", bands))
            if value is None
        ]
        return Route("open", None, f"{' and '.join(missing)} not verified (TODO(verify))")
    available = set(bands) | {
        k for k, v in independent.SUBSTITUTIONS.get(info.sensor, {}).items() if v in bands
    }
    lacking = [b for b in algo.inputs if b not in available]
    if lacking:
        return Route("n/a", None, f"the dataset lacks {', '.join(lacking)}")
    swaps = independent.SUBSTITUTIONS.get(info.sensor, {})
    substituted = [k for k in algo.inputs if k not in bands and k in swaps]
    note = f" with {', '.join(substituted)} substituted" if substituted else ""
    return Route("run", f"reference_{algo.reference}", f"published model run on the cache{note}")


def _source(report_data: Mapping[str, object]) -> str:
    data = report_data.get("data")
    source = data.get("source") if isinstance(data, dict) else None
    return str(source or CLOUDSEN12)


def measured(
    reports: Reports, splits: Sequence[str] = ("test", "independent")
) -> dict[tuple[str, str], list[str]]:
    """{(model or report name, dataset): [report files]} of the evaluations held."""
    out: dict[tuple[str, str], list[str]] = {}
    for r in reports.evaluation:
        if r.data.get("split") not in splits:
            continue
        dataset = _source(r.data)
        config = r.data.get("config")
        name = config.get("name") if isinstance(config, dict) else None
        if name:
            out.setdefault((str(name), dataset), []).append(r.source)
        baselines = r.data.get("baselines")
        for key in baselines if isinstance(baselines, dict) else {}:
            out.setdefault((str(key), dataset), []).append(r.source)
    return out


def cell(model: str, dataset: str, held: Mapping[tuple[str, str], list[str]]) -> str:
    """The text of one cell: measured, or the route and its reason."""
    if model not in ALGORITHMS:
        if (model, dataset) in held:
            return "measured"
        return "not measured: `evaluate --data` (test split: maintainer, FINAL=1)"
    r = route(model, dataset)
    if r.report_name and (r.report_name, dataset) in held:
        return "measured"
    return f"{r.kind}: {r.reason}"


def render(reports: Reports, date: dt.date, own: Sequence[str] = OWN_MODELS) -> str:
    held = measured(reports)
    names = {CLOUDSEN12: "CloudSEN12+ (test)"} | {v: k for k, v in PAPER_DATASETS.items()}
    blocks = [
        header_block(
            "Coverage",
            "in development",
            "Every model of this repository and every algorithm of the CloudSEN12 paper's "
            "Table 6 against CloudSEN12+ and the nine datasets of the paper's Table 1, built by "
            "`python -m tiefer_lab.paper_models` from the report files and the dataset facts; "
            "do not edit it by hand. It holds no metric value: the values are in "
            "reports/comparison.md.",
            "../docs/assets/header.png",
        )
    ]
    for number, (title, models) in enumerate(
        (("Models of this repository", list(own)), ("Algorithms of the paper", PAPER_MODELS)),
        start=1,
    ):
        rows = [[model, *(cell(model, d, held) for d in DATASET_COLUMNS)] for model in models]
        table = markdown_table(["", *(names[d] for d in DATASET_COLUMNS)], [Group("", rows)])
        blocks.append(f"\n## {number}. {title}\n\n{table}\n")
    total = len(DATASET_COLUMNS) * (len(own) + len(PAPER_MODELS))
    done = sum(
        cell(m, d, held) == "measured" for m in (*own, *PAPER_MODELS) for d in DATASET_COLUMNS
    )
    when = f"{date.day} {date:%B %Y}"
    blocks.append(
        f"\n## 3. Count\n\n{done} of {total} cells are measured.\n"
        f"\n---\n\n## Changelog\n\n- {when}: generated from "
        f"{len(reports.evaluation)} evaluation reports.\n"
    )
    return "".join(blocks)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.paper_models")
    parser.add_argument("--models", default=",".join(OWN_MODELS))
    args = parser.parse_args(argv)
    reports = load_reports(paths.reports_dir())
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    own = [m for m in args.models.split(",") if m]
    out.write_text(render(reports, dt.date.today(), own), encoding="utf-8")
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
