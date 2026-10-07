# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Every tracked Markdown file follows docs/STYLE.md."""

from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest

STATUS = re.compile(
    r"^Status: (draft|in development|in use|superseded)\. Owner: Tiefer\. Licence: MPL 2\.0\.$"
)
HEADING = re.compile(r"^(#{1,6}) \S")
CHANGELOG_LINE = re.compile(
    r"^- \d{1,2} (January|February|March|April|May|June|July|August|September|October|"
    r"November|December) \d{4}: \S"
)
HYPE = re.compile(
    r"\b(revolutionary|cutting-edge|game-changing|ai-powered|seamless|unlock|leverage|"
    r"empower|magic)\w*",
    re.IGNORECASE,
)
# These two documents define the hype word list and must quote it.
HYPE_EXEMPT = {"docs/SPEC.md", "docs/STYLE.md"}


def is_pull_request_template(rel: Path) -> bool:
    """Pull request templates are bodies of pull requests, not documents (docs/STYLE.md, 12.33).

    They have no header image, title, status line or changelog; every other rule applies.
    """
    return rel == Path(".github/pull_request_template.md") or rel.parent == Path(
        ".github/PULL_REQUEST_TEMPLATE"
    )


def _markdown_files(tracked_files: list[Path]) -> list[Path]:
    return [p for p in tracked_files if p.suffix == ".md"]


def _header_path(rel: Path) -> str:
    if rel.parent == Path("docs"):
        return "assets/header.png"
    return "../" * len(rel.parent.parts) + "docs/assets/header.png"


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """Lines outside fenced code blocks, with their line numbers."""
    out, fenced = [], False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((number, line))
    return out


def check_header(rel: Path, lines: list[str]) -> list[str]:
    problems = []
    expected = f'<img alt="Tiefer Lab" src="{_header_path(rel)}" width="100%">'
    if lines[0] != expected:
        problems.append(f"first line must be {expected}")
    if len(lines) < 9 or not lines[2].startswith("# "):
        problems.append("line 3 must be the title")
    elif not STATUS.match(lines[4]):
        problems.append("line 5 must be the status line")
    elif "---" not in lines[6:12]:
        problems.append("the purpose must be followed by ---")
    return problems


def check_structure(text: str, title_required: bool = True) -> list[str]:
    problems = []
    levels = []
    for number, line in _prose_lines(text):
        match = HEADING.match(line)
        if match:
            levels.append((number, len(match.group(1)), line))
        if re.search(r"<table|<div style|style=\"", line):
            problems.append(f"line {number}: HTML table or inline style; use a Markdown table")
    if title_required and sum(1 for _, level, _ in levels if level == 1) != 1:
        problems.append("exactly one # heading is required")
    for (_, previous, _), (number, level, _) in itertools.pairwise(levels):
        if level > previous + 1:
            problems.append(f"line {number}: heading level skipped")
    sections = [line for _, level, line in levels if level == 2]
    if "## Changelog" in sections and sections[-1] != "## Changelog":
        problems.append("Changelog must be the last section")
    lines = text.split("\n")
    if "## Changelog" in lines:
        entries = [x for x in lines[lines.index("## Changelog") + 1 :] if x.startswith("- ")]
        problems += [
            f"changelog line not dated as '1 October 2026: ...': {e}"
            for e in entries
            if not CHANGELOG_LINE.match(e)
        ]
    fenced, language = False, ""
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            if not fenced and line.strip() == "```":
                problems.append(f"line {number}: code block without a language")
            fenced = not fenced
            language = line.strip()[3:]
        elif fenced and language == "bash" and re.match(r"^\s*\$ ", line):
            problems.append(f"line {number}: command with a $ prompt")
    return problems


