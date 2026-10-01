#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Smoke run on one GPU: environment check, configs/smoke.toml on the real
# cache, and a validation evaluation. Its outputs are labelled smoke and are
# never results.
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

run_id="smoke-${SLURM_JOB_ID}"
python3 -m tiefer_lab.train --config configs/smoke.toml --run-id "${run_id}"
python3 -m tiefer_lab.evaluate --run "${run_id}" --split val --baselines
echo "smoke run ${run_id} finished"
