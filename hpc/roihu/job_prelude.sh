# shellcheck shell=bash
# "return N || exit N" stops a sourced file with return and an executed one with
# exit; shellcheck reads the exit as unreachable (SC2317), so that check is off here.
# shellcheck disable=SC2317
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Clean start for a Roihu job. Source it, do not run it:
#
#   source hpc/roihu/job_prelude.sh
#
# The module environment belongs to the node the job runs on. CPU jobs take it
# from roihu-cpu.csc.fi through sbatch's default export. GPU jobs get only a
# few variables (hpc/roihu/submit.sh) and build it on the GPU node: the job
# script is a login shell (#!/bin/bash --login) and CSC_ENV_INIT_NON_INTERACTIVE
# is yes, so /etc/profile.d/zz-csc-env.sh initialises the CSC environment and
# the module system for that node's architecture. When 'module' is still
# missing, for example in a shell that setup.sh starts inside the job, this
# file runs the same CSC initialisation. Inside a job it also sets
# SLURM_EXPORT_ENV=ALL, so srun passes on the environment the job has built
# instead of the short --export list. Source:
# https://docs.csc.fi/computing/running/submitting-jobs-across-architectures/
#
# Then it prints the node, its architecture and how the environment was made,
# and runs 'module purge' with errexit, nounset and pipefail turned off and the
# caller's options restored afterwards (shell_options.sh). Source
# hpc/roihu/env.sh only after this; it loads the Python module and the virtual
# environment for the node's architecture.

# shellcheck source=hpc/roihu/shell_options.sh
source "$(dirname "${BASH_SOURCE[0]}")/shell_options.sh"

TIEFER_NODE_ARCH="$(uname -m)"
export TIEFER_NODE_ARCH

# CSC's initialisation of a non-interactive shell; the path can be changed for tests.
tiefer_init_csc_env() {
  local init="${TIEFER_CSC_ENV_INIT:-/etc/profile.d/zz-csc-env.sh}"
  [[ -r "${init}" ]] || return 0
  export CSC_ENV_INIT_NON_INTERACTIVE=yes
  tiefer_relax_shell
  # shellcheck source=/dev/null
  source "${init}"
  tiefer_restore_shell
}
if ! command -v module >/dev/null 2>&1; then
  tiefer_init_csc_env
fi
if ! command -v module >/dev/null 2>&1; then
  echo "error: the 'module' command is not available in this ${TIEFER_NODE_ARCH} job; submit it with hpc/roihu/submit.sh from a Roihu login node" >&2
  return 1 2>/dev/null || exit 1
fi

if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  export SLURM_EXPORT_ENV=ALL
  if [[ "${CSC_ENV_INIT_NON_INTERACTIVE:-}" == "yes" ]]; then
    tiefer_made="built on this node"
  else
    tiefer_made="inherited from the login node"
  fi
  echo "job environment: node $(hostname) (${TIEFER_NODE_ARCH}), submitted on ${TIEFER_SUBMIT_HOST_ARCH:-${TIEFER_NODE_ARCH}}, module environment ${tiefer_made}"
  unset tiefer_made
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
