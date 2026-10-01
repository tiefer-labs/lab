# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Run provenance for every result file.

Records the git commit, platform, library versions, device and Slurm fields.
Paths are never recorded as absolute paths (see `paths.portable`), and the
Slurm account (the CSC project) is deliberately not recorded.
"""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import os
import platform
import subprocess
import sys
from typing import Any

import torch

from tiefer_lab import __version__
from tiefer_lab.utils import paths

LIBRARIES = ("torch", "numpy", "onnx", "onnxruntime", "tacoreader", "rasterio")
SLURM_FIELDS = {
    "job_id": "SLURM_JOB_ID",
    "job_name": "SLURM_JOB_NAME",
    "partition": "SLURM_JOB_PARTITION",
    "node": "SLURMD_NODENAME",
    "gpus": "SLURM_GPUS_ON_NODE",
    "cpus_per_task": "SLURM_CPUS_PER_TASK",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def git_commit() -> dict[str, Any]:
    """Commit of the checkout the code runs from, and whether it has local changes."""
    root = paths.repo_root()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "unknown", "dirty": None}
    return {"commit": commit, "dirty": bool(status)}


def library_versions() -> dict[str, str]:
    versions = {}
    for name in LIBRARIES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    # The CSC module may ship torch without package metadata.
    versions["torch"] = torch.__version__
    return versions


def slurm_fields() -> dict[str, str]:
    return {key: os.environ[env] for key, env in SLURM_FIELDS.items() if os.environ.get(env)}


def _cudnn_version() -> int | None:
    cudnn = torch.backends.cudnn
    if not cudnn.is_available():  # type: ignore[no-untyped-call]
        return None
    version = cudnn.version()  # type: ignore[no-untyped-call]
    return int(version) if version is not None else None


def platform_info(device: torch.device | None = None) -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": platform.python_version(),
        "implementation": sys.implementation.name,
        "system": platform.system(),
        "machine": platform.machine(),
        "tiefer_lab": __version__,
        "libraries": library_versions(),
        "cuda_runtime": torch.version.cuda,
        "cudnn": _cudnn_version(),
    }
    if device is not None:
        info["device"] = device.type
        if device.type == "cuda":
            info["gpu"] = torch.cuda.get_device_name(device)
            info["gpu_count"] = torch.cuda.device_count()
    return info


def provenance(device: torch.device | None = None) -> dict[str, Any]:
    """The provenance block shared by run metadata and every report."""
    return {
        "git": git_commit(),
        "platform": platform_info(device),
        "slurm": slurm_fields(),
        "time": now(),
    }
