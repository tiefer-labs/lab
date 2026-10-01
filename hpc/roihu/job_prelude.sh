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
# and runs 'module purge', both with errexit, nounset and pipefail turned off
# and the caller's options restored afterwards (shell_options.sh). Source
# hpc/roihu/env.sh only after this. TIEFER_SYSTEM_PROFILE replaces
# /etc/profile in tests.

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

# shellcheck source=hpc/roihu/shell_options.sh
source "$(dirname "${BASH_SOURCE[0]}")/shell_options.sh"

# /etc/profile and the module command are not written for 'set -euo pipefail':
# on Roihu a profile.d script ends with a non-zero 'return'.
if ! command -v module >/dev/null 2>&1; then
  tiefer_system_profile="${TIEFER_SYSTEM_PROFILE:-/etc/profile}"
  if [[ -r "${tiefer_system_profile}" ]]; then
    tiefer_relax_shell
    # shellcheck disable=SC1090,SC1091
    source "${tiefer_system_profile}"
    tiefer_restore_shell
  fi
  unset tiefer_system_profile
fi
if ! command -v module >/dev/null 2>&1; then
  echo "error: the 'module' command is not available, even after sourcing /etc/profile" >&2
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
