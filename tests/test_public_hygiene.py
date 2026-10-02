# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Public repository hygiene for every tracked file and file name.

Patterns are built from string pieces so this file never matches itself.
"""

from __future__ import annotations

import re
from pathlib import Path

ALLOWED_EMAIL = "hello" + "@" + "tiefer.space"

ABSOLUTE_PATHS = [
    re.compile("/" + "(?:home|Users|users)" + "/" + r"[A-Za-z0-9._-]+"),
    re.compile(r"(?<![\w.])/" + "root" + "/"),
    re.compile("/" + "(?:scratch|projappl)" + "/" + "project" + r"_\d"),
    re.compile(r"[A-Za-z]:\\" + "Users" + r"\\"),
]
PROJECT_ID = re.compile(r"\b" + "project" + r"_\d{3,}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+" + "@" + r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRETS = [
    re.compile("gh" + "p_" + r"[A-Za-z0-9]{30,}"),
    re.compile("github" + "_pat_" + r"[A-Za-z0-9_]{20,}"),
    re.compile("AK" + "IA" + r"[0-9A-Z]{16}"),
    re.compile("-----BEGIN " + r"[A-Z ]*" + "PRIVATE KEY-----"),
    re.compile(r"\b" + "hf" + "_" + r"[A-Za-z0-9]{30,}"),
    re.compile(r"\b" + "sk" + "-" + r"[A-Za-z0-9_-]{20,}"),
    re.compile("xox" + r"[baprs]-[A-Za-z0-9-]{10,}"),
]
TOOL_NAMES = re.compile(
    "|".join(
        [
            "cla" + "ude",
            "anthr" + "opic",
            "co" + "pilot",
            "chat" + "gpt",
            "open" + "ai",
            "code" + "ium",
            "tab" + "nine",
            "wind" + "surf",
            "gem" + "ini",
            "co" + "dex",
        ]
    ),
    re.IGNORECASE,
)

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}


def findings(text: str) -> list[str]:
    found = []
    for pattern in ABSOLUTE_PATHS:
        if pattern.search(text):
            found.append(f"absolute path ({pattern.pattern})")
    if PROJECT_ID.search(text):
        found.append("CSC project identifier")
    for email in EMAIL.findall(text):
        if email != ALLOWED_EMAIL:
            found.append(f"email address {email}")
    for pattern in SECRETS:
        if pattern.search(text):
            found.append("key or token")
    match = TOOL_NAMES.search(text)
    if match:
        found.append(f"coding tool or vendor name '{match.group()}'")
    return found


def test_patterns_catch_examples() -> None:
    assert findings("/" + "home/someone/x")
    assert findings("/" + "scratch/" + "project" + "_2001234/x")
    assert findings("account=" + "project" + "_2001234")
    assert findings("mail " + "someone" + "@" + "example.org")
    assert findings("token " + "gh" + "p_" + "a" * 36)
    assert findings("made with " + "Cla" + "ude")
    assert not findings("/projappl/<project>/tiefer-lab and " + ALLOWED_EMAIL)
    assert not findings("ssh <user>@roihu-gpu.csc.fi and /scratch/$TIEFER_CSC_PROJECT")


def test_tracked_files_are_clean(repo_root: Path, tracked_files: list[Path]) -> None:
    problems: list[str] = []
    for rel in tracked_files:
        for finding in findings(rel.as_posix()):
            problems.append(f"{rel} (path): {finding}")
        if rel.suffix in BINARY_SUFFIXES:
            continue
        text = (repo_root / rel).read_text(encoding="utf-8", errors="replace")
        problems.extend(f"{rel}: {finding}" for finding in findings(text))
    assert not problems, "\n".join(problems)


PRETRAINED = re.compile(
    r"torch\.hub|load_state_dict_from_url|pretrained\s*=\s*True|from_pretrained|timm\.create_model"
)


def test_no_pretrained_weights_are_loaded(repo_root: Path) -> None:
    """NOTICE.md states that every model is trained from random initialisation."""
    offenders = [
        f"{path.relative_to(repo_root)}: {line.strip()}"
        for path in sorted((repo_root / "src").rglob("*.py"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if PRETRAINED.search(line)
    ]
    assert not offenders, "\n".join(offenders)
