# shellcheck shell=bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Clean start for a Roihu job or compute-node shell. Source it, do not run it:
#
#   source hpc/roihu/job_prelude.sh
#
# Jobs run with --export=NONE, so nothing leaks in from the submitting shell.
# On a fresh compute-node shell HOME and USER can be empty and the module
# command can be missing. This sets HOME and USER from the password database
# when they are empty, sources /etc/profile when 'module' is not available,
# and runs 'module purge'. Source hpc/roihu/env.sh only after this.

if [[ -z "${HOME:-}" || -z "${USER:-}" ]]; then
  tiefer_passwd="$(getent passwd "$(id -u)")"
  if [[ -z "${USER:-}" ]]; then
    USER="$(cut -d: -f1 <<<"${tiefer_passwd}")"
    export USER
  fi
  if [[ -z "${HOME:-}" ]]; then
    HOME="$(cut -d: -f6 <<<"${tiefer_passwd}")"
    export HOME
  fi
  unset tiefer_passwd
fi

# /etc/profile and the module command are not written for 'set -u'.
tiefer_nounset=0
[[ $- == *u* ]] && tiefer_nounset=1
set +u
if ! command -v module >/dev/null 2>&1 && [[ -r /etc/profile ]]; then
  # shellcheck disable=SC1091
  source /etc/profile
fi
if ! command -v module >/dev/null 2>&1; then
  echo "error: the 'module' command is not available, even after sourcing /etc/profile" >&2
  [[ "${tiefer_nounset}" == "1" ]] && set -u
  return 1 2>/dev/null || exit 1
fi
module purge
[[ "${tiefer_nounset}" == "1" ]] && set -u
unset tiefer_nounset