def _cells(row: str) -> list[str]:
    inner = row.strip()[1:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def check_tables(text: str) -> list[str]:
    """Markdown tables follow docs/STYLE.md, section 10."""
    problems = []
    lines = text.split("\n")
    fenced, i = False, 0
    while i < len(lines):
        if lines[i].lstrip().startswith("```"):
            fenced = not fenced
        if fenced or not lines[i].startswith("|"):
            i += 1
            continue
        start = i
        while i < len(lines) and lines[i].startswith("|"):
            i += 1
        block = lines[start:i]
        where = f"line {start + 1}"
        if start > 0 and lines[start - 1] != "":
            problems.append(f"{where}: no empty line before a table")
        if i < len(lines) and lines[i] != "":
            problems.append(f"{where}: no empty line after a table")
        if not all(line.rstrip().endswith("|") for line in block) or len(block) < 3:
            problems.append(f"{where}: a table has a header, an alignment row and rows")
            continue
        columns = len(_cells(block[0]))
        expected = "| :--- | " + " | ".join([":---:"] * (columns - 1)) + " |"
        if block[1] != expected:
            problems.append(f"{where}: alignment row must be {expected}")
        if any(not c for c in _cells(block[0])[1:]):
            problems.append(f"{where}: only the top-left header cell may be empty")
        for k, row in enumerate(block[2:], start=start + 3):
            cells = _cells(row)
            if len(cells) != columns:
                problems.append(f"line {k}: row with {len(cells)} cells, table has {columns}")
                continue
            category = re.fullmatch(r"\*\*[^*]+\*\*", cells[0]) and not any(cells[1:])
            if not category and not all(cells):
                problems.append(f"line {k}: empty cell; write not measured or n/a")
    return problems


def test_checks_catch_examples() -> None:
    assert check_structure("# A\n\n### skipped\n")
    assert check_structure('# A\n\n<table style="x"></table>\n')
    assert check_structure("# A\n\n```\nls\n```\n")
    assert check_structure("# A\n\n```bash\n$ ls\n```\n")
    assert not check_structure("# A\n\n## B\n\n### C\n\n```bash\nls\n```\n")
    from tiefer_lab.tables import Group, markdown_table

    good = "x\n\n" + markdown_table(["", "A"], [Group("G", [["r", "1"]])]) + "\n\ny"
    assert not check_tables(good)
    assert check_tables(good.replace(":---:", "---"))
    assert check_tables(good.replace("| r | 1 |", "| r | |"))
    assert check_tables(good.replace("| r | 1 |", "| r | 1 | 2 |"))
    assert check_tables(good.replace("\n\ny", "\ny"))
    assert not check_tables("x\n\n| a \\| b | c |\n| :--- | :---: |\n| d | e |\n")
    template = "## 1. Summary\n\n### 1. What changes?\nOne or two sentences.\n"
    assert not check_structure(template, title_required=False)
    assert check_structure(template)
    assert check_structure("## 1. A\n\n#### 1. B\n", title_required=False)
    assert is_pull_request_template(Path(".github/PULL_REQUEST_TEMPLATE/code.md"))
    assert is_pull_request_template(Path(".github/pull_request_template.md"))
    assert not is_pull_request_template(Path("docs/STYLE.md"))


def test_markdown_files_follow_the_standard(repo_root: Path, tracked_files: list[Path]) -> None:
    files = _markdown_files(tracked_files)
    assert files
    problems = []
    for rel in files:
        text = (repo_root / rel).read_text(encoding="utf-8")
        template = is_pull_request_template(rel)
        found = [] if template else check_header(rel, text.split("\n"))
        found += check_structure(text, title_required=not template) + check_tables(text)
        if rel.as_posix() not in HYPE_EXEMPT:
            found += [f"hype word '{m.group()}'" for m in HYPE.finditer(text)]
        problems += [f"{rel}: {p}" for p in found]
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("rel", ["reports/test_log.md"])
def test_generated_files_are_tracked(repo_root: Path, rel: str) -> None:
    assert (repo_root / rel).is_file()
