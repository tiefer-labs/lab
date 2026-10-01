#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Submit a Tiefer Lab job. #SBATCH lines cannot read environment variables,
# so the account (the CSC project) and the log location are passed here.
#
#   bash hpc/roihu/submit.sh hpc/roihu/<job>.sbatch [job arguments]
#
# Logs go to $TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: bash hpc/roihu/submit.sh hpc/roihu/<job>.sbatch [arguments]" >&2
  exit 2
fi
script="$1"
shift
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ -f "${script}" ]] || { echo "error: job script not found: ${script}" >&2; exit 2; }

# shellcheck source=hpc/roihu/env.sh
TIEFER_ENV_PATHS_ONLY=1 source "${repo}/hpc/roihu/env.sh"

sbatch \
  --account="${TIEFER_CSC_PROJECT}" \
  --chdir="${repo}" \
  --output="${TIEFER_RUNS_DIR}/slurm/%x-%j.out" \
  "${script}" "$@"
