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

| Milestone L1 component | Code | Measured |
| :--- | :---: | :---: |
| **Part A: repository** | | |
| Data cache (CloudSEN12+, Level-1C, four bands) | done | n/a |
| Metrics and baselines | done | not yet measured |
| Model and training | done | not yet measured |
| Evaluation with test split guard | done | not yet measured |
| ONNX export and INT8 quantisation | done | not yet measured |
| Jetson Orin benchmark scripts | done | not yet measured |
| CSC Roihu job scripts and guide | done | n/a |
| **Part B: results** | | |
| Training and evaluation on CSC Roihu | n/a | not yet measured |
| Model card and checksums | n/a | not yet measured |

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

| Variable | Default | Contents |
| :--- | :---: | :---: |
| `TIEFER_DATA_DIR` | `./data` | the data cache |
| `TIEFER_RUNS_DIR` | `./runs` | training runs: configuration, metadata, metrics, checkpoints, ONNX files |
| `TIEFER_REPORTS_DIR` | `./reports` | evaluation, export, Jetson and compute reports |

### Run on CSC Roihu

Training and full evaluation run on CSC Roihu GPU nodes (NVIDIA GH200). The step-by-step guide, including setup, the data cache, Slurm jobs and copying results back, is in [hpc/roihu/README.md](hpc/roihu/README.md).

---

## Repository layout

| Path | Contents |
| :--- | :---: |
| `src/tiefer_lab/` | data access, model, training, evaluation, export and results code |
| `configs/` | training configurations in TOML: `smoke.toml` and `l1_base.toml` |
| `tests/` | unit tests on synthetic data, text rules and public hygiene |
| `hpc/roihu/` | Slurm jobs, setup and guide for CSC Roihu |
| `jetson/` | benchmark scripts for an NVIDIA Jetson Orin |
| `reports/` | report files written by the scripts, and the test split log |
| `models/cloud-filter/` | model cards and checksums; model files are not distributed here |
| `docs/` | specification, style, data card, assumptions, dependencies and results |

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
