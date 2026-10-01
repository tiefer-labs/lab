# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The test split guard and the evaluation report, on synthetic data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiefer_lab import evaluate, train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache

TINY = {
    "name": "tiny",
    "data": {"cache_name": "synthetic", "crop_size": 32, "batch_size": 4, "num_workers": 0},
    "model": {"widths": [8, 16]},
    "train": {"epochs": 1, "max_steps_per_epoch": 2},
    "evaluation": {"bootstrap_resamples": 100},
}


@pytest.fixture
def trained_run(tiefer_env: dict[str, Path]) -> Path:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    run = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-run"
    train.train(config_from_dict(TINY), run, device_name="cpu", allow_synthetic=True)
    return run


def test_test_split_refuses_without_final(tiefer_env: dict[str, Path]) -> None:
    with pytest.raises(evaluate.TestGuardError, match="only for final evaluation"):
        evaluate.check_test_guard("test", final=False, reason=None)
    with pytest.raises(evaluate.TestGuardError, match="--reason"):
        evaluate.check_test_guard("test", final=True, reason="  ")
    with pytest.raises(evaluate.TestGuardError):
        evaluate.check_test_guard("val", final=True, reason="x")
    evaluate.check_test_guard("val", final=False, reason=None)
    code = evaluate.main(["--run", "anything", "--split", "test"])
    assert code == 2
    assert not (tiefer_env["TIEFER_REPORTS_DIR"] / evaluate.TEST_LOG).exists()


def test_validation_report_with_baselines(trained_run: Path, tiefer_env: dict[str, Path]) -> None:
    code = evaluate.main(
        [
            "--run",
            str(trained_run),
            "--split",
            "val",
            "--baselines",
            "--device",
            "cpu",
            "--allow-synthetic",
        ]
    )
    assert code == 0
    out = tiefer_env["TIEFER_REPORTS_DIR"] / "evaluation" / "tiny-run_val.json"
    text = out.read_text()
    report = json.loads(text)
    assert report["smoke"] is True and report["split"] == "val" and report["final"] is False
    model = report["model"]
    assert model["patches"] == 6
    assert set(model["frame"]["thresholds"]) == {"0.30", "0.50", "0.70"}
    assert "false_discard_rate" in model
    assert model["intervals"]["mean_iou"]["resamples"] == 100
    assert {"always_send", "threshold_rule"} <= set(report["baselines"])
    assert report["baselines"]["always_send"]["false_discard_rate"] in (0.0, None)
    assert "synthetic_group" in report["breakdown"]
    frames = report["frames"]
    assert len(frames) == 6 and frames[0]["patch_id"] == "synthetic-val-00000"
    assert {f["decision"] for f in frames} <= {"send", "keep"}
    assert all(0.0 <= f["predicted_shadow_fraction"] <= 1.0 for f in frames)
    assert report["provenance"]["git"]["commit"]
    assert str(tiefer_env["TIEFER_DATA_DIR"]) not in text
    assert not (tiefer_env["TIEFER_REPORTS_DIR"] / evaluate.TEST_LOG).exists()


def test_final_test_evaluation_is_logged_first(
    trained_run: Path, tiefer_env: dict[str, Path]
) -> None:
    args = ["--run", "tiny-run", "--split", "test", "--final", "--reason", "milestone check"]
    assert evaluate.main([*args, "--device", "cpu", "--allow-synthetic"]) == 0
    log = (tiefer_env["TIEFER_REPORTS_DIR"] / evaluate.TEST_LOG).read_text()
    assert "run `tiny-run`" in log and "milestone check" in log and "commit `" in log
    report = json.loads(
        (tiefer_env["TIEFER_REPORTS_DIR"] / "evaluation" / "tiny-run_test.json").read_text()
    )
    assert report["final"] is True and report["split"] == "test"


def test_committed_test_log_starts_with_the_standard_header(repo_root: Path) -> None:
    text = (repo_root / "reports" / evaluate.TEST_LOG).read_text()
    assert text.startswith(evaluate.test_log_header())
