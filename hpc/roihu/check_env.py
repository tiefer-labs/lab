# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Check the Python environment on CSC Roihu.

    python3 hpc/roihu/check_env.py              # GPU nodes and roihu-gpu.csc.fi
    python3 hpc/roihu/check_env.py --data-only  # x86 CPU nodes: data cache build only

Imports every dependency, prints versions, CPU architecture, GPU name and
CUDA and bf16 availability, and exits with a clear message if anything is
missing. Inside a Slurm job that was given a GPU, no visible GPU is an error.
"""

from __future__ import annotations

import argparse
import importlib
import os
import platform
import sys

DATA_MODULES = ["numpy", "tacoreader", "rasterio", "fsspec", "aiohttp", "pandas", "pyarrow"]
TRAIN_MODULES = ["torch", "onnx", "onnxruntime"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-only", action="store_true", help="skip torch, onnx, GPU checks")
    args = parser.parse_args(argv)
    print(f"python {platform.python_version()} on {platform.machine()}")
    # The module Python may be older than the version this package targets.
    if sys.version_info < (3, 12):  # noqa: UP036
        print("error: Python 3.12 or newer is needed; load another module", file=sys.stderr)
        return 1
    missing = []
    modules = DATA_MODULES + ([] if args.data_only else TRAIN_MODULES) + ["tiefer_lab"]
    for name in modules:
        try:
            module = importlib.import_module(name)
        except ImportError as err:
            missing.append(f"{name} ({err})")
            continue
        print(f"{name} {getattr(module, '__version__', 'version unknown')}")
    if missing:
        print("error: missing modules: " + ", ".join(missing), file=sys.stderr)
        print("run: bash hpc/roihu/setup.sh", file=sys.stderr)
        return 1
    if args.data_only:
        print("environment ready for the data cache build")
        return 0
    import torch

    cuda = torch.cuda.is_available()
    print(f"CUDA available: {cuda}; CUDA runtime {torch.version.cuda}")
    if cuda:
        print(f"GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.device_count()} visible)")
        print(f"bf16 supported: {torch.cuda.is_bf16_supported()}")
    elif os.environ.get("SLURM_GPUS_ON_NODE") or os.environ.get("SLURM_JOB_GPUS"):
        print("error: no GPU visible inside a GPU job", file=sys.stderr)
        return 1
    else:
        print("no GPU visible: fine on a login node, an error inside a GPU job")
    print("environment ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
