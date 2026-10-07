# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The pull request templates follow docs/STYLE.md, section 12.33.

Each question is a `### <n>. <question>` heading, a description line, and
either a list of `- [ ]` options or an empty answer line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from tests.test_issue_forms import (
    ACKNOWLEDGEMENTS,
    AI_IDS,
    COMPLIANCE,
    DP_IDS,
    FORMS,
    REQUIRED_IDS,
    by_id,
    load,
)
from tests.test_text_rules import violations

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB = REPO_ROOT / ".github"
KINDS = [
    "code",
    "documentation",
    "results_and_reports",
    "configs_and_hpc_run",
    "data",
    "model_card_release",
    "dependencies",
    "ci_and_tooling",
    "governance_and_policy",
]
TEMPLATES = [GITHUB / "pull_request_template.md"] + [
    GITHUB / "PULL_REQUEST_TEMPLATE" / f"{kind}.md" for kind in KINDS
]
QUESTION = re.compile(r"^### (\d+)\. (.+)$")
SECTION = re.compile(r"^## (\d+)\. \S")
REQUIRED = " (required)"


@dataclass
class Question:
    number: int
    text: str
    required: bool
    description: str
    options: list[str] = field(default_factory=list)


def parse(text: str) -> list[Question]:
    found: list[Question] = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        match = QUESTION.match(line)
        if match:
            title = match.group(2)
            required = title.endswith(REQUIRED)
            if required:
                title = title[: -len(REQUIRED)]
            description = lines[i + 1] if i + 1 < len(lines) else ""
            found.append(Question(int(match.group(1)), title, required, description))
        elif found and line.startswith("- [ ] "):
            found[-1].options.append(line[len("- [ ] ") :])
    return found


def test_parse_reads_open_and_closed_questions() -> None:
    text = (
        "## 1. Summary\n\n### 1. What? (required)\nOne line.\n\n\n"
        "### 2. Kind\nChoose one.\n\n- [ ] A\n- [ ] B\n"
    )
    first, second = parse(text)
    assert (first.number, first.text, first.required, first.options) == (1, "What?", True, [])
    assert (second.text, second.description, second.options) == ("Kind", "Choose one.", ["A", "B"])


def test_every_template_exists() -> None:
    assert all(path.is_file() for path in TEMPLATES)
    extra = sorted(p.name for p in (GITHUB / "PULL_REQUEST_TEMPLATE").glob("*.md"))
    assert extra == sorted(f"{kind}.md" for kind in KINDS)


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_template_follows_the_question_rules(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    found = parse(text)
    assert 50 <= len(found) <= 60, f"{len(found)} questions"
    assert [q.number for q in found] == list(range(1, len(found) + 1)), "numbers have gaps"
    for q in found:
        where = f"question {q.number}"
        assert q.description.strip(), f"{where}: no description line"
        assert not q.description.startswith(("- [ ]", "#")), f"{where}: no description line"
        if q.options:
            assert len(q.options) >= 2, f"{where}: fewer than two options"
            assert len(q.options) == len(set(q.options)), f"{where}: options are not distinct"
            assert re.search(r"Choose (one|all that apply)\.", q.description), where
    sections = [int(m.group(1)) for line in text.split("\n") if (m := SECTION.match(line))]
    assert sections == list(range(1, len(sections) + 1)), "sections have gaps"
    first = text.split("\n", 1)[0]
    assert "Only the questions marked required must be answered" in first
    numbers = [q.number for q in found if q.required]
    assert all(str(n) in first for n in numbers)
    assert 6 <= len(numbers) <= 11
    assert "SECURITY.md" in text.split("## 1.", 1)[0]


def _labels(form_items: dict[str, dict[str, Any]], ids: list[str]) -> list[str]:
    return [str(form_items[i]["attributes"]["label"]) for i in ids]


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_ai_and_data_protection_blocks_match_the_forms(path: Path) -> None:
    form = by_id(load(FORMS[0]))
    found = {q.text: q for q in parse(path.read_text(encoding="utf-8"))}
    for text in _labels(form, AI_IDS + DP_IDS):
        assert text in found, f"missing: {text}"
    for text in _labels(form, REQUIRED_IDS):
        assert found[text].required, f"must be required: {text}"
    acknowledgement = found[_labels(form, ["dp_acknowledgement"])[0]]
    assert acknowledgement.options == ACKNOWLEDGEMENTS
    blocks = [line for line in path.read_text(encoding="utf-8").split("\n") if SECTION.match(line)]
    assert blocks[-3].endswith("AI assistance disclosure")
    assert blocks[-2].endswith("Data protection and AI regulation acknowledgement")
    assert blocks[-1].endswith("Closing checklist")


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_template_text_rules(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not violations(text)
    assert not COMPLIANCE.search(text)
