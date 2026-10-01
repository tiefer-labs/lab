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


def precision_for(device: torch.device) -> Precision:
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


def data_workers(configured: int) -> int:
    """Data loader workers: inside a Slurm job, SLURM_CPUS_PER_TASK minus one core
    for the main process; elsewhere the configured value."""
    value = os.environ.get("SLURM_CPUS_PER_TASK", "").strip()
    if value.isdigit() and int(value) > 1:
        return int(value) - 1
    return configured
