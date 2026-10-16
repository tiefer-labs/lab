# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Loading report files: smoke reports are left out, reports without provenance refused."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiefer_lab import acceptance, compare
from tiefer_lab.reports import ReportError, load_reports, require_one_device


def _write(reports: Path, kind: str, name: str, payload: dict) -> None:
    (reports / kind).mkdir(parents=True, exist_ok=True)
    (reports / kind / name).write_text(json.dumps(payload))


def _evaluation(smoke: bool, time: str) -> dict:
    """A hand-written report in the evaluation format; the values are test values."""
    return {
        "kind": "evaluation",
        "smoke": smoke,
        "run_id": "sieb_base-test",
        "split": "val",
        "provenance": {"git": {"commit": "0123456789abcdef"}, "time": time},
    }


def test_smoke_reports_are_never_loaded(tmp_path: Path) -> None:
    _write(tmp_path, "evaluation", "b_val.json", _evaluation(False, "2026-10-02T00:00:00+00:00"))
    _write(tmp_path, "evaluation", "a_val.json", _evaluation(False, "2026-10-01T00:00:00+00:00"))
    _write(tmp_path, "evaluation", "smoke_val.json", _evaluation(True, "2026-10-03T00:00:00+00:00"))
    _write(tmp_path, "compute", "123.json", {"job_id": "123"})
    reports = load_reports(tmp_path)
    assert [r.path.name for r in reports.evaluation] == ["a_val.json", "b_val.json"]
    assert reports.skipped_smoke == 1
    assert len(reports.compute) == 1
    first = reports.evaluation[0]
    assert first.source == "`reports/evaluation/a_val.json`"
    assert first.commit == "`0123456789ab`"


def test_a_report_without_git_provenance_is_refused(tmp_path: Path) -> None:
    payload = _evaluation(False, "2026-10-01T00:00:00+00:00")
    payload["provenance"] = {}
    _write(tmp_path, "export", "run.json", payload)
    with pytest.raises(ReportError, match="no git provenance"):
        load_reports(tmp_path)


def test_an_empty_folder_has_no_reports(tmp_path: Path) -> None:
    reports = load_reports(tmp_path)
    assert not (reports.evaluation or reports.export or reports.jetson or reports.compute)


def test_one_table_never_mixes_evaluation_devices(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    reports_dir = tiefer_env["TIEFER_REPORTS_DIR"]
    cpu = {**_evaluation(False, "2026-10-01T00:00:00+00:00"), "evaluation_device": "cpu"}
    _write(reports_dir, "evaluation", "a_val.json", cpu)
    _write(reports_dir, "evaluation", "b_val.json", {**cpu, "run_id": "wandler_1m-test"})
    assert require_one_device(load_reports(reports_dir)) == "cpu"
    assert require_one_device(load_reports(tiefer_env["TIEFER_RUNS_DIR"])) is None
    gpu = {**cpu, "run_id": "sieb-test", "evaluation_device": "cuda"}
    _write(reports_dir, "evaluation", "c_val.json", gpu)
    with pytest.raises(ReportError, match="different devices") as err:
        require_one_device(load_reports(reports_dir))
    assert "cpu: a_val.json, b_val.json" in str(err.value)
    assert "cuda: c_val.json" in str(err.value) and "evaluate_cpu.sbatch" in str(err.value)
    # Both table writers refuse, say why, and write nothing.
    assert acceptance.main([]) == 2 and compare.main([]) == 2
    assert "fp32" in capsys.readouterr().err
    assert not (reports_dir / acceptance.REPORT).exists()
    # A report that does not record its device is a device of its own.
    _write(
        reports_dir,
        "evaluation",
        "c_val.json",
        {k: v for k, v in gpu.items() if k != "evaluation_device"},
    )
    with pytest.raises(ReportError, match="not recorded"):
        require_one_device(load_reports(reports_dir))
