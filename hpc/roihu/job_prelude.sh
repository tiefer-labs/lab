# shellcheck shell=bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Clean start for a Roihu job. Source it, do not run it:
#
#   source hpc/roihu/job_prelude.sh
#
# Jobs use sbatch's default export (hpc/roihu/submit.sh), so the module
# command and MODULEPATH come from the login shell that submitted the job.
# This stops with a clear message when 'module' is missing, and runs
# 'module purge' with errexit, nounset and pipefail turned off and the
# caller's options restored afterwards (shell_options.sh). Source
# hpc/roihu/env.sh only after this.

# shellcheck source=hpc/roihu/shell_options.sh
source "$(dirname "${BASH_SOURCE[0]}")/shell_options.sh"

if ! command -v module >/dev/null 2>&1; then
  echo "error: the 'module' command is not available in this job; submit it with hpc/roihu/submit.sh from a Roihu login node" >&2
  return 1 2>/dev/null || exit 1
fi
tiefer_relax_shell
module purge
tiefer_status=$?
tiefer_restore_shell
if [[ "${tiefer_status}" != "0" ]]; then
  echo "error: 'module purge' failed with status ${tiefer_status}" >&2
  unset tiefer_status
  return 1 2>/dev/null || exit 1
fi
unset tiefer_status
