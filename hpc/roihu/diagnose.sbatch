#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Read-only diagnostics on validation and training data on a CPU node.
#
#   bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch seeds <run-dir> [<run-dir> ...]
#   bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch frames <validation report> --cache <name>
#
# python -m tiefer_lab.diagnose never reads the test split and writes only
# reports/diagnosis/. The x86 environment has no torch, so the INT8 diagnosis,
# which exports the model, runs on a GPU node: hpc/roihu/diagnose_gpu.sbatch.
#
# CPU partition 'small': up to 72 hours on one node.
# Source: https://docs.csc.fi/computing/running/batch-job-partitions/
#SBATCH --job-name=tiefer-diagnose
#SBATCH --partition=small
#SBATCH --time=06:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
set -euo pipefail

case "$(uname -m)" in
  aarch64 | x86_64) ;;
  *)
    echo "error: unsupported architecture $(uname -m); expected aarch64 or x86_64" >&2
    exit 1
    ;;
esac

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
if [[ "${1:-}" == "int8" ]]; then
  echo "error: the INT8 diagnosis needs torch; submit hpc/roihu/diagnose_gpu.sbatch" >&2
  exit 2
fi
python3 -m tiefer_lab.diagnose "$@"
