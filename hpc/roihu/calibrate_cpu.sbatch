#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Choose the cloud logit bias and the temperature of a run on the validation
# split only, on the CPU (python -m tiefer_lab.calibrate), for every band set:
#
#   bash hpc/roihu/submit.sh hpc/roihu/calibrate_cpu.sbatch <run-id>
#
# A CPU job, the default of hpc/roihu/plan.md: no GPU billing units are used.
# It needs torch in venv-x86_64 (the CPU build that hpc/roihu/setup.sh installs).
# Submitted from roihu-cpu.csc.fi. The body is shared with the GPU job
# calibrate.sbatch (hpc/roihu/model_jobs.sh).
#
# CPU partition 'small', billed at the larger of 0.75 BU per core-hour and
# 0.375 BU per GiB-hour of memory, on the runtime:
# https://docs.csc.fi/computing/hpc-billing/ (read 16 October 2026). 32 cores
# and 64 GiB cost 24 CPU BU per hour.
#SBATCH --job-name=tiefer-calibrate-cpu
#SBATCH --partition=small
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
set -euo pipefail

# CPU partitions run on x86_64 nodes; stop before loading anything elsewhere.
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "error: this CPU job needs an x86_64 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
tiefer_require_torch
tiefer_cpu_threads
export TIEFER_DEVICE=cpu
tiefer_calibrate_job "${1:?usage: calibrate_cpu.sbatch <run-id>}" "${@:2}"
