#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Several training runs at once on one reserved GH200 GPU, as separate
# processes (python -m tiefer_lab.packed run): the seeds of one config, or
# one-change variants of one reference. Each run has its own seed, run folder
# and log ($TIEFER_RUNS_DIR/slurm/packed-<job-id>/<config>-seed<N>.log), is
# exactly what it would be alone, and records runs_per_gpu in its metadata.
# The job's 72 cores and its memory are divided between the runs.
#
#   bash hpc/roihu/submit.sh --time=<HH:MM:SS> hpc/roihu/train_packed.sbatch \
#     configs/sieb.toml@0 configs/sieb.toml@1 configs/sieb.toml@2
#   bash hpc/roihu/submit.sh --time=<HH:MM:SS> hpc/roihu/train_packed.sbatch \
#     resume:<run-id> resume:<run-id>   # continue after the time limit
#
# The time limit comes from the packing report of the timing step plus its
# margin (python -m tiefer_lab.packed time-limit), never a fixed large value;
# the default below is short, so a job submitted without --time ends early and
# resumes. Slurm sends SIGUSR1 300 s before the limit; it is passed to every
# run, which saves last.pt and stops. A job that ends early releases its GPU
# and is billed on its runtime: 200 GPU BU per GPU-hour, cores and memory
# included (https://docs.csc.fi/computing/hpc-billing/, read 16 October 2026).
#SBATCH --job-name=tiefer-train-packed
#SBATCH --partition=gpumedium
#SBATCH --gres=gpu:gh200:1
#SBATCH --time=00:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
#SBATCH --signal=B:USR1@300
set -euo pipefail

# GPU jobs run only on the ARM (aarch64) GH200 nodes; stop before loading anything.
if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "error: this GPU job needs an aarch64 GH200 node, but runs on $(uname -m); check the partition" >&2
  exit 1
fi
[[ $# -ge 1 ]] || { echo "usage: train_packed.sbatch <config>@<seed>|resume:<run-id> ..." >&2; exit 2; }

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# Every run of one job reads the same cache: stage it once for all of them.
first="$1"
if [[ "${first}" == resume:* ]]; then
  config_file="$(python3 -c 'import sys; from tiefer_lab.train import resolve_run_dir; print(resolve_run_dir(sys.argv[1]) / "config.toml")' "${first#resume:}")"
else
  config_file="${first%@*}"
fi
cache_name="$(python3 -c 'import sys; from pathlib import Path; from tiefer_lab.config import load_config; print(load_config(Path(sys.argv[1])).data.cache_name)' "${config_file}")"
tiefer_stage_cache "${cache_name}"

# The launcher waits for every run; Slurm's SIGUSR1 reaches it through this shell.
python3 -m tiefer_lab.packed run "$@" &
launcher=$!
trap 'kill -USR1 "${launcher}" 2>/dev/null || true' USR1
trap 'kill -TERM "${launcher}" 2>/dev/null || true' TERM
status=0
wait "${launcher}" || status=$?
# A trapped signal interrupts wait; wait again until every run has saved and exited.
while kill -0 "${launcher}" 2>/dev/null; do
  status=0
  wait "${launcher}" || status=$?
done
echo "packed runs exited with status ${status}; resubmit interrupted runs as resume:<run-id>"
exit "${status}"
