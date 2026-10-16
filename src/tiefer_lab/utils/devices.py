# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Device and precision choice: CUDA, Apple MPS or CPU, overridable with --device.

Mixed precision: bf16 autocast on CUDA devices that support it (Hopper GPUs
on Roihu), fp16 with gradient scaling on other CUDA devices, fp32 on CPU
and MPS.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from typing import Literal

import torch

from tiefer_lab.data import cache

Precision = Literal["bf16", "fp16", "fp32"]
DEVICE_CHOICES = ("auto", "cuda", "mps", "cpu")


def select_device(requested: str = "auto") -> torch.device:
    """The requested device, or the best available one for "auto"."""
    if requested not in DEVICE_CHOICES and not requested.startswith("cuda:"):
        raise ValueError(f"device must be one of {DEVICE_CHOICES} or cuda:<n>, got {requested!r}")
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS was requested but is not available")
    return torch.device(requested)


def precision_for(device: torch.device, setting: str = "auto") -> Precision:
    """bf16 or fp16 autocast on CUDA, fp32 elsewhere; `setting` "fp32" turns it off."""
    if setting == "fp32":
        return "fp32"
    if device.type == "cuda":
        return "bf16" if torch.cuda.is_bf16_supported() else "fp16"
    return "fp32"


@contextlib.contextmanager
def autocast(device: torch.device, precision: Precision) -> Iterator[None]:
    """Autocast for bf16 or fp16; a no-op for fp32."""
    if precision == "fp32":
        yield
        return
    dtype = torch.bfloat16 if precision == "bf16" else torch.float16
    with torch.autocast(device_type=device.type, dtype=dtype):
        yield


def device_name(device: torch.device) -> str:
    if device.type == "cuda":
        return str(torch.cuda.get_device_name(device))
    if device.type == "mps":
        return "Apple MPS"
    return "CPU"


def cores_per_run() -> int | None:
    """Inside a Slurm job, its cores (72 per GH200 GPU) divided by the runs that
    share them (cache.runs_per_gpu); None outside Slurm."""
    value = os.environ.get("SLURM_CPUS_PER_TASK", "").strip()
    if not value.isdigit() or int(value) < 1:
        return None
    return max(1, int(value) // cache.runs_per_gpu())


def data_workers(configured: int) -> int:
    """Data loader workers: inside a Slurm job, the cores of this run minus one for
    the main process; elsewhere the configured value."""
    cores = cores_per_run()
    if cores is not None and cores > 1:
        return cores - 1
    return configured


def set_cpu_threads() -> int:
    """Torch CPU threads: the cores of this run inside a Slurm job; returns the count."""
    cores = cores_per_run()
    if cores is not None:
        torch.set_num_threads(cores)
    return int(torch.get_num_threads())
