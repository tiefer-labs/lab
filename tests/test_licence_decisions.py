# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Licence decisions of 15 October 2026: refused sources stop and leave every default list."""

from __future__ import annotations

import dataclasses
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from tiefer_lab import calibrate, compare, diagnose, evaluate, paper_models, train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache, cache, cloudsen12_2022, independent
from tiefer_lab.data.source import (
    NO_DECISION,
    DataSourceError,
    LicenceDecision,
    LicenceRefusedError,
)
from tiefer_lab.reports import Report, Reports

REFUSED = (
    "s2_hollstein",
    "landsat8_38cloud",
    "landsat8_95cloud",
    "s2_cesbio",
    "whus2_cd",
    "landsat8_biome",
    "landsat8_sparcs",
)
USED = ("s2_cloud_catalogue", "kappaset")


def test_the_decisions_are_recorded_next_to_the_facts() -> None:
    for name in REFUSED:
        decision = independent.DATASETS[name].decision
        assert decision.refused and decision.date == "15 October 2026"
        assert decision.reason
    for name in ("whus2_cd", "landsat8_biome", "landsat8_sparcs"):
        assert independent.DATASETS[name].decision.status == "candidate, no decision yet"
    assert independent.PRODUCT_IMAGERY.status == "not used"
    assert cloudsen12_2022.LICENCE_DECISION.status == "declined, pending legal review"
    for name in USED:
        decision = independent.DATASETS[name].decision
        assert decision.status == "used" and decision.licence == "CC BY 4.0"
    assert independent.allowed_datasets() == list(USED)
    # Every dataset has a record: none is left at "no decision".
    assert all(i.decision.status != "no decision" for i in independent.DATASETS.values())


def test_a_dataset_without_a_record_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    info = independent.DATASETS["s2_cloud_catalogue"]
    monkeypatch.setitem(
        independent.DATASETS, "s2_cloud_catalogue", dataclasses.replace(info, decision=NO_DECISION)
    )
    assert "s2_cloud_catalogue" not in independent.allowed_datasets()
    with pytest.raises(LicenceRefusedError, match="no licence decision"):
        list(independent.READERS["s2_cloud_catalogue"](tmp_path, ["B02"]))


def test_every_refused_source_raises(tmp_path: Path) -> None:
    for name in REFUSED:
        with pytest.raises(LicenceRefusedError, match="15 October 2026"):
            list(independent.READERS[name](tmp_path, ["B02"]))
        with pytest.raises(LicenceRefusedError, match=independent.DATASETS[name].decision.status):
            build_cache.build_independent(tmp_path / name, name, tmp_path, ["B02"])
    with pytest.raises(LicenceRefusedError, match="declined, pending legal review"):
        cloudsen12_2022.check_ready()
    # The message names the decision's issue.
    with pytest.raises(LicenceRefusedError, match="issue 7"):
        list(independent.READERS["s2_cesbio"](tmp_path, ["B02"]))


def test_a_cache_of_a_refused_dataset_is_never_evaluated(tmp_path: Path) -> None:
    directory = tmp_path / "s2_cesbio"
    directory.mkdir()
    index = {
        "format": cache.CACHE_FORMAT,
        "source": "s2_cesbio",
        "independent": {"dataset": "s2_cesbio"},
        "splits": {},
    }
    (directory / cache.INDEX_NAME).write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(LicenceRefusedError):
        cache.load_independent(directory, ["B02"])


def test_refused_sources_leave_every_default_list(repo_root: Path) -> None:
    allowed = independent.allowed_datasets()
    columns = paper_models.dataset_columns()
    for name in REFUSED:
        assert name not in allowed and name not in columns
    with pytest.raises(SystemExit):
        build_cache.main(["--split", "test", "--source", "s2_cesbio", "--root", "x"])
    for script in ("independent.sbatch", "evaluate_all.sh"):
        text = (repo_root / "hpc" / "roihu" / script).read_text(encoding="utf-8")
        for name in REFUSED:
            assert name not in text, (script, name)
    page = paper_models.render(Reports(), dt.date(2026, 10, 15))
    headers = [line for line in page.splitlines() if line.startswith("|  |")]
    assert headers
    for paper_name, name in paper_models.PAPER_DATASETS.items():
        for header in headers:
            assert (paper_name in header) == (name in allowed)
    # The omission is visible: one note names each left-out dataset and links the decisions.
    note = next(line for line in page.splitlines() if line.startswith("Left out by licence"))
    for paper_name, name in paper_models.PAPER_DATASETS.items():
        assert (paper_name in note) == (name not in allowed)
    assert "../docs/DATASETS.md" in note and "section 1.1" in note


