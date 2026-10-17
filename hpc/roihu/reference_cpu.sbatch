#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Run a cleared reference model (references/run_reference.py) on one split of a
# cache, on the CPU, and add its masks to the cache:
#
#   bash hpc/roihu/submit.sh hpc/roihu/reference_cpu.sbatch <model> <cache> val
#
# Item 1 of the optional queue (hpc/roihu/plan.md, section 3.9). A model stops
# until its licence decision is "used" and its runner is added, each in its own
# pull request (references/README.md); nothing is downloaded by this job. The
# test split needs --final and --reason and is logged; only the maintainer runs it.
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

model="${1:?usage: reference_cpu.sbatch <model> <cache> <split> [--final --reason <why>]}"
cache_name="${2:?usage: reference_cpu.sbatch <model> <cache> <split>}"
split="${3:?usage: reference_cpu.sbatch <model> <cache> <split>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
tiefer_cpu_threads
tiefer_stage_cache "${cache_name}"
python3 references/run_reference.py --model "${model}" --cache "${cache_name}" --split "${split}" "${@:4}"
