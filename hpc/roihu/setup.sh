#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# One-time setup on CSC Roihu: create the virtual environment for this
# node's architecture, install the pinned dependencies and the package, and
# run the environment check.
#
#   bash hpc/roihu/setup.sh   # on roihu-gpu.csc.fi (required, ARM)
#   bash hpc/roihu/setup.sh   # on roihu-cpu.csc.fi (only for data.sbatch, x86)
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=hpc/roihu/env.sh
source "${repo}/hpc/roihu/env.sh"

echo "architecture: ${TIEFER_ARCH}"
echo "python: $(command -v python3) ($(python3 --version))"

if [[ ! -d "${TIEFER_VENV}" ]]; then
  python3 -m venv --system-site-packages "${TIEFER_VENV}"
fi
# shellcheck disable=SC1091
source "${TIEFER_VENV}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install -r "${repo}/hpc/roihu/requirements.txt"
python3 -m pip install --no-deps -e "${repo}"

if [[ "${TIEFER_ARCH}" == "aarch64" ]]; then
  python3 "${repo}/hpc/roihu/check_env.py"
else
  python3 "${repo}/hpc/roihu/check_env.py" --data-only
fi
echo "setup complete: ${TIEFER_VENV}"
