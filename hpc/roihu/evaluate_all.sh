#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Evaluate one run on every independent dataset of the CloudSEN12 paper's
# Table 1 that the maintainer's licence decisions allow (docs/DATASETS.md),
# one evaluate.sbatch job per dataset, with the baselines and the reference
# masks each dataset holds.
#
#   REASON="<why>" bash hpc/roihu/evaluate_all.sh [--test-only] <run-id>
#
# A dataset whose cache is not built yet (independent.sbatch) is listed and
# skipped, never guessed. The list is allowed_datasets() of
# src/tiefer_lab/data/independent.py, in the order of the paper's Table 1
# (tests/test_paper_models.py checks it); reports/coverage.md
# (python -m tiefer_lab.paper_models) shows what is still not measured.
set -euo pipefail

usage='usage: REASON="<why>" bash hpc/roihu/evaluate_all.sh [--test-only] <run-id>'
options=()
if [[ "${1:-}" == "--test-only" ]]; then
  options+=(--test-only)
  shift
fi
run_id="${1:?${usage}}"
: "${REASON:?${usage}}"
datasets=(
  landsat8_sparcs
  landsat8_biome
  s2_cloud_catalogue
  whus2_cd
  kappaset
)
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
missing=()
for dataset in "${datasets[@]}"; do
  if [[ ! -f "${TIEFER_DATA_DIR:?TIEFER_DATA_DIR is not set; source hpc/roihu/env.sh}/${dataset}/index.json" ]]; then
    missing+=("${dataset}")
    continue
  fi
  DATA="${dataset}" FULL_METRICS=1 bash "${here}/submit.sh" "${options[@]}" \
    hpc/roihu/evaluate.sbatch "${run_id}"
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "not built yet, skipped: ${missing[*]} (bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch <dataset>)" >&2
fi
