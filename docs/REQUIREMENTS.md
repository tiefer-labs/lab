<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Requirements

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Every requirement and every acceptance target of milestone L2 has an ID and the test or report that verifies it. `python -m tiefer_lab.requirements` and a test check that no ID is without verification and that no verification points to something missing.

---

## 1. How to read this page

- An ID names one requirement: `REQ-<area>-<number>` for requirements of the code, and the acceptance target IDs of `src/tiefer_lab/acceptance.py` (`ACC`, `IND`, `FRM`, `CMP`, `OBD`, `STD`).
- "Verified by" lists tests as `tests/<file>.py::<test>` and files by their path. Files under `reports/` are generated on CSC Roihu or a Jetson and are not in the repository until they are copied in.
- The status words are those of [STYLE.md](STYLE.md), section 4: `met` and `not met` are judged against the minimum unless the row says target; `pending` means measured, with the value not yet in the repository; `not measured` means never measured.
- A code requirement (`REQ-...`) is met when its tests pass. Every test passed in `make check` on 7 October 2026; that run is the evidence for every `REQ-...` row marked met. Further evidence of a row is given below its table.
- Every acceptance target that needs a measured value is `pending` until the v2 campaign ([hpc/roihu/plan.md](../hpc/roihu/plan.md)). `python -m tiefer_lab.acceptance` writes `reports/acceptance.md` from the report files; it is committed with the report files of the v2 campaign.
- `acceptance.py` defines the accuracy, frame and compression targets on the final test evaluation of the 1 M band-flexible model (`l2_flex_1m`) with the four bands B02, B03, B04 and B08. The product decision between it and the four-band specialist is taken under [ASSUMPTIONS.md](ASSUMPTIONS.md), section 7.
- A status of this page says whether a target is met; whether a value may be quoted, and in which form, is decided by [POLICY.md](../POLICY.md), gate 2, and [BENCHMARK-AUTHORITY.md](../BENCHMARK-AUTHORITY.md).
- A minimum or target written "above" is strict; "at least" and "at most" include the bound. Values are rounded to 3 decimals, half up, as in RESULTS.md.

---

