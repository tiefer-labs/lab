# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Train, evaluate and export a band-flexible model and a four-band specialist.

Synthetic 13-band data; the numbers mean nothing, the plumbing is tested.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import pytest

from tiefer_lab import evaluate, train
from tiefer_lab.config import config_from_dict, dump_toml
from tiefer_lab.data import build_cache
from tiefer_lab.data.source import L1C_BAND_NAMES, USED_BANDS
from tiefer_lab.export import __main__ as export

RGB = ["B04", "B03", "B02"]
BASE = {
    "data": {
        "cache_name": "synthetic13",
        "crop_size": 32,
        "batch_size": 4,
        "eval_batch_size": 2,
        "num_workers": 0,
    },
    "model": {"widths": [8, 16]},
    "train": {"epochs": 2, "max_steps_per_epoch": 3, "patience": 5, "log_every": 1},
    "evaluation": {"bootstrap_resamples": 100},
    "export": {"input_size": 64, "calibration_patches": 2, "max_verify_patches": 2},
}


@pytest.fixture
def cache13(tiefer_env: dict[str, Path]) -> None:
    args = ["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"]
    build_cache.main([*args, "--bands", "all", "--name", "synthetic13"])


def _write(tmp_path: Path, raw: dict) -> str:
    path = tmp_path / f"{raw['name']}.toml"
    path.write_text(dump_toml(config_from_dict(raw)), encoding="utf-8")
    return str(path)


def test_flexible_model_trains_evaluates_and_exports_per_band_set(
    cache13: None, tiefer_env: dict[str, Path], tmp_path: Path
) -> None:
    raw = {
        **BASE,
        "name": "flex",
        "data": {**BASE["data"], "bands": list(L1C_BAND_NAMES)},
        "model": {**BASE["model"], "input": "flexible", "flexible_design": "placeholder"},
        "train": {
            **BASE["train"],
            "band_sets": [RGB, list(USED_BANDS), list(L1C_BAND_NAMES)],
            "distill_weight": 0.5,
            "class_weighting": "none",
        },
    }
    config = _write(tmp_path, raw)
    args = ["--config", config, "--run-id", "flex", "--device", "cpu", "--allow-synthetic"]
    assert train.main(args) == 0
    run = tiefer_env["TIEFER_RUNS_DIR"] / "flex"
    records = [json.loads(line) for line in (run / train.METRICS_NAME).read_text().splitlines()]
    assert set(records[-1]["val_mean_iou_by_band_set"]) == {
        "B04+B03+B02",
        "+".join(USED_BANDS),
        "+".join(L1C_BAND_NAMES),
    }
    meta = json.loads((run / train.METADATA_NAME).read_text())
    assert meta["model"]["input"] == "flexible" and meta["model"]["parameters"] > 0

    # Evaluation needs a band set and names its report after it.
    assert evaluate.main(["--run", "flex", "--split", "val", "--allow-synthetic"]) == 2
    common = ["--run", "flex", "--split", "val", "--allow-synthetic", "--device", "cpu"]
    assert evaluate.main([*common, "--band-set", ",".join(RGB), "--baselines"]) == 0
    report_path = tiefer_env["TIEFER_REPORTS_DIR"] / "evaluation" / "flex_val_B04+B03+B02.json"
    report = json.loads(report_path.read_text())
    assert report["band_set"] == RGB
    assert "cloud" in report["model"]["binary"] and "threshold_rule" in report["baselines"]

    # Export: the ONNX model takes only the three bands of the set.
    assert export.main(["--run", "flex", "--skip-int8", "--allow-synthetic"]) == 2
    assert (
        export.main(
            ["--run", "flex", "--skip-int8", "--allow-synthetic", "--band-set", ",".join(RGB)]
        )
        == 0
    )
    exported = json.loads(
        (tiefer_env["TIEFER_REPORTS_DIR"] / "export" / "flex_B04+B03+B02.json").read_text()
    )
    assert exported["band_set"] == RGB and exported["input_shape"] == [1, 3, 64, 64]
    assert exported["verification"]["fp32"]["argmax_agreement"] >= 0.999
    model = onnx.load(str(run / "export" / "B04+B03+B02" / export.FILES["fp32"]))
    dims = [d.dim_value for d in model.graph.input[0].type.tensor_type.shape.dim]
    assert dims == [1, 3, 64, 64]


def test_specialist_reads_four_bands_from_the_13_band_cache(
    cache13: None, tiefer_env: dict[str, Path], tmp_path: Path
) -> None:
    raw = {**BASE, "name": "specialist", "data": {**BASE["data"], "bands": list(USED_BANDS)}}
    config = _write(tmp_path, raw)
    args = ["--config", config, "--run-id", "spec", "--device", "cpu", "--allow-synthetic"]
    assert train.main(args) == 0
    common = ["--run", "spec", "--split", "val", "--allow-synthetic", "--device", "cpu"]
    assert evaluate.main([*common, "--baselines"]) == 0
    report = json.loads(
        (tiefer_env["TIEFER_REPORTS_DIR"] / "evaluation" / "spec_val.json").read_text()
    )
    assert report["band_set"] == list(USED_BANDS)
    assert np.isfinite(report["model"]["pixel"]["overall_accuracy"])
    # A fixed sensor perturbation is recorded in the report and its name.
    assert evaluate.main([*common, "--perturb", "rescale=0.5"]) == 0
    perturbed = json.loads(
        (tiefer_env["TIEFER_REPORTS_DIR"] / "evaluation" / "spec_val_rescale=0.5.json").read_text()
    )
    assert perturbed["perturbation"] == "rescale=0.5"
    assert perturbed["model"]["pixel"]["pixels"] < report["model"]["pixel"]["pixels"]
