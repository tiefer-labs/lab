#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Download and cache one independent test dataset on a CPU node.
#
#   bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch <dataset> [extra build_cache arguments]
#
# <dataset>: s2_cloud_catalogue or kappaset (downloaded here), or landsat8_sparcs or
# landsat8_biome (downloaded by hand into $TIEFER_DATA_DIR/downloads/<dataset>/ first,
# hpc/roihu/plan.md, section 3.9), the datasets of src/tiefer_lab/data/independent.py
# that the maintainer's licence decisions record as used (docs/DATASETS.md); any other
# dataset, azersky included, stops with its decision before anything is downloaded. The
# Zenodo files are downloaded into
# $TIEFER_DATA_DIR/downloads/<dataset>/ with a capped rate (TIEFER_DOWNLOAD_RATE,
# default 20M per second) and resumed where a download stopped; an archive is
# unpacked once, and deleted once the cache is complete (TIEFER_KEEP_DOWNLOADS=1 keeps them).
# The build stops on every fact that is not verified (docs/INDEPENDENT.md,
# section 6) and resumes at the next scene when submitted again. Sentinel-2
# datasets drop the products used by CloudSEN12+ first, so the CloudSEN12+
# cache must be complete (TIEFER_CLOUDSEN12_CACHE, default cloudsen12-l1c-all).
#
# CPU partition 'small': up to 72 hours on one node.
# Source: https://docs.csc.fi/computing/running/batch-job-partitions/
#SBATCH --job-name=tiefer-independent
#SBATCH --partition=small
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
set -euo pipefail

case "$(uname -m)" in
  aarch64 | x86_64) ;;
  *)
    echo "error: unsupported architecture $(uname -m); expected aarch64 or x86_64" >&2
    exit 1
    ;;
esac

dataset="${1:?usage: independent.sbatch <dataset> [build_cache arguments]}"
shift || true
case "${dataset}" in
  s2_cloud_catalogue)
    record="4172871"
    files=(classification_tags.csv masks.zip subscenes.zip README.pdf)
    ;;
  kappaset)
    record="7100327"
    files=(kappaset.zip README.pdf)
    ;;
  landsat8_sparcs | landsat8_biome)
    # Downloaded by hand; the build reads the files already there.
    record=""
    files=()
    ;;
  *)
    record=""
    files=()
    unknown=1
    ;;
esac

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
# The licence decision of the dataset is read from its record; a refused dataset
# stops here with the decision, before any download.
python3 -c 'import sys; from tiefer_lab.data import independent; independent.require_dataset_allowed(sys.argv[1])' "${dataset}"
if [[ "${unknown:-0}" == "1" ]]; then
  echo "error: unknown dataset '${dataset}'" >&2
  exit 2
fi
python3 hpc/roihu/check_env.py --data-only

root="${TIEFER_DATA_DIR}/downloads/${dataset}"
mkdir -p "${root}"
rate="${TIEFER_DOWNLOAD_RATE:-20M}"
for name in "${files[@]}"; do
  if [[ -f "${root}/${name}.done" ]]; then
    continue
  fi
  echo "download ${dataset}/${name} (resumable, at most ${rate} per second)"
  curl --fail --location --retry 5 --retry-delay 30 --continue-at - --limit-rate "${rate}" \
    --output "${root}/${name}" "https://zenodo.org/records/${record}/files/${name}?download=1"
  if [[ "${name}" == *.zip ]]; then
    python3 -m zipfile -e "${root}/${name}" "${root}/"
  fi
  touch "${root}/${name}.done"
done
if [[ -z "${record}" && -z "$(ls -A "${root}")" ]]; then
  echo "error: download ${dataset} by hand from its source page into \$TIEFER_DATA_DIR/downloads/${dataset}/" >&2
  exit 2
fi

extra=()
if [[ "${dataset}" == s2_cloud_catalogue || "${dataset}" == kappaset ]]; then
  extra=(--cloudsen12-cache "${TIEFER_CLOUDSEN12_CACHE:-cloudsen12-l1c-all}")
fi
python3 -m tiefer_lab.data.build_cache --split test --source "${dataset}" --root "${root}" \
  "${extra[@]}" "$@"

# Archives are deleted once the cache is built and checked: its test split is
# complete in its index (the builder verifies the counts before it marks it). The
# cache stays on /scratch; TIEFER_KEEP_DOWNLOADS=1 keeps the downloads.
if python3 -c 'import sys; from tiefer_lab.data import cache; sys.exit(0 if cache.read_index(cache.cache_dir(sys.argv[1]))["splits"]["test"].get("complete") else 1)' "${dataset}"; then
  if [[ "${TIEFER_KEEP_DOWNLOADS:-0}" != "1" ]]; then
    rm -rf "${root}"
    echo "cache ${dataset} complete; downloads deleted"
  fi
else
  echo "cache ${dataset} not complete; downloads kept for the next run"
fi