## 2. Data

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-DAT-01` | Only the dataset's high quality 509 x 509 patches are cached for train, val and test; kept and dropped counts are recorded | met | `tests/test_bands_and_labels.py::test_select_keeps_high_quality_509_patches_and_counts_dropped` |
| `REQ-DAT-02` | The reader stops with a clear message when a metadata field it needs is missing | met | `tests/test_bands_and_labels.py::test_missing_split_field_stops_with_a_clear_message` |
| `REQ-DAT-03` | Unknown label codes stop the build | met | `tests/test_bands_and_labels.py::test_unknown_label_code_is_an_error` |
| `REQ-DAT-04` | Builds are resumable, also in the finishing step, and never reread a written patch | met | `tests/test_cache.py::test_real_builder_resumes_after_interruption`, `tests/test_cache.py::test_finishing_step_resumes_after_it_failed` |
| `REQ-DAT-05` | A build with another selection never resets or replaces an existing split | met | `tests/test_cache.py::test_a_limited_build_never_resets_or_replaces_the_full_cache` |
| `REQ-DAT-06` | The finishing step stays within bounded memory (chunked counts and statistics) | met | `tests/test_cache.py::test_class_pixels_are_counted_in_chunks_without_loading_the_split`, `tests/test_cache.py::test_band_statistics_are_chunked` |
| `REQ-DAT-07` | One cache stores all 13 bands; models select their bands by name at load time | met | `tests/test_cache.py::test_bands_are_selected_by_name_at_load_time` |
| `REQ-DAT-08` | Shards never write the same file and merge into the same cache as one build | met | `tests/test_cache.py::test_shards_write_apart_and_merge_into_the_same_cache_as_one_build`, `tests/test_cache.py::test_an_interrupted_merge_resumes` |
| `REQ-DAT-09` | Reads respect a shared rate cap and back off on HTTP 429; the token is never printed | met | `tests/test_cache.py::test_the_rate_cap_is_shared_between_shards`, `tests/test_http.py::test_a_pause_holds_every_reader`, `tests/test_http.py::test_token_goes_to_gdal_and_is_never_printed` |
| `REQ-DAT-10` | Extra training patches never share a location with the validation or test split | met | `tests/test_extra_patches.py::test_built_index_proves_no_training_patch_shares_a_location_with_val_or_test` |
| `REQ-DAT-11` | Facts not yet verified stop the code instead of being guessed | met | `tests/test_extra_patches.py::test_extra_patches_wait_for_verified_facts`, `tests/test_references.py::test_references_wait_for_verified_facts` |
| `REQ-DAT-12` | Reference masks are linked and encoded only with verified encodings; unknown values stop | met | `tests/test_references.py::test_references_are_linked_encoded_and_resumable`, `tests/test_references.py::test_unknown_raw_values_stop_the_encoding` |
| `REQ-DAT-13` | The richness report states class shares, cloud cover bins and shadow per split, and interprets verified metadata fields only | met | `tests/test_richness.py::test_patch_statistics_by_hand`, `tests/test_richness.py::test_field_summary_reports_verified_fields_only` |

---

## 3. Training

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-TRN-01` | Training is resumable and gives the same result after an interruption | met | `tests/test_checkpoint_resume.py::test_interrupted_run_resumes_to_the_same_result` |
| `REQ-TRN-02` | Runs with different seeds never share a run folder; the seed is recorded | met | `tests/test_checkpoint_resume.py::test_seed_override_goes_into_metadata_and_run_id` |
| `REQ-TRN-03` | Learning rate warm-up and cosine decay, and a moving average of the weights for validation and best.pt | met | `tests/test_checkpoint_resume.py::test_learning_rate_warms_up_linearly_then_follows_a_cosine_to_zero`, `tests/test_checkpoint_resume.py::test_best_checkpoint_holds_the_averaged_weights` |
| `REQ-TRN-04` | Unavailable bands never change the output of a band-flexible model | met | `tests/test_flexible_model.py::test_unavailable_bands_never_change_the_output` |
| `REQ-TRN-05` | Pixels without a label add nothing to the loss | met | `tests/test_flexible_model.py::test_ignored_pixels_add_nothing_to_the_loss` |
| `REQ-TRN-06` | The size ladder hits its parameter targets and every variant changes one setting | met | `tests/test_config.py::test_l2_ladder_sizes_and_one_change_per_variant` |
| `REQ-TRN-07` | Every run records its config, seed, commit, job ID and GPU hours; reports/experiments.md is built from the run folders | met | `tests/test_checkpoint_resume.py::test_run_metadata_has_provenance_and_no_absolute_paths`, `tests/test_experiments.py::test_one_row_per_run_from_its_folder` |

Further evidence: `REQ-TRN-07`: the metadata test passes; no run of the v2 campaign exists yet.

---

