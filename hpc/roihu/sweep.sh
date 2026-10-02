#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Submit configurations and seeds as separate one-GPU jobs.
#
#   bash hpc/roihu/sweep.sh [--seeds 0,1,2] [--timing] [--test-only] config.toml [config.toml ...]
#
# Every (config, seed) pair is one train.sbatch job with SEED set, so runs
# with different seeds never share a run folder. --timing submits one
# timing.sbatch job per config instead (seeds are ignored). --test-only checks
# every request with sbatch --test-only and submits nothing.
set -euo pipefail

usage="usage: bash hpc/roihu/sweep.sh [--seeds 0,1,2] [--timing] [--test-only] config.toml ..."
seeds="0"
timing=0
options=()
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --seeds)
      seeds="${2:?--seeds needs a list such as 0,1,2}"
      shift 2
      ;;
    --timing)
      timing=1
      shift
      ;;
    --test-only)
      options+=(--test-only)
      shift
      ;;
    *)
      echo "error: unknown option $1" >&2
      echo "${usage}" >&2
      exit 2
      ;;
  esac
done
[[ $# -ge 1 ]] || { echo "${usage}" >&2; exit 2; }
[[ "${seeds}" =~ ^[0-9]+(,[0-9]+)*$ ]] || { echo "error: --seeds takes whole numbers such as 0,1,2" >&2; exit 2; }
for config in "$@"; do
  [[ -f "${config}" ]] || { echo "error: config not found: ${config}" >&2; exit 2; }
done

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for config in "$@"; do
  if [[ "${timing}" == "1" ]]; then
    bash "${here}/submit.sh" "${options[@]}" hpc/roihu/timing.sbatch "${config}"
    continue
  fi
  IFS=',' read -r -a list <<<"${seeds}"
  for seed in "${list[@]}"; do
    SEED="${seed}" bash "${here}/submit.sh" "${options[@]}" hpc/roihu/train.sbatch "${config}"
  done
done
