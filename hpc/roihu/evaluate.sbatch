#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Evaluate a run on the validation split, with the baselines, on every band
# set of the run (a specialist has one).
#
#   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
#
# ROBUSTNESS=1 also evaluates every band set under each fixed sensor
# perturbation in PERTURBATIONS (space-separated, default below):
#
#   ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
#
# The test split is only for final evaluation. It runs only with FINAL=1 and
# a REASON, and every such run is appended to $TIEFER_REPORTS_DIR/test_log.md:
#
#   FINAL=1 REASON="<why>" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
#SBATCH --job-name=tiefer-evaluate
#SBATCH --partition=gpumedium
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=02:00:00
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
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
export TIEFER_DEVICE=auto
tiefer_evaluate_job "${1:?usage: evaluate.sbatch <run-id>}" "${@:2}"
