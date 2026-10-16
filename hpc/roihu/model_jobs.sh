# shellcheck shell=bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# The bodies of the jobs that read a trained run without training it:
# evaluation, calibration, export and the INT8 diagnosis. Each has a CPU job
# (evaluate_cpu.sbatch, calibrate_cpu.sbatch, export_cpu.sbatch, the int8
# command of diagnose.sbatch), the default of hpc/roihu/plan.md, and the
# GPU job of the same name without _cpu. Source it after env.sh:
#
#   source hpc/roihu/model_jobs.sh
#   tiefer_evaluate_job <run-id>
#
# TIEFER_DEVICE (cpu in the CPU jobs, auto in the GPU jobs) is passed to the
# commands that take --device; export and the INT8 diagnosis run on the CPU
# in either job (ONNX Runtime, CPUExecutionProvider).

# Stop with a clear message when the environment has no torch (an x86 venv
# made before the CPU build of torch was installed by setup.sh).
tiefer_require_torch() {
  if ! python3 -c 'import torch' 2>/dev/null; then
    echo "error: torch is not installed in ${TIEFER_VENV}; run 'bash hpc/roihu/setup.sh' on this architecture again" >&2
    exit 1
  fi
}

# One CPU thread per reserved core, never the whole node.
tiefer_cpu_threads() {
  export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
  export MKL_NUM_THREADS="${OMP_NUM_THREADS}"
  echo "cpu threads: ${OMP_NUM_THREADS}"
}

tiefer_cache_of_run() {
  python3 -c 'import sys; from tiefer_lab.config import load_config; from tiefer_lab.train import resolve_run_dir; print(load_config(resolve_run_dir(sys.argv[1]) / "config.toml").data.cache_name)' "$1"
}

tiefer_evaluate_job() {
  local run_id="${1:?usage: evaluate <run-id>}"
  tiefer_stage_cache "$(tiefer_cache_of_run "${run_id}")"
  # Evaluation protocol options, each off unless set (docs/SPEC.md, section 9).
  local eval_options=() split_args=()
  [[ -n "${CLOUD_BIAS:-}" ]] && eval_options+=(--cloud-bias "${CLOUD_BIAS}")
  [[ -n "${FRACTION:-}" ]] && eval_options+=(--fraction "${FRACTION}")
  # DATA=<cache>: an independent dataset cache (build_cache --source), a clean check
  # that needs REASON and is logged; SUBSTITUTE=1 reads B08 from B8A on Landsat 8.
  # FULL_METRICS=1 adds the full metric set, a protocol option off by default.
  if [[ -n "${DATA:-}" ]]; then
    [[ "${FINAL:-0}" == "1" ]] && { echo "error: DATA and FINAL=1 are separate evaluations" >&2; exit 2; }
    split_args=(--data "${DATA}" --reason "${REASON:?DATA needs REASON}")
    [[ "${SUBSTITUTE:-0}" == "1" ]] && split_args+=(--substitute)
  elif [[ "${FINAL:-0}" == "1" ]]; then
    split_args=(--split test --final --reason "${REASON:?FINAL=1 needs REASON}")
  else
    split_args=(--split val)
  fi
  [[ "${FULL_METRICS:-0}" == "1" ]] && split_args+=(--full-metrics)
  split_args+=("${eval_options[@]}" --device "${TIEFER_DEVICE:-auto}")
  python3 -m tiefer_lab.evaluate --run "${run_id}" "${split_args[@]}" --band-set all --baselines

  if [[ "${ROBUSTNESS:-0}" == "1" ]]; then
    local perturbation
    for perturbation in ${PERTURBATIONS:-rescale=0.5 rescale=2 gain=0.9 gain=1.1 offset=0.01 noise=0.01 blur=1}; do
      python3 -m tiefer_lab.evaluate --run "${run_id}" "${split_args[@]}" --band-set all --perturb "${perturbation}"
    done
  fi
}

tiefer_calibrate_job() {
  local run_id="${1:?usage: calibrate <run-id>}"
  tiefer_stage_cache "$(tiefer_cache_of_run "${run_id}")"
  python3 -m tiefer_lab.calibrate --run "${run_id}" --band-set all --device "${TIEFER_DEVICE:-auto}"
}

tiefer_export_job() {
  local run_id="${1:?usage: export <run-id>}"
  tiefer_stage_cache "$(tiefer_cache_of_run "${run_id}")"
  # Export options, each off unless set: CLOUD_BIAS=auto (or a value) folds the cloud
  # bias chosen on validation into the last convolution; EXPORT_CONFIG=configs/<name>.toml
  # takes the [export] settings of a committed config (INT8 calibration variants).
  # INT8 is measured with ONNX Runtime on the CPU: a proxy for CMP-03; the TensorRT
  # values come from the Jetson benchmark.
  local options=()
  [[ -n "${CLOUD_BIAS:-}" ]] && options+=(--cloud-bias "${CLOUD_BIAS}")
  [[ -n "${EXPORT_CONFIG:-}" ]] && options+=(--settings-from "${EXPORT_CONFIG}")
  if [[ "${FINAL:-0}" == "1" ]]; then
    python3 -m tiefer_lab.export --run "${run_id}" --band-set all "${options[@]}" --final --reason "${REASON:?FINAL=1 needs REASON}"
  else
    python3 -m tiefer_lab.export --run "${run_id}" --band-set all "${options[@]}"
  fi
}

tiefer_int8_job() {
  local run_id="${1:?usage: int8 <run-id> [diagnose arguments]}"
  shift
  tiefer_stage_cache "$(tiefer_cache_of_run "${run_id}")"
  python3 -m tiefer_lab.diagnose int8 --run "${run_id}" "$@"
}
