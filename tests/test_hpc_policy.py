# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Every command in hpc/ follows the CSC Roihu usage policy.

https://docs.csc.fi/computing/usage-policy/ (page of 15 October 2026, read
16 October 2026): no service on Roihu that lets an agent on a system you do not
control run commands (no MCP server, reverse tunnel or listening port); list only
your own jobs and processes; no tight polling loops of Slurm; no recursive find
or grep over Lustre. The scripts and the shell blocks of every Markdown file in
hpc/ are checked, comments left out.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SCRIPT_SUFFIXES = {".sh", ".sbatch", ".py"}

# Services that would let something outside Roihu run commands on it.
SERVICE = [
    re.compile(r"\bssh\b[^\n]*\s-[A-Za-z]*[RLDw]\b"),
    re.compile(r"\b(nc|ncat|netcat)\b[^\n]*\s-[A-Za-z]*l"),
    re.compile(r"\b(socat|ngrok|cloudflared|autossh|sshd|frpc|chisel)\b"),
    re.compile(r"\bhttp\.server\b|\bjupyter\b|\bmcp\b|--port\b", re.IGNORECASE),
    re.compile(r"\.(listen|bind)\("),
]
# Other users' jobs and processes, polling and recursive searches over Lustre.
OTHERS = [
    (re.compile(r"\bsqueue\b"), re.compile(r"--me\b|-u \"\$\{?USER")),
    (re.compile(r"\bsacct\b"), re.compile(r"-u \"\$\{?USER")),
    (re.compile(r"\bps\b(?=\s+-?[a-zA-Z])"), re.compile(r"-u \"?\$\{?USER")),
]
FORBIDDEN = [
    re.compile(r"\bsacct\b[^\n]*\s-a\b|\bsacct\b[^\n]*--allusers"),
    re.compile(r"\bps\s+(aux|ax|-e|-A|-ef)\b"),
    re.compile(r"(^|[;&|`(]\s*|\$\(\s*)(who|top|htop|w)(\s|$)"),
    re.compile(r"\bwatch\b"),
    re.compile(r"\bwhile\b[^\n]*\b(squeue|sacct)\b"),
    re.compile(r"\bfind\s|\bgrep\s+-[a-zA-Z]*[rR]|\bls\s+-[a-zA-Z]*R"),
]


def _commands(root: Path) -> list[tuple[str, str]]:
    """(place, line) for every non-comment script line and Markdown shell line in hpc/."""
    out = []
    for path in sorted((root / "hpc").rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix in SCRIPT_SUFFIXES:
            lines = path.read_text(encoding="utf-8").splitlines()
            code = [line for line in lines if not line.lstrip().startswith("#")]
        elif path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            blocks = re.findall(r"```(?:bash|sh|console)\n(.*?)```", text, re.S)
            code = [line for block in blocks for line in block.splitlines()]
        else:
            continue
        out += [(f"{rel}: {line.strip()}", line) for line in code if line.strip()]
    return out


def _violations(lines: list[tuple[str, str]]) -> list[str]:
    found = []
    for place, line in lines:
        if any(p.search(line) for p in SERVICE):
            found.append(f"service: {place}")
        for command, restriction in OTHERS:
            if command.search(line) and not restriction.search(line):
                found.append(f"other users: {place}")
        if any(p.search(line) for p in FORBIDDEN):
            found.append(f"forbidden: {place}")
    return found


def test_no_script_or_runbook_command_breaks_the_usage_policy(repo_root: Path) -> None:
    lines = _commands(repo_root)
    assert any("squeue --me" in line for _, line in lines), "the runbook was read"
    assert _violations(lines) == []


@pytest.mark.parametrize(
    "line",
    [
        "ssh -R 8022:localhost:22 host",
        "ssh -fNL 9000:localhost:9000 host",
        "nc -l 4444",
        "python3 -m http.server 8000",
        "jupyter lab --no-browser",
        "socat TCP-LISTEN:5000 -",
        "squeue",
        "squeue -p gpumedium",
        "sacct -a",
        "sacct -j 1",
        "ps aux",
        "top",
        "who",
        "watch squeue --me",
        'while true; do squeue -u "$USER"; sleep 1; done',
        "find /scratch/project -name '*.npy'",
        "grep -r pattern /scratch/project",
    ],
)
def test_each_rule_catches_its_case(line: str) -> None:
    assert _violations([("example", line)])


@pytest.mark.parametrize(
    "line",
    ["squeue --me", 'sacct -u "$USER" -j 1', 'ps -u "$USER"', "grep -E pattern file.log"],
)
def test_own_jobs_and_processes_are_allowed(line: str) -> None:
    assert not _violations([("example", line)])
