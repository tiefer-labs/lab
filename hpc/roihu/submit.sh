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
# Jobs run with --export=NONE: only TIEFER_CSC_PROJECT and, when set, SEED,
# FINAL, REASON, TIEFER_PYTORCH_MODULE and TIEFER_CPU_PYTHON_MODULE are
# passed to the job. sbatch options before the job
# script are passed on, for example --test-only or --time=24:00:00.
#
# Logs go to $TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out.
set -euo pipefail

usage="usage: bash hpc/roihu/submit.sh [sbatch options] hpc/roihu/<job>.sbatch [arguments]"
options=()
while [[ $# -gt 0 && "$1" == -* ]]; do
  case "$1" in
    --account* | -A* | --export* | --output* | -o* | --chdir* | -D*)
      echo "error: $1 is set by submit.sh" >&2
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

# --export takes a comma-separated list, so every value is checked first.
if [[ ! "${TIEFER_CSC_PROJECT}" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "error: TIEFER_CSC_PROJECT must be a CSC project name (letters, digits, _), got '${TIEFER_CSC_PROJECT}'" >&2
  exit 2
fi
export_list="NONE,TIEFER_CSC_PROJECT=${TIEFER_CSC_PROJECT}"
if [[ -n "${SEED:-}" ]]; then
  [[ "${SEED}" =~ ^[0-9]+$ ]] || { echo "error: SEED must be a whole number, got '${SEED}'" >&2; exit 2; }
  export_list+=",SEED=${SEED}"
fi
if [[ -n "${FINAL:-}" ]]; then
  [[ "${FINAL}" =~ ^[01]$ ]] || { echo "error: FINAL must be 0 or 1, got '${FINAL}'" >&2; exit 2; }
  export_list+=",FINAL=${FINAL}"
fi
for name in TIEFER_PYTORCH_MODULE TIEFER_CPU_PYTHON_MODULE; do
  value="${!name:-}"
  if [[ -n "${value}" ]]; then
    [[ "${value}" =~ ^[A-Za-z0-9._/-]+$ ]] || { echo "error: ${name} must be a module name, got '${value}'" >&2; exit 2; }
    export_list+=",${name}=${value}"
  fi
done
if [[ -n "${REASON:-}" ]]; then
  if [[ "${REASON}" == *,* || "${REASON}" == *\'* || "${REASON}" == *\"* ]]; then
    echo "error: REASON cannot contain commas or quotes (sbatch --export splits on commas)" >&2
    exit 2
  fi
  export_list+=",REASON=${REASON}"
fi

sbatch \
  --account="${TIEFER_CSC_PROJECT}" \
  --chdir="${repo}" \
  --output="${TIEFER_RUNS_DIR}/slurm/%x-%j.out" \
  --export="${export_list}" \
  "${options[@]}" \
  "${script}" "$@"
