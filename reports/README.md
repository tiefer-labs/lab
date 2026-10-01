<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Reports

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What each report file is and which script writes it. Every number in [docs/RESULTS.md](../docs/RESULTS.md) comes from a file in this folder, and every file records the git commit, configuration and platform that produced it.

---

## Requirements

- Reports from real runs only. Smoke runs write their reports elsewhere (`$TIEFER_RUNS_DIR/smoke/reports/`), are marked `"smoke": true`, and are ignored by the results generator.

---

## Steps

1. Run the scripts below, on CSC Roihu or locally; they write into `$TIEFER_REPORTS_DIR` (default `./reports`).
2. Copy the files from Roihu with `hpc/roihu/collect.sh` (see [hpc/roihu/README.md](../hpc/roihu/README.md)).
3. Regenerate the results page:

   ```bash
   make results
   ```

---

## Files

| File | Written by | Contents |
| :--- | :---: | :---: |
| `evaluation/<run-id>_val.json` | `python -m tiefer_lab.evaluate --split val` | pixel and frame metrics, false discard rate, bootstrap intervals, breakdown by metadata, baselines, provenance |
| `evaluation/<run-id>_test.json` | `python -m tiefer_lab.evaluate --split test --final` | the same on the test split, final evaluation only |
| `export/<run-id>.json` | `python -m tiefer_lab.export` | SHA-256 of the ONNX files, parameters, operations, operators, ONNX Runtime check, INT8 change |
| `jetson/<label>_<UTC time>.json` | `jetson/bench.py` on a Jetson Orin | latency, throughput, power, energy per tile, temperatures |
| `compute/<job-id>.json` | `hpc/roihu/usage.sh` | `sacct` record of a Roihu job |
| `test_log.md` | `python -m tiefer_lab.evaluate` and `python -m tiefer_lab.export` with `--final` | one entry per use of the test split: date, run ID, git commit, reason |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `make results` refuses to run | no real evaluation report in `reports/evaluation/` | evaluate a real run first, or use `python -m tiefer_lab.results --placeholder` |
| A report is missing from `docs/RESULTS.md` | it is marked as a smoke report | smoke reports are never results; evaluate a real run |
