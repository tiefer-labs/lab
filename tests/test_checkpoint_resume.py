# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Checkpoints, signals and resuming a run, on a tiny model and synthetic data."""

from __future__ import annotations

import json
import os
import pickle
import signal
from pathlib import Path

import pytest
import torch

from tiefer_lab import train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache
from tiefer_lab.data.dataset import DeviceTrainBatches
from tiefer_lab.utils import checkpoint
from tiefer_lab.utils.signals import StopRequest

TINY = {
    "name": "tiny",
    "data": {
        "cache_name": "synthetic",
        "crop_size": 32,
        "batch_size": 4,
        "eval_batch_size": 2,
        "num_workers": 0,
    },
    "model": {"widths": [8, 16]},
    "train": {"epochs": 3, "max_steps_per_epoch": 2, "patience": 10, "log_every": 1},
    "evaluation": {"bootstrap_resamples": 100},
}


@pytest.fixture
def synthetic_cache(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "8", "--patch-size", "64"])


def test_checkpoint_round_trip_uses_weights_only(tmp_path: Path) -> None:
    state = {"model": {"w": torch.arange(3.0)}, "epochs_done": 2, "name": "x"}
    checkpoint.save_checkpoint(tmp_path / "a.pt", state)
    loaded = checkpoint.load_checkpoint(tmp_path / "a.pt")
    torch.testing.assert_close(loaded["model"]["w"], torch.arange(3.0))
    assert loaded["epochs_done"] == 2
    assert not list(tmp_path.glob("*.tmp"))
    # Objects that need unpickling of arbitrary classes are refused.
    torch.save({"bad": object()}, tmp_path / "bad.pt")
    with pytest.raises(pickle.UnpicklingError):
        checkpoint.load_checkpoint(tmp_path / "bad.pt")


def test_stop_request_records_sigusr1_and_restores_handler() -> None:
    before = signal.getsignal(signal.SIGUSR1)
    with StopRequest() as stop:
        assert not stop.requested
        os.kill(os.getpid(), signal.SIGUSR1)
        assert stop.requested and stop.signal_name == "SIGUSR1"
    assert signal.getsignal(signal.SIGUSR1) == before


def test_synthetic_cache_is_refused_without_flag(synthetic_cache: None) -> None:
    with pytest.raises(train.TrainingError, match="synthetic"):
        train.open_cache(config_from_dict(TINY), allow_synthetic=False)


def test_interrupted_run_resumes_to_the_same_result(
    synthetic_cache: None, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = config_from_dict(TINY)
    runs = tiefer_env["TIEFER_RUNS_DIR"]
    status = train.train(config, runs / "full", device_name="cpu", allow_synthetic=True)
    assert status == "completed"

    # Second run: send SIGUSR1 while the first batch of epoch 2 is prepared.
    original = DeviceTrainBatches.epoch

    def interrupting(self: DeviceTrainBatches, epoch: int):  # type: ignore[no-untyped-def]
        for n, batch in enumerate(original(self, epoch)):
            if epoch == 1 and n == 0:
                os.kill(os.getpid(), signal.SIGUSR1)
            yield batch

    monkeypatch.setattr(DeviceTrainBatches, "epoch", interrupting)
    run = runs / "interrupted"
    assert train.train(config, run, device_name="cpu", allow_synthetic=True) == "interrupted"
    assert checkpoint.load_checkpoint(run / checkpoint.LAST)["epochs_done"] == 1
    meta = json.loads((run / train.METADATA_NAME).read_text())
    assert meta["status"] == "interrupted" and meta["data"]["train_placement"] == "cpu"
    monkeypatch.setattr(DeviceTrainBatches, "epoch", original)

    assert train.main(["--resume", str(run), "--device", "cpu", "--allow-synthetic"]) == 0
    meta = json.loads((run / train.METADATA_NAME).read_text())
    assert meta["status"] == "completed" and len(meta["resumed"]) == 1
    epochs = [
        json.loads(line)["epoch"] for line in (run / train.METRICS_NAME).read_text().splitlines()
    ]
    assert epochs == [1, 2, 3]

    full = checkpoint.load_checkpoint(runs / "full" / checkpoint.LAST)["model"]
    resumed = checkpoint.load_checkpoint(run / checkpoint.LAST)["model"]
    for key in full:
        torch.testing.assert_close(resumed[key], full[key])


def test_run_metadata_has_provenance_and_no_absolute_paths(
    synthetic_cache: None, tiefer_env: dict[str, Path]
) -> None:
    run = tiefer_env["TIEFER_RUNS_DIR"] / "meta"
    train.train(config_from_dict(TINY), run, device_name="cpu", allow_synthetic=True)
    text = (run / train.METADATA_NAME).read_text()
    meta = json.loads(text)
    assert meta["smoke"] is True and meta["seed"] == 0
    assert meta["provenance"]["git"]["commit"]
    assert meta["provenance"]["platform"]["machine"]
    assert meta["data"]["cache"] == "$TIEFER_DATA_DIR/synthetic"
    assert str(tiefer_env["TIEFER_RUNS_DIR"]) not in text
    assert (run / checkpoint.BEST).is_file() and (run / train.CONFIG_NAME).is_file()


def test_epochs_are_timed_and_timing_runs_are_marked_smoke(
    synthetic_cache: None, tiefer_env: dict[str, Path], tmp_path: Path
) -> None:
    from tiefer_lab.config import dump_toml

    config_path = tmp_path / "tiny.toml"
    config_path.write_text(dump_toml(config_from_dict(TINY)), encoding="utf-8")
    args = ["--config", str(config_path), "--run-id", "timed", "--device", "cpu"]
    args += ["--epochs", "1", "--max-steps-per-epoch", "1", "--allow-synthetic"]
    assert train.main(args) == 0
    run = tiefer_env["TIEFER_RUNS_DIR"] / "timed"
    record = json.loads((run / train.METRICS_NAME).read_text().splitlines()[0])
    assert record["steps"] == 1 and record["steps_per_full_epoch"] == 2
    assert record["full_epoch_estimated"] is True
    assert record["train_seconds"] >= 0 and record["val_seconds"] >= 0
    assert record["full_epoch_seconds"] >= record["val_seconds"]
    meta = json.loads((run / train.METADATA_NAME).read_text())
    assert meta["smoke"] is True and meta["timing_run"] is True
    assert meta["data"]["ready_seconds"] >= 0
    assert "full epoch" in train.timing_line(record)


def test_seed_override_goes_into_metadata_and_run_id(
    synthetic_cache: None, tiefer_env: dict[str, Path], tmp_path: Path
) -> None:
    from tiefer_lab.config import dump_toml

    config_path = tmp_path / "tiny.toml"
    config_path.write_text(dump_toml(config_from_dict(TINY)), encoding="utf-8")
    base = ["--config", str(config_path), "--device", "cpu", "--allow-synthetic"]
    assert train.main([*base, "--seed", "1"]) == 0
    assert train.main([*base, "--seed", "2"]) == 0
    runs = sorted(p for p in tiefer_env["TIEFER_RUNS_DIR"].iterdir() if p.is_dir())
    assert len(runs) == 2, "two seeds never share a run folder"
    assert "-seed1-" in runs[0].name and "-seed2-" in runs[1].name
    for run, seed in zip(runs, (1, 2), strict=True):
        meta = json.loads((run / train.METADATA_NAME).read_text())
        assert meta["seed"] == seed and meta["seed_from_command_line"] is True
        assert f"seed = {seed}" in (run / train.CONFIG_NAME).read_text()
