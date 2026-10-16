#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# The INT8 diagnosis of a run on one GH200 node: the cloud BOA loss on
# validation patches when one Conv node at a time is quantised, and the range
# of the normalised training input. It needs torch to export the model, which
# only the GPU environment has; the quantisation itself runs on the CPU cores
# of the node. Validation and training data only.
#
#   bash hpc/roihu/submit.sh hpc/roihu/diagnose_gpu.sbatch <run-id> [--band-set <bands>] [--patches N]
#SBATCH --job-name=tiefer-diagnose-gpu
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

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# shellcheck source=hpc/roihu/model_jobs.sh
source hpc/roihu/model_jobs.sh
export TIEFER_DEVICE=auto
tiefer_int8_job "${1:?usage: diagnose_gpu.sbatch <run-id> [diagnose arguments]}" "${@:2}"
