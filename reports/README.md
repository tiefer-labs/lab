<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Reports

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What each report file is and which script writes it. [docs/RESULTS.md](../docs/RESULTS.md) is written by hand. Every value names the report file in `reports/` that it was copied from, and the report file records the git commit, configuration and platform.

---

## Requirements

- Reports from real runs only. Smoke runs write their reports elsewhere (`$TIEFER_RUNS_DIR/smoke/reports/`), are marked `"smoke": true`, and are left out by the report loader (`src/tiefer_lab/reports.py`) and by `docs/RESULTS.md`.

---

## Steps

1. Run the scripts below, on CSC Roihu or locally; they write into `$TIEFER_REPORTS_DIR` (default `./reports`).
2. Copy the files from Roihu with `hpc/roihu/collect.sh` (see [hpc/roihu/README.md](../hpc/roihu/README.md)).
3. Commit the report files unchanged, then copy their values by hand into [docs/RESULTS.md](../docs/RESULTS.md), naming the file of each value in its source column and its appendix A. A value whose report file is not yet in this folder is written `pending` there.

---

## Files

| File | Written by | Contents |
| :--- | :---: | :---: |
| `evaluation/<run-id>_val.json` | `python -m tiefer_lab.evaluate --split val` | pixel and frame metrics, false discard rate, bootstrap intervals, breakdown by metadata, per-frame cloud fraction, shadow fraction and send or keep decision, baselines, provenance |
| `evaluation/<run-id>_test.json` | `python -m tiefer_lab.evaluate --split test --final` | the same on the test split, final evaluation only |
| `export/<run-id>.json` | `python -m tiefer_lab.export` | SHA-256 of the ONNX files, parameters, operations, operators, ONNX Runtime check, INT8 change |
| `jetson/<label>_<UTC time>.json` | `jetson/bench.py` on a Jetson Orin | latency, throughput, power, energy per tile, temperatures |
| `compute/<job-id>.json` | `hpc/roihu/usage.sh` | `sacct` record of a Roihu job |
| `test_log.md` | `python -m tiefer_lab.evaluate` and `python -m tiefer_lab.export` with `--final` | one entry per use of the test split: date, run ID, git commit, reason |

The report files of the runs of 2 and 3 October 2026 are still on CSC Roihu: 23 evaluation, 3 export and 16 compute reports, plus the entries of the test evaluations in its `test_log.md`. [docs/RESULTS.md](../docs/RESULTS.md) lists each of them in appendix A and writes `pending` for every value that only these files hold. Copy them here unchanged; trained models (`best.pt`, `.onnx`) are never committed.

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| A value in `docs/RESULTS.md` is `pending` | its report file is not yet in this folder | copy the file from CSC Roihu unchanged (`hpc/roihu/collect.sh`), then replace `pending` with its value and name the file |
| A report is not used in `docs/RESULTS.md` | it is marked as a smoke report | smoke reports are never results; evaluate a real run |

---

## Changelog

- 7 October 2026: the report files of 2 and 3 October are still on CSC Roihu and are pending in docs/RESULTS.md.
- 7 October 2026: docs/RESULTS.md is written by hand from these files; the results generator and `make results` are removed.
