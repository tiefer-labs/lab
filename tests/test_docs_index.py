# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""INDEX.md lists every tracked Markdown file, and every file it lists exists."""

from __future__ import annotations

import re
from pathlib import Path

LINK = re.compile(r"\]\(([^)#]+\.md)\)")


def listed(repo_root: Path) -> set[str]:
    text = (repo_root / "INDEX.md").read_text(encoding="utf-8")
    return set(LINK.findall(text))


def test_every_markdown_file_is_in_the_index(repo_root: Path, tracked_files: list[Path]) -> None:
    markdown = {p.as_posix() for p in tracked_files if p.suffix == ".md"}
    missing = sorted(markdown - listed(repo_root))
    assert not missing, f"not in INDEX.md: {missing}"


def test_every_indexed_file_exists(repo_root: Path) -> None:
    absent = sorted(p for p in listed(repo_root) if not (repo_root / p).is_file())
    assert not absent, f"listed in INDEX.md but missing: {absent}"
