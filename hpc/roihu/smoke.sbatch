#!/bin/bash -l
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Smoke run on one GPU: environment check, configs/smoke.toml on the real
# cache, a validation evaluation, and a timing run of configs/l1_base.toml.
# Its outputs are labelled smoke and are never results.
#
# If the train and val splits of the full cache are not complete (missing, or
# data.sbatch still building them), the job builds a tiny real cache (32 train
# and 16 validation patches) in $TIEFER_SCRATCH/smoke/data instead, never in
# the full cache folder, and skips the timing run, which needs the full
# training split.
#
#   bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
#SBATCH --job-name=tiefer-smoke
#SBATCH --partition=gputest
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
set -euo pipefail

# GPU jobs run only on the ARM (aarch64) GH200 nodes; stop before loading anything.
if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "error: this GPU job needs an aarch64 GH200 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
python3 hpc/roihu/check_env.py

# The full cache is only read, and only when its train and val splits are
# complete and not being built (data.sbatch may be running). Otherwise a tiny
# cache is built in its own folder, which can never be the full cache folder.
cache_name="cloudsen12-l1c-high"
full_data_dir="${TIEFER_DATA_DIR}"
smoke_data_dir="${TIEFER_SCRATCH}/smoke/data"
tiny_cache=0
if python3 -m tiefer_lab.data.cache ready "${cache_name}" train val; then
  echo "full cache: ${full_data_dir}/${cache_name} (read only)"
else
  echo "full cache not ready: ${full_data_dir}/${cache_name} (missing, or train or val still being built); it is not touched"
  mkdir -p "${smoke_data_dir}"
  if [[ "$(realpath -m "${smoke_data_dir}")" == "$(realpath -m "${full_data_dir}")" ]]; then
    echo "error: the smoke cache folder ${smoke_data_dir} is the full cache folder; unset TIEFER_DATA_DIR and submit again" >&2
    exit 1
  fi
  export TIEFER_DATA_DIR="${smoke_data_dir}"
  echo "tiny smoke cache: ${TIEFER_DATA_DIR}/${cache_name}"
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
