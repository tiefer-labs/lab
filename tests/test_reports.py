# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Loading report files: smoke reports are left out, reports without provenance refused."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiefer_lab.reports import ReportError, load_reports


def _write(reports: Path, kind: str, name: str, payload: dict) -> None:
    (reports / kind).mkdir(parents=True, exist_ok=True)
    (reports / kind / name).write_text(json.dumps(payload))


def _evaluation(smoke: bool, time: str) -> dict:
    """A hand-written report in the evaluation format; the values are test values."""
    return {
        "kind": "evaluation",
        "smoke": smoke,
        "run_id": "l1_base-test",
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
