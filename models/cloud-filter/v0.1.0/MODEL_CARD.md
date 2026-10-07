<img alt="Tiefer Lab" src="../../../docs/assets/header.png" width="100%">

# Model card: cloud filter v0.1.0

Status: draft. Owner: Tiefer. Licence: MPL 2.0.

Draft model card of the milestone L1 cloud filter `l1_base s0` for four-band Level-1C imagery. The model files are not distributed in this repository, and no licence is granted for them: checkpoints and ONNX files stay with Tiefer, and the checksums below identify them. Values are rounded to 3 decimals, half up.

---

## Summary

| Field | Value | Source |
| :--- | :---: | :---: |
| Task | per-pixel classes clear, thick cloud, thin cloud, cloud shadow; per-frame send or keep decision | `docs/SPEC.md`, section 8 |
| Architecture and parameters | `CloudFilterNet`, 240,564 parameters | `metadata.json`: `model.architecture`, parameters |
| Band set | B02, B03, B04, B08 (blue, green, red, near infrared) | `configs/l1_base.toml` |
| Input | 1 x 4 x 512 x 512 | export report: input shape |
| Output | 4 class logits per pixel | export report |
| Operations | 2,190,082,048 multiply-accumulates for one 512 x 512 tile | `metadata.json`: `model.macs_512x512` |
| Formats | FP32, FP16, INT8 | export report |
| Training run and commit | `l1_base-seed0-20261003T093922Z-81ab34b`, commit `81ab34b03bcc`, made from a working tree with uncommitted changes; the base commit is in the history of this repository, and only the uncommitted diff is lost | `metadata.json`: run ID, `git_commit`; [RESULTS.md](../../../docs/RESULTS.md), section 4 |
| Training | batch 128, learning rate 0.008, best epoch 32, early stopped (patience 15 of a 150-epoch schedule) | `config.toml`; evaluation report: `run.best_epoch`, `run.status` |
| Dataset revision and cache | `f9490f7de11b4f387f72ef800e73ccbb754711de`, cache `cloudsen12-l1c-high` | evaluation report; [DATA.md](../../../docs/DATA.md), section 10 |
| Selected model | no; the selected model of [RESULTS.md](../../../docs/RESULTS.md), section 7, is `l2_spec_1m s0` | [RESULTS.md](../../../docs/RESULTS.md), section 7 |
| Pretrained weights | none; trained from random initialisation | `NOTICE.md` |
| Weight licence | not distributed; no licence is granted for the model files | `LICENSING.md` |
| Date | 3 October 2026 | `metadata.json`: end of the last session |

---

## Intended use

Deciding on board whether a frame is worth sending, from its cloud fraction and an operator-set threshold, inside the operational design domain of `docs/SPEC.md`, section 9. A frame outside it is sent and flagged by `tiefer_lab.onboard`.

---

## Out of scope

- Sensors other than Sentinel-2 until the model is measured on that sensor's data.
- Band sets other than the one in the summary.
- Any use where a lost frame is acceptable but a false send is not: the filter is built to send when in doubt.
- Atmospheric correction, cloud height or cloud type beyond the four classes.

---

## Training data

CloudSEN12+ Level-1C, training split, 8,490 patches of 509 x 509 pixels with high quality labels, as described in [DATA.md](../../../docs/DATA.md), section 2.3.

---

## Evaluation

Every test evaluation appends an entry to the test log on the machine that runs it; the entry for the test evaluation of this model was made on CSC Roihu and is pending a copy into [reports/test_log.md](../../../reports/test_log.md).

Validation split, report written at commit `81ab34b03bcc` (the version of `b0-val` read in full; a second version written at commit `4ce677d1811b` is on CSC Roihu, [RESULTS.md](../../../docs/RESULTS.md), section 4):

| Metric | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: |
| Mean IoU, four classes | 0.649 | [0.630, 0.667] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| False discard rate at 50 percent | 0.042 | [0.022, 0.066] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Decision accuracy at 50 percent | 0.936 | [0.916, 0.957] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Cloud fraction mean absolute error | 0.061 | [0.053, 0.071] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Cloud balanced overall accuracy (BOA), median over patches | pending | pending | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json`, version at `4ce677d1811b` |
| Shadow BOA, median over patches | pending | pending | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json`, version at `4ce677d1811b` |
| Expected calibration error | pending | n/a | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json`, `calibration` |
| Worst stratum, cloud BOA | pending | n/a | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json`, `worst_stratum` |

Test split, report written at commit `81ab34b03bcc`; the values are copied from the generated page at commit c3e861a ([RESULTS.md](../../../docs/RESULTS.md), section 6):

| Metric | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: |
| Mean IoU, four classes | 0.635 | [0.621, 0.649] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| False discard rate at 50 percent | 0.039 | [0.024, 0.055] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Decision accuracy at 50 percent | 0.927 | [0.910, 0.943] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Cloud fraction mean absolute error | 0.062 | [0.055, 0.070] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Cloud BOA and shadow BOA | not measured | n/a | the code at `81ab34b03bcc` has no cloud and shadow measures ([RESULTS.md](../../../docs/RESULTS.md), section 11) |

Fail-safe cases that end in a discarded frame: 0 of the nine cases of `tiefer_lab.onboard.failsafe_check` (`tests/test_onboard.py`); this is a property of the decision code, not of these weights.

Results by region (`equi_zone`) on the validation split range from a mean IoU of 0.685 (EU, 105 patches) to 0.561 (OC, 50 patches); see [RESULTS.md](../../../docs/RESULTS.md), section 9. Every value of this model is in [RESULTS.md](../../../docs/RESULTS.md), sections 6, 8, 9, 13 and 14.

---