## 4. Evaluation

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-EVL-01` | The test split is used only with FINAL=1 and a reason, and every use is logged | pending | `tests/test_test_guard.py::test_test_split_refuses_without_final`, `tests/test_test_guard.py::test_final_test_evaluation_is_logged_first` |
| `REQ-EVL-02` | BOA, PA, UA and OA per patch for cloud and shadow, with the median and bootstrap intervals | met | `tests/test_binary_metrics.py::test_cloud_problem_by_hand`, `tests/test_binary_metrics.py::test_scores_leave_ignored_pixels_out_and_report_intervals` |
| `REQ-EVL-03` | Reference algorithms are scored by this repository's code on the same patches | met | `tests/test_binary_metrics.py::test_binary_only_scores_report_the_cloud_problem_only`, `tests/test_references.py::test_references_are_linked_encoded_and_resumable` |
| `REQ-EVL-04` | Expected calibration error and the worst stratum are reported | met | `tests/test_binary_metrics.py::test_expected_calibration_error_by_hand`, `tests/test_binary_metrics.py::test_worst_stratum_is_named` |
| `REQ-EVL-05` | Sensor perturbations are measured as fixed perturbations on validation | met | `tests/test_sensor.py::test_perturbations_parse_and_apply` |
| `REQ-EVL-06` | Report files are read only with their git provenance, and smoke reports are never read as results | met | `tests/test_reports.py::test_smoke_reports_are_never_loaded`, `tests/test_reports.py::test_a_report_without_git_provenance_is_refused` |
| `REQ-EVL-07` | Evaluation and export cover every band set of a run when asked for all of them | met | `tests/test_flexible_pipeline.py::test_flexible_model_trains_evaluates_and_exports_per_band_set`, `tests/test_roihu_scripts.py::test_evaluate_and_export_cover_every_band_set` |

Further evidence:

- `REQ-EVL-01`: the guard's tests pass; `reports/test_log.md` has no entries yet. The status stays pending until the first logged test evaluation of the v2 campaign is copied in.
- `REQ-EVL-03`: the code is tested; no reference algorithm has been scored yet ([RESULTS.md](RESULTS.md), section 10).
- `REQ-EVL-05`: verified by the perturbation test; no robustness result yet (v2 pending).
- `REQ-EVL-07`: verified by the tests; no result per band set yet (v2 pending).

---

## 5. Export

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-EXP-01` | ONNX FP32 matches PyTorch; FP16 and INT8 are measured against FP32 | met | `tests/test_export.py::test_fp32_round_trip_matches_pytorch`, `tests/test_quantise.py::test_int8_model_is_qdq_and_scores`, `tests/test_binary_metrics.py::test_int8_comparison_reports_the_boa_change` |
| `REQ-EXP-02` | One ONNX file per band set takes only the bands of that set | met | `tests/test_flexible_pipeline.py::test_flexible_model_trains_evaluates_and_exports_per_band_set`, `tests/test_flexible_model.py::test_band_set_model_matches_the_flexible_model` |

Further evidence: `REQ-EXP-01`: verified by the tests; no export report yet (v2 pending).

---

