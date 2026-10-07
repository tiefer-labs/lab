<img alt="Tiefer Lab" src="../../../docs/assets/header.png" width="100%">

# Model card: cloud filter v0.1.0

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Official release of milestone L1 onboard cloud filter for four-band Level-1C imagery. Checkpoints and ONNX files stay with Tiefer; checksums below verify provenance against CSC Roihu training and evaluation runs.

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
| Training run and commit | `l1_base-seed0-20261003T093922Z-81ab34b`, `81ab34b03bcc` | `metadata.json`: run ID, `git_commit` |
| Pretrained weights | none; trained from random initialisation | `NOTICE.md` |
| Date | 2026-10-03 | `metadata.json`: end of the last session |

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

Validation unless a row says test; every test result has an entry in `reports/test_log.md`.

| Metric | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: |
| Mean IoU, four classes (val) | 0.649 | [0.630, 0.667] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Mean IoU, four classes (test) | 0.635 | [0.621, 0.649] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| False discard rate at 50% (val) | 0.042 | [0.022, 0.066] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| False discard rate at 50% (test) | 0.039 | [0.024, 0.055] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Decision accuracy at 50% (val) | 0.936 | [0.916, 0.957] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_val.json` |
| Decision accuracy at 50% (test) | 0.927 | [0.910, 0.943] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |
| Cloud fraction MAE (test) | 0.062 | [0.055, 0.070] | `reports/evaluation/l1_base-seed0-20261003T093922Z-81ab34b_test.json` |

---

## Quantisation

| Format | Mean IoU change against FP32 | Cloud BOA change | Source |
| :--- | :---: | :---: | :---: |
| FP16 | 0.000 | 0.000 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json` |
| INT8 | -0.070 | -0.009 | `reports/export/l1_base-seed0-20261003T093922Z-81ab34b.json` |

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

- 3 October 2026: official release v0.1.0 from CSC Roihu GH200 training run `l1_base-seed0-20261003T093922Z-81ab34b`.
