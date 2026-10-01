# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Shared fixtures. Every array made here is synthetic and only used by tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def tracked_files() -> list[Path]:
    """Files in the git index, relative to the repository root."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    names = [n for n in result.stdout.decode("utf-8").split("\0") if n]
    return [Path(n) for n in names if (REPO_ROOT / n).is_file()]


@pytest.fixture
def tiefer_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Point every TIEFER_* location at a fresh temporary directory."""
    dirs = {
        "TIEFER_DATA_DIR": tmp_path / "data",
        "TIEFER_RUNS_DIR": tmp_path / "runs",
        "TIEFER_REPORTS_DIR": tmp_path / "reports",
    }
    for name, path in dirs.items():
        path.mkdir()
        monkeypatch.setenv(name, str(path))
    return dirs
