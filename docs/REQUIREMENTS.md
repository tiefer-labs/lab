<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Requirements

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Every requirement and every acceptance target of milestone L2 has an ID and the test or report that verifies it. `python -m tiefer_lab.requirements` and a test check that no ID is without verification and that no verification points to something missing.

---

## 1. How to read this page

- An ID names one requirement: `REQ-<area>-<number>` for requirements of the code, and the acceptance target IDs of `tiefer_lab.acceptance` (`ACC`, `IND`, `FRM`, `CMP`, `OBD`, `STD`).
- "Verified by" lists tests as `tests/<file>.py::<test>` and files by their path. Files under `reports/` are generated on Roihu or a Jetson and are not in the repository until they are copied in. The GPU maintenance of CSC Roihu began on 6 October 2026 at 08:00 Finnish time (05:00 UTC); no GPU job of this repository has run since. The report files of 2 and 3 October 2026 are therefore still on Roihu.
- Acceptance targets are measured by `python -m tiefer_lab.acceptance`, which writes `reports/acceptance.md`.
- Status, on 7 October 2026: `met`, `not met`, `pending` (measured, but the value is not yet in the repository) or `not measured`, with the evidence. A code requirement is met when its tests pass. The acceptance targets are defined on the final test evaluation of `l2_flex_1m` with four bands; values are taken from [RESULTS.md](RESULTS.md), and a value from the session notes is marked so.

---

## 2. Data

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-DAT-01` | Only the dataset's high quality 509 x 509 patches are cached for train, val and test; kept and dropped counts are recorded | met | its tests pass (`make check`, 7 October 2026) | `tests/test_bands_and_labels.py::test_select_keeps_high_quality_509_patches_and_counts_dropped` |
| `REQ-DAT-02` | The reader stops with a clear message when a metadata field it needs is missing | met | its tests pass (`make check`, 7 October 2026) | `tests/test_bands_and_labels.py::test_missing_split_field_stops_with_a_clear_message` |
| `REQ-DAT-03` | Unknown label codes stop the build | met | its tests pass (`make check`, 7 October 2026) | `tests/test_bands_and_labels.py::test_unknown_label_code_is_an_error` |
| `REQ-DAT-04` | Builds are resumable, also in the finishing step, and never reread a written patch | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_real_builder_resumes_after_interruption`, `tests/test_cache.py::test_finishing_step_resumes_after_it_failed` |
| `REQ-DAT-05` | A build with another selection never resets or replaces an existing split | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_a_limited_build_never_resets_or_replaces_the_full_cache` |
| `REQ-DAT-06` | The finishing step stays within bounded memory (chunked counts and statistics) | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_class_pixels_are_counted_in_chunks_without_loading_the_split`, `tests/test_cache.py::test_band_statistics_are_chunked` |
| `REQ-DAT-07` | One cache stores all 13 bands; models select their bands by name at load time | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_bands_are_selected_by_name_at_load_time` |
| `REQ-DAT-08` | Shards never write the same file and merge into the same cache as one build | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_shards_write_apart_and_merge_into_the_same_cache_as_one_build`, `tests/test_cache.py::test_an_interrupted_merge_resumes` |
| `REQ-DAT-09` | Reads respect a shared rate cap and back off on HTTP 429; the token is never printed | met | its tests pass (`make check`, 7 October 2026) | `tests/test_cache.py::test_the_rate_cap_is_shared_between_shards`, `tests/test_http.py::test_a_pause_holds_every_reader`, `tests/test_http.py::test_token_goes_to_gdal_and_is_never_printed` |
| `REQ-DAT-10` | Extra training patches never share a location with the validation or test split | met | its tests pass (`make check`, 7 October 2026) | `tests/test_extra_patches.py::test_built_index_proves_no_training_patch_shares_a_location_with_val_or_test` |
| `REQ-DAT-11` | Facts not yet verified stop the code instead of being guessed | met | its tests pass (`make check`, 7 October 2026) | `tests/test_extra_patches.py::test_extra_patches_wait_for_verified_facts`, `tests/test_references.py::test_references_wait_for_verified_facts` |
| `REQ-DAT-12` | Reference masks are linked and encoded only with verified encodings; unknown values stop | met | its tests pass (`make check`, 7 October 2026) | `tests/test_references.py::test_references_are_linked_encoded_and_resumable`, `tests/test_references.py::test_unknown_raw_values_stop_the_encoding` |
| `REQ-DAT-13` | The richness report states class shares, cloud cover bins and shadow per split, and interprets verified metadata fields only | met | its tests pass (`make check`, 7 October 2026) | `tests/test_richness.py::test_patch_statistics_by_hand`, `tests/test_richness.py::test_field_summary_reports_verified_fields_only` |

