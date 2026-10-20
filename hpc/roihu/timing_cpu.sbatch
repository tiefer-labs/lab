#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# CPU training as a measured option: one epoch of a config, cut to 50 steps, on
# one full medium node, then the CPU BU per epoch against the GPU BU per epoch of
# the chosen GPU packing (python -m tiefer_lab.packed cpu-compare), written to
# reports/timing/cpu_<config>.json. CSC asks to use whichever of CPU or GPU costs
# fewer BU, and one CPU BU equals one GPU BU
# (https://docs.csc.fi/computing/usage-policy/, page of 15 October 2026, read
# 16 October 2026). The run is a timing run, never a result.
#
#   bash hpc/roihu/submit.sh hpc/roihu/timing_cpu.sbatch configs/sieb.toml
#
# Partition 'medium': full M nodes of 384 cores and 744 GiB, 288 CPU BU per
# node-hour (https://docs.csc.fi/computing/running/batch-job-partitions/ and
# https://docs.csc.fi/computing/hpc-billing/, read 16 October 2026). It needs the
# CPU build of torch in venv-x86_64 (setup_cpu.sbatch). Run it after the GPU
# timing step, so the comparison has the GPU packing report.
#SBATCH --job-name=tiefer-timing-cpu
#SBATCH --partition=medium
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=384
set -euo pipefail

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "error: this CPU job needs an x86_64 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

config="${1:?usage: timing_cpu.sbatch <config>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
tiefer_require_torch
tiefer_cpu_threads
cache_name="$(python3 -c 'import sys; from pathlib import Path; from tiefer_lab.config import load_config; print(load_config(Path(sys.argv[1])).data.cache_name)' "${config}")"
tiefer_stage_cache "${cache_name}"
name="$(basename "${config}" .toml)"
run_id="timing-cpu-${name}-${SLURM_JOB_ID:-local}"
python3 -m tiefer_lab.train --config "${config}" --run-id "${run_id}" --device cpu \
  --epochs 1 --max-steps-per-epoch 50
python3 -m tiefer_lab.packed cpu-compare --config "${config}" --cpu-run "${run_id}" \
  --gpu-report "${TIEFER_REPORTS_DIR}/timing/packing_${name}.json"
