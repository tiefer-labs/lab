<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Model card template: cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Copy this file to `models/cloud-filter/<version>/MODEL_CARD.md` and replace every "not yet measured" with the value from the report named next to it. A value without a report stays "not yet measured". The model files are not distributed in this repository; only this card, `SHA256SUMS` and `config.toml` are committed.

---

## Summary

| Field | Value | Source |
| :--- | :---: | :---: |
| Task | per-pixel classes clear, thick cloud, thin cloud, cloud shadow; per-frame send or keep decision | `docs/SPEC.md`, section 8 |
| Architecture and size | not yet measured | `metadata.json` of the run: `model.architecture`, parameters |
| Band set of this file | not yet measured | export report: `band_set` |
| Input | not yet measured | export report: input shape |
| Output | 4 class logits per pixel | export report |
| Operations | not yet measured | `metadata.json`: `model.macs_512x512` |
| Formats | not yet measured | export report: FP32, FP16, INT8 |
| Training run and commit | not yet measured | `metadata.json`: run ID, `git_commit` |
| Pretrained weights | none; trained from random initialisation | `NOTICE.md` |
| Date | not yet measured | `metadata.json`: end of the last session |

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

CloudSEN12+ Level-1C, training split, as described in `docs/DATA.md`; the selection counts come from `index.json` of the cache. Extra scribble or nolabel patches: not yet measured (`index.json`, split `train_extra`).

---

## Evaluation

Validation unless a row says test. Every test evaluation appends an entry to `reports/test_log.md` on the machine that runs it; say whether the entry of each test row is in the repository yet.

| Metric | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: |
| Mean IoU, four classes | not yet measured | not yet measured | `reports/evaluation/<run-id>_<split>_<bandset>.json` |
| Cloud balanced overall accuracy, median over patches | not yet measured | not yet measured | same report, `binary` |
| Shadow balanced overall accuracy, median over patches | not yet measured | not yet measured | same report, `binary` |
| False discard rate at the operator threshold | not yet measured | not yet measured | same report, `frame` |
| Expected calibration error | not yet measured | not applicable | same report, `calibration` |
| Worst stratum, cloud balanced overall accuracy | not yet measured | not applicable | same report, `worst_stratum` |
| Fail-safe cases that end in a discarded frame | not yet measured | not applicable | `reports/acceptance.md`, `STD-02` |

---

## Quantisation

| Format | Mean IoU change against FP32 | Cloud BOA change | Source |
| :--- | :---: | :---: | :---: |
| FP16 | not yet measured | not yet measured | export report |
| INT8 | not yet measured | not yet measured | export report |

---

## Hardware measurements

| Device and setting | Latency per 512 x 512 tile | Frames per second at the frame size | Source |
| :--- | :---: | :---: | :---: |
| Jetson, FP16 | not measured | not measured | `reports/jetson/` |
| Jetson, INT8 | not measured | not measured | `reports/jetson/` |

---

## Limitations

- Trained and validated on Sentinel-2 at 10 m only; no target-sensor data was used.
- Human agreement on thin cloud and shadow limits what any model can score on them; the dataset paper's figure is TODO(verify).
- Results hold for the band set and size in the summary only.
- Standards: no agency or operator standard is claimed; see `docs/STANDARDS.md`.

---

## Files

| File | SHA-256 |
| :--- | :---: |
| not yet measured | not yet measured |

---

## Changelog

- 7 October 2026: a test row says whether its entry in `reports/test_log.md` is in the repository yet.
- 2 October 2026: template.
