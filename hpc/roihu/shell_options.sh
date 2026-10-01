# shellcheck shell=bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Run system code that is not written for 'set -euo pipefail' inside a job
# script that uses it. Source it, do not run it:
#
#   tiefer_relax_shell
#   source /etc/profile     # or: module purge, module load <name>
#   tiefer_restore_shell
#
# On Roihu, /etc/profile.d/colorls.sh ends a non-interactive shell with a
# non-zero 'return', and with errexit set that ends the whole job.
# tiefer_relax_shell saves every 'set -o' option and turns off errexit,
# nounset and pipefail; tiefer_restore_shell restores exactly the saved options.

tiefer_relax_shell() {
  TIEFER_SAVED_SHELL="$(set +o)"
  # A command substitution clears errexit in bash, so it is recorded here.
  if [[ -o errexit ]]; then
    TIEFER_SAVED_SHELL+=$'\nset -o errexit'
  else
    TIEFER_SAVED_SHELL+=$'\nset +o errexit'
  fi
  set +o errexit +o nounset +o pipefail
}

tiefer_restore_shell() {
  eval "${TIEFER_SAVED_SHELL}"
  unset TIEFER_SAVED_SHELL
}
