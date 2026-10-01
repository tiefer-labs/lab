#!/bin/bash -l
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Train on one GH200 GPU. Resumable.
#
#   bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml
#   bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml <run-id>   # resume
#   SEED=1 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml      # other seed
#
# Slurm sends SIGUSR1 to this script 300 s before the time limit; it is
# forwarded to the training process, which saves last.pt and stops. Submit
# again with the run ID to continue. Default time 12 hours; gpumedium allows
# up to 36 hours (override with sbatch --time through submit.sh options).
# 200 GPU BU per GPU hour, with up to 72 cores and 212 GiB memory per GPU
# included (https://docs.csc.fi/computing/hpc-billing/); data loader workers
# follow SLURM_CPUS_PER_TASK. Slurm adds memory per GPU automatically
# (https://docs.csc.fi/computing/running/creating-job-scripts-roihu/).
#SBATCH --job-name=tiefer-train
#SBATCH --partition=gpumedium
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
#SBATCH --signal=B:USR1@300
#SBATCH --export=NONE
set -euo pipefail

# GPU jobs run only on the ARM (aarch64) GH200 nodes; stop before loading anything.
if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "error: this GPU job needs an aarch64 GH200 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi

config="${1:?usage: train.sbatch <config> [run-id to resume]}"
resume="${2:-}"

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
cache_name="$(python3 -c 'import sys; from pathlib import Path; from tiefer_lab.config import load_config; print(load_config(Path(sys.argv[1])).data.cache_name)' "${config}")"
tiefer_stage_cache "${cache_name}"

seed_args=()
if [[ -n "${SEED:-}" ]]; then
  seed_args=(--seed "${SEED}")
fi
if [[ -n "${resume}" ]]; then
  python3 -m tiefer_lab.train --resume "${resume}" &
else
  python3 -m tiefer_lab.train --config "${config}" "${seed_args[@]}" &
fi
pid=$!
trap 'echo "forwarding SIGUSR1 to training"; kill -USR1 "${pid}"' USR1
trap 'echo "forwarding SIGTERM to training"; kill -TERM "${pid}"' TERM

status=0
wait "${pid}" || status=$?
# A trapped signal interrupts wait; wait again until the training process exits.
while kill -0 "${pid}" 2>/dev/null; do
  status=0
  wait "${pid}" || status=$?
done
echo "training process exited with status ${status}"
echo "if the log says 'interrupted', resubmit with the run ID to continue"
exit "${status}"
