# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""No document claims a standard is met by an agency or operator, and the standards matrix is valid.

The correct statement is "self-assessed alignment with <document>, see
docs/STANDARDS.md"; qualification for a mission is done with the operator.
"""

from __future__ import annotations

import re
from pathlib import Path

CLAIM = re.compile(r"\b(compliant|compliance|certified|qualified|approved)\b", re.IGNORECASE)
AUTHORITY = re.compile(r"\b(NASA|ESA|ECSS|Azercosmos)\b")
STATUSES = {"met", "partly", "not met", "not applicable", "not read", "no document"}


def claims(text: str) -> list[str]:
    """Lines with a claim word and an agency, standard or operator name."""
    return [line for line in text.splitlines() if CLAIM.search(line) and AUTHORITY.search(line)]


def test_the_check_catches_examples() -> None:
    assert claims("The filter is ECSS compliant.")
    assert claims("Certified by NASA for flight.")
    assert claims("approved for Azercosmos missions")
    assert not claims("Self-assessed alignment with ECSS-E-ST-40C, see docs/STANDARDS.md.")
    assert not claims("The model is qualified for nothing yet.")


def test_no_tracked_document_claims_compliance(tracked_files: list[Path], repo_root: Path) -> None:
    offenders = []
    for path in tracked_files:
        if path.suffix not in {".md", ".py", ".toml", ".sh", ".sbatch", ".txt", ".yml"}:
            continue
        if path.name == "test_wording.py":
            continue
        for line in claims((repo_root / path).read_text(encoding="utf-8")):
            offenders.append(f"{path}: {line.strip()}")
    assert not offenders, "\n".join(offenders)


def test_standards_matrix_rows_have_a_valid_status(repo_root: Path) -> None:
    text = (repo_root / "docs" / "STANDARDS.md").read_text(encoding="utf-8")
    section = text.split("## 2. Matrix", 1)[1].split("\n---", 1)[0]
    rows = [
        line
        for line in section.splitlines()
        if line.startswith("| ") and not line.startswith("| :")
    ]
    body = rows[1:]  # without the header row
    assert body
    for row in body:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 10, row
        assert cells[-1] in STATUSES, row
        if cells[-1] in {"met", "partly"}:
            assert cells[4] not in {"not read", "n/a"}, f"a met row must cite a read clause: {row}"
            assert cells[6] not in {"not read", "n/a"}, f"a met row must give the date read: {row}"
