#!/bin/bash -l
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Survey the CloudSEN12+ metadata and a few items of every label type, to
# verify facts before a build (counts, splits, locations, label and reference
# mask encodings). Short CPU job; it reads only metadata and a few patches.
#
#   bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch [--samples 3]
#
# The report is $TIEFER_REPORTS_DIR/data/survey.json; collect.sh packs it.
#SBATCH --job-name=tiefer-survey
#SBATCH --partition=small
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
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
python3 -m tiefer_lab.data.survey "$@"
