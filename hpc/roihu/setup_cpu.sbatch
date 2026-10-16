#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# CPU side of the one-time setup, as a short job on an x86 CPU node: runs
# hpc/roihu/setup.sh, which creates or updates venv-x86_64 with the package, its
# requirements and the CPU build of torch, and runs check_env.py. Installing
# packages is not light work, so it never runs on a login node: login nodes are
# for editing, submitting, moving data and one-core jobs of minutes under 1 GiB
# (https://docs.csc.fi/computing/usage-policy/, page of 15 October 2026, read
# 16 October 2026).
#
#   bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch
#
# CPU partition 'small': 4 cores and 8 GiB cost 3 CPU BU per hour
# (https://docs.csc.fi/computing/hpc-billing/, read 16 October 2026).
#SBATCH --job-name=tiefer-setup-cpu
#SBATCH --partition=small
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
set -euo pipefail

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "error: this CPU job needs an x86_64 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

# setup.sh sources job_prelude.sh and env.sh itself.
bash hpc/roihu/setup.sh
