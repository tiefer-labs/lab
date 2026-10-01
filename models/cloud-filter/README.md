<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Cloud filter releases

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What a release folder of the cloud filter contains. The model files themselves are never published from this repository: checkpoints and ONNX files stay with Tiefer, and the checksums here let Tiefer show which model produced which result.

---

## Requirements

- A finished training run in `$TIEFER_RUNS_DIR/<run-id>/` with `best.pt`.
- Its export report from `python -m tiefer_lab.export --run <run-id>`, in `reports/export/<run-id>.json`.
- Its evaluation reports in `reports/evaluation/`.

## Steps

Release folders are written in Part B of milestone L1, after the runs on CSC Roihu.

1. Create the folder `models/cloud-filter/<version>/`, for example `models/cloud-filter/v0.1.0/`.
2. Copy the resolved configuration of the run:

   ```bash
   cp runs/<run-id>/config.toml models/cloud-filter/<version>/config.toml
   ```

3. Write the checksums of the exported files (the same values are in the export report):

   ```bash
   (cd runs/<run-id>/export && sha256sum cloud_filter_*.onnx) > models/cloud-filter/<version>/SHA256SUMS
   ```

4. Write `MODEL_CARD.md` following `docs/STYLE.md`, section 7, with every number taken from a report file.

## Files

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">File</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Contents</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Committed</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Release folder</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>MODEL_CARD.md</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">summary, intended use, data, evaluation, quantisation, hardware, limitations</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">yes</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>SHA256SUMS</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">SHA-256 of every ONNX file of the release</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">yes</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>config.toml</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">resolved training configuration</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">yes</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Kept by Tiefer, never committed</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>best.pt</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">PyTorch checkpoint</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cloud_filter_fp32.onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">FP32, fixed input 1 x 4 x 512 x 512</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cloud_filter_fp32_dynamic.onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">FP32, dynamic batch</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cloud_filter_fp16.onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">FP16</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cloud_filter_int8.onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">INT8, QDQ format</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no</td>
</tr>
</tbody>
</table>
</div>

## Troubleshooting

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Symptom</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Cause</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Fix</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sha256sum</code> values differ from the export report</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the files were exported again or changed after the report</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">export once, and copy the report and the files together</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>git add</code> ignores an <code>.onnx</code> file</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">model files are excluded by <code>.gitignore</code> on purpose</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">keep them outside git; commit only the release folder files</td>
</tr>
</tbody>
</table>
</div>