---

## 3. Training

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-TRN-01` | Training is resumable and gives the same result after an interruption | met | its tests pass (`make check`, 7 October 2026) | `tests/test_checkpoint_resume.py::test_interrupted_run_resumes_to_the_same_result` |
| `REQ-TRN-02` | Runs with different seeds never share a run folder; the seed is recorded | met | its tests pass (`make check`, 7 October 2026) | `tests/test_checkpoint_resume.py::test_seed_override_goes_into_metadata_and_run_id` |
| `REQ-TRN-03` | Learning rate warm-up and cosine decay, and a moving average of the weights for validation and best.pt | met | its tests pass (`make check`, 7 October 2026) | `tests/test_checkpoint_resume.py::test_learning_rate_warms_up_linearly_then_follows_a_cosine_to_zero`, `tests/test_checkpoint_resume.py::test_best_checkpoint_holds_the_averaged_weights` |
| `REQ-TRN-04` | Unavailable bands never change the output of a band-flexible model | met | its tests pass (`make check`, 7 October 2026) | `tests/test_flexible_model.py::test_unavailable_bands_never_change_the_output` |
| `REQ-TRN-05` | Pixels without a label add nothing to the loss | met | its tests pass (`make check`, 7 October 2026) | `tests/test_flexible_model.py::test_ignored_pixels_add_nothing_to_the_loss` |
| `REQ-TRN-06` | The size ladder hits its parameter targets and every variant changes one setting | met | its tests pass (`make check`, 7 October 2026) | `tests/test_config.py::test_l2_ladder_sizes_and_one_change_per_variant` |
| `REQ-TRN-07` | Every run records its config, seed, commit, job ID and GPU hours; reports/experiments.md is built from the run folders | met | its tests pass; l1_base s0 records commit 81ab34b03bcc, which is in the history, made from a working tree with uncommitted changes (only that diff is lost) ([RESULTS.md](RESULTS.md), section 4) | `tests/test_checkpoint_resume.py::test_run_metadata_has_provenance_and_no_absolute_paths`, `tests/test_experiments.py::test_one_row_per_run_from_its_folder` |

---

## 4. Evaluation

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-EVL-01` | The test split is used only with FINAL=1 and a reason, and every use is logged | pending | the guard's tests pass; at least eight test evaluations ran on 3 October 2026 and their log entries are on CSC Roihu, pending a copy into `reports/test_log.md`, which has no entries yet | `tests/test_test_guard.py::test_test_split_refuses_without_final`, `tests/test_test_guard.py::test_final_test_evaluation_is_logged_first` |
| `REQ-EVL-02` | BOA, PA, UA and OA per patch for cloud and shadow, with the median and bootstrap intervals | met | its tests pass (`make check`, 7 October 2026) | `tests/test_binary_metrics.py::test_cloud_problem_by_hand`, `tests/test_binary_metrics.py::test_scores_leave_ignored_pixels_out_and_report_intervals` |
| `REQ-EVL-03` | Reference algorithms are scored by this repository's code on the same patches | met | its tests pass (`make check`, 7 October 2026) | `tests/test_binary_metrics.py::test_binary_only_scores_report_the_cloud_problem_only`, `tests/test_references.py::test_references_are_linked_encoded_and_resumable` |
| `REQ-EVL-04` | Expected calibration error and the worst stratum are reported | met | its tests pass (`make check`, 7 October 2026) | `tests/test_binary_metrics.py::test_expected_calibration_error_by_hand`, `tests/test_binary_metrics.py::test_worst_stratum_is_named` |
| `REQ-EVL-05` | Sensor perturbations are measured as fixed perturbations on validation | met | its tests pass; measured for l1_base s0 ([RESULTS.md](RESULTS.md), section 13) | `tests/test_sensor.py::test_perturbations_parse_and_apply`, `tests/test_flexible_pipeline.py::test_specialist_reads_four_bands_from_the_13_band_cache` |
| `REQ-EVL-06` | Report files are read only with their git provenance, and smoke reports are never read as results | met | its tests pass (`make check`, 7 October 2026) | `tests/test_reports.py::test_smoke_reports_are_never_loaded`, `tests/test_reports.py::test_a_report_without_git_provenance_is_refused` |
| `REQ-EVL-07` | Evaluation and export cover every band set of a run when asked for all of them | met | its tests pass; l2_flex_1m s0 was evaluated per band set ([RESULTS.md](RESULTS.md), section 12) | `tests/test_flexible_pipeline.py::test_flexible_model_trains_evaluates_and_exports_per_band_set`, `tests/test_roihu_scripts.py::test_evaluate_and_export_cover_every_band_set` |

