#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Run a cleared reference model (references/run_reference.py) on the CPU and add
# its masks to the cache it reads:
#
#   bash hpc/roihu/submit.sh hpc/roihu/reference_cpu.sbatch <model> --cache <cache> --split val
#   bash hpc/roihu/submit.sh hpc/roihu/reference_cpu.sbatch <model> --data <independent cache> \
#     --reason "<why>"
#
# Item 1 of the optional queue (hpc/roihu/plan.md, section 3.9). --data reads an
# independent dataset cache only, logs the use in reports/test_log.md and never
# selects or trains anything; the CloudSEN12+ test split needs --final and
# --reason and is logged, and only the maintainer runs it. The first job installs
# the pinned packages of references/requirements.txt into references/.packages
# (--no-deps, last on the import path); a CD-FCNN model downloads its published
# weights from their recorded URL into references/.weights, checked against the
# recorded size. Neither is ever committed.
#
# CPU partition 'small', billed at the larger of 0.75 BU per core-hour and
# 0.375 BU per GiB-hour of memory, on the runtime:
# https://docs.csc.fi/computing/hpc-billing/ (read 16 October 2026). 32 cores
# and 64 GiB cost 24 CPU BU per hour.
#SBATCH --job-name=tiefer-reference-cpu
#SBATCH --partition=small
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
set -euo pipefail

# CPU partitions run on x86_64 nodes; stop before loading anything elsewhere.
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "error: this CPU job needs an x86_64 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

usage="usage: reference_cpu.sbatch <model> --cache <cache> --split val | <model> --data <independent cache> --reason <why>"
model="${1:?${usage}}"
shift
cache_name=""
args=("$@")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cache | --data) cache_name="${2:-}"; shift ;;
  esac
  shift
done
[[ -n "${cache_name}" ]] || { echo "error: ${usage}" >&2; exit 2; }

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
tiefer_require_torch
tiefer_cpu_threads
if [[ ! -f references/.packages/.installed ]]; then
  python3 -m pip install --no-deps --target references/.packages -r references/requirements.txt
  touch references/.packages/.installed
fi
tiefer_stage_cache "${cache_name}"
python3 references/run_reference.py --model "${model}" "${args[@]}"
