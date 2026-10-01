#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Smoke run on one GPU: environment check, configs/smoke.toml on the real
# cache, a validation evaluation, and a timing run of configs/l1_base.toml.
# Its outputs are labelled smoke and are never results.
#
# If the full cache has no index.json yet, the job first builds a tiny real
# cache (32 train and 16 validation patches) under $TIEFER_SCRATCH/smoke and
# skips the timing run, whose estimate needs the full training split.
#
#   bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
#SBATCH --job-name=tiefer-smoke
#SBATCH --partition=gputest
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
set -euo pipefail

# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
python3 hpc/roihu/check_env.py

cache_name="cloudsen12-l1c-high"
tiny_cache=0
if [[ ! -f "${TIEFER_DATA_DIR}/${cache_name}/index.json" ]]; then
  echo "no cache index in ${TIEFER_DATA_DIR}/${cache_name}; building a tiny cache for the smoke run"
  export TIEFER_DATA_DIR="${TIEFER_SCRATCH}/smoke/data"
  mkdir -p "${TIEFER_DATA_DIR}"
  python3 -m tiefer_lab.data.build_cache --split train --limit 32 --name "${cache_name}"
  python3 -m tiefer_lab.data.build_cache --split val --limit 16 --name "${cache_name}"
  tiny_cache=1
fi

run_id="smoke-${SLURM_JOB_ID}"
python3 -m tiefer_lab.train --config configs/smoke.toml --run-id "${run_id}"
python3 -m tiefer_lab.evaluate --run "${run_id}" --split val --baselines

# Real duration: the full training configuration, cut to one epoch of 50
# steps. Its line "full epoch ... s (estimated)" is the time per epoch of
# configs/l1_base.toml on this GPU; the run is marked as smoke.
if [[ "${tiny_cache}" == "1" ]]; then
  echo "timing run skipped: it needs the full cache (hpc/roihu/data.sbatch)"
else
  python3 -m tiefer_lab.train --config configs/l1_base.toml --run-id "timing-${SLURM_JOB_ID}" \
    --epochs 1 --max-steps-per-epoch 50
fi
echo "smoke run ${run_id} finished"