---

## 5. Export

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-EXP-01` | ONNX FP32 matches PyTorch; FP16 and INT8 are measured against FP32 | met | its tests pass; FP32, FP16 and INT8 measured for three L1 runs ([RESULTS.md](RESULTS.md), section 14) | `tests/test_export.py::test_fp32_round_trip_matches_pytorch`, `tests/test_quantise.py::test_int8_model_is_qdq_and_scores`, `tests/test_binary_metrics.py::test_int8_comparison_reports_the_boa_change` |
| `REQ-EXP-02` | One ONNX file per band set takes only the bands of that set | met | its tests pass (`make check`, 7 October 2026) | `tests/test_flexible_pipeline.py::test_flexible_model_trains_evaluates_and_exports_per_band_set`, `tests/test_flexible_model.py::test_band_set_model_matches_the_flexible_model` |

---

## 6. On board

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-OBD-01` | Invalid, missing, saturated or out-of-domain input never causes a discarded frame; the frame is sent and flagged | met | its tests pass (`make check`, 7 October 2026) | `tests/test_onboard.py::test_invalid_input_is_sent_and_flagged_never_kept`, `tests/test_onboard.py::test_failsafe_check_counts_no_discarded_frame` |
| `REQ-OBD-02` | The model file hash is checked before inference; a mismatch stops inference with a clear status | met | its tests pass (`make check`, 7 October 2026) | `tests/test_onboard.py::test_corrupted_model_files_stop_inference` |
| `REQ-OBD-03` | No exception during inference ends in a discarded frame | met | its tests pass (`make check`, 7 October 2026) | `tests/test_onboard.py::test_an_error_during_inference_is_sent_and_flagged` |
| `REQ-OBD-04` | Large frames are resampled to 10 m, run in overlapping tiles and resampled back | met | its tests pass (`make check`, 7 October 2026) | `tests/test_onboard.py::test_tiles_give_the_same_mask_as_the_whole_frame`, `tests/test_onboard.py::test_a_finer_frame_is_resampled_and_its_mask_has_the_frame_size` |
| `REQ-OBD-05` | The Jetson scripts measure latency, throughput, power and the large-frame rate | met | its tests pass in dry-run mode; nothing is measured on a Jetson yet ([RESULTS.md](RESULTS.md), section 15) | `tests/test_jetson_dry_run.py::test_latency_throughput_and_energy_formulas`, `tests/test_jetson_dry_run.py::test_tiles_and_frames_of_the_large_frame_path` |

---

## 7. Repository and supply chain

