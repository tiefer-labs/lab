# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The CloudScout re-implementation is labelled in every report and document.

hpc/roihu/plan.md, section 3.1: every report of it carries `model_label`, and
every document that describes it says it is a re-implementation trained by
Tiefer Lab, not the flown model.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path

import pytest

from tiefer_lab import acceptance, compare, diagnose
from tiefer_lab.reports import CLOUDSCOUT_LABEL, Report, add_model_label, model_label


@pytest.mark.parametrize(
    "name, architecture, labelled",
    [
        ("cloudscout_reimpl_step1_th30", None, True),
        ("cloudscout_reimpl_th70-seed0-20261016", None, True),
        ("timing-cpu-cloudscout_reimpl_step1_th30-7", None, True),
        ("frames", "cloudscout", True),
        ("sieb", None, False),
        ("lupe_1m-seed0", "separable_unet", False),
    ],
)
def test_label_by_name_or_architecture(name: str, architecture: str | None, labelled: bool) -> None:
    assert (model_label(name, architecture) == CLOUDSCOUT_LABEL) is labelled
    assert ("model_label" in add_model_label({}, name, architecture)) is labelled


def test_comparison_names_the_re_implementation() -> None:
    data = {"config": {"name": "cloudscout_reimpl_th70", "model": {"architecture": "cloudscout"}}}
    name = compare._model_name(Report(Path("x_val.json"), data))
    assert name == f"cloudscout_reimpl_th70, {CLOUDSCOUT_LABEL}"
    plain = compare._model_name(Report(Path("y_val.json"), {"config": {"name": "sieb"}}))
    assert plain == "sieb"


def test_acceptance_page_of_the_re_implementation_is_labelled() -> None:
    page = acceptance.render([], dt.date(2026, 10, 16), "cloudscout_reimpl_th70")
    assert f"Acceptance of cloudscout_reimpl_th70 ({CLOUDSCOUT_LABEL})" in page
    assert CLOUDSCOUT_LABEL not in acceptance.render([], dt.date(2026, 10, 16), "sieb")


def test_diagnosis_reports_are_labelled(tiefer_env: dict[str, Path]) -> None:
    out = diagnose._write("seeds_cloudscout_reimpl_th70", {"runs": []})
    assert json.loads(out.read_text())["model_label"] == CLOUDSCOUT_LABEL
    out = diagnose._write("seeds_sieb", {"runs": []})
    assert "model_label" not in json.loads(out.read_text())


def test_every_document_that_describes_it_says_so(repo_root: Path) -> None:
    """Prose lines outside code blocks and changelog lines (history, never edited)."""
    names = re.compile(r"CloudScout re-implementation|re-implementation of CloudScout")
    files = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.split()
    missing = []
    for name in files:
        in_code = False
        for number, line in enumerate((repo_root / name).read_text(encoding="utf-8").splitlines()):
            if line.startswith("```"):
                in_code = not in_code
            changelog = re.match(r"- \d{1,2} [A-Z][a-z]+ \d{4}: ", line)
            if in_code or changelog or not names.search(line):
                continue
            if "not the flown model" not in line:
                missing.append(f"{name}:{number + 1}")
    assert missing == []
