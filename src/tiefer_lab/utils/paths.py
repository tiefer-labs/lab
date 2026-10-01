# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Locations from the TIEFER_* environment variables, with local defaults.

Paths written into report and metadata files go through `portable`, so they
never contain an absolute path from anyone's machine or from Roihu.
"""

from __future__ import annotations

import os
from pathlib import Path

DATA_ENV = "TIEFER_DATA_DIR"
RUNS_ENV = "TIEFER_RUNS_DIR"
REPORTS_ENV = "TIEFER_REPORTS_DIR"

DEFAULTS = {DATA_ENV: "data", RUNS_ENV: "runs", REPORTS_ENV: "reports"}


def repo_root() -> Path:
    """The repository root when running from a checkout, else the working directory."""
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "tiefer_lab").is_dir():
        return candidate
    return Path.cwd().resolve()


def _location(env: str) -> Path:
    value = os.environ.get(env, "").strip()
    path = Path(value).expanduser() if value else Path.cwd() / DEFAULTS[env]
    return path.resolve()


def data_dir() -> Path:
    """Where the data cache lives (`TIEFER_DATA_DIR`, default `./data`)."""
    return _location(DATA_ENV)


def runs_dir() -> Path:
    """Where training runs are written (`TIEFER_RUNS_DIR`, default `./runs`)."""
    return _location(RUNS_ENV)


def reports_dir() -> Path:
    """Where reports are written (`TIEFER_REPORTS_DIR`, default `./reports`)."""
    return _location(REPORTS_ENV)


def portable(path: Path | str) -> str:
    """A form of `path` that is safe to publish.

    Paths under a TIEFER_* location become `$TIEFER_.../rest`, paths inside the
    repository become relative paths, anything else keeps only its file name.
    """
    resolved = Path(path).expanduser().resolve()
    for env, base in ((DATA_ENV, data_dir()), (RUNS_ENV, runs_dir()), (REPORTS_ENV, reports_dir())):
        if resolved == base or base in resolved.parents:
            rest = resolved.relative_to(base).as_posix()
            return f"${env}" if rest == "." else f"${env}/{rest}"
    root = repo_root()
    if resolved == root or root in resolved.parents:
        return resolved.relative_to(root).as_posix()
    return f"<external>/{resolved.name}"
