# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""INDEX.md lists every tracked Markdown file, and every file it lists exists.

Pull request templates are bodies of pull requests, not documents; INDEX.md
lists their folder in one row (docs/STYLE.md, 12.33).
"""

from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"\]\(([^)#]+\.md)\)")
TEMPLATES = re.compile(r"^\.github/(pull_request_template\.md|PULL_REQUEST_TEMPLATE/[^/]+\.md)$")


def listed(repo_root: Path) -> set[str]:
    text = (repo_root / "INDEX.md").read_text(encoding="utf-8")
    return set(LINK.findall(text))


def test_every_markdown_file_is_in_the_index(repo_root: Path, tracked_files: list[Path]) -> None:
    markdown = {
        p.as_posix()
        for p in tracked_files
        if p.suffix == ".md" and not TEMPLATES.match(p.as_posix())
    }
    missing = sorted(markdown - listed(repo_root))
    assert not missing, f"not in INDEX.md: {missing}"


def test_every_indexed_file_exists(repo_root: Path) -> None:
    absent = sorted(p for p in listed(repo_root) if not (repo_root / p).is_file())
    assert not absent, f"listed in INDEX.md but missing: {absent}"


def test_templates_are_recognised() -> None:
    assert TEMPLATES.match(".github/pull_request_template.md")
    assert TEMPLATES.match(".github/PULL_REQUEST_TEMPLATE/code.md")
    assert not TEMPLATES.match("docs/STYLE.md")
    assert not TEMPLATES.match(".github/PULL_REQUEST_TEMPLATE/sub/x.md")
