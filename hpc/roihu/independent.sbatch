#!/bin/bash --login
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Download and cache one independent test dataset on a CPU node.
#
#   bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch <dataset> [extra build_cache arguments]
#
# <dataset>: s2_cloud_catalogue, kappaset, landsat8_biome or landsat8_sparcs
# (src/tiefer_lab/data/independent.py). The Zenodo files are downloaded into
# $TIEFER_DATA_DIR/downloads/<dataset>/ with a capped rate (TIEFER_DOWNLOAD_RATE,
# default 20M per second) and resumed where a download stopped; an archive is
# unpacked once. The Landsat 8 datasets are downloaded by hand from their USGS
# pages into the same folder, because their file URLs are not verified yet.
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
  landsat8_biome | landsat8_sparcs)
    record=""
    files=()
    ;;
  *)
    echo "error: unknown dataset '${dataset}'" >&2
    exit 2
    ;;
esac

# shellcheck source=hpc/roihu/job_prelude.sh
source hpc/roihu/job_prelude.sh
# shellcheck source=hpc/roihu/env.sh
source hpc/roihu/env.sh
tiefer_require_venv
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
  echo "error: download ${dataset} by hand from its USGS page into \$TIEFER_DATA_DIR/downloads/${dataset}/" >&2
  exit 2
fi

extra=()
if [[ "${dataset}" == s2_cloud_catalogue || "${dataset}" == kappaset ]]; then
  extra=(--cloudsen12-cache "${TIEFER_CLOUDSEN12_CACHE:-cloudsen12-l1c-all}")
fi
python3 -m tiefer_lab.data.build_cache --split test --source "${dataset}" --root "${root}" \
  "${extra[@]}" "$@"
