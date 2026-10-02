# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Traceability of docs/REQUIREMENTS.md: every requirement is verified, every link exists.

A requirement is a table row whose first cell is an ID in backticks, such as
`REQ-DATA-01` or an acceptance target ID such as `ACC-01`. Its last cell lists
what verifies it, as inline code, separated by commas:

- a test, `tests/test_x.py::test_name` (the function must exist in the file);
- a file, `src/tiefer_lab/x.py` or `reports/acceptance.md` (the file must exist,
  except under reports/, which holds generated files);
- for acceptance targets, `tiefer_lab.acceptance`.

`check` returns the IDs without a verification, the verifications that point
to nothing, duplicate IDs, and acceptance targets missing from the document.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROW_ID = re.compile(r"^\| `([A-Z]{3}(?:-[A-Z]+)?-\d{2})` \|")
CODE = re.compile(r"`([^`]+)`")
GENERATED = ("reports/",)


def parse(path: Path) -> dict[str, list[str]]:
    """{ID: [verification, ...]} from the table rows of the document."""
    out: dict[str, list[str]] = {}
    duplicates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_ID.match(line)
        if not match:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        ident = match.group(1)
        if ident in out:
            duplicates.append(ident)
        out[ident] = CODE.findall(cells[-1]) if len(cells) > 1 else []
    if duplicates:
        out["__duplicates__"] = duplicates
    return out


def _exists(link: str, repo: Path) -> bool:
    if link == "tiefer_lab.acceptance":
        return (repo / "src" / "tiefer_lab" / "acceptance.py").is_file()
    if "::" in link:
        file, name = link.split("::", 1)
        path = repo / file
        return (
            path.is_file()
            and re.search(rf"^def {re.escape(name)}\(", path.read_text(), re.M) is not None
        )
    if link.startswith(GENERATED):
        return True
    return (repo / link).exists()


def check(path: Path, repo: Path) -> dict[str, Any]:
    from tiefer_lab.acceptance import TARGETS

    table = parse(path)
    duplicates = table.pop("__duplicates__", [])
    unverified = sorted(i for i, links in table.items() if not links)
    broken = sorted(
        f"{i}: {link}" for i, links in table.items() for link in links if not _exists(link, repo)
    )
    missing_targets = sorted(t.id for t in TARGETS if t.id not in table)
    return {
        "requirements": len(table),
        "unverified": unverified,
        "broken_links": broken,
        "duplicates": sorted(duplicates),
        "missing_acceptance_targets": missing_targets,
    }


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    result = check(repo / "docs" / "REQUIREMENTS.md", repo)
    problems = {k: v for k, v in result.items() if k != "requirements" and v}
    print(f"{result['requirements']} requirements; problems: {problems or 'none'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
