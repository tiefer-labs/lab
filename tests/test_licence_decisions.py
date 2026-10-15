# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Licence decisions of 15 October 2026: refused sources stop and leave every default list."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from pathlib import Path

import pytest

from tiefer_lab import compare, paper_models
from tiefer_lab.data import build_cache, cache, cloudsen12_2022, independent
from tiefer_lab.data.source import NO_DECISION, DataSourceError, LicenceRefusedError
from tiefer_lab.reports import Report, Reports

REFUSED = ("s2_hollstein", "landsat8_38cloud", "landsat8_95cloud", "s2_cesbio")


def test_the_decisions_are_recorded_next_to_the_facts() -> None:
    for name in REFUSED:
        decision = independent.DATASETS[name].decision
        assert decision.status == "not used" and decision.date == "15 October 2026"
        assert decision.reason
    assert independent.PRODUCT_IMAGERY.status == "not used"
    assert cloudsen12_2022.LICENCE_DECISION.status == "declined, pending legal review"
    for name in ("s2_cloud_catalogue", "kappaset", "landsat8_biome", "landsat8_sparcs"):
        assert not independent.DATASETS[name].decision.refused


def test_every_refused_source_raises(tmp_path: Path) -> None:
    for name in REFUSED:
        with pytest.raises(LicenceRefusedError, match="15 October 2026"):
            list(independent.READERS[name](tmp_path, ["B02"]))
        with pytest.raises(LicenceRefusedError, match="not used"):
            build_cache.build_independent(tmp_path / name, name, tmp_path, ["B02"])
    with pytest.raises(LicenceRefusedError, match="declined, pending legal review"):
        cloudsen12_2022.check_ready()


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
    for paper_name, name in paper_models.PAPER_DATASETS.items():
        assert (paper_name in page) == (name in allowed)


def _report(source: str, baselines: dict[str, object]) -> Report:
    return Report(
        Path("evaluation/x.json"),
        {
            "split": "independent",
            "data": {"source": source},
            "config": {"name": "l1_full"},
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
        "l1_full",
        "reference_sen2cor",
    ]
    held = paper_models.measured(reports)
    assert ("l1_full", "s2_cesbio") not in held
    assert ("reference_2022_fmask", "kappaset") not in held
    page = paper_models.render(reports, dt.date(2026, 10, 15))
    assert "S2-CESBIO" not in page


def test_only_a_changed_record_changes_a_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = independent.DATASETS["landsat8_95cloud"]
    monkeypatch.setitem(
        independent.DATASETS, "landsat8_95cloud", dataclasses.replace(info, decision=NO_DECISION)
    )
    assert "landsat8_95cloud" in independent.allowed_datasets()
    assert "landsat8_95cloud" in paper_models.dataset_columns()
    # Allowed now, it stops on the next fact that is not verified, not on the licence.
    with pytest.raises(DataSourceError, match="not verified yet") as err:
        list(independent.READERS["landsat8_95cloud"](tmp_path, ["B02"]))
    assert not isinstance(err.value, LicenceRefusedError)