## Quantisation

Validation split, ONNX Runtime, report written at commit `81ab34b03bcc`; INT8 calibrated on 256 training patches (`export.calibration_patches` of `config.toml`).

| Format | File size in bytes | Mean IoU | Mean IoU change against FP32 | Cloud BOA change | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| FP32 | 993,280 | 0.649 | n/a | n/a | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json`; size (notes) |
| FP16 | 518,144 | 0.649 | 0.000 | 0.000 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json`; size and values (notes) |
| INT8 | 455,680 | 0.579 | -0.070 | -0.009 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json`; size (notes); cloud BOA change (note below) |

- The file sizes and the FP16 values come from the session notes and are checked against the export report when it is in `reports/` ([RESULTS.md](../../../docs/RESULTS.md), section 20).
- The false discard rate at 50 percent of the FP32 file is 0.039 in ONNX Runtime, against 0.042 in the PyTorch evaluation of the validation table above. The two come from different runtimes; the cause of the difference is not yet investigated ([RESULTS.md](../../../docs/RESULTS.md), section 14).
- The cloud BOA changes were written into the first version of this card. The code at commit `81ab34b03bcc` does not compute cloud BOA, so their source is pending ([RESULTS.md](../../../docs/RESULTS.md), sections 14 and 20).
- INT8 is 62,464 bytes smaller than FP16 and loses 0.070 mean IoU (0.649 to 0.579), more than the one point of `docs/SPEC.md`, section 10.

---

## Hardware measurements

| Device and setting | Latency p50 per 512 x 512 tile | Latency p99 | Energy per tile | Source |
| :--- | :---: | :---: | :---: | :---: |
| Jetson Orin, FP16 | not measured | not measured | not measured | `reports/jetson/` |
| Jetson Orin, INT8 | not measured | not measured | not measured | `reports/jetson/` |

---

## Limitations

- Trained and validated on Sentinel-2 at 10 m only; no target-sensor data was used.
- Human agreement limits what any model can score on thin cloud and shadow: the CloudSEN12 paper reports a median BOA of 0.99 for cloud and 0.99 for cloud shadow between the labels before and after its quality control, and a producer's accuracy of 0.780 for thin cloud, on its 975 test patches and the labels of the 2022 release, not this repository's revision ([DATA.md](../../../docs/DATA.md), section 3).
- Results hold for the band set and size in the summary only.
- INT8 loses 0.070 mean IoU, more than the one point of `docs/SPEC.md`, section 10; the INT8 file is not yet usable for flight.
- Later runs score higher on test: `l1_full s0` 0.689 and `l2_spec_1m s0` 0.720 mean IoU against 0.635 here ([RESULTS.md](../../../docs/RESULTS.md), section 6).
- One seed only, trained from a working tree with uncommitted changes.
- Mean IoU differs by region, from 0.685 to 0.561 on validation ([RESULTS.md](../../../docs/RESULTS.md), section 9).
- The cached patches are 512 x 512 and hold the dataset's padding; every metric counts the padded pixels ([DATA.md](../../../docs/DATA.md), section 5).
- Standards: no agency or operator standard is claimed; see `docs/STANDARDS.md`.

---

## Files

The SHA-256 of each model file, as listed in `SHA256SUMS`.

| File | SHA-256 |
| :--- | :---: |
| `cloud_filter_fp32.onnx` | `6bc7f261b8e7defb37e4119a8ec04c418c808b3f57f77e0e3b11f93e4d6d5663` |
| `cloud_filter_fp32_dynamic.onnx` | `99e80ef3c5fac60b0c6ec2e501a765c0211e3af7679d5daa328b57cbe18b2396` |
| `cloud_filter_fp16.onnx` | `8ebc479b7684740f291a2d8edd680f4ea68c52241820695388f0331e3a260083` |
| `cloud_filter_int8.onnx` | `527f7f287e6564cb5e53af08b2305d97de0ac5893f06885e79e610e7e5e7aa08` |

Excluded: `best.pt`. Its SHA-256 (`bd6767cb5e06f489f81a6a5e79cc826f8b3437a127307bde7ec7fa4ef9a5aafc`) was written into the first version of this card without a recorded source and is not in `SHA256SUMS`; it is added there once it is checked against the checkpoint.

---

## Changelog

- 7 October 2026: the weight licence row cites LICENSING.md, which now states it.
- 7 October 2026: the sources of the file sizes and FP16 values are the session notes; the difference between 0.042 (PyTorch) and 0.039 (ONNX Runtime) is explained; the cloud BOA changes of INT8 and FP16 have no source in the committed code yet.
- 7 October 2026: `best.pt` is excluded from the file table, since its hash is not in `SHA256SUMS`.
- 7 October 2026: the rows the template requires: cloud and shadow BOA (validation pending, test not measured), calibration error and worst stratum (pending), the fail-safe count, and latency p99 and energy (not measured); the human agreement of the CloudSEN12 paper.
- 7 October 2026: the rounding rule, a commit per evaluation table, the dataset revision and cache, "selected model: no", the weight licence, the training data source, and the limitation on the padded pixels; "50 percent" and "mean absolute error" written out.
- 7 October 2026: correction: the test log entry of this model is on CSC Roihu and pending a copy; `reports/test_log.md` has no entries yet.
- 7 October 2026: correction: commit 81ab34b03bcc is in the history of this repository; only the uncommitted diff is lost.
- 7 October 2026: status draft instead of release; file sizes, the FP16 result, the best epoch, the region breakdown and limitations on INT8, later runs and provenance added.
- 3 October 2026: model card v0.1.0 from CSC Roihu GH200 training run `l1_base-seed0-20261003T093922Z-81ab34b`.
