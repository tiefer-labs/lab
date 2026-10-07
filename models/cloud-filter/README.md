<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Cloud filter releases

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What a release folder of the cloud filter contains. The model files themselves are never published from this repository: checkpoints and ONNX files stay with Tiefer, and the checksums here let Tiefer show which model produced which result.

---

## Requirements

- A finished training run in `$TIEFER_RUNS_DIR/<run-id>/` with `best.pt`.
- Its export report from `python -m tiefer_lab.export --run <run-id>`, in `reports/export/<run-id>.json`.
- Its evaluation reports in `reports/evaluation/`.

---

## Steps

Release folders are written after the runs on CSC Roihu. `v0.1.0` (`l1_base` seed 0) is a draft. A folder for `l2_spec_1m` seed 0 waits for its export report and the SHA-256 of its ONNX files; its quantisation is not measured yet ([docs/RESULTS.md](../../docs/RESULTS.md), section 14).

1. Create the folder `models/cloud-filter/<version>/`, for example `models/cloud-filter/v0.1.0/`.
2. Copy the resolved configuration of the run:

   ```bash
   cp runs/<run-id>/config.toml models/cloud-filter/<version>/config.toml
   ```

3. Write the checksums of the exported files (the same values are in the export report):

   ```bash
   (cd runs/<run-id>/export && sha256sum cloud_filter_*.onnx) > models/cloud-filter/<version>/SHA256SUMS
   ```

4. Copy `models/cloud-filter/MODEL_CARD_TEMPLATE.md` to `MODEL_CARD.md` in the release folder and fill it following `docs/STYLE.md`, section 7, with every number taken from a report file and the same value as in `docs/RESULTS.md`. Put the INT8 file size next to its loss in mean IoU.

---

## Files

| File | Contents | Committed |
| :--- | :---: | :---: |
| **Release folder** | | |
| `MODEL_CARD.md` | summary, intended use, data, evaluation, quantisation, hardware, limitations | yes |
| `SHA256SUMS` | SHA-256 of every ONNX file of the release | yes |
| `config.toml` | resolved training configuration | yes |
| **Kept by Tiefer, never committed** | | |
| `best.pt` | PyTorch checkpoint | no |
| `cloud_filter_fp32.onnx` | FP32, fixed input 1 x 4 x 512 x 512 | no |
| `cloud_filter_fp32_dynamic.onnx` | FP32, dynamic batch | no |
| `cloud_filter_fp16.onnx` | FP16 | no |
| `cloud_filter_int8.onnx` | INT8, QDQ format | no |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `sha256sum` values differ from the export report | the files were exported again or changed after the report | export once, and copy the report and the files together |
| `git add` ignores an `.onnx` file | model files are excluded by `.gitignore` on purpose | keep them outside git; commit only the release folder files |

---

## Changelog

- 7 October 2026: v0.1.0 is a draft; the folder for `l2_spec_1m` waits for its export report; values match `docs/RESULTS.md`, which is written by hand.
