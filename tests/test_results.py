# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The results generator: refuses without real reports, never shows smoke runs."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from tiefer_lab import results

SECTIONS = [
    "## 1. Summary",
    "## 2. Environment",
    "## 3. Data",
    "## 4. Model",
    "## 5. Baselines and model",
    "## 6. Pixel and frame metrics",
    "## 7. Quantisation",
    "## 8. Hardware",
    "## 9. Compute used",
    "## 10. Limitations",
    "## 11. How to reproduce",
    "## Changelog",
]


def _evaluation(smoke: bool) -> dict:
    """A hand-written report in the evaluation format; the numbers are test values."""
    model = {
        "patches": 3,
        "decision_threshold": 0.5,
        "false_discard_rate": 0.125,
        "pixel": {"mean_iou": 0.625, "overall_accuracy": 0.9, "iou": [0.9, 0.7, 0.4, 0.5]},
        "frame": {
            "cloud_fraction_mae": 0.05,
            "thresholds": {
                f"{t:.2f}": {"false_discard_rate": 0.125, "decision_accuracy": 0.875}
                for t in (0.3, 0.5, 0.7)
            },
        },
        "intervals": {"mean_iou": {"low": 0.5, "high": 0.75}},
    }
    return {
        "kind": "evaluation",
        "smoke": smoke,
        "run_id": "l1_base-test",
        "split": "val",
        "provenance": {"git": {"commit": "0123456789abcdef"}, "time": "2026-10-01T00:00:00+00:00"},
        "run": {"provenance": {"platform": {"machine": "aarch64"}}},
        "data": {"split_count": 3, "dataset": {"revision": "rev"}},
        "model": model,
        "baselines": {"always_send": {**model, "intervals": {}}},
    }


def _write(reports: Path, name: str, payload: dict) -> None:
    (reports / "evaluation").mkdir(parents=True, exist_ok=True)
    (reports / "evaluation" / name).write_text(json.dumps(payload))


def test_refuses_without_real_reports(tiefer_env: dict[str, Path], tmp_path: Path) -> None:
    out = tmp_path / "RESULTS.md"
    assert results.main(["--output", str(out)]) == 2
    _write(tiefer_env["TIEFER_REPORTS_DIR"], "smoke_val.json", _evaluation(smoke=True))
    assert results.main(["--output", str(out)]) == 2
    assert not out.exists()


def test_placeholder_has_every_section_and_no_numbers(tmp_path: Path) -> None:
    out = tmp_path / "RESULTS.md"
    assert results.main(["--placeholder", "--output", str(out), "--date", "2026-10-01"]) == 0
    text = out.read_text()
    assert text.startswith('<img alt="Tiefer Lab" src="assets/header.png" width="100%">')
    positions = [text.index(s) for s in SECTIONS]
    assert positions == sorted(positions)
    assert "not yet measured" in text
    for phrase in ("10 m", "four bands", "Level-1C", "space environment"):
        assert phrase in text
    assert not re.search(r"\| 0\.\d+", text), "no measured values in the placeholder"


def test_real_report_values_appear_with_source(tiefer_env: dict[str, Path], tmp_path: Path) -> None:
    _write(tiefer_env["TIEFER_REPORTS_DIR"], "l1_base-test_val.json", _evaluation(smoke=False))
    _write(tiefer_env["TIEFER_REPORTS_DIR"], "smoke_val.json", _evaluation(smoke=True))
    out = tmp_path / "RESULTS.md"
    assert results.main(["--output", str(out), "--date", "2026-10-02"]) == 0
    text = out.read_text()
    assert "0.625 [0.500, 0.750]" in text
    assert "reports/evaluation/l1_base-test_val.json" in text
    assert "smoke_val.json" not in text
    assert "0123456789ab" in text
    # Every result table names its source and commit (docs/STYLE.md, section 6).
    lines = text.split("\n")
    headers = [lines[i - 1] for i, line in enumerate(lines) if line.startswith("| :---")]
    assert len(headers) >= 8
    for header in headers:
        assert "| Source |" in header and "| Commit |" in header
    assert "2 October 2026" in text


def test_committed_results_page_is_the_placeholder(repo_root: Path, tmp_path: Path) -> None:
    committed = (repo_root / "docs" / "RESULTS.md").read_text()
    match = re.search(r"^- (\d+) (\w+) (\d{4}): generated", committed, re.MULTILINE)
    assert match, "changelog line not found"
    date = dt.datetime.strptime(" ".join(match.groups()), "%d %B %Y").date()
    out = tmp_path / "RESULTS.md"
    results.main(["--placeholder", "--output", str(out), "--date", date.isoformat()])
    assert committed == out.read_text(), (
        "regenerate with: python -m tiefer_lab.results --placeholder"
    )
