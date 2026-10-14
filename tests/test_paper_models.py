# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Every paper algorithm and own model has a defined route on every Table 1 dataset."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from tiefer_lab import paper_models
from tiefer_lab.data import independent
from tiefer_lab.data.source import DataSourceError
from tiefer_lab.reports import Report, Reports

KINDS = {"shipped", "release 2022", "run", "needs product", "open", "n/a"}


def test_all_nine_table_1_datasets_are_registered_with_a_reader() -> None:
    assert len(paper_models.PAPER_DATASETS) == 9
    assert set(paper_models.PAPER_DATASETS.values()) == set(independent.DATASETS)
    assert set(independent.READERS) == set(independent.DATASETS)
    assert len(paper_models.PAPER_MODELS) == 9
    assert set(paper_models.PAPER_MODELS) == set(paper_models.ALGORITHMS)


def test_every_cell_has_a_route_with_a_reason() -> None:
    for model in paper_models.PAPER_MODELS:
        for dataset in paper_models.DATASET_COLUMNS:
            r = paper_models.route(model, dataset)
            assert r.kind in KINDS and r.reason
            assert (r.report_name is not None) == (r.kind in {"shipped", "release 2022", "run"})


def test_routes_by_hand() -> None:
    route = paper_models.route
    assert route("sen2cor", "cloudsen12").report_name == "reference_cloudmask_sen2cor"
    assert route("fmask", "cloudsen12").report_name == "reference_2022_fmask"
    assert route("sen2cor", "kappaset").kind == "shipped"
    assert route("sen2cor", "landsat8_biome").kind == "n/a"
    assert "reference_landsat_qa" in route("qa60", "landsat8_sparcs").reason
    assert route("qa60", "s2_cloud_catalogue").kind == "needs product"
    assert route("fmask", "landsat8_biome").kind == "run"
    assert route("kappamask_l2a", "s2_cloud_catalogue").kind == "n/a"
    # Input bands of the learned models are not verified yet: open, never guessed.
    assert route("unetmobv2", "s2_cloud_catalogue").kind == "open"
    assert route("unetmobv2", "landsat8_95cloud").kind == "open"
    assert route("fmask", "s2_cesbio").kind == "needs product"
    hollstein = paper_models.cell("l1_full", "s2_hollstein", {})
    assert hollstein.startswith("needs product")


def test_unread_datasets_stop(tmp_path: Path) -> None:
    for name in (*independent.PAPER_ONLY, "landsat8_38cloud", "landsat8_95cloud", "whus2_cd"):
        with pytest.raises(DataSourceError, match="not verified yet"):
            list(independent.READERS[name](tmp_path, ["B02"]))


def _report(source: str, config: str, baselines: dict[str, object]) -> Report:
    return Report(
        Path("evaluation/x.json"),
        {
            "split": "independent",
            "data": {"source": source},
            "config": {"name": config},
            "baselines": baselines,
        },
    )


def test_coverage_page_counts_measured_cells() -> None:
    empty = paper_models.render(Reports(), dt.date(2026, 10, 14))
    assert "0 of 110 cells are measured" in empty
    for paper_name in paper_models.PAPER_DATASETS:
        assert paper_name in empty
    reports = Reports(evaluation=[_report("kappaset", "l1_full", {"reference_sen2cor": {}})])
    page = paper_models.render(reports, dt.date(2026, 10, 14))
    assert "2 of 110 cells are measured" in page


def test_evaluate_all_lists_every_dataset(repo_root: Path) -> None:
    text = (repo_root / "hpc" / "roihu" / "evaluate_all.sh").read_text(encoding="utf-8")
    block = re.search(r"datasets=\(\n(.*?)\n\)", text, re.S)
    assert block is not None
    assert block.group(1).split() == list(paper_models.PAPER_DATASETS.values())
