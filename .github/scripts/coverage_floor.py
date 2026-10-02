# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Fail when the coverage floor in pyproject.toml is lower than in the base commit.

    python3 .github/scripts/coverage_floor.py <base-pyproject.toml> <pyproject.toml>

The floor (`tool.coverage.report.fail_under`) is the measured total rounded
down. It may rise with coverage; lowering it to make a commit pass is refused.
A base without a floor (or an empty base file) passes.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def floor(text: str) -> float | None:
    if not text.strip():
        return None
    report = tomllib.loads(text).get("tool", {}).get("coverage", {}).get("report", {})
    value = report.get("fail_under")
    return None if value is None else float(value)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__.splitlines()[2].strip(), file=sys.stderr)
        return 2
    base = floor(Path(args[0]).read_text(encoding="utf-8"))
    head = floor(Path(args[1]).read_text(encoding="utf-8"))
    if head is None:
        print("error: pyproject.toml has no tool.coverage.report.fail_under", file=sys.stderr)
        return 1
    if base is not None and head < base:
        print(f"error: the coverage floor was lowered from {base:g} to {head:g}", file=sys.stderr)
        return 1
    print(f"coverage floor {head:g} (base {'none' if base is None else f'{base:g}'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
