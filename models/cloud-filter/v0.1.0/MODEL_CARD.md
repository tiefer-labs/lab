<img alt="Tiefer Lab" src="../../../docs/assets/header.png" width="100%">

# Model card: cloud filter v0.1.0

Status: draft. Owner: Tiefer. Licence: MPL 2.0.

Draft model card of the milestone L1 cloud filter `l1_base` seed 0 for four-band Level-1C imagery. The model files are not distributed in this repository: checkpoints and ONNX files stay with Tiefer, and the checksums below identify them.

---

## Summary

| Field | Value | Source |
| :--- | :---: | :---: |
| Task | per-pixel classes clear, thick cloud, thin cloud, cloud shadow; per-frame send or keep decision | `docs/SPEC.md`, section 8 |
| Architecture and size | `CloudFilterNet`, 240,564 parameters | `metadata.json`: `model.architecture`, parameters |
| Band set of this file | `B02, B03, B04, B08` (Blue, Green, Red, Near Infrared) | `configs/l1_base.toml` |
| Input | `1 x 4 x 512 x 512` | export report: input shape |
| Output | 4 class logits per pixel | export report |
| Operations | 2,190,082,048 multiply-accumulates (1 x 4 x 512 x 512) | `metadata.json`: `model.macs_512x512` |
| Formats | FP32, FP16, INT8 | export report: FP32, FP16, INT8 |
| Training run and commit | `l1_base-seed0-20261003T093922Z-81ab34b`, `81ab34b03bcc`, made with uncommitted changes; the base commit is in the history of this repository, only the uncommitted diff is lost | `metadata.json`: run ID, `git_commit`; [RESULTS.md](../../../docs/RESULTS.md), section 4 |
| Training | batch 128, learning rate 0.008, best epoch 32, early stopped (patience 15 of a 150-epoch schedule) | `config.toml`; evaluation report: `run.best_epoch`, `run.status` |
| Pretrained weights | none; trained from random initialisation | `NOTICE.md` |
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

CloudSEN12+ Level-1C, training split (8,490 patches), as described in `docs/DATA.md`.

---

## Evaluation

Validation unless a row says test. Every test evaluation appends an entry to the test log on the machine that runs it; the entry for the test evaluation of this model was made on CSC Roihu and is pending a copy into [reports/test_log.md](../../../reports/test_log.md).

| Metric | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: |
| Mean IoU, four classes (val) | 0.649 | [0.630, 0.667] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Mean IoU, four classes (test) | 0.635 | [0.621, 0.649] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| False discard rate at 50% (val) | 0.042 | [0.022, 0.066] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| False discard rate at 50% (test) | 0.039 | [0.024, 0.055] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Decision accuracy at 50% (val) | 0.936 | [0.916, 0.957] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Decision accuracy at 50% (test) | 0.927 | [0.910, 0.943] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Cloud fraction MAE (test) | 0.062 | [0.055, 0.070] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |

Results by region (`equi_zone`) on the validation split range from a mean IoU of 0.685 (EU, 105 patches) to 0.561 (OC, 50 patches); see [RESULTS.md](../../../docs/RESULTS.md), section 9. Every value of this model on one page: [RESULTS.md](../../../docs/RESULTS.md), sections 6, 8, 9, 13 and 14.

---

## Quantisation

Validation split, ONNX Runtime, INT8 calibrated on 256 training patches.

| Format | File size in bytes | Mean IoU change against FP32 | Cloud BOA change | Source |
| :--- | :---: | :---: | :---: | :---: |
| FP32 | 993,280 | n/a | n/a | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json` |
| FP16 | 518,144 | 0.000 | 0.000 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json` |
| INT8 | 455,680 | -0.070 | -0.009 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json` |

FP16 kept the mean IoU (0.649) and the false discard rate at 50 percent (0.039) unchanged at 3 decimals. INT8 is 62,464 bytes smaller than FP16 and loses 0.070 mean IoU (0.649 to 0.579). The file sizes and the FP16 values come from the session notes and are checked against the export report when it is in `reports/` ([RESULTS.md](../../../docs/RESULTS.md), section 20).

---

## Hardware measurements

| Device and setting | Latency per 512 x 512 tile | Frames per second at the frame size | Source |
| :--- | :---: | :---: | :---: |
| Jetson, FP16 | not measured | not measured | `reports/jetson/` |
| Jetson, INT8 | not measured | not measured | `reports/jetson/` |

---

## Limitations

- Trained and validated on Sentinel-2 at 10 m only; no target-sensor data was used.

- Human agreement on thin cloud and shadow limits what any model can score on them.

- Results hold for the band set and size in the summary only.

- INT8 loses 0.070 mean IoU, more than the one point of `docs/SPEC.md`, section 10; the INT8 file is not yet usable for flight.
- Later runs score higher on test: `l1_full` seed 0 0.689 and `l2_spec_1m` seed 0 0.720 mean IoU against 0.635 here ([RESULTS.md](../../../docs/RESULTS.md), section 6).
- One seed only, trained from a working tree with uncommitted changes.
- Mean IoU differs by region, from 0.685 to 0.561 on validation ([RESULTS.md](../../../docs/RESULTS.md), section 9).
- Standards: no agency or operator standard is claimed; see `docs/STANDARDS.md`.

---

## Files

| File | SHA-256 |
| :--- | :---: |
| `cloud_filter_fp32.onnx` | `6bc7f261b8e7defb37e4119a8ec04c418c808b3f57f77e0e3b11f93e4d6d5663` |
| `cloud_filter_fp32_dynamic.onnx` | `99e80ef3c5fac60b0c6ec2e501a765c0211e3af7679d5daa328b57cbe18b2396` |
| `cloud_filter_fp16.onnx` | `8ebc479b7684740f291a2d8edd680f4ea68c52241820695388f0331e3a260083` |
| `cloud_filter_int8.onnx` | `527f7f287e6564cb5e53af08b2305d97de0ac5893f06885e79e610e7e5e7aa08` |
| `best.pt` | `bd6767cb5e06f489f81a6a5e79cc826f8b3437a127307bde7ec7fa4ef9a5aafc` |

---

## Changelog

- 7 October 2026: correction: the test log entry of this model is on CSC Roihu and pending a copy; `reports/test_log.md` has no entries yet.
- 7 October 2026: correction: commit 81ab34b03bcc is in the history of this repository; only the uncommitted diff is lost.
- 7 October 2026: status draft instead of release; file sizes, the FP16 result, the best epoch, the region breakdown and limitations on INT8, later runs and provenance added.
- 3 October 2026: model card v0.1.0 from CSC Roihu GH200 training run `l1_base-seed0-20261003T093922Z-81ab34b`.
