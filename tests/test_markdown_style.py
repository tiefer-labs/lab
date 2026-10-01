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
CELL = re.compile(r"<(th|td)\b([^>]*)>(.*?)</\1>")
HYPE = re.compile(
    r"\b(revolutionary|cutting-edge|game-changing|ai-powered|seamless|unlock|leverage|"
    r"empower|magic)\w*",
    re.IGNORECASE,
)
# These two documents define the hype word list and must quote it.
HYPE_EXEMPT = {"docs/SPEC.md", "docs/STYLE.md"}


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


def check_structure(text: str) -> list[str]:
    problems = []
    levels = []
    for number, line in _prose_lines(text):
        match = HEADING.match(line)
        if match:
            levels.append((number, len(match.group(1)), line))
        if re.match(r"^\s*\|.*\|\s*$", line):
            problems.append(f"line {number}: Markdown pipe table; use the house table style")
    if sum(1 for _, level, _ in levels if level == 1) != 1:
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


def check_tables(text: str) -> list[str]:
    problems = []
    lines = text.split("\n")
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if fenced or not line.startswith("<div style="):
            continue
        end = next(j for j in range(i, len(lines)) if lines[j] == "</div>")
        block = lines[i : end + 1]
        if "" in block:
            problems.append(f"line {i + 1}: empty line inside a table block")
        if i > 0 and lines[i - 1] != "":
            problems.append(f"line {i + 1}: no empty line before a table block")
        if end + 1 < len(lines) and lines[end + 1] != "":
            problems.append(f"line {end + 1}: no empty line after a table block")
        html = "\n".join(block)
        head = html.split("</thead>")[0]
        columns = len(re.findall(r"<th\b", head))
        for colspan in re.findall(r'colspan="(\d+)"', html):
            if int(colspan) != columns:
                problems.append(f"line {i + 1}: category colspan {colspan}, table has {columns}")
        for row in re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL):
            cells = CELL.findall(row)
            for k, (tag, attrs, content) in enumerate(cells):
                if "colspan" in attrs:
                    continue
                want = 'align="left"' if k == 0 else 'align="center"'
                if want not in attrs:
                    problems.append(f"line {i + 1}: {tag} {k + 1} needs {want}")
                if not content.strip() and not (tag == "th" and k == 0):
                    problems.append(f"line {i + 1}: empty cell; write not measured or n/a")
            if cells and "colspan" not in cells[0][1] and len(cells) != columns:
                problems.append(f"line {i + 1}: row with {len(cells)} cells, table has {columns}")
        for colour in re.findall(r"#[0-9A-Fa-f]{6}|rgba\([^)]*\)", html):
            if colour not in (
                "#0C003D",
                "rgba(12, 0, 61, 0.2)",
                "rgba(12, 0, 61, 0.1)",
                "rgba(128, 128, 128, 0.15)",
            ):
                problems.append(f"line {i + 1}: colour {colour} is not a house colour")
    return problems


def test_checks_catch_examples() -> None:
    assert check_structure("# A\n\n### skipped\n")
    assert check_structure("# A\n\n| a | b |\n|---|---|\n")
    assert check_structure("# A\n\n```\nls\n```\n")
    assert check_structure("# A\n\n```bash\n$ ls\n```\n")
    assert not check_structure("# A\n\n## B\n\n### C\n\n```bash\nls\n```\n")
    from tiefer_lab.tables import Group, house_table

    good = "x\n\n" + house_table(["", "A"], [Group("G", [["r", "1"]])]) + "\n\ny"
    assert not check_tables(good)
    assert check_tables(good.replace('align="center"', ""))
    assert check_tables(good.replace("<thead>", "\n<thead>"))
    assert check_tables(good.replace(">1</td>", "></td>"))


def test_markdown_files_follow_the_standard(repo_root: Path, tracked_files: list[Path]) -> None:
    files = _markdown_files(tracked_files)
    assert files
    problems = []
    for rel in files:
        text = (repo_root / rel).read_text(encoding="utf-8")
        found = check_header(rel, text.split("\n")) + check_structure(text) + check_tables(text)
        if rel.as_posix() not in HYPE_EXEMPT:
            found += [f"hype word '{m.group()}'" for m in HYPE.finditer(text)]
        problems += [f"{rel}: {p}" for p in found]
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("rel", ["docs/RESULTS.md", "reports/test_log.md"])
def test_generated_files_are_tracked(repo_root: Path, rel: str) -> None:
    assert (repo_root / rel).is_file()
