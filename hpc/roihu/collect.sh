#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Pack the small result files of a run into one archive for copying back.
#
#   bash hpc/roihu/collect.sh <run-id>
#
# Writes $TIEFER_SCRATCH/collect/tiefer-<run-id>.tar.gz with paths relative to
# $TIEFER_SCRATCH (reports/... and runs/<run-id>/...), so it unpacks into the
# repository on another computer. Contents: evaluation, export and compute
# reports, the test log, run configuration, metadata, metrics, the best
# checkpoint and the ONNX files. Slurm logs are not included.
set -euo pipefail

run_id="${1:?usage: collect.sh <run-id>}"
[[ "${run_id}" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "error: invalid run ID" >&2; exit 2; }
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=hpc/roihu/env.sh
TIEFER_ENV_PATHS_ONLY=1 source "${repo}/hpc/roihu/env.sh"

base="${TIEFER_SCRATCH}"
for dir in "${TIEFER_RUNS_DIR}" "${TIEFER_REPORTS_DIR}"; do
  [[ "${dir}" == "${base}/"* ]] || { echo "error: ${dir} is not under ${base}" >&2; exit 2; }
done
runs_rel="${TIEFER_RUNS_DIR#"${base}/"}"
reports_rel="${TIEFER_REPORTS_DIR#"${base}/"}"
[[ -d "${TIEFER_RUNS_DIR}/${run_id}" ]] || { echo "error: run ${run_id} not found" >&2; exit 2; }

files=()
add() { [[ -e "${base}/$1" ]] && files+=("$1") || true; }
add "${runs_rel}/${run_id}/config.toml"
add "${runs_rel}/${run_id}/metadata.json"
add "${runs_rel}/${run_id}/metrics.jsonl"
add "${runs_rel}/${run_id}/best.pt"
for f in "${TIEFER_RUNS_DIR}/${run_id}"/export/*.onnx; do
  [[ -e "${f}" ]] && files+=("${f#"${base}/"}")
done
for f in "${TIEFER_REPORTS_DIR}"/evaluation/"${run_id}"_*.json "${TIEFER_REPORTS_DIR}"/export/"${run_id}".json "${TIEFER_REPORTS_DIR}"/compute/*.json; do
  [[ -e "${f}" ]] && files+=("${f#"${base}/"}")
done
add "${reports_rel}/test_log.md"
add "${reports_rel}/data/survey.json"

mkdir -p "${base}/collect"
archive="${base}/collect/tiefer-${run_id}.tar.gz"
tar -czf "${archive}" -C "${base}" "${files[@]}"
echo "packed ${#files[@]} files:"
tar -tzf "${archive}"
echo "archive: \$TIEFER_SCRATCH/collect/tiefer-${run_id}.tar.gz"
