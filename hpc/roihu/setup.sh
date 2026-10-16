#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# One-time setup on CSC Roihu: create the virtual environment for this
# node's architecture, install the pinned dependencies and the package, and
# run the environment check.
#
#   bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch   # x86 side: a small job
#                                                          # creates venv-x86_64
#   bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch   # ARM side: a gputest job
#                                                          # creates venv-aarch64
#
# Both run on compute nodes, never on a login node: installing packages is not
# the light work login nodes are for (https://docs.csc.fi/computing/usage-policy/,
# read 16 October 2026); outside a Slurm job this script stops.
#
# Why plain venvs and not Tykky: CSC recommends a venv made with
# --system-site-packages to add packages on top of a CSC module
# (https://docs.csc.fi/support/tutorials/python-usage-guide/, read 16 October
# 2026), which is what both sides do (python-pytorch on GH200, python-data on x86),
# and Tykky for whole Conda or pip environments. The venvs live in /projappl, never
# in home or scratch. The x86 venv holds the CPU build of torch, the largest part;
# the time to import torch is printed below and recorded by step 0 of
# hpc/roihu/plan.md, which moves that venv into a Tykky container if it is slow.
set -euo pipefail
if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "error: run the setup as a job, not on a login node: bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch (x86) or setup_gpu.sbatch (GH200)" >&2
  exit 2
fi

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=hpc/roihu/job_prelude.sh
source "${repo}/hpc/roihu/job_prelude.sh"
# shellcheck source=hpc/roihu/env.sh
source "${repo}/hpc/roihu/env.sh"

echo "architecture: ${TIEFER_ARCH}"
echo "python: $(command -v python3) ($(python3 --version))"

# A venv on top of the loaded module, keeping the module's packages:
# https://docs.csc.fi/support/tutorials/python-usage-guide/
if [[ ! -d "${TIEFER_VENV}" ]]; then
  python3 -m venv --system-site-packages "${TIEFER_VENV}"
fi
# shellcheck disable=SC1091
source "${TIEFER_VENV}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -r "${repo}/hpc/roihu/requirements.txt"
python3 -m pip install --no-deps -e "${repo}"

if [[ "${TIEFER_ARCH}" != "aarch64" ]]; then
  # The jobs that do not train (evaluation, calibration, export, diagnosis) run
  # on x86 CPU nodes and need torch there. requirements.txt leaves torch out, so
  # the CPU build of the version of the GPU module is installed from the PyTorch
  # CPU index, without the CUDA libraries. TODO(verify): that this index is
  # reachable from roihu-cpu.csc.fi and that the wheel installs on Python 3.12
  # of the CPU module; resolved by step 0 of hpc/roihu/plan.md.
  python3 -m pip install "${TIEFER_CPU_TORCH:-torch==2.10.0}" \
    --index-url "${TIEFER_CPU_TORCH_INDEX:-https://download.pytorch.org/whl/cpu}"
fi
python3 "${repo}/hpc/roihu/check_env.py"
# What step 0 records about the environment: packages, and the time to import torch
# from /projappl, which decides whether a Tykky container is needed.
echo "installed packages: $(python3 -m pip list --format=freeze 2>/dev/null | wc -l)"
python3 -c 'import time; t = time.monotonic(); import torch, tiefer_lab; print(f"import torch and tiefer_lab: {time.monotonic() - t:.1f} s")'
echo "setup complete: ${TIEFER_VENV}"
