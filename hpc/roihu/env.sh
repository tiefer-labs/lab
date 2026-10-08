# shellcheck shell=bash
# "return N || exit N" stops a sourced file with return and an executed one with
# exit; shellcheck reads the exit as unreachable (SC2317), so that check is off here.
# shellcheck disable=SC2317
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Environment for every Tiefer Lab job on CSC Roihu. Source it, do not run it:
#
#   source hpc/roihu/env.sh
#
# Needs TIEFER_CSC_PROJECT (the CSC project name, set in ~/.bashrc).
# Sets the TIEFER_* locations under /scratch, the pip cache outside the home
# directory, loads the Python module for this node's architecture and
# activates the matching virtual environment.
#
# GPU nodes and roihu-gpu.csc.fi are ARM (aarch64) and use the PyTorch module.
# CPU nodes and roihu-cpu.csc.fi are x86_64 (AMD); they only run the data cache
# build, which does not need PyTorch.
# Source: https://docs.csc.fi/computing/systems-roihu/
#
# With TIEFER_ENV_PATHS_ONLY=1 only the paths are set (used by submit.sh).

if [[ -z "${TIEFER_CSC_PROJECT:-}" ]]; then
  echo "error: TIEFER_CSC_PROJECT is not set; add 'export TIEFER_CSC_PROJECT=<project>' to ~/.bashrc" >&2
  return 1 2>/dev/null || exit 1
fi
if [[ ! "${TIEFER_CSC_PROJECT}" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "error: TIEFER_CSC_PROJECT='${TIEFER_CSC_PROJECT}' is not a CSC project name (letters, digits, _); if ~/.bashrc holds the literal placeholder, remove that line (hpc/roihu/README.md, step 1)" >&2
  return 1 2>/dev/null || exit 1
fi

export TIEFER_PROJAPPL="${TIEFER_PROJAPPL:-/projappl/${TIEFER_CSC_PROJECT}/tiefer-lab}"
export TIEFER_SCRATCH="${TIEFER_SCRATCH:-/scratch/${TIEFER_CSC_PROJECT}/tiefer-lab}"
export TIEFER_SRC="${TIEFER_SRC:-${TIEFER_PROJAPPL}/src}"
export TIEFER_DATA_DIR="${TIEFER_DATA_DIR:-${TIEFER_SCRATCH}/data}"
export TIEFER_RUNS_DIR="${TIEFER_RUNS_DIR:-${TIEFER_SCRATCH}/runs}"
export TIEFER_REPORTS_DIR="${TIEFER_REPORTS_DIR:-${TIEFER_SCRATCH}/reports}"
export PIP_CACHE_DIR="${TIEFER_SCRATCH}/pip-cache"
mkdir -p "${TIEFER_DATA_DIR}" "${TIEFER_RUNS_DIR}/slurm" "${TIEFER_REPORTS_DIR}" "${PIP_CACHE_DIR}"

if [[ "${TIEFER_ENV_PATHS_ONLY:-0}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

TIEFER_ARCH="$(uname -m)"
export TIEFER_ARCH
# python-pytorch/2.10: https://docs.csc.fi/support/tutorials/gpu-ml/
# Observed on Roihu, 1 October 2026: 'module avail python-pytorch' lists 2.10 and
# 2.13 (default); 2.10 gives Python 3.12.12, torch 2.10.0+cu130, CUDA 13.0 and
# bf16 on GH200.
export TIEFER_PYTORCH_MODULE="${TIEFER_PYTORCH_MODULE:-python-pytorch/2.10}"
# Observed on Roihu, 1 October 2026: python-data/3.12-31.03 gives Python 3.12.13
# on x86.
export TIEFER_CPU_PYTHON_MODULE="${TIEFER_CPU_PYTHON_MODULE:-python-data/3.12-31.03}"
export TIEFER_VENV="${TIEFER_PROJAPPL}/venv-${TIEFER_ARCH}"

if [[ "${TIEFER_ARCH}" == "aarch64" ]]; then
  tiefer_module="${TIEFER_PYTORCH_MODULE}"
else
  tiefer_module="${TIEFER_CPU_PYTHON_MODULE}"
fi
# The module command is not written for 'set -euo pipefail'; relax the
# options around it and restore exactly the saved ones (shell_options.sh).
# shellcheck source=hpc/roihu/shell_options.sh
source "$(dirname "${BASH_SOURCE[0]}")/shell_options.sh"
tiefer_relax_shell
module purge
tiefer_status=$?
if [[ "${tiefer_status}" == "0" ]]; then
  module load "${tiefer_module}"
  tiefer_status=$?
fi
tiefer_restore_shell
if [[ "${tiefer_status}" != "0" ]]; then
  echo "error: cannot load ${tiefer_module} (module status ${tiefer_status})" >&2
  unset tiefer_module tiefer_status
  return 1 2>/dev/null || exit 1
fi
unset tiefer_module tiefer_status

# GPU jobs: expandable segments in the PyTorch CUDA allocator reduce memory
# fragmentation. This setting alone may not let a 13-band model fit at batch
# 128; the L2 configs halve the batch size instead (configs/l2_flex_1m.toml).
# A value set before the job is kept.
if [[ "${TIEFER_ARCH}" == "aarch64" ]]; then
  export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
fi

if [[ -f "${TIEFER_VENV}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${TIEFER_VENV}/bin/activate"
fi

# Stop with a clear message when setup.sh has not been run for this architecture.
tiefer_require_venv() {
  if [[ ! -f "${TIEFER_VENV}/bin/activate" ]]; then
    echo "error: no virtual environment ${TIEFER_VENV}; run 'bash hpc/roihu/setup.sh' on a ${TIEFER_ARCH} node first (hpc/roihu/README.md, step 2)" >&2
    return 1
  fi
}

# Copy a cache folder to the job's local disk ($TMPDIR) when there is room,
# and point TIEFER_DATA_DIR at the copy. Usage: tiefer_stage_cache <cache-name>
# $TMPDIR is set for every job without a request: https://docs.csc.fi/support/faq/roihu/
# Its size per partition: https://docs.csc.fi/computing/running/batch-job-partitions/
tiefer_stage_cache() {
  local name="$1"
  local src="${TIEFER_DATA_DIR}/${name}"
  if [[ -z "${TMPDIR:-}" || ! -d "${src}" ]]; then
    echo "cache staging skipped: no \$TMPDIR or no cache ${name}"
    return 0
  fi
  local need have
  need=$(du -sk "${src}" | cut -f1)
  have=$(df -Pk "${TMPDIR}" | awk 'NR==2 {print $4}')
  if (( have < need + need / 10 )); then
    echo "cache staging skipped: ${need} KiB needed, ${have} KiB free in \$TMPDIR"
    return 0
  fi
  mkdir -p "${TMPDIR}/data"
  cp -r "${src}" "${TMPDIR}/data/"
  export TIEFER_DATA_DIR="${TMPDIR}/data"
  echo "cache ${name} staged to local disk"
}
