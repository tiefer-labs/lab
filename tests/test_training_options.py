# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The training options on a tiny model and synthetic data; every option is off by default."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest
import torch

from tiefer_lab import train
from tiefer_lab.config import ConfigError, TrainConfig, config_from_dict
from tiefer_lab.data import build_cache
from tiefer_lab.models.cloudscout import CloudScoutNet, frame_loss

TINY: dict[str, Any] = {
    "name": "tiny",
    "data": {
        "cache_name": "synthetic",
        "crop_size": 32,
        "batch_size": 4,
        "eval_batch_size": 2,
        "num_workers": 0,
    },
    "model": {"widths": [8, 16]},
    "train": {"epochs": 2, "max_steps_per_epoch": 2, "patience": 10, "log_every": 1},
    "evaluation": {"bootstrap_resamples": 100},
}


def _with(section: str, **values: Any) -> dict[str, Any]:
    raw = copy.deepcopy(TINY)
    raw[section].update(values)
    return raw


@pytest.fixture
def synthetic_cache(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "8", "--patch-size", "64"])


def test_defaults_are_off() -> None:
    t = TrainConfig()
    assert (t.grad_clip_norm, t.skip_nonfinite, t.frame_loss_weight, t.lovasz_weight) == (
        0.0,
        False,
        0.0,
        0.0,
    )
    assert t.task == "segmentation" and t.init_checkpoint is None and t.teacher_run is None
    assert t.select_band_set == ()


def test_gradient_clip_by_hand_and_nonfinite_steps_are_skipped() -> None:
    w = torch.nn.Parameter(torch.zeros(2))
    w.grad = torch.tensor([3.0, 4.0])  # global norm 5
    assert train.step_gradients_ok([w], TrainConfig(grad_clip_norm=1.0))
    assert torch.allclose(w.grad, torch.tensor([0.6, 0.8]))
    w.grad = torch.tensor([math.inf, 0.0])
    assert not train.step_gradients_ok([w], TrainConfig(skip_nonfinite=True))
    # Off: nothing is computed and the step is taken, as before.
    w.grad = torch.tensor([3.0, 4.0])
    assert train.step_gradients_ok([w], TrainConfig())
    assert torch.equal(w.grad, torch.tensor([3.0, 4.0]))


def test_options_train_and_skipped_steps_are_counted(
    synthetic_cache: None, tiefer_env: dict[str, Path]
) -> None:
    raw = _with(
        "train", grad_clip_norm=1.0, skip_nonfinite=True, frame_loss_weight=0.5, lovasz_weight=0.5
    )
    run = tiefer_env["TIEFER_RUNS_DIR"] / "options"
    assert train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True) == (
        "completed"
    )
    meta = json.loads((run / "metadata.json").read_text())
    assert meta["skipped_steps"] == 0
    lines = (run / "metrics.jsonl").read_text().splitlines()
    assert all("skipped_steps" in json.loads(line) for line in lines)


def test_init_checkpoint_and_teacher_name_one_run(
    synthetic_cache: None, tiefer_env: dict[str, Path]
) -> None:
    first = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-seed0-first"
    train.train(config_from_dict(TINY), first, device_name="cpu", allow_synthetic=True)
    raw = _with("train", init_checkpoint="tiny-seed0", teacher_run="tiny-seed0", teacher_weight=1.0)
    run = tiefer_env["TIEFER_RUNS_DIR"] / "student"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    meta = json.loads((run / "metadata.json").read_text())
    assert meta["init_checkpoint"] == "tiny-seed0-first"
    assert meta["teacher_run"] == "tiny-seed0-first"
    # A prefix that matches no finished run, or two, is an error, never a guess.
    with pytest.raises(train.TrainingError, match="exactly one"):
        train.resolve_run_reference("no-such-run")
    second = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-seed0-second"
    train.train(config_from_dict(TINY), second, device_name="cpu", allow_synthetic=True)
    with pytest.raises(train.TrainingError, match="exactly one"):
        train.resolve_run_reference("tiny-seed0")


def test_frame_loss_by_hand() -> None:
    # p(cloudy) = 0.5 for both frames: a cloudy frame costs log 2, a clear one 2 log 2.
    logits = torch.zeros(2, 2)
    value = frame_loss(logits, torch.tensor([1.0, 0.0]), false_positive_weight=2.0)
    assert value.item() == pytest.approx((math.log(2) + 2 * math.log(2)) / 2)


def test_cloudscout_gives_one_class_per_frame_and_trains(
    synthetic_cache: None, tiefer_env: dict[str, Path]
) -> None:
    net = CloudScoutNet((8, 16, 16), in_channels=3).eval()
    assert net.downsampling == 8
    x = torch.randn(2, 3, 32, 32)
    out = net(x)
    assert out.shape == (2, 4, 32, 32)
    mask = out.argmax(dim=1)
    assert all(int(m.min()) == int(m.max()) and int(m.max()) in (0, 1) for m in mask)
    assert torch.allclose(out[:, :2, 0, 0], net.frame_logits(x))
    raw = copy.deepcopy(TINY)
    raw["data"]["bands"] = ["B02", "B03", "B04"]
    raw["model"] = {"widths": [8, 16], "architecture": "cloudscout"}
    raw["train"].update({"task": "frame", "frame_label_threshold": 0.7})
    run = tiefer_env["TIEFER_RUNS_DIR"] / "frames"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    record = json.loads((run / "metrics.jsonl").read_text().splitlines()[-1])
    assert record["val_mean_iou"] is None and record["val_frame_accuracy"] is not None
    # Second step of the paper: only the decision layers learn.
    raw["train"].update({"train_only": "decision", "init_checkpoint": "frames"})
    run2 = tiefer_env["TIEFER_RUNS_DIR"] / "frames-decision"
    before = torch.load(run / "best.pt", weights_only=True)["model"]
    train.train(config_from_dict(raw), run2, device_name="cpu", allow_synthetic=True)
    after = torch.load(run2 / "last.pt", weights_only=True)["model"]
    assert torch.equal(before["stem.0.0.weight"], after["stem.0.0.weight"])


@pytest.mark.parametrize(
    "train_values, message",
    [
        ({"teacher_run": "x"}, "go together"),
        ({"train_only": "decision"}, "task = frame"),
        ({"task": "frame"}, "cloudscout"),
        ({"select_band_set": ["B02"]}, "flexible"),
    ],
)
def test_invalid_option_combinations(train_values: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        config_from_dict(_with("train", **train_values))
