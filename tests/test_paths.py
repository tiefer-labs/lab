# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from pathlib import Path

import pytest

from tiefer_lab.utils import paths


def test_locations_come_from_environment(tiefer_env: dict[str, Path]) -> None:
    assert paths.data_dir() == tiefer_env["TIEFER_DATA_DIR"].resolve()
    assert paths.runs_dir() == tiefer_env["TIEFER_RUNS_DIR"].resolve()
    assert paths.reports_dir() == tiefer_env["TIEFER_REPORTS_DIR"].resolve()


def test_defaults_are_relative_to_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for env in ("TIEFER_DATA_DIR", "TIEFER_RUNS_DIR", "TIEFER_REPORTS_DIR"):
        monkeypatch.delenv(env, raising=False)
    monkeypatch.chdir(tmp_path)
    assert paths.data_dir() == (tmp_path / "data").resolve()
    assert paths.runs_dir() == (tmp_path / "runs").resolve()
    assert paths.reports_dir() == (tmp_path / "reports").resolve()


def test_empty_variable_falls_back_to_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TIEFER_DATA_DIR", "  ")
    monkeypatch.chdir(tmp_path)
    assert paths.data_dir() == (tmp_path / "data").resolve()


def test_portable_paths_never_absolute(tiefer_env: dict[str, Path], tmp_path: Path) -> None:
    run_file = tiefer_env["TIEFER_RUNS_DIR"] / "run-1" / "metadata.json"
    assert paths.portable(run_file) == "$TIEFER_RUNS_DIR/run-1/metadata.json"
    assert paths.portable(tiefer_env["TIEFER_DATA_DIR"]) == "$TIEFER_DATA_DIR"
    inside_repo = paths.repo_root() / "configs" / "smoke.toml"
    assert paths.portable(inside_repo) == "configs/smoke.toml"
    outside = tmp_path / "elsewhere" / "file.txt"
    assert paths.portable(outside) == "<external>/file.txt"
