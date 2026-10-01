# shellcheck shell=bash
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
# CPU nodes and roihu-cpu.csc.fi are x86_64; they only run the data cache
# build, which does not need PyTorch.
#
# With TIEFER_ENV_PATHS_ONLY=1 only the paths are set (used by submit.sh).

if [[ -z "${TIEFER_CSC_PROJECT:-}" ]]; then
  echo "error: TIEFER_CSC_PROJECT is not set; add 'export TIEFER_CSC_PROJECT=<project>' to ~/.bashrc" >&2
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
# TODO(verify) with 'module avail python-pytorch' on roihu-gpu.csc.fi.
export TIEFER_PYTORCH_MODULE="${TIEFER_PYTORCH_MODULE:-python-pytorch/2.10}"
# TODO(verify) with 'module avail python' on roihu-cpu.csc.fi: a Python 3.12 module for x86 nodes.
export TIEFER_CPU_PYTHON_MODULE="${TIEFER_CPU_PYTHON_MODULE:-python-data}"
export TIEFER_VENV="${TIEFER_PROJAPPL}/venv-${TIEFER_ARCH}"

module purge
if [[ "${TIEFER_ARCH}" == "aarch64" ]]; then
  module load "${TIEFER_PYTORCH_MODULE}" || { echo "error: cannot load ${TIEFER_PYTORCH_MODULE}" >&2; return 1 2>/dev/null || exit 1; }
else
  module load "${TIEFER_CPU_PYTHON_MODULE}" || { echo "error: cannot load ${TIEFER_CPU_PYTHON_MODULE}" >&2; return 1 2>/dev/null || exit 1; }
fi

if [[ -f "${TIEFER_VENV}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${TIEFER_VENV}/bin/activate"
fi

# Copy a cache folder to the job's local disk ($TMPDIR) when there is room,
# and point TIEFER_DATA_DIR at the copy. Usage: tiefer_stage_cache <cache-name>
# TODO(verify) whether local disk in $TMPDIR must be requested in the job script.
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
