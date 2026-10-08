#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Submit a Tiefer Lab job. #SBATCH lines cannot read environment variables,
# so the account (the CSC project) and the log location are passed here.
#
#   bash hpc/roihu/submit.sh [sbatch options] hpc/roihu/<job>.sbatch [job arguments]
#
# Every job can be submitted from roihu-cpu.csc.fi (x86_64); GPU jobs can also
# be submitted from roihu-gpu.csc.fi (aarch64). sbatch options before the job
# script are passed on, for example --test-only or --time=24:00:00.
#
# CPU jobs (the data job, the survey) use sbatch's default export: they run on
# x86 CPU nodes like roihu-cpu.csc.fi and see the environment of the
# submitting shell. GPU jobs run on ARM GH200 nodes, so they never take the
# login node's environment: they get only HOME, CSC_ENV_INIT_NON_INTERACTIVE=yes
# and the variables the jobs read (TIEFER_CSC_PROJECT, the TIEFER_* paths and,
# when set, SEED, FINAL, REASON, ROBUSTNESS, PERTURBATIONS,
# TIEFER_PYTORCH_MODULE, TIEFER_CPU_PYTHON_MODULE and PYTORCH_CUDA_ALLOC_CONF),
# and the job's login shell builds the module environment of its own node
# (job_prelude.sh). This is CSC's way of submitting across architectures, and
# it works the same from either login node:
# https://docs.csc.fi/computing/running/submitting-jobs-across-architectures/
#
# Logs go to $TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out.
set -euo pipefail

usage="usage: bash hpc/roihu/submit.sh [sbatch options] hpc/roihu/<job>.sbatch [arguments]"
options=()
while [[ $# -gt 0 && "$1" == -* ]]; do
  case "$1" in
    --account* | -A* | --output* | -o* | --chdir* | -D*)
      echo "error: $1 is set by submit.sh" >&2
      exit 2
      ;;
    --export*)
      echo "error: $1 is set by submit.sh (hpc/roihu/README.md)" >&2
      exit 2
      ;;
  esac
  options+=("$1")
  shift
done
if [[ $# -lt 1 ]]; then
  echo "${usage}" >&2
  exit 2
fi
script="$1"
shift
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ -f "${script}" ]] || { echo "error: job script not found: ${script}" >&2; exit 2; }

# shellcheck source=hpc/roihu/env.sh
TIEFER_ENV_PATHS_ONLY=1 source "${repo}/hpc/roihu/env.sh"

host_arch="$(uname -m)"
gpu_job=0
if grep -q '^#SBATCH --gres=gpu' "${script}"; then
  gpu_job=1
elif [[ "${host_arch}" != "x86_64" ]]; then
  # CPU jobs (the data job, the survey) run on x86 CPU nodes.
  if [[ "$(basename "${script}")" == "data.sbatch" ]]; then
    echo "error: this host is ${host_arch}; submit the data job from roihu-cpu.csc.fi" >&2
  else
    echo "error: this host is ${host_arch}; submit CPU jobs from roihu-cpu.csc.fi" >&2
  fi
  exit 2
fi

if [[ -n "${SEED:-}" && ! "${SEED}" =~ ^[0-9]+$ ]]; then
  echo "error: SEED must be a whole number, got '${SEED}'" >&2
  exit 2
fi
if [[ -n "${FINAL:-}" && ! "${FINAL}" =~ ^[01]$ ]]; then
  echo "error: FINAL must be 0 or 1, got '${FINAL}'" >&2
  exit 2
fi
# Plain environment variables; sbatch's default export passes them to a CPU job.
export TIEFER_CSC_PROJECT
[[ -n "${SEED:-}" ]] && export SEED
[[ -n "${FINAL:-}" ]] && export FINAL
[[ -n "${REASON:-}" ]] && export REASON

# GPU jobs: only these variables reach the job. A name without a value passes
# its current value, so a REASON with commas or spaces arrives unchanged.
if [[ "${gpu_job}" == "1" ]]; then
  export_list="HOME,CSC_ENV_INIT_NON_INTERACTIVE=yes,TIEFER_SUBMIT_HOST_ARCH=${host_arch}"
  for name in TIEFER_CSC_PROJECT TIEFER_PROJAPPL TIEFER_SCRATCH TIEFER_SRC \
    TIEFER_DATA_DIR TIEFER_RUNS_DIR TIEFER_REPORTS_DIR TIEFER_PYTORCH_MODULE \
    TIEFER_CPU_PYTHON_MODULE PYTORCH_CUDA_ALLOC_CONF SEED FINAL REASON \
    ROBUSTNESS PERTURBATIONS; do
    if [[ -n "${!name:-}" ]]; then
      export "${name?}"
      export_list+=",${name}"
    fi
  done
  options=("--export=${export_list}" "${options[@]}")
fi

sbatch \
  --account="${TIEFER_CSC_PROJECT}" \
  --chdir="${repo}" \
  --output="${TIEFER_RUNS_DIR}/slurm/%x-%j.out" \
  "${options[@]}" \
  "${script}" "$@"
