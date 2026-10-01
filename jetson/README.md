<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Jetson benchmark

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How to measure latency, throughput, power and energy of the cloud filter on an NVIDIA Jetson Orin, the flight-like reference hardware for milestone L1. The Jetson Orin is not flight hardware, and radiation, vacuum and thermal effects are out of scope.

---

## Requirements

- An NVIDIA Jetson Orin with JetPack installed, which provides `trtexec`, `tegrastats`, `nvpmodel` and `jetson_clocks`.
- The exported files of a run, from `python -m tiefer_lab.export --run <run-id>`: `cloud_filter_fp32.onnx` and `cloud_filter_int8.onnx`.
- A copy of this repository on the board. The scripts use the system Python 3 and its standard library only.

## Steps

1. Record the device and set the power mode you want to measure. Note the mode in the label of each run.

   ```bash
   bash jetson/device_info.sh
   ```

2. Build the TensorRT engines (FP16 from the FP32 ONNX file, INT8 from the QDQ ONNX file):

   ```bash
   bash jetson/build_engines.sh --fp32 <export-dir>/cloud_filter_fp32.onnx --int8 <export-dir>/cloud_filter_int8.onnx --out engines
   ```

   With a TensorRT calibration cache instead of the QDQ file, pass `--calib <calibration.cache>` in place of `--int8`.

3. Benchmark each engine (at least 1,000 runs after a 2 s warm-up, with tegrastats sampling the input power rail):

   ```bash
   python3 jetson/bench.py --engine engines/cloud_filter_fp16.engine --label fp16
   python3 jetson/bench.py --engine engines/cloud_filter_int8.engine --label int8
   ```

4. Copy the JSON files from `reports/jetson/` into the repository, so `python -m tiefer_lab.results` can use them.

Every script has a dry run that validates the inputs and prints the plan without running anything. It is used automatically on a machine that is not a Jetson:

```bash
python3 jetson/bench.py --engine engines/cloud_filter_fp16.engine --label fp16 --dry-run
```

## What is measured

- Latency per tile with batch 1: p50, p95, p99, mean, minimum and maximum, from the per-inference times that `trtexec --exportTimes` writes.
- Throughput: tiles per second = 1000 / mean latency in ms. Square kilometres per second = tiles per second x tile area, where tile area = (512 px x 10 m)^2 = (5.12 km)^2 = 26.2144 km2 for Sentinel-2 sampling.
- Power: the input rail from `tegrastats`, sampled every 100 ms during the run and for 10 s at idle before it.
- Energy per tile in millijoules = mean input power (W) x mean latency (s) x 1000, for the total board power and for the power above idle.
- Board temperatures at the start and the end of the run.

## Files

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">File</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Purpose</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>device_info.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">board model, L4T, JetPack, TensorRT, power mode, clocks</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>build_engines.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>trtexec</code> FP16 and INT8 engines</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>bench.py</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">latency, throughput, power, energy and temperature; JSON report to <code>reports/jetson/</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>power.py</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tegrastats</code> sampler and parser</td>
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
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">The scripts only print a plan</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not a Jetson board, or <code>trtexec</code> not found</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">run on the board; pass <code>--trtexec &lt;path&gt;</code> or set <code>TRTEXEC</code> for <code>build_engines.sh</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>no known input rail</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the module names its input rail differently</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">check <code>tegrastats --interval 1000</code> and pass <code>--rail &lt;name&gt;</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>no latency field</code> in trtexec times</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the TensorRT version writes other field names</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">check the times file and extend <code>LATENCY_FIELDS</code> in <code>bench.py</code> (TODO(verify) on the board)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvpmodel</code> or <code>jetson_clocks</code> show permission errors</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">they need root on some JetPack versions</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">run <code>device_info.sh</code> with <code>sudo</code> (TODO(verify) on the board)</td>
</tr>
</tbody>
</table>
</div>
