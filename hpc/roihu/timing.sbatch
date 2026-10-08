#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Measure the time per epoch of a configuration on one GH200 GPU: one epoch
# cut to 50 steps, then validation. The log line "full epoch ... s (estimated)"
# and metrics.jsonl (full_epoch_seconds) give the real cost of the config,
# which replaces the upper-bound estimate in hpc/roihu/plan.md. The run is
# marked as a timing run and never appears in results.
#
#   bash hpc/roihu/submit.sh hpc/roihu/timing.sbatch configs/l2_flex_1m.toml
#SBATCH --job-name=tiefer-timing
#SBATCH --partition=gputest
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
set -euo pipefail

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "error: this GPU job needs an aarch64 GH200 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

config="${1:?usage: timing.sbatch <config>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
name="$(basename "${config}" .toml)"
python3 -m tiefer_lab.train --config "${config}" --run-id "timing-${name}-${SLURM_JOB_ID}" \
  --epochs 1 --max-steps-per-epoch 50
