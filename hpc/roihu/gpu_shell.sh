#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Open an interactive shell on one GH200 GPU (gputest, 15 minutes). Use it
# to run setup.sh for the GPU side (venv-aarch64) when you only have a shell
# on the x86 login node roihu-cpu.csc.fi:
#
#   bash hpc/roihu/gpu_shell.sh
#   bash hpc/roihu/setup.sh        # inside the GPU shell
#   exit
#
# The shell starts with --export=NONE. Inside it, the same steps as in every
# job run first (hpc/roihu/job_prelude.sh): HOME and USER from the password
# database when empty, /etc/profile when 'module' is missing, 'module purge'.
set -euo pipefail

if [[ -z "${TIEFER_CSC_PROJECT:-}" ]]; then
  echo "error: TIEFER_CSC_PROJECT is not set (hpc/roihu/README.md, step 1)" >&2
  exit 2
fi
if [[ ! "${TIEFER_CSC_PROJECT}" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "error: TIEFER_CSC_PROJECT must be a CSC project name (letters, digits, _), got '${TIEFER_CSC_PROJECT}'" >&2
  exit 2
fi
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "${repo}" == *\'* ]]; then
  echo "error: the repository path cannot contain a single quote" >&2
  exit 2
fi

# Run the prelude, then replace the login shell with an interactive shell
# that keeps HOME, USER, the purged modules and TIEFER_CSC_PROJECT.
inner="cd '${repo}' && export TIEFER_CSC_PROJECT=${TIEFER_CSC_PROJECT} && source hpc/roihu/job_prelude.sh && echo \"GPU shell on \$(hostname) (\$(uname -m)); run: bash hpc/roihu/setup.sh\" && exec /bin/bash -i"

exec srun --account="${TIEFER_CSC_PROJECT}" --partition=gputest --gres=gpu:gh200:1 \
  --cpus-per-task=16 --time=00:15:00 --export=NONE --pty /bin/bash -l -c "${inner}"
