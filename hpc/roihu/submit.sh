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
# Jobs use sbatch's default export, the standard CSC way: the job sees the
# environment of the submitting shell, including TIEFER_CSC_PROJECT and, when
# set, SEED, FINAL, REASON, TIEFER_PYTORCH_MODULE and TIEFER_CPU_PYTHON_MODULE.
# GPU jobs are submitted from roihu-gpu.csc.fi (aarch64) and CPU jobs (the
# data job, the survey) from roihu-cpu.csc.fi (x86_64). sbatch options before
# the job script are passed on, for example --test-only or --time=24:00:00.
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
      echo "error: $1: jobs need sbatch's default export (hpc/roihu/README.md)" >&2
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

# GPU nodes are ARM and CPU nodes are x86: submit each job from the login node
# of the same architecture, so the job inherits a matching environment.
host_arch="$(uname -m)"
if grep -q '^#SBATCH --gres=gpu' "${script}"; then
  if [[ "${host_arch}" != "aarch64" ]]; then
    echo "error: this is a GPU job and this host is ${host_arch}; submit GPU jobs from roihu-gpu.csc.fi" >&2
    exit 2
  fi
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
# Plain environment variables; sbatch's default export passes them to the job.
export TIEFER_CSC_PROJECT
[[ -n "${SEED:-}" ]] && export SEED
[[ -n "${FINAL:-}" ]] && export FINAL
[[ -n "${REASON:-}" ]] && export REASON

sbatch \
  --account="${TIEFER_CSC_PROJECT}" \
  --chdir="${repo}" \
  --output="${TIEFER_RUNS_DIR}/slurm/%x-%j.out" \
  "${options[@]}" \
  "${script}" "$@"
