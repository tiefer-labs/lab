<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Jetson reports

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Where the Jetson Orin benchmark results land. Each file is written by `jetson/bench.py` on the board and copied here unchanged.

---

## Requirements

- Results from `python3 jetson/bench.py` on an NVIDIA Jetson Orin, as described in [jetson/README.md](../../jetson/README.md).

## Steps

1. Run the benchmark on the board; it writes `reports/jetson/<label>_<UTC time>.json`.
2. Copy the files into this folder of the repository and commit them.
3. Regenerate the results page:

   ```bash
   make results
   ```

## Files

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">File</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Contents</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>&lt;label&gt;_&lt;UTC time&gt;.json</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">device, latency percentiles, throughput, power, energy per tile, temperatures, out of scope note</td>
</tr>
</tbody>
</table>
</div>

No Jetson measurements exist yet: every hardware value in [docs/RESULTS.md](../../docs/RESULTS.md) is "not yet measured".
