<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Model card template: cloud filter

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Copy this file to `models/cloud-filter/<version>/MODEL_CARD.md`, set its status line to `draft`, and replace every placeholder in angle brackets with the value from the source named next to it. A value without its source is written with a word of [docs/STYLE.md](../../docs/STYLE.md), section 4: `not measured` (never measured), `pending` (measured, the report is not yet in the repository) or `n/a`.

The model files are not distributed in this repository, and no licence is granted for them; only the model card, `SHA256SUMS` and `config.toml` are committed. Values are rounded to 3 decimals, half up.

---

## Summary

| Field | Value | Source |
| :--- | :---: | :---: |
| Task | per-pixel classes clear, thick cloud, thin cloud, cloud shadow; per-frame send or keep decision | `docs/SPEC.md`, section 8 |
| Architecture and parameters | `<architecture>`, `<parameters>` parameters | `metadata.json` of the run: `model.architecture`, parameters |
| Band set | `<bands>` | export report: `band_set` |
| Input | `1 x <bands> x 512 x 512` | export report: input shape |
| Output | 4 class logits per pixel | export report |
| Operations | `<multiply-accumulates>` multiply-accumulates for one 512 x 512 tile | `metadata.json`: `model.macs_512x512` |
| Formats | `<formats>` | export report: FP32, FP16, INT8 |
| Training run and commit | `<run-id>`, `<commit>`; say whether the working tree had uncommitted changes | `metadata.json`: run ID, `git_commit`, `dirty` |
| Training | batch `<batch>`, learning rate `<rate>`, `<epochs>` epochs, best epoch `<best>`, `<stop>` | `config.toml`; evaluation report: `run.best_epoch`, `run.status` |
| Dataset revision and cache | `<revision>`, cache `<cache-name>` | evaluation report; `index.json` of the cache |
| Selected model | `<yes or no>`, with the reason | `docs/RESULTS.md` |
| Pretrained weights | none; trained from random initialisation | `NOTICE.md` |
| Weight licence | not distributed; no licence is granted for the model files | `LICENSING.md` |
| Date | `<date>` | `metadata.json`: end of the last session |

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

CloudSEN12+ Level-1C, training split, `<patches>` patches, as described in `docs/DATA.md`, section 2.3; the selection counts come from `index.json` of the cache. Extra scribble or nolabel patches: `<patches or none>` (`index.json`, split `train_extra`).

---

## Evaluation

Every test evaluation appends an entry to `reports/test_log.md` on the machine that runs it; say whether the entry of each test row is in the repository yet. Commit of the reports in this table: `<commit per report>`.

| Metric | Split | Value | 95 percent interval | Source |
| :--- | :---: | :---: | :---: | :---: |
| Mean IoU, four classes | `<split>` | `<value>` | `<interval>` | `reports/evaluation/<run-id>_<split>.json` |
| Cloud balanced overall accuracy (BOA), median over patches | `<split>` | `<value>` | `<interval>` | same report, `binary` |
| Shadow BOA, median over patches | `<split>` | `<value>` | `<interval>` | same report, `binary` |
| False discard rate at the operator threshold | `<split>` | `<value>` | `<interval>` | same report, `frame` |
| Expected calibration error | `<split>` | `<value>` | n/a | same report, `calibration` |
| Worst stratum, cloud BOA | `<split>` | `<value>` | n/a | same report, `worst_stratum` |
| Fail-safe cases that end in a discarded frame | n/a | `<value>` | n/a | `reports/acceptance.md`, `STD-02`, or `tests/test_onboard.py` |

---

## Quantisation

Split `<split>`, ONNX Runtime, INT8 calibrated on `<patches>` training patches.

| Format | File size in bytes | Mean IoU | Change against FP32 | Cloud BOA change | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| FP32 | `<bytes>` | `<value>` | n/a | n/a | export report |
| FP16 | `<bytes>` | `<value>` | `<change>` | `<change>` | export report |
| INT8 | `<bytes>` | `<value>` | `<change>` | `<change>` | export report |

---

## Hardware measurements

| Device and setting | Latency p50 per 512 x 512 tile | Latency p99 | Energy per tile | Source |
| :--- | :---: | :---: | :---: | :---: |
| Jetson Orin, FP16 | `<ms>` | `<ms>` | `<mJ>` | `reports/jetson/` |
| Jetson Orin, INT8 | `<ms>` | `<ms>` | `<mJ>` | `reports/jetson/` |

---

## Limitations

- Trained and validated on Sentinel-2 at 10 m only; no target-sensor data was used.
- Human agreement on thin cloud and shadow limits what any model can score on them: `<value, verify from the CloudSEN12 paper, Table 6, and docs/DATA.md, section 3>`.
- Results hold for the band set and size in the summary only.
- Standards: no agency or operator standard is claimed; see `docs/STANDARDS.md`.

---

## Files

Every file named here has its SHA-256 in `SHA256SUMS`; a file that is not in it is excluded explicitly below the table, with the reason.

| File | SHA-256 |
| :--- | :---: |
| `<file>` | `<sha-256>` |

---

## Changelog

- 7 October 2026: the weight licence row cites LICENSING.md, which now states it.
- 7 October 2026: status `in use`; placeholders in angle brackets and the words of docs/STYLE.md, section 4, instead of "not yet measured" and `TODO(verify)`; the rounding rule and the licence statement.
- 7 October 2026: new fields: training settings, dataset revision and cache, selected model, weight licence; a split column and a commit per evaluation table; FP32 row and file sizes in quantisation; latency p99 and energy per tile in hardware; BOA, calibration error, worst stratum and fail-safe rows; every file hashed or excluded.
- 7 October 2026: a test row says whether its entry in `reports/test_log.md` is in the repository yet.
- 2 October 2026: template.
