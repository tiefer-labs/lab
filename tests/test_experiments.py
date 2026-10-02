# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""reports/experiments.md is built from the run folders, nothing typed by hand."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from tests.test_checkpoint_resume import TINY
from tests.test_markdown_style import check_header, check_structure
from tiefer_lab import experiments, train
from tiefer_lab.config import config_from_dict, dump_toml
from tiefer_lab.data import build_cache


@pytest.fixture
def two_runs(tiefer_env: dict[str, Path], tmp_path: Path) -> Path:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "8", "--patch-size", "64"])
    raw = {**TINY, "name": "tinyexp"}
    path = tmp_path / "tinyexp.toml"
    path.write_text(dump_toml(config_from_dict(raw)), encoding="utf-8")
    base = ["--config", str(path), "--device", "cpu", "--allow-synthetic"]
    assert train.main([*base, "--run-id", "a", "--seed", "3"]) == 0
    assert train.main([*base, "--run-id", "timing", "--epochs", "1"]) == 0
    runs = tiefer_env["TIEFER_RUNS_DIR"]
    # The tiny config is not a smoke config, so only the timing run is left out.
    meta = json.loads((runs / "a" / train.METADATA_NAME).read_text())
    meta["smoke"] = False
    (runs / "a" / train.METADATA_NAME).write_text(json.dumps(meta))
    return runs


def test_one_row_per_run_from_its_folder(two_runs: Path) -> None:
    rows = experiments.collect(two_runs)
    assert [r["run_id"] for r in rows] == ["a"]
    row = rows[0]
    assert row["seed"] == 3 and row["config"] == "tinyexp" and row["epochs"] == 3
    assert row["gpu_hours"] == 0.0  # trained on the CPU
    text = experiments.render(rows, dt.date(2026, 10, 2))
    lines = text.split("\n")
    assert not check_header(Path("reports/experiments.md"), lines)
    assert not check_structure(text)
    assert "`a`" in text and "2 October 2026" in text


def test_gpu_hours_sum_sessions_and_unknown_stays_unknown() -> None:
    meta = {
        "sessions": [
            {"start": "2026-10-02T10:00:00+00:00", "end": "2026-10-02T11:30:00+00:00", "gpus": 1},
            {"start": "2026-10-02T12:00:00+00:00", "end": "2026-10-02T12:30:00+00:00", "gpus": 1},
        ]
    }
    assert experiments.gpu_hours(meta) == pytest.approx(2.0)
    meta["sessions"].append({"start": "2026-10-02T13:00:00+00:00", "end": None, "gpus": 1})
    assert experiments.gpu_hours(meta) is None
    assert experiments.gpu_hours({}) is None
