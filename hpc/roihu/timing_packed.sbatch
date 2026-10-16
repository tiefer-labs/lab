#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# The timing step of a config on one GH200 GPU: it trains the config with 1, 2,
# 3 and 4 runs on the GPU at once (seeds 0 to N-1), each one epoch cut to 50
# steps and then validation, while nvidia-smi samples the GPU's utilisation
# and memory every second. It then writes reports/timing/packing_<config>.json
# (python -m tiefer_lab.packed report): per packing the time per epoch, GPU
# utilisation, GPU memory and data wait, the chosen packing and the slowdown
# rule. The runs are timing runs, marked as such, never results.
#
#   bash hpc/roihu/submit.sh hpc/roihu/timing_packed.sbatch configs/sieb.toml
#
# The time limit is an upper bound for 1 + 2 + 3 + 4 cut epochs before any
# report exists; the job ends when the last packing has finished and is billed
# on its runtime (https://docs.csc.fi/computing/hpc-billing/, read 16 October 2026).
#SBATCH --job-name=tiefer-timing-packed
#SBATCH --partition=gpumedium
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
set -euo pipefail

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "error: this GPU job needs an aarch64 GH200 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

config="${1:?usage: timing_packed.sbatch <config>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
cache_name="$(python3 -c 'import sys; from pathlib import Path; from tiefer_lab.config import load_config; print(load_config(Path(sys.argv[1])).data.cache_name)' "${config}")"
tiefer_stage_cache "${cache_name}"

job="${SLURM_JOB_ID:-local}"
samples="${TIEFER_RUNS_DIR}/slurm/packed-${job}/gpu_samples.csv"
mkdir -p "$(dirname "${samples}")"
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used --format=csv,noheader,nounits \
  -lms 1000 > "${samples}" &
sampler=$!
status=0
for runs in 1 2 3 4; do
  python3 -m tiefer_lab.packed run "${config}" --timing "${runs}" --job "${job}" || status=$?
done
kill "${sampler}" 2>/dev/null || true
python3 -m tiefer_lab.packed report --config "${config}" --job "${job}" --samples "${samples}"
exit "${status}"
