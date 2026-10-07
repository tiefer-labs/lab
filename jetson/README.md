<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Jetson benchmark

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How to measure latency, throughput, power and energy of the cloud filter on an NVIDIA Jetson Orin, the flight-like reference hardware for milestone L1. The Jetson Orin is not flight hardware, and radiation, vacuum and thermal effects are out of scope. What is installed on the board is in [INSTALL.md](../INSTALL.md), section 2.5; a value measured here appears in [docs/RESULTS.md](../docs/RESULTS.md) only under [POLICY.md](../POLICY.md), gate 1; another hardware target follows [EXTENDING.md](../EXTENDING.md), section 9.

---

## Requirements

- An NVIDIA Jetson Orin with JetPack installed, which provides `trtexec`, `tegrastats`, `nvpmodel` and `jetson_clocks`.
- The exported files of a run, from `python -m tiefer_lab.export --run <run-id>`: `cloud_filter_fp32.onnx` and `cloud_filter_int8.onnx`.
- A copy of this repository on the board. The scripts use the system Python 3 and its standard library only.

---

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

4. Copy the JSON files from `reports/jetson/` into the same folder of the repository unchanged, and copy their values by hand into [docs/RESULTS.md](../docs/RESULTS.md), section 15, naming each file.

Every script has a dry run that validates the inputs and prints the plan without running anything. It is used automatically on a machine that is not a Jetson:

```bash
python3 jetson/bench.py --engine engines/cloud_filter_fp16.engine --label fp16 --dry-run
```

---

## What is measured

- Latency per tile with batch 1: p50, p95, p99, mean, minimum and maximum, from the per-inference times that `trtexec --exportTimes` writes.
- Throughput: tiles per second = 1000 / mean latency in ms. Square kilometres per second = tiles per second x tile area, where tile area = (512 px x 10 m)^2 = (5.12 km)^2 = 26.2144 km2 for Sentinel-2 sampling.
- Power: the input rail from `tegrastats`, sampled every 100 ms during the run and for 10 s at idle before it.
- Energy per tile in millijoules = mean input power (W) x mean latency (s) x 1000, for the total board power and for the power above idle.
- Board temperatures at the start and the end of the run.
- Large frames, with `--frame-pixels N`: frames per second of the tiled path (`tiefer_lab.onboard.predict_frame`) for a square frame of N pixels at the training resolution, = 1000 / (mean tile latency in ms x tiles per frame), with tiles of 512 pixels overlapping by `--overlap` pixels (default 64). Resampling and stitching are not included.

---

## Files

| File | Purpose |
| :--- | :---: |
| `device_info.sh` | board model, L4T, JetPack, TensorRT, power mode, clocks |
| `build_engines.sh` | `trtexec` FP16 and INT8 engines |
| `bench.py` | latency, throughput, power, energy and temperature; JSON report to `reports/jetson/` |
| `power.py` | `tegrastats` sampler and parser |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| The scripts only print a plan | not a Jetson board, or `trtexec` not found | run on the board; pass `--trtexec <path>` or set `TRTEXEC` for `build_engines.sh` |
| `no known input rail` | the module names its input rail differently | check `tegrastats --interval 1000` and pass `--rail <name>` |
| `no latency field` in trtexec times | the TensorRT version writes other field names | check the times file and extend `LATENCY_FIELDS` in `bench.py` (TODO(verify) on the board) |
| `nvpmodel` or `jetson_clocks` show permission errors | they need root on some JetPack versions | run `device_info.sh` with `sudo` (TODO(verify) on the board) |

---

## Changelog

- 7 October 2026: the purpose links INSTALL.md, POLICY.md and EXTENDING.md.
- 7 October 2026: step 4 copies the values into docs/RESULTS.md by hand; the results generator is removed.
