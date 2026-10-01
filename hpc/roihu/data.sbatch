#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Build the full CloudSEN12+ cache in /scratch on a CPU node.
#
#   bash hpc/roihu/submit.sh hpc/roihu/data.sbatch [split] [extra build_cache arguments]
#
# The build reads the dataset over HTTPS. If compute nodes cannot reach
# huggingface.co, build the cache on the login node instead (hpc/roihu/README.md,
# step 4). The build is resumable: submit again after a time limit.
#
# TODO(verify) the CPU partition name and its time limit with 'sinfo' on Roihu.
#SBATCH --job-name=tiefer-data
#SBATCH --partition=small
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
set -euo pipefail

split="${1:-all}"
shift || true

# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
python3 hpc/roihu/check_env.py --data-only
python3 -m tiefer_lab.data.build_cache --split "${split}" "$@"
