# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Diagnostics read validation and training data only and change nothing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiefer_lab import diagnose, evaluate, train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache


def _frame(true: float, pred: float) -> dict:
    return {
        "patch_id": f"p{true}-{pred}",
        "true_cloud_fraction": true,
        "predicted_cloud_fraction": pred,
        "decision": "send" if pred < 0.5 else "keep",
        "decision_from_reference": "send" if true < 0.5 else "keep",
    }


def test_false_discards_by_hand() -> None:
    report = {
        "split": "val",
        "model": {"decision_threshold": 0.5},
        "frames": [_frame(0.42, 0.52), _frame(0.47, 0.8), _frame(0.1, 0.1), _frame(0.9, 0.9)],
    }
    out = diagnose.false_discards(report)
    assert (out["useful_frames"], out["false_discards"]) == (3, 2)
    bins = {b["from"]: b["frames"] for b in out["true_fraction_bins"]}
    assert bins[0.4] == 1 and bins[0.45] == 1
    assert out["predicted_above_threshold"]["within_0_05"] == 1
    assert out["predicted_above_threshold"]["beyond_0_10"] == 1
    with pytest.raises(ValueError, match="validation"):
        diagnose.false_discards({**report, "split": "test"})


def test_seeds_frames_and_int8_on_synthetic(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    raw = {
        "name": "tiny",
        "data": {
            "cache_name": "synthetic",
            "crop_size": 32,
            "batch_size": 4,
            "eval_batch_size": 2,
            "num_workers": 0,
        },
        "model": {"widths": [8, 16]},
        "train": {"epochs": 2, "max_steps_per_epoch": 1, "log_every": 1},
        "evaluation": {"bootstrap_resamples": 100},
        "export": {"input_size": 64, "calibration_patches": 3},
    }
    run = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-seed0-x"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    assert diagnose.main(["seeds", str(run)]) == 0
    seeds = json.loads(
        next((tiefer_env["TIEFER_REPORTS_DIR"] / "diagnosis").glob("seeds_*")).read_text()
    )
    assert seeds["runs"][0]["epochs"] == 2 and seeds["runs"][0]["epochs_with_nonfinite_loss"] == []
    report = evaluate.evaluate_run(run, "val", allow_synthetic=True)
    assert diagnose.main(["frames", str(report), "--cache", "synthetic"]) == 0
    assert diagnose.main(["int8", "--run", str(run), "--patches", "2"]) == 0
    int8 = json.loads(
        next((tiefer_env["TIEFER_REPORTS_DIR"] / "diagnosis").glob("int8_*")).read_text()
    )
    assert int8["nodes"] and "cloud_boa_loss" in int8["nodes"][0]
    assert int8["normalised_input_percentiles"]["0"] <= int8["normalised_input_percentiles"]["100"]