## 6. On board

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-OBD-01` | Invalid, missing, saturated or out-of-domain input never causes a discarded frame; the frame is sent and flagged | met | `tests/test_onboard.py::test_invalid_input_is_sent_and_flagged_never_kept`, `tests/test_onboard.py::test_failsafe_check_counts_no_discarded_frame` |
| `REQ-OBD-02` | The model file hash is checked before inference; a mismatch stops inference with a clear status | met | `tests/test_onboard.py::test_corrupted_model_files_stop_inference` |
| `REQ-OBD-03` | No exception during inference ends in a discarded frame | met | `tests/test_onboard.py::test_an_error_during_inference_is_sent_and_flagged` |
| `REQ-OBD-04` | Large frames are resampled to 10 m, run in overlapping tiles and resampled back | met | `tests/test_onboard.py::test_tiles_give_the_same_mask_as_the_whole_frame`, `tests/test_onboard.py::test_a_finer_frame_is_resampled_and_its_mask_has_the_frame_size` |
| `REQ-OBD-05` | The Jetson scripts measure latency, throughput, power and the large-frame rate | met | `tests/test_jetson_dry_run.py::test_latency_throughput_and_energy_formulas`, `tests/test_jetson_dry_run.py::test_tiles_and_frames_of_the_large_frame_path` |

Further evidence: `REQ-OBD-05`: the tests pass in dry-run mode; nothing is measured on a Jetson yet ([RESULTS.md](RESULTS.md), section 15).

---

## 7. Repository and supply chain

| ID | Requirement | Status | Verified by |
| :--- | :---: | :---: | :---: |
| `REQ-REP-01` | Tracked files follow the character rules and the Markdown standard | met | `tests/test_text_rules.py::test_tracked_text_files_follow_character_rules`, `tests/test_markdown_style.py::test_markdown_files_follow_the_standard` |
| `REQ-REP-02` | No secrets, project IDs, personal paths or tool names in tracked files | met | `tests/test_public_hygiene.py::test_tracked_files_are_clean` |
| `REQ-REP-03` | Pinned dependencies: requirements.txt is exactly what uv export writes from uv.lock | met | `tests/test_requirements_sync.py::test_file_is_exactly_what_uv_export_writes` |
| `REQ-REP-04` | Every requirement and acceptance target has a verification, and every verification exists | met | `tests/test_requirements_doc.py::test_every_requirement_is_verified` |
| `REQ-REP-05` | A software bill of materials lists every locked package with its licence and hashes, and is generated in CI | met | `tests/test_sbom.py::test_every_locked_package_is_a_component_with_licence_and_hash`, `tests/test_sbom.py::test_missing_licence_row_stops` |
| `REQ-REP-06` | No document claims that a standard is met for an agency or operator; standards matrix statuses are valid | met | `tests/test_wording.py::test_no_tracked_document_claims_compliance`, `tests/test_wording.py::test_standards_matrix_rows_have_a_valid_status` |
| `REQ-REP-07` | No pretrained weights are loaded | met | `tests/test_public_hygiene.py::test_no_pretrained_weights_are_loaded` |
| `REQ-REP-08` | Every shell script under hpc/ and jetson/ is checked by shellcheck in CI | met | `tests/test_roihu_scripts.py::test_every_shell_script_is_in_the_shellcheck_list`, `.github/workflows/ci.yml` |
| `REQ-REP-09` | An accepted vulnerability finding has a reason and expires within 90 days | met | `tests/test_audit_exceptions.py::test_invalid_entries_fail`, `.github/workflows/audit.yml` |
| `REQ-REP-10` | The test coverage floor is never lowered | met | `tests/test_coverage_floor.py::test_lowering_the_floor_fails` |

---

## 8. Acceptance targets

| ID | Requirement | Minimum | Target | Measured value | Run | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Accuracy on the 975 test patches, four-band set, 1 M model unless stated** | | | | | | | | |
| `ACC-01` | Cloud against non-cloud, median BOA | above 0.84 | at least 0.90 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-02` | Same, largest model, all 13 bands | at least 0.90 | at least 0.92 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-03` | Cloud shadow, median BOA | above 0.74 | at least 0.85 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-04` | Reference algorithms (except UNetMobV2) whose cloud BOA interval overlaps the model's | at most 0 | at most 0 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-05` | Mean IoU, four classes | at least 0.70 | at least 0.75 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-06` | Thin cloud producer's and user's accuracy | reported | above every reference except UNetMobV2 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-07` | Cloud cover per patch, mean absolute error | at most 0.08 | at most 0.05 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-08` | Expected calibration error | at most 0.08 | at most 0.05 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-09` | Spread over three seeds, cloud BOA (standard deviation) | at most 0.02 | at most 0.01 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| **Independent datasets, four-band set, never used for training or selection** | | | | | | | | |
| `IND-01` | Independent datasets evaluated | at least 2 | 4, from at least 3 sensors | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-02` | Each independent Sentinel-2 dataset, cloud BOA | above Sen2Cor on the same pixels | within 0.03 of the CloudSEN12+ test result | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-03` | Each other-sensor dataset, cloud BOA | above the dataset's operational mask, where one exists | within 0.05 of the CloudSEN12+ test result | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-04` | Worst biome or surface class on any independent dataset, BOA | at least 0.75 | at least 0.85 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| **Frame decision, at the decision threshold of 50 percent** | | | | | | | | |
| `FRM-01` | Useful frames wrongly discarded (false discard rate) | at most 0.02 | at most 0.01 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `FRM-02` | Cloudy frames detected (1 minus the false send rate) | at least 0.85 | at least 0.90 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| **Compression and flexibility** | | | | | | | | |
| `CMP-01` | ONNX FP32 against PyTorch, argmax agreement | at least 0.999 | at least 0.999 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-02` | FP16 against FP32, cloud BOA loss | at most 0.005 | at most 0.002 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-03` | INT8 against FP32, cloud BOA loss | at most 0.02 | at most 0.01 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-04` | Flexible model against specialist, four bands, cloud BOA loss | at most 0.01 | within the specialist's interval | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-05` | Rescaling 0.5x to 2x, cloud BOA loss | at most 0.04 | at most 0.02 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-06` | Other sensors against Sentinel-2, cloud BOA loss | at most 0.08 | at most 0.05 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-07` | Red, green and blue only, cloud BOA | reported | reported | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| **On board (Jetson), provisional** | | | | | | | | |
| `OBD-01` | Throughput, 512 x 512 tiles per second | at least 20 | at least 40 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-02` | Latency per tile, INT8 or FP16 | at most 50 ms | at most 25 ms | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-03` | Model file of the 1 M model | at most 4,000,000 bytes (4 MB) in FP32 | at most 1,500,000 bytes (1.5 MB) in INT8 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-04` | Memory during inference | at most 2 GB | at most 1 GB | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-05` | Board power during inference | at most 25 W | at most 15 W | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-06` | Same input, same output across runs | bit identical per runtime | n/a | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| **Standards alignment** | | | | | | | | |
| `STD-01` | Worst stratum, cloud BOA | at least 0.75 | at least 0.85 | pending | pending | pending | v2 pending | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-02` | Invalid or out-of-domain input that ends in a discarded frame | at most 0 | at most 0 | 0 | n/a | met | `tiefer_lab.onboard.failsafe_check` discards no frame (`tests/test_onboard.py`) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-03` | Requirements without a linked verification | at most 0 | at most 0 | 0 | n/a | met | `tests/test_requirements_doc.py` | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-04` | Rows of the standards matrix with status "not read" | reported | at most 0 | 8 | n/a | not met against the target | [STANDARDS.md](STANDARDS.md) | `tiefer_lab.acceptance`, `reports/acceptance.md` |

