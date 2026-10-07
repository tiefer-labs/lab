<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Extending Tiefer Lab

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For contributors who build on Tiefer Lab. This document owns the golden paths: for each kind of extension, the files to change, the tests to add, the documents to update and the evidence required before a result may appear in [docs/RESULTS.md](docs/RESULTS.md). The process of a contribution is in [CONTRIBUTING.md](CONTRIBUTING.md), and the gates in [POLICY.md](POLICY.md).

---

## 1. Before any extension

1. Open an issue that states what you add and why ([CONTRIBUTING.md](CONTRIBUTING.md), section 2). A change to metrics, splits, thresholds or the evaluation protocol needs the maintainer's agreement first ([GOVERNANCE.md](GOVERNANCE.md), section 2).
2. Follow the path below for your extension.
3. Run `make check`, and `make smoke SMOKE_SOURCE=synthetic` when the pipeline changes ([GETTING-STARTED.md](GETTING-STARTED.md)).
4. Update [INDEX.md](INDEX.md) for a new Markdown file and [CLAIMS.md](CLAIMS.md) for a new capability; status `IMPLEMENTED` until a result passes gate 1 of [POLICY.md](POLICY.md).

---

## 2. Add a training config

| Step | What |
| :--- | :---: |
| Files | a new `configs/<name>.toml` with the MPL notice, a comment on what it changes and against which config; the keys are the fields of `DataConfig`, `ModelConfig`, `TrainConfig`, `EvaluationConfig` and `ExportConfig` in `src/tiefer_lab/config.py` |
| Tests | `tests/test_config.py::test_repository_configs_load` loads every config; for a variant of the L2 family, extend `tests/test_config.py::test_l2_ladder_sizes_and_one_change_per_variant`; for an L1 config, add it to `tests/test_model_budget.py::test_parameter_budget` |
| Documents | the settings table of [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 6, when the config differs from its family; the configs list of [docs/SPEC.md](docs/SPEC.md), section 14; a row in [hpc/roihu/plan.md](hpc/roihu/plan.md) with its estimated cost before a run |
| Evidence for RESULTS.md | the evaluation report of a run made from a commit that holds the config unchanged (`"dirty": false`); gates 1 and 7 of [POLICY.md](POLICY.md) |

---

## 3. Add a band set

| Step | What |
| :--- | :---: |
| Files | `train.band_sets` of an L2 config; band names must be Level-1C band names of `L1C_BAND_NAMES` in `src/tiefer_lab/data/source.py`; the cache must hold the bands (`--bands all`, [docs/DATA.md](docs/DATA.md), section 10) |
| Tests | `tests/test_flexible_model.py::test_band_set_model_matches_the_flexible_model` and `tests/test_flexible_pipeline.py::test_flexible_model_trains_evaluates_and_exports_per_band_set` cover every band set of a config |
| Documents | the band table of [docs/DATA.md](docs/DATA.md), section 2.1 (column "Used by"); for bands of another sensor, the band-matching rule of [docs/DATASETS.md](docs/DATASETS.md), section 3 |
| Evidence for RESULTS.md | an evaluation per band set (`python -m tiefer_lab.evaluate --band-set <bands>`) and, for export, one ONNX file per band set (`python -m tiefer_lab.export --band-set <bands>`) |

---

## 4. Add a model architecture or size

| Step | What |
| :--- | :---: |
| Files | a module in `src/tiefer_lab/models/`; its name in `ARCHITECTURES` and a branch in `backbone()` of `src/tiefer_lab/models/flexible.py`; the literal of `ModelConfig.architecture` in `src/tiefer_lab/config.py`. A new size is a config with other `model.widths` |
| Tests | copy `tests/test_flexible_model.py::test_convnext_unet_shapes_and_operations`; check the ONNX operators with `tests/test_model_budget.py::test_onnx_operators_are_allowed_and_batch_norm_is_folded`; only operators that TensorRT handles well in INT8 are allowed ([docs/SPEC.md](docs/SPEC.md), section 4) |
| Documents | [docs/SPEC.md](docs/SPEC.md), section 8; the size ladder of [hpc/roihu/plan.md](hpc/roihu/plan.md) |
| Evidence for RESULTS.md | parameters and multiply-accumulates from `metadata.json` (`count_parameters`, `count_macs` in `src/tiefer_lab/models/cloud_filter.py`), and the evaluation and export reports of a clean run |

---

## 5. Add a metric

| Step | What |
| :--- | :---: |
| Files | a function in `src/tiefer_lab/metrics.py` (pixel and frame metrics) or `src/tiefer_lab/binary_metrics.py` (per-patch binary problems); its call in `evaluate_run()` of `src/tiefer_lab/evaluate.py`; intervals with `src/tiefer_lab/bootstrap.py` |
| Tests | a test by hand, like `tests/test_metrics.py::test_iou_f1_accuracy_by_hand` or `tests/test_binary_metrics.py::test_cloud_problem_by_hand`, with an undefined case like `tests/test_metrics.py::test_false_discard_rate_undefined_without_useful_frames` |
| Documents | the metric definitions of [docs/RESULTS.md](docs/RESULTS.md), section 2; for a metric that matches a published one, [docs/DATASETS.md](docs/DATASETS.md), section 4; a changelog line in [docs/SPEC.md](docs/SPEC.md), because the evaluation protocol changes ([GOVERNANCE.md](GOVERNANCE.md), section 2) |
| Evidence for RESULTS.md | evaluation reports written by the commit that adds the metric; values of older reports are not recomputed by hand |

---

## 6. Add a baseline or a reference algorithm

| Step | What |
| :--- | :---: |
| Files | a baseline: a function in `src/tiefer_lab/baselines.py` and its entry in `evaluate_baselines()` of `src/tiefer_lab/evaluate.py`; thresholds are tuned on validation only. A reference mask of the dataset: `REFERENCE_MASK_ITEMS`, `REFERENCE_LINK_FIELD` and `REFERENCE_ENCODINGS` in `src/tiefer_lab/data/source.py`, set only from the survey, then `build_cache --references` |
| Tests | copy `tests/test_baselines.py::test_threshold_rule_predicts_by_hand`; for references, `tests/test_references.py::test_references_are_linked_encoded_and_resumable` and `tests/test_references.py::test_unknown_raw_values_stop_the_encoding` |
| Documents | [docs/RESULTS.md](docs/RESULTS.md), section 10; the algorithm's published values only in [docs/LANDSCAPE.md](docs/LANDSCAPE.md), section 4; the open facts of [docs/DATA.md](docs/DATA.md), section 13 |
| Evidence for RESULTS.md | the baseline or reference scored by this repository's code on the same pixels; gate 5 of [POLICY.md](POLICY.md) before any comparison |

---

## 7. Add a dataset

| Step | What |
| :--- | :---: |
| Files | a reader in `src/tiefer_lab/data/` that stops on every unverified fact with `require_verified()` of `src/tiefer_lab/data/source.py`, as the CloudSEN12+ reader does; a cache through `src/tiefer_lab/data/build_cache.py` |
| Tests | copy `tests/test_bands_and_labels.py::test_unknown_label_code_is_an_error` and `tests/test_extra_patches.py::test_extra_patches_wait_for_verified_facts`; read a synthetic file as `tests/test_bands_and_labels.py::test_read_patch_selects_used_bands_from_synthetic_file` does |
| Documents | a row in the catalogue of [docs/DATASETS.md](docs/DATASETS.md), section 1, with licence, URL and role; a data card like [docs/DATA.md](docs/DATA.md); [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), targets `IND-01` to `IND-04`, when it is an independent test |
| Evidence for RESULTS.md | gate 6 of [POLICY.md](POLICY.md): licence from a primary source, no personal data, data card updated |

---

## 8. Add a perturbation

| Step | What |
| :--- | :---: |
| Files | its name in `PERTURBATIONS` and its handling in `Perturbation` of `src/tiefer_lab/data/sensor.py`; for training, a field of `DataConfig` and a step in `augment()` |
| Tests | copy `tests/test_sensor.py::test_perturbations_parse_and_apply` and `tests/test_sensor.py::test_gain_offset_noise_blur_stay_in_range` |
| Documents | the perturbation table of [docs/RESULTS.md](docs/RESULTS.md), section 13, with what it simulates; it stays `SIMULATED` in [CLAIMS.md](CLAIMS.md) |
| Evidence for RESULTS.md | an evaluation report from `python -m tiefer_lab.evaluate --perturb <kind>=<value>` on validation |

---

## 9. Add a hardware target

| Step | What |
| :--- | :---: |
| Files | scripts in a folder named after the target, like `jetson/`, with a `--dry-run` mode that validates the inputs off the device; reports under `reports/<target>/` |
| Tests | copy `tests/test_jetson_dry_run.py::test_bench_dry_run_off_device` and `tests/test_jetson_dry_run.py::test_latency_throughput_and_energy_formulas`; add the shell scripts to the `Makefile` list so that `tests/test_roihu_scripts.py::test_every_shell_script_is_in_the_shellcheck_list` passes |
| Documents | a folder guide like [jetson/README.md](jetson/README.md); [docs/RESULTS.md](docs/RESULTS.md), section 15; targets `OBD-01` to `OBD-06` of [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md); [CLAIMS.md](CLAIMS.md) |
| Evidence for RESULTS.md | a report written on the device, with device, software versions and power mode, copied unchanged into `reports/` |

---

## 10. Add an HPC site

| Step | What |
| :--- | :---: |
| Files | a folder `hpc/<site>/` with the parts of `hpc/roihu/`: an environment script that sets the `TIEFER_*` locations (`src/tiefer_lab/utils/paths.py`), a submit wrapper, job scripts, a setup script and `collect.sh`; no project numbers or personal paths in any file |
| Tests | copy the tests of `tests/test_roihu_scripts.py` with stub `sbatch` and `sacct`, for example `tests/test_roihu_scripts.py::test_submit_adds_account_and_log_location` and `tests/test_roihu_scripts.py::test_collect_packs_relative_paths_only`; `tests/test_public_hygiene.py` checks the files |
| Documents | a guide `hpc/<site>/README.md` with its own facts table and sources; [INSTALL.md](INSTALL.md), section 1; a plan with costs before the first run ([POLICY.md](POLICY.md), gate 7) |
| Evidence for RESULTS.md | report files with Slurm fields and the compute report of every job ([docs/RESULTS.md](docs/RESULTS.md), section 16) |

---

## Changelog

- 7 October 2026: first version: golden paths for a config, a band set, a model, a metric, a baseline or reference, a dataset, a perturbation, a hardware target and an HPC site.
