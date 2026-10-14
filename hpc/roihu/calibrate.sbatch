#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Choose the cloud logit bias and the temperature of a run on the validation
# split only (python -m tiefer_lab.calibrate), for every band set of the run.
# Never reads the test split. The values are written to the run folder and to
# reports/calibration/; evaluate.sbatch and export.sbatch read them with
# CLOUD_BIAS=auto and FRACTION=soft.
#
#   bash hpc/roihu/submit.sh hpc/roihu/calibrate.sbatch <run-id>
#SBATCH --job-name=tiefer-calibrate
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

run_id="${1:?usage: calibrate.sbatch <run-id>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
cache_name="$(python3 -c 'import sys; from tiefer_lab.config import load_config; from tiefer_lab.train import resolve_run_dir; print(load_config(resolve_run_dir(sys.argv[1]) / "config.toml").data.cache_name)' "${run_id}")"
tiefer_stage_cache "${cache_name}"
python3 -m tiefer_lab.calibrate --run "${run_id}" --band-set all
