<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Tiefer Lab

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Tiefer Lab is where Tiefer trains, compresses and measures the models that run on board Earth observation satellites.

[Website](https://tiefer.space) | [Specification](docs/SPEC.md) | [Results](docs/RESULTS.md) | [Licence](LICENSE)

---

## About

Tiefer builds software that lets an Earth observation satellite analyse its own images in orbit. Instead of sending every raw frame to the ground, the onboard pipeline works in four stages: filter (keep frames that are not useful on board), detect (run event models on the useful frames), alert (send a small packet through the first available link) and update (replace models in orbit with small, signed updates). Each model is trained, compressed and measured in this repository before it is considered for flight.

The repository is public because results are published with their method: measured, not claimed. Every number in [docs/RESULTS.md](docs/RESULTS.md) is generated from a report file written by a script in this repository, and every report records the git commit, configuration and platform that produced it. Trained models are not published here.

---

## Status

Milestone L1 is the first stage, the onboard cloud filter: a small network that labels every pixel of a four-band frame as clear, thick cloud, thin cloud or cloud shadow, and decides per frame whether it is worth sending to the ground. Part A (the code, tests and guides) is done; Part B (training and measurement on CSC Roihu and a Jetson Orin) has not started.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Milestone L1 component</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Code</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Measured</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Part A: repository</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Data cache (CloudSEN12+, Level-1C, four bands)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">n/a</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Metrics and baselines</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Model and training</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Evaluation with test split guard</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">ONNX export and INT8 quantisation</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Jetson Orin benchmark scripts</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">CSC Roihu job scripts and guide</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">done</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">n/a</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Part B: results</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Training and evaluation on CSC Roihu</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">n/a</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Model card and checksums</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">n/a</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
</tbody>
</table>
</div>

Results: [docs/RESULTS.md](docs/RESULTS.md). Every value there is "not yet measured" until the runs of Part B.

---

## Quick start

### Run locally

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/). The code runs on CUDA, Apple MPS or CPU, chosen automatically; every command accepts `--device` to override the choice.

```bash
git clone https://github.com/tiefer-labs/lab.git
cd lab
make setup
make check
make smoke
```

- `make setup` installs the locked environment from `uv.lock`.
- `make check` runs `ruff`, `mypy --strict` on `src/` and `pytest`. Tests use small synthetic arrays only and run on CPU.
- `make smoke` runs the whole pipeline on a tiny subset in a few minutes on CPU: data cache, training, evaluation, ONNX export, INT8 quantisation and the Jetson scripts in dry-run mode. It uses real CloudSEN12+ patches when the dataset is reachable and synthetic scenes otherwise, writes only to `runs/smoke/`, and its outputs are never results.

The full pipeline, one command per step:

```bash
uv run python -m tiefer_lab.data.build_cache --split all
uv run python -m tiefer_lab.train --config configs/l1_base.toml
uv run python -m tiefer_lab.evaluate --run <run-id> --split val --baselines
uv run python -m tiefer_lab.export --run <run-id>
uv run python -m tiefer_lab.results
```

Locations come from three environment variables, documented in [.env.example](.env.example):

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Variable</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Default</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Contents</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>TIEFER_DATA_DIR</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>./data</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the data cache</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>TIEFER_RUNS_DIR</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>./runs</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">training runs: configuration, metadata, metrics, checkpoints, ONNX files</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>TIEFER_REPORTS_DIR</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>./reports</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">evaluation, export, Jetson and compute reports</td>
</tr>
</tbody>
</table>
</div>

### Run on CSC Roihu

Training and full evaluation run on CSC Roihu GPU nodes (NVIDIA GH200). The step-by-step guide, including setup, the data cache, Slurm jobs and copying results back, is in [hpc/roihu/README.md](hpc/roihu/README.md).

---

## Repository layout

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Path</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Contents</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>src/tiefer_lab/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">data access, model, training, evaluation, export and results code</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>configs/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">training configurations in TOML: <code>smoke.toml</code> and <code>l1_base.toml</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tests/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">unit tests on synthetic data, text rules and public hygiene</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>hpc/roihu/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Slurm jobs, setup and guide for CSC Roihu</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>jetson/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">benchmark scripts for an NVIDIA Jetson Orin</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>reports/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">report files written by the scripts, and the test split log</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>models/cloud-filter/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">model cards and checksums; model files are not distributed here</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>docs/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">specification, style, data card, assumptions, dependencies and results</td>
</tr>
</tbody>
</table>
</div>

---

## Documentation

- [docs/SPEC.md](docs/SPEC.md): the specification for milestone L1.
- [docs/DATA.md](docs/DATA.md): the data card for CloudSEN12+, with every dataset fact the code depends on.
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md): sensor, data, decision and hardware assumptions to revisit.
- [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md): every dependency, why it is needed, and its licence.
- [docs/RESULTS.md](docs/RESULTS.md): results, generated from report files.
- [docs/STYLE.md](docs/STYLE.md): the Markdown standard for Tiefer repositories.
- [hpc/roihu/README.md](hpc/roihu/README.md), [jetson/README.md](jetson/README.md), [reports/README.md](reports/README.md) and [models/cloud-filter/README.md](models/cloud-filter/README.md): guides for each folder.
- Security policy, contributing guide, code of conduct and support: [tiefer-labs/.github](https://github.com/tiefer-labs/.github).

---

## Principles

1. Measured, not claimed: every number is reproducible with one command, and anything not measured is written as "not measured".
2. Think like the sensor on board: four bands (blue, green, red, near infrared) and top-of-atmosphere Level-1C data only.
3. Small and friendly to the hardware: at most 1.0 million parameters and only operators that TensorRT handles well in INT8.
4. Reproducible: fixed seeds, versioned configurations, a locked environment, the dataset revision and the git commit in every result file.
5. The test split is used only for final evaluation, and every use is logged in [reports/test_log.md](reports/test_log.md).

---

## Licence

The repository (code, scripts, configurations, documentation and reports) is licensed under the Mozilla Public License 2.0, see [LICENSE](LICENSE). Trained models are not part of the repository and are not covered by any licence here. The Tiefer name and logo are trademarks and are not licensed.

Data and dependencies: CloudSEN12+ is a third-party dataset under CC0 1.0 and is not included in the repository; every dependency and its licence is listed in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md). Details are in [NOTICE.md](NOTICE.md).

---

## Contact

`hello@tiefer.space`
