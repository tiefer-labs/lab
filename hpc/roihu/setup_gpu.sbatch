#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# GPU side of the one-time setup, as a short job, so that no shell on
# roihu-gpu.csc.fi is needed: runs hpc/roihu/setup.sh on a GH200 node, which
# creates or updates venv-aarch64 with the PyTorch module and runs
# check_env.py. The job fails when no GPU is visible.
#
#   bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
#
# gputest allows 15 minutes and is meant for tests, not production
# (https://docs.csc.fi/computing/running/batch-job-partitions/). One GPU hour
# costs 200 GPU BU, so this job costs at most 50
# (https://docs.csc.fi/computing/hpc-billing/).
#SBATCH --job-name=tiefer-setup-gpu
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

# setup.sh sources job_prelude.sh and env.sh itself.
bash hpc/roihu/setup.sh