def _report(source: str, baselines: dict[str, object]) -> Report:
    return Report(
        Path("evaluation/x.json"),
        {
            "split": "independent",
            "data": {"source": source},
            "config": {"name": "sieb"},
            "model": {},
            "baselines": baselines,
        },
    )


def test_comparison_and_coverage_drop_refused_rows() -> None:
    reports = Reports(
        evaluation=[
            _report("s2_cesbio", {}),
            _report("kappaset", {"reference_2022_fmask": {}, "reference_sen2cor": {}}),
        ]
    )
    groups = compare.collect_rows(reports)
    assert [k[1] for k in groups] == ["kappaset"]
    assert [r.name for r in groups[("independent", "kappaset", "none")]] == [
        "sieb",
        "reference_sen2cor",
    ]
    held = paper_models.measured(reports)
    assert ("sieb", "s2_cesbio") not in held
    assert ("reference_2022_fmask", "kappaset") not in held
    page = paper_models.render(reports, dt.date(2026, 10, 15))
    assert all("S2-CESBIO" not in line for line in page.splitlines() if line.startswith("|"))


def test_only_a_changed_record_changes_a_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = independent.DATASETS["landsat8_95cloud"]
    monkeypatch.setitem(
        independent.DATASETS,
        "landsat8_95cloud",
        dataclasses.replace(info, decision=LicenceDecision("used", "CC0")),
    )
    assert "landsat8_95cloud" in independent.allowed_datasets()
    assert "landsat8_95cloud" in paper_models.dataset_columns()
    # Allowed now, it stops on the next fact that is not verified, not on the licence.
    with pytest.raises(DataSourceError, match="not verified yet") as err:
        list(independent.READERS["landsat8_95cloud"](tmp_path, ["B02"]))
    assert not isinstance(err.value, LicenceRefusedError)


# Every reader of a cache split: a cache of a dataset that is not allowed is never read.


def _tiny_run(runs: Path) -> Path:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    raw = {
        "name": "tiny",
        "data": {
            "cache_name": "synthetic",
            "crop_size": 32,
            "batch_size": 4,
            "eval_batch_size": 2,
            "num_workers": 0,
        },
        "model": {"widths": [8, 16]},
        "train": {"epochs": 1, "max_steps_per_epoch": 1, "log_every": 1},
        "evaluation": {"bootstrap_resamples": 100},
    }
    run = runs / "tiny-seed0-x"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    return run


def _mark_as_independent(name: str, dataset: str) -> None:
    """Turn a built cache into one of an independent dataset, as an old cache could be."""
    directory = cache.cache_dir(name)
    index = cache.read_index(directory)
    index["source"] = dataset
    index["independent"] = {"dataset": dataset}
    cache.write_index(directory, index)


@pytest.fixture
def refused_cache_run(tiefer_env: dict[str, Path]) -> Path:
    run = _tiny_run(tiefer_env["TIEFER_RUNS_DIR"])
    _mark_as_independent("synthetic", "s2_cesbio")
    return run


def test_load_split_refuses_a_cache_of_a_dataset_not_allowed(refused_cache_run: Path) -> None:
    with pytest.raises(LicenceRefusedError, match="not used"):
        cache.load_split(cache.cache_dir("synthetic"), "val")


def test_evaluate_without_data_cannot_read_it(refused_cache_run: Path) -> None:
    with pytest.raises(LicenceRefusedError):
        evaluate.evaluate_run(refused_cache_run, "val", allow_synthetic=True)


def test_calibrate_cannot_read_it(refused_cache_run: Path) -> None:
    with pytest.raises(LicenceRefusedError):
        calibrate.calibrate_run(refused_cache_run, None, "cpu")


def test_diagnose_cannot_read_it(refused_cache_run: Path) -> None:
    with pytest.raises(LicenceRefusedError):
        diagnose.frame_details([], "synthetic")


def test_run_reference_cannot_read_it(
    refused_cache_run: Path, repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = importlib.util.spec_from_file_location(
        "run_reference", repo_root / "references" / "run_reference.py"
    )
    assert spec and spec.loader
    ref = importlib.util.module_from_spec(spec)
    sys.modules["run_reference"] = ref
    spec.loader.exec_module(ref)
    cleared = dataclasses.replace(
        ref.REFERENCES["fmask4"],
        licence="test",
        decision=LicenceDecision("used", "test"),
        runner=lambda data: np.zeros(data.labels.shape, np.uint8),
    )
    monkeypatch.setitem(ref.REFERENCES, "fmask4", cleared)
    with pytest.raises(LicenceRefusedError):
        ref.run("fmask4", "synthetic", "val")
