<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Tiefer Lab

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Tiefer Lab is where Tiefer trains, compresses and measures the models that run on board Earth observation satellites.

[Website](https://tiefer.space) | [Specification](docs/SPEC.md) | [Results](docs/RESULTS.md) | [Licence](LICENSE)

---

## About

Tiefer builds software that lets an Earth observation satellite analyse its own images in orbit. The onboard pipeline has four stages: filter, detect, alert and update. Each model is trained, compressed and measured in this repository before it is considered for flight.

The repository is public because results are published with their method. Every number in [docs/RESULTS.md](docs/RESULTS.md) is generated from a report file written by a script in this repository, and every report records the git commit, configuration and platform that produced it.

## Status

Milestone L1 is the first stage, the onboard cloud filter: a small network that labels every pixel of a four-band frame as clear, thick cloud, thin cloud or cloud shadow, and decides per frame whether it is worth sending to the ground.

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

## Quick start

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/tiefer-labs/lab.git
cd lab
make setup
make check
```

`make check` runs `ruff`, `mypy --strict` on `src/` and `pytest`. Tests use small synthetic arrays only and run on CPU.

`make smoke` runs the whole pipeline on a tiny subset in a few minutes on CPU: data cache, training, evaluation, ONNX export, INT8 quantisation and the Jetson scripts in dry-run mode. It uses real CloudSEN12+ patches when the dataset is reachable and synthetic scenes otherwise, writes only to `runs/smoke/`, and its outputs are never results.

Locations come from three environment variables, documented in [.env.example](.env.example): `TIEFER_DATA_DIR` (default `./data`), `TIEFER_RUNS_DIR` (default `./runs`) and `TIEFER_REPORTS_DIR` (default `./reports`).

Training and full evaluation run on CSC Roihu GPU nodes. The step-by-step guide is in [hpc/roihu/README.md](hpc/roihu/README.md).

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
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Data access, model, training, evaluation, export and results code</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>configs/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Training configurations in TOML</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tests/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Unit tests on synthetic data, text rules and public hygiene</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>hpc/roihu/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Slurm jobs and setup for CSC Roihu</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>jetson/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Benchmark scripts for an NVIDIA Jetson Orin</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>reports/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Report files written by the scripts</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>models/cloud-filter/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Model cards and checksums (model files are not distributed here)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>docs/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Specification, style, data card, assumptions, dependencies and results</td>
</tr>
</tbody>
</table>
</div>

## Documentation

- [docs/SPEC.md](docs/SPEC.md): the specification for milestone L1.
- [docs/DATA.md](docs/DATA.md): the data card for CloudSEN12+.
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md): sensor and data assumptions to revisit.
- [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md): every dependency, why it is needed, its licence.
- [docs/RESULTS.md](docs/RESULTS.md): results, generated from report files.
- [docs/STYLE.md](docs/STYLE.md): the Markdown standard for Tiefer repositories.
- Security policy, contributing guide, code of conduct and support: [tiefer-labs/.github](https://github.com/tiefer-labs/.github).

## Principles

1. Measured, not claimed: every number is reproducible with one command, and anything not measured is written as "not measured".
2. Think like the sensor on board: four bands (blue, green, red, near infrared) and top-of-atmosphere Level-1C data only.
3. Small and friendly to the hardware: at most 1.0 million parameters and only operators that TensorRT handles well in INT8.
4. Reproducible: fixed seeds, versioned configurations, a locked environment and the git commit in every result file.
5. The test split is used only for final evaluation, and every use is logged in [reports/test_log.md](reports/test_log.md).

## Licence

The repository is licensed under the Mozilla Public License 2.0, see [LICENSE](LICENSE). Trained models are not part of the repository. Licence notes for data, dependencies and trademarks are in [NOTICE.md](NOTICE.md).

## Contact

`hello@tiefer.space`