Notes:

- `ACC-06`: the CloudSEN12 paper reports PA and UA for cloud and for cloud shadow as the share of test patches with a value below 0.1, between 0.1 and 0.9, and above 0.9 (Table 6), not per class and not as medians, so no published thin cloud PA or UA of a reference compares to this target (CloudSEN12, Scientific Data, 2022, https://doi.org/10.1038/s41597-022-01878-2, Table 6 and the text that defines it, accessed 7 October 2026).
- `ACC-09`: the target is defined on three seeds of the 1 M model.
- `OBD-03`: `acceptance.py` divides the file size in bytes by 1,000,000, so MB here is a decimal unit.

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: section 1 links POLICY.md and BENCHMARK-AUTHORITY.md for how values may be quoted.
- 7 October 2026: `STD-04` counts 8 rows `not read` in the revised standards matrix.
- 7 October 2026: restructured to the requirements matrix of docs/STYLE.md: the acceptance targets have columns Minimum, Target, Measured value, Run, Status and Evidence, with the bounds of `src/tiefer_lab/acceptance.py`, and category rows for the target groups.
- 7 October 2026: section 1 states once that the statuses were set by hand and that `make check` of 7 October 2026 is the evidence for every code requirement; the repeated evidence cells are removed and further evidence is listed below each table.
- 7 October 2026: `ACC-06`: the CloudSEN12 paper reports PA and UA as shares of patches, so no published comparison exists. `FRM-02` is 1 minus the false send rate. `OBD-03` gives the bounds in bytes. `CMP-07` links Appendix A of RESULTS.md.
- 7 October 2026: correction: `CMP-03` is not measured, not "not met": its target is a cloud BOA loss of the 1 M model, which has no export report yet.
- 7 October 2026: correction: `CMP-04` no longer cites the test split for the product decision.
- 7 October 2026: a status and its evidence for every requirement and acceptance target, from RESULTS.md.
- 7 October 2026: `REQ-EVL-06` is verified by the report loader tests in `tests/test_reports.py`; the results generator and its tests are removed.
- 2 October 2026: shellcheck, accepted vulnerability findings and the coverage floor.
- 2 October 2026: richness report, every band set, software bill of materials, wording and pretrained weights requirements.
- 2 October 2026: first version, with the requirements and acceptance targets of milestone L2.
