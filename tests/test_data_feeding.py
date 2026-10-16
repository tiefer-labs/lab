# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The data feeding options never change a run beyond floating point.

Where the training split is held (in memory or memory-mapped from the cache
files), how many runs share the GPU, its cores and its memory, and the number of
data loader workers draw the same batches for the same config and seed: on the
CPU, with the same number of threads, the trained weights are bit for bit the
same. The CPU thread count reorders floating point sums only, and precision
("fp32" turns autocast off) changes floating point only.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest
import torch

from tests.test_checkpoint_resume import TINY
from tiefer_lab import train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache, cache
from tiefer_lab.utils import checkpoint, devices


@pytest.fixture
def synthetic_cache(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "8", "--patch-size", "64"])


def _weights(run: Path) -> dict[str, torch.Tensor]:
    state: dict[str, torch.Tensor] = checkpoint.load_checkpoint(run / checkpoint.LAST)["model"]
    return state


def test_placement_and_packing_draw_the_same_batches(
    synthetic_cache: None, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tiefer_env["TIEFER_RUNS_DIR"]
    base = config_from_dict(TINY)
    in_memory = dataclasses.replace(base, data=dataclasses.replace(base.data, load_mode="memory"))
    mapped = dataclasses.replace(base, data=dataclasses.replace(base.data, load_mode="mmap"))
    threads = torch.get_num_threads()
    try:
        # One run alone on 2 cores, its split in memory.
        monkeypatch.setenv("SLURM_CPUS_PER_TASK", "2")
        assert train.train(in_memory, runs / "memory", device_name="cpu", allow_synthetic=True)
        # Two runs share the job's 4 cores: 2 threads and 1 worker each, data memory-mapped.
        monkeypatch.setenv(cache.RUNS_PER_GPU_ENV, "2")
        monkeypatch.setenv("SLURM_CPUS_PER_TASK", "4")
        assert train.train(mapped, runs / "packed", device_name="cpu", allow_synthetic=True)
        # The same packed run on 1 thread: the CPU thread count only reorders floating
        # point sums, so the weights agree to floating point, not bit for bit.
        monkeypatch.setenv("SLURM_CPUS_PER_TASK", "2")
        assert train.train(mapped, runs / "one_thread", device_name="cpu", allow_synthetic=True)
    finally:
        torch.set_num_threads(threads)

    one, two = _weights(runs / "memory"), _weights(runs / "packed")
    assert one.keys() == two.keys()
    for key in one:
        assert torch.equal(one[key], two[key]), key
    for key, value in _weights(runs / "one_thread").items():
        torch.testing.assert_close(value, one[key], rtol=1e-4, atol=1e-5)
    meta = json.loads((runs / "packed" / train.METADATA_NAME).read_text())
    assert meta["runs_per_gpu"] == 2 and meta["sessions"][-1]["runs_per_gpu"] == 2
    assert meta["data"]["train_placement"] == "memmap" and meta["data"]["load_mode"] == "mmap"
    assert meta["data"]["cpu_threads"] == 2 and meta["data"]["data_workers"] == 1
    assert meta["data"]["cache_staged_local"] is False
    assert meta["precision"] == "fp32" and meta["precision_setting"] == "auto"
    first = json.loads((runs / "packed" / train.METRICS_NAME).read_text().splitlines()[0])
    assert first["data_wait_seconds"] >= 0 and first["gpu_memory_peak_bytes"] is None
    memory_meta = json.loads((runs / "memory" / train.METADATA_NAME).read_text())
    assert memory_meta["data"]["train_placement"] == "cpu" and memory_meta["runs_per_gpu"] == 1


def test_runs_per_gpu_divides_cores_and_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(cache.RUNS_PER_GPU_ENV, raising=False)
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "72")
    assert cache.runs_per_gpu() == 1 and devices.cores_per_run() == 72
    assert devices.data_workers(4) == 71
    monkeypatch.setenv(cache.RUNS_PER_GPU_ENV, "4")
    assert devices.cores_per_run() == 18 and devices.data_workers(4) == 17
    monkeypatch.delenv("SLURM_CPUS_PER_TASK")
    assert devices.cores_per_run() is None and devices.data_workers(4) == 4
    for bad in ("0", "two", "-1"):
        monkeypatch.setenv(cache.RUNS_PER_GPU_ENV, bad)
        with pytest.raises(cache.CacheError, match="whole number"):
            cache.runs_per_gpu()


def test_precision_setting() -> None:
    cpu = torch.device("cpu")
    assert devices.precision_for(cpu) == "fp32"
    assert devices.precision_for(cpu, "fp32") == "fp32"
    with pytest.raises(ValueError, match="precision"):
        config_from_dict({**TINY, "train": {**TINY["train"], "precision": "fp8"}})
