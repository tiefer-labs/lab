#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# ONNX export, check against PyTorch, and INT8 quantisation calibrated on the
# cached training split. Measures the INT8 change on validation; on test only
# with FINAL=1 and a REASON (logged in test_log.md).
#
#   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
#SBATCH --job-name=tiefer-export
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

run_id="${1:?usage: export.sbatch <run-id>}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
cache_name="$(python3 -c 'import sys; from tiefer_lab.config import load_config; from tiefer_lab.train import resolve_run_dir; print(load_config(resolve_run_dir(sys.argv[1]) / "config.toml").data.cache_name)' "${run_id}")"
tiefer_stage_cache "${cache_name}"

if [[ "${FINAL:-0}" == "1" ]]; then
  python3 -m tiefer_lab.export --run "${run_id}" --band-set all --final --reason "${REASON:?FINAL=1 needs REASON}"
else
  python3 -m tiefer_lab.export --run "${run_id}" --band-set all
fi
