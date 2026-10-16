# shellcheck shell=bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# The worst-case cost of a job before it is submitted, against what is left.
# Sourced by submit.sh and sweep.sh:
#
#   tiefer_budget_check <jobs> <job script> [sbatch options]
#
# A running job finishes even past a zero balance, and a project whose balance
# stays negative is closed after 60 days; when the storage BUs run out, no job
# can be submitted and access to /scratch and /projappl ends 30 days later
# (https://docs.csc.fi/computing/usage-policy/, page of 15 October 2026, read
# 16 October 2026). So every submission is refused when its worst case does not
# fit:
#
#   GPU partitions:  time limit x GPUs x 200 BU
#   small, test and the other core-based CPU partitions:
#                    time limit x max(0.75 BU x cores, 0.375 BU x GiB of memory)
#   medium, large:   time limit x nodes x 288 BU
#
# (https://docs.csc.fi/computing/hpc-billing/, page of 15 October 2026, read
# 16 October 2026). The balance left is never fetched here: copy it from your own
# `csc-projects` output into TIEFER_GPU_BU_LEFT, TIEFER_CPU_BU_LEFT and
# TIEFER_STORAGE_BU_LEFT. The reserve kept back is TIEFER_GPU_BU_RESERVE (default
# 500, the reserve under the stop line of hpc/roihu/plan.md) and
# TIEFER_CPU_BU_RESERVE (default 0).

# A Slurm time limit (minutes, MM:SS, HH:MM:SS, D-HH, D-HH:MM, D-HH:MM:SS) in hours.
tiefer_hours() {
  awk -v t="$1" 'BEGIN {
    days = 0
    if (index(t, "-")) { split(t, d, "-"); days = d[1]; t = d[2]; dashed = 1 }
    n = split(t, p, ":")
    if (dashed) { h = p[1]; m = (n >= 2 ? p[2] : 0); s = (n >= 3 ? p[3] : 0) }
    else if (n == 1) { h = 0; m = p[1]; s = 0 }
    else if (n == 2) { h = 0; m = p[1]; s = p[2] }
    else { h = p[1]; m = p[2]; s = p[3] }
    printf "%.6f", days * 24 + h + m / 60 + s / 3600
  }'
}

# GiB from a Slurm memory value (K, M, G, T suffix; no suffix is MiB).
tiefer_gib() {
  awk -v m="$1" 'BEGIN {
    unit = toupper(substr(m, length(m)))
    value = m + 0
    if (unit == "K") value /= 1048576
    else if (unit == "M" || unit ~ /[0-9]/) value /= 1024
    else if (unit == "T") value *= 1024
    printf "%.6f", value
  }'
}

# Prints "<kind> <cost>" for one job: kind is gpu or cpu.
tiefer_job_cost() {
  local script="$1"
  shift
  local partition time gres cpus mem nodes value
  partition="$(sed -n 's/^#SBATCH --partition=//p' "${script}" | head -n 1)"
  time="$(sed -n 's/^#SBATCH --time=//p' "${script}" | head -n 1)"
  gres="$(sed -n 's/^#SBATCH --gres=//p' "${script}" | head -n 1)"
  cpus="$(sed -n 's/^#SBATCH --cpus-per-task=//p' "${script}" | head -n 1)"
  mem="$(sed -n 's/^#SBATCH --mem=//p' "${script}" | head -n 1)"
  nodes="$(sed -n 's/^#SBATCH --nodes=//p' "${script}" | head -n 1)"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --partition=*) partition="${1#*=}" ;;
      --time=*) time="${1#*=}" ;;
      --gres=*) gres="${1#*=}" ;;
      --cpus-per-task=*) cpus="${1#*=}" ;;
      --mem=*) mem="${1#*=}" ;;
      --nodes=*) nodes="${1#*=}" ;;
      -p | -t | -c | -N | --partition | --time | --gres | --cpus-per-task | --mem | --nodes)
        value="${2:-}"
        case "$1" in
          -p | --partition) partition="${value}" ;;
          -t | --time) time="${value}" ;;
          --gres) gres="${value}" ;;
          -c | --cpus-per-task) cpus="${value}" ;;
          --mem) mem="${value}" ;;
          -N | --nodes) nodes="${value}" ;;
        esac
        shift
        ;;
    esac
    shift
  done
  [[ -n "${time}" ]] || { echo "error: ${script} has no time limit, so its cost cannot be bounded" >&2; return 2; }
  local hours
  hours="$(tiefer_hours "${time}")"
  if [[ "${gres}" == gpu:* ]]; then
    awk -v h="${hours}" -v g="${gres##*:}" 'BEGIN { printf "gpu %.1f\n", h * g * 200 }'
  elif [[ "${partition}" == medium || "${partition}" == large ]]; then
    awk -v h="${hours}" -v n="${nodes:-1}" 'BEGIN { printf "cpu %.1f\n", h * n * 288 }'
  else
    [[ -n "${mem}" ]] || { echo "error: ${script} has no --mem, so its CPU cost cannot be bounded" >&2; return 2; }
    awk -v h="${hours}" -v c="${cpus:-1}" -v m="$(tiefer_gib "${mem}")" \
      'BEGIN { a = 0.75 * c; b = 0.375 * m; printf "cpu %.1f\n", h * (a > b ? a : b) }'
  fi
}

# Refuse when <jobs> jobs of this script do not fit in what is left.
tiefer_budget_check() {
  local jobs="$1"
  shift
  local script="$1"
  shift
  local kind cost
  read -r kind cost < <(tiefer_job_cost "${script}" "$@") || return 2
  [[ -n "${kind}" ]] || return 2
  local storage="${TIEFER_STORAGE_BU_LEFT:-}"
  if [[ ! "${storage}" =~ ^-?[0-9]+([.][0-9]+)?$ ]]; then
    echo "error: set TIEFER_STORAGE_BU_LEFT to the storage BU left in your csc-projects output" >&2
    return 2
  fi
  if awk -v s="${storage}" 'BEGIN { exit !(s <= 0) }'; then
    echo "error: no storage BU left (${storage}): no job can be submitted, and access to /scratch and /projappl ends 30 days later" >&2
    return 2
  fi
  local left reserve name
  if [[ "${kind}" == gpu ]]; then
    name=GPU
    left="${TIEFER_GPU_BU_LEFT:-}"
    reserve="${TIEFER_GPU_BU_RESERVE:-500}"
  else
    name=CPU
    left="${TIEFER_CPU_BU_LEFT:-}"
    reserve="${TIEFER_CPU_BU_RESERVE:-0}"
  fi
  if [[ ! "${left}" =~ ^-?[0-9]+([.][0-9]+)?$ ]]; then
    echo "error: set TIEFER_${name}_BU_LEFT to the ${name} BU left in your csc-projects output" >&2
    return 2
  fi
  if ! awk -v n="${jobs}" -v c="${cost}" -v l="${left}" -v r="${reserve}" 'BEGIN { exit !(n * c <= l - r) }'; then
    awk -v n="${jobs}" -v c="${cost}" -v l="${left}" -v r="${reserve}" -v k="${name}" \
      'BEGIN { printf "error: worst case %.1f %s BU (%d job(s) of %.1f) exceeds the %.1f left minus the reserve of %.1f\n", n * c, k, n, c, l, r }' >&2
    return 2
  fi
  awk -v n="${jobs}" -v c="${cost}" -v l="${left}" -v r="${reserve}" -v k="${name}" \
    'BEGIN { printf "worst case %.1f %s BU (%d job(s) of %.1f); %.1f left after it, above the reserve of %.1f\n", n * c, k, n, c, l - n * c, r }'
}
