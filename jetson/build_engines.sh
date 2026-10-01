#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Build TensorRT engines from the exported ONNX files with trtexec.
#
#   bash jetson/build_engines.sh --fp32 <cloud_filter_fp32.onnx> --int8 <cloud_filter_int8.onnx> --out <dir>
#   bash jetson/build_engines.sh ... --calib <calibration.cache>   # implicit INT8 instead
#   bash jetson/build_engines.sh ... --dry-run                       # validate and print the plan
#
# FP16 engine: from the FP32 ONNX with --fp16.
# INT8 engine: from the QDQ ONNX (explicit quantisation, scales calibrated on
# training patches by tiefer_lab.export), or, with --calib, from the FP32 ONNX
# with a TensorRT calibration cache (implicit quantisation).
# On a machine that is not a Jetson, the script runs as a dry run.
set -euo pipefail

fp32="" int8="" out="" calib="" dry_run=0
trtexec="${TRTEXEC:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fp32) fp32="$2"; shift 2 ;;
    --int8) int8="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --calib) calib="$2"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    *) echo "error: unknown argument $1" >&2; exit 2 ;;
  esac
done

fail() { echo "error: $*" >&2; exit 2; }
[[ -n "$fp32" && -n "$out" ]] || fail "--fp32 and --out are required"
[[ -f "$fp32" ]] || fail "FP32 ONNX not found: $fp32"
if [[ -n "$calib" ]]; then
  [[ -f "$calib" ]] || fail "calibration cache not found: $calib"
else
  [[ -n "$int8" ]] || fail "--int8 (QDQ ONNX) or --calib is required"
  [[ -f "$int8" ]] || fail "INT8 ONNX not found: $int8"
fi

if [[ -z "$trtexec" ]]; then
  trtexec="$(command -v trtexec || true)"
  [[ -z "$trtexec" && -x /usr/src/tensorrt/bin/trtexec ]] && trtexec=/usr/src/tensorrt/bin/trtexec
fi

fp16_cmd=("${trtexec:-trtexec}" "--onnx=$fp32" --fp16 "--saveEngine=$out/cloud_filter_fp16.engine")
if [[ -n "$calib" ]]; then
  int8_cmd=("${trtexec:-trtexec}" "--onnx=$fp32" --int8 --fp16 "--calib=$calib" "--saveEngine=$out/cloud_filter_int8.engine")
else
  int8_cmd=("${trtexec:-trtexec}" "--onnx=$int8" --int8 --fp16 "--saveEngine=$out/cloud_filter_int8.engine")
fi

if [[ $dry_run -eq 1 || ! -f /etc/nv_tegra_release || -z "$trtexec" ]]; then
  echo "dry run: inputs are valid. Plan:"
  echo "  mkdir -p $out"
  echo "  ${fp16_cmd[*]}"
  echo "  ${int8_cmd[*]}"
  exit 0
fi

mkdir -p "$out"
"${fp16_cmd[@]}"
"${int8_cmd[@]}"
echo "engines written to $out"
