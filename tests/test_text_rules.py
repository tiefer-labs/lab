# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Character rules for every tracked text file.

Patterns are written as escape sequences so this file never flags itself.
"""

from __future__ import annotations

from pathlib import Path

import regex

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".sh",
    ".sbatch",
    ".json",
    ".cff",
    ".cfg",
    ".lock",
}
TEXT_NAMES = {
    "LICENSE",
    "Makefile",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".env.example",
    ".python-version",
}

EM_DASH = "\u2014"
HORIZONTAL_BAR = "\u2015"
VARIATION_SELECTOR_16 = "\ufe0f"
EN_DASH = "\u2013"

PICTOGRAPHIC = regex.compile(r"\p{Extended_Pictographic}")
# An en dash is accepted only directly between two characters, as in a range.
# The hyphenated spelling is written in two pieces so this file never flags itself;
# a capitalised form inside a quoted title is allowed (docs/STYLE.md, section 3).
HYPHENATED_ONBOARD = "on" + "-board"
URL = regex.compile(r"https?://\S+")
LOOSE_EN_DASH = regex.compile(r"(?:^|\s)" + EN_DASH + r"|" + EN_DASH + r"(?:\s|$)", regex.MULTILINE)


def is_text_file(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES


def violations(text: str) -> list[str]:
    found = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if EM_DASH in line:
            found.append(f"line {line_no}: em dash (U+2014)")
        if HORIZONTAL_BAR in line:
            found.append(f"line {line_no}: horizontal bar (U+2015)")
        if VARIATION_SELECTOR_16 in line:
            found.append(f"line {line_no}: variation selector (U+FE0F)")
        match = PICTOGRAPHIC.search(line)
        if match:
            found.append(f"line {line_no}: pictographic character U+{ord(match.group()):04X}")
        if LOOSE_EN_DASH.search(line):
            found.append(f"line {line_no}: en dash (U+2013) next to a space or line boundary")
        if HYPHENATED_ONBOARD in URL.sub("", line):
            found.append(f"line {line_no}: write 'onboard' or 'on board'")
    return found


def test_rules_catch_each_forbidden_character() -> None:
    assert violations("a " + EM_DASH + " b")
    assert violations("a" + HORIZONTAL_BAR + "b")
    assert violations("ok" + VARIATION_SELECTOR_16)
    assert violations("rocket \U0001f680")
    assert violations("pause " + EN_DASH + " here")
    assert violations(EN_DASH + "start")
    assert violations("end" + EN_DASH)
    assert not violations("2026" + EN_DASH + "2028, pages 12" + EN_DASH + "18")
    assert not violations("plain-hyphen and (parentheses): fine.")
    assert violations("the " + HYPHENATED_ONBOARD + " computer")
    assert not violations("the onboard computer, run on board, On" + "-Board Cloud Detection")
    assert not violations("see https://example.org/processed-" + HYPHENATED_ONBOARD + "-satellite/")


def test_tracked_text_files_follow_character_rules(
    repo_root: Path, tracked_files: list[Path]
) -> None:
    checked = 0
    problems: list[str] = []
    for rel in tracked_files:
        if rel.parts[:2] == ("docs", "assets") or not is_text_file(rel):
            continue
        text = (repo_root / rel).read_text(encoding="utf-8")
        problems.extend(f"{rel}: {v}" for v in violations(text))
        checked += 1
    assert checked > 0, "no tracked text files found"
    assert not problems, "\n".join(problems)
