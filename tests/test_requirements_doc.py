# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""docs/REQUIREMENTS.md: every ID verified, every verification present."""

from __future__ import annotations

from pathlib import Path

from tiefer_lab import requirements


def test_every_requirement_is_verified(repo_root: Path) -> None:
    result = requirements.check(repo_root / "docs" / "REQUIREMENTS.md", repo_root)
    assert result["requirements"] > 0
    assert result["unverified"] == []
    assert result["broken_links"] == []
    assert result["duplicates"] == []
    assert result["missing_acceptance_targets"] == []