| ID | Requirement | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `REQ-REP-01` | Tracked files follow the character rules and the Markdown standard | met | its tests pass (`make check`, 7 October 2026) | `tests/test_text_rules.py::test_tracked_text_files_follow_character_rules`, `tests/test_markdown_style.py::test_markdown_files_follow_the_standard` |
| `REQ-REP-02` | No secrets, project IDs, personal paths or tool names in tracked files | met | its tests pass (`make check`, 7 October 2026) | `tests/test_public_hygiene.py::test_tracked_files_are_clean` |
| `REQ-REP-03` | Pinned dependencies: requirements.txt is exactly what uv export writes from uv.lock | met | its tests pass (`make check`, 7 October 2026) | `tests/test_requirements_sync.py::test_file_is_exactly_what_uv_export_writes` |
| `REQ-REP-04` | Every requirement and acceptance target has a verification, and every verification exists | met | its tests pass (`make check`, 7 October 2026) | `tests/test_requirements_doc.py::test_every_requirement_is_verified` |
| `REQ-REP-05` | A software bill of materials lists every locked package with its licence and hashes, and is generated in CI | met | its tests pass (`make check`, 7 October 2026) | `tests/test_sbom.py::test_every_locked_package_is_a_component_with_licence_and_hash`, `tests/test_sbom.py::test_missing_licence_row_stops` |
| `REQ-REP-06` | No document claims that a standard is met for an agency or operator; standards matrix statuses are valid | met | its tests pass (`make check`, 7 October 2026) | `tests/test_wording.py::test_no_tracked_document_claims_compliance`, `tests/test_wording.py::test_standards_matrix_rows_have_a_valid_status` |
| `REQ-REP-07` | No pretrained weights are loaded | met | its tests pass (`make check`, 7 October 2026) | `tests/test_public_hygiene.py::test_no_pretrained_weights_are_loaded` |
| `REQ-REP-08` | Every shell script under hpc/ and jetson/ is checked by shellcheck in CI | met | its tests pass (`make check`, 7 October 2026) | `tests/test_roihu_scripts.py::test_every_shell_script_is_in_the_shellcheck_list`, `.github/workflows/ci.yml` |
| `REQ-REP-09` | An accepted vulnerability finding has a reason and expires within 90 days | met | its tests pass (`make check`, 7 October 2026) | `tests/test_audit_exceptions.py::test_invalid_entries_fail`, `.github/workflows/audit.yml` |
| `REQ-REP-10` | The test coverage floor is never lowered | met | its tests pass (`make check`, 7 October 2026) | `tests/test_coverage_floor.py::test_lowering_the_floor_fails` |

---

## 8. Acceptance targets

