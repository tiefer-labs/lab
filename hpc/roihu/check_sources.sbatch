#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Check on a CPU node that every data source and reference model can be
# obtained, without downloading any of them.
#
#   bash hpc/roihu/submit.sh hpc/roihu/check_sources.sbatch [--interval 1.0]
#
# python -m tiefer_lab.data.check_sources sends HEAD requests (or asks for the
# first byte) for every file of the fact records, waits between requests and
# sends no credential. The job unsets the credential variables of the
# submitting shell first. It writes $TIEFER_REPORTS_DIR/data/sources.json and
# prints a short summary; hpc/roihu/collect.sh packs it with the other report
# files.
#
# CPU partition 'small'; a few hundred requests at one per second.
# Source: https://docs.csc.fi/computing/running/batch-job-partitions/
#SBATCH --job-name=tiefer-sources
#SBATCH --partition=small
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
set -euo pipefail

case "$(uname -m)" in
  aarch64 | x86_64) ;;
  *)
    echo "error: unsupported architecture $(uname -m); expected aarch64 or x86_64" >&2
    exit 1
    ;;
esac

# No credential reaches the check, whatever the submitting shell holds.
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
python3 -m tiefer_lab.data.check_sources "$@"
