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

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">File</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Written by</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Contents</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>evaluation/&lt;run-id&gt;_val.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>python -m tiefer_lab.evaluate --split val</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">pixel and frame metrics, false discard rate, bootstrap intervals, breakdown by metadata, baselines, provenance</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>evaluation/&lt;run-id&gt;_test.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>python -m tiefer_lab.evaluate --split test --final</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the same on the test split, final evaluation only</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>export/&lt;run-id&gt;.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>python -m tiefer_lab.export</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">SHA-256 of the ONNX files, parameters, operations, operators, ONNX Runtime check, INT8 change</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>jetson/&lt;label&gt;_&lt;UTC time&gt;.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>jetson/bench.py</code> on a Jetson Orin</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">latency, throughput, power, energy per tile, temperatures</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>compute/&lt;job-id&gt;.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>hpc/roihu/usage.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sacct</code> record of a Roihu job</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>test_log.md</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>python -m tiefer_lab.evaluate</code> and <code>python -m tiefer_lab.export</code> with <code>--final</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">one entry per use of the test split: date, run ID, git commit, reason</td>
</tr>
</tbody>
</table>
</div>

---

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
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>make results</code> refuses to run</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no real evaluation report in <code>reports/evaluation/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">evaluate a real run first, or use <code>python -m tiefer_lab.results --placeholder</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">A report is missing from <code>docs/RESULTS.md</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">it is marked as a smoke report</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">smoke reports are never results; evaluate a real run</td>
</tr>
</tbody>
</table>
</div>