| ID | Target | Status | Evidence | Verified by |
| :--- | :---: | :---: | :---: | :---: |
| `ACC-01` | Cloud against non-cloud, median BOA | pending | four-band cloud BOA of l2_flex_1m s0 not yet transcribed ([RESULTS.md](RESULTS.md), section 11) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-02` | Same, largest model, all 13 bands | not measured | no model of the largest size was trained ([RESULTS.md](RESULTS.md), section 3) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-03` | Cloud shadow, median BOA | pending | four-band shadow BOA of l2_flex_1m s0 not yet transcribed ([RESULTS.md](RESULTS.md), section 11) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-04` | Reference algorithms (except UNetMobV2) whose cloud BOA interval overlaps the model's | not measured | reference algorithms not measured ([RESULTS.md](RESULTS.md), section 10) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-05` | Mean IoU, four classes | not met | l2_flex_1m s0, four bands, test: 0.609 (notes), minimum 0.70 ([RESULTS.md](RESULTS.md), section 12) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-06` | Thin cloud producer's and user's accuracy | pending | thin cloud PA and UA of l2_flex_1m s0 not yet transcribed; references not measured ([RESULTS.md](RESULTS.md), sections 10 and 11) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-07` | Cloud cover per patch, mean absolute error | pending | l2_flex_1m s0, four bands, not yet transcribed ([RESULTS.md](RESULTS.md), section 8) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-08` | Expected calibration error | pending | in the evaluation reports, not yet transcribed | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `ACC-09` | Spread over three seeds, cloud BOA (standard deviation) | not measured | every run is a single seed ([RESULTS.md](RESULTS.md), section 18) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-01` | Independent datasets evaluated | not measured | no independent dataset evaluated (docs/DATASETS.md, section 2) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-02` | Each independent Sentinel-2 dataset, cloud BOA | not measured | no independent dataset evaluated | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-03` | Each other-sensor dataset, cloud BOA | not measured | no independent dataset evaluated | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `IND-04` | Worst biome or surface class on any independent dataset, BOA | not measured | no independent dataset evaluated | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `FRM-01` | Useful frames wrongly discarded | not met | l2_flex_1m s0, four bands, test false discard rate 0.084 (notes), minimum 0.02 ([RESULTS.md](RESULTS.md), section 12) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `FRM-02` | Cloudy frames detected | pending | false send rate of l2_flex_1m s0 not yet transcribed ([RESULTS.md](RESULTS.md), section 20) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-01` | ONNX FP32 against PyTorch, argmax agreement | not measured | l2_flex_1m s0 has no export report yet; export jobs 2002028, 2002101 and 2002148 are not matched to a run; the three exported L1 runs passed the check at 0.999 ([RESULTS.md](RESULTS.md), section 14) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-02` | FP16 against FP32, cloud BOA loss | not measured | l2_flex_1m s0 has no export report yet; export jobs 2002028, 2002101 and 2002148 are not matched to a run; for l1_base s0 the FP16 change is 0.000 ([RESULTS.md](RESULTS.md), section 14) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-03` | INT8 against FP32, cloud BOA loss | not met | l2_flex_1m s0 has no export report yet; export jobs 2002028, 2002101 and 2002148 are not matched to a run; INT8 loses 0.060 to 0.154 mean IoU on every exported L1 run, above the one point of docs/SPEC.md, section 10 ([RESULTS.md](RESULTS.md), section 14) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-04` | Flexible model against specialist, four bands, cloud BOA loss | pending | cloud BOA of the four-band set not yet transcribed; on test, the four-band mean IoU is outside the specialist's interval ([RESULTS.md](RESULTS.md), section 12) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-05` | Rescaling 0.5x to 2x, cloud BOA loss | not measured | no rescaling evaluation of l2_flex_1m s0; l1_base s0 is in [RESULTS.md](RESULTS.md), section 13 | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-06` | Other sensors against Sentinel-2, cloud BOA loss | not measured | no other-sensor dataset evaluated | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `CMP-07` | Red, green and blue only, cloud BOA | pending | `x-test-3` not yet transcribed ([RESULTS.md](RESULTS.md), section 12) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-01` | Throughput, 512 x 512 tiles per second | not measured | no Jetson measurement ([RESULTS.md](RESULTS.md), section 15) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-02` | Latency per tile, INT8 or FP16, ms | not measured | no Jetson measurement ([RESULTS.md](RESULTS.md), section 15) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-03` | Model file of the 1 M model, MB | not measured | l2_flex_1m s0 has no export report yet; export jobs 2002028, 2002101 and 2002148 are not matched to a run; l1_base s0 FP32 is 993,280 bytes (notes, [RESULTS.md](RESULTS.md), section 14) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-04` | Memory during inference, GB | not measured | not measured by the Jetson scripts yet | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-05` | Board power during inference, W | not measured | no Jetson measurement ([RESULTS.md](RESULTS.md), section 15) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `OBD-06` | Same input, same output across runs | not measured | not measured by the Jetson scripts yet | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-01` | Worst stratum, cloud BOA | pending | worst stratum in the evaluation reports, not yet transcribed | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-02` | Invalid or out-of-domain input that ends in a discarded frame | met | `tiefer_lab.onboard.failsafe_check` discards no frame (`tests/test_onboard.py`) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-03` | Requirements without a linked verification | met | none (`tests/test_requirements_doc.py`) | `tiefer_lab.acceptance`, `reports/acceptance.md` |
| `STD-04` | Rows of the standards matrix with status "not read" | not met | reported: every row of docs/STANDARDS.md is not read; target 0 | `tiefer_lab.acceptance`, `reports/acceptance.md` |

---

## Changelog

- 7 October 2026: correction: `CMP-01`, `CMP-02`, `CMP-03` and `OBD-03`: the L2 runs have no export report yet, and three export jobs are not matched to a run.
- 7 October 2026: section 1 says why the report files of 2 and 3 October 2026 are not yet committed.
- 7 October 2026: correction: `REQ-EVL-01` is pending, not met, until the test log entries of 3 October 2026 are copied in.
- 7 October 2026: correction: `REQ-TRN-07`, commit 81ab34b03bcc is in the history of this repository.
- 7 October 2026: a status and its evidence for every requirement and acceptance target, from RESULTS.md.
- 7 October 2026: `REQ-EVL-06` is verified by the report loader tests in `tests/test_reports.py`; the results generator and its tests are removed.
- 2 October 2026: shellcheck, accepted vulnerability findings and the coverage floor.
- 2 October 2026: richness report, every band set, software bill of materials, wording and pretrained weights requirements.
- 2 October 2026: first version, with the requirements and acceptance targets of milestone L2.
