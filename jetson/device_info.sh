#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Device facts for the Jetson benchmark, as key=value lines:
# board model, L4T release, JetPack and TensorRT package versions, power mode
# (nvpmodel -q) and current clocks (jetson_clocks --show).
#
#   bash jetson/device_info.sh            # on a Jetson board
#   bash jetson/device_info.sh --dry-run  # anywhere: print what would be read
#
# TODO(verify) on the board: whether nvpmodel -q and jetson_clocks --show
# need sudo on the installed JetPack version.
set -euo pipefail

plan() {
  echo "dry run: device_info.sh would read"
  echo "  /proc/device-tree/model"
  echo "  /etc/nv_tegra_release"
  echo "  dpkg-query -W nvidia-jetpack tensorrt"
  echo "  nvpmodel -q"
  echo "  jetson_clocks --show"
}

if [[ "${1:-}" == "--dry-run" || ! -f /etc/nv_tegra_release ]]; then
  plan
  exit 0
fi

oneline() { tr '\n' ' ' | tr -s ' ' | sed 's/ $//'; }

echo "model=$(tr -d '\0' < /proc/device-tree/model)"
echo "l4t=$(head -n 1 /etc/nv_tegra_release | oneline)"
echo "jetpack=$(dpkg-query -W -f='${Version}' nvidia-jetpack 2>/dev/null || echo unknown)"
echo "tensorrt=$(dpkg-query -W -f='${Version}' tensorrt 2>/dev/null || echo unknown)"
echo "nvpmodel=$(nvpmodel -q 2>&1 | oneline || echo unknown)"
echo "jetson_clocks=$(jetson_clocks --show 2>&1 | head -n 20 | oneline || echo unknown)"
