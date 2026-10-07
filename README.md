<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Tiefer Lab

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Tiefer Lab is where Tiefer trains, compresses and measures the models that run on board Earth observation satellites.

[Website](https://tiefer.space) | [Specification](docs/SPEC.md) | [Results](docs/RESULTS.md) | [Licence](LICENSE)

---

## About

Tiefer builds software that lets an Earth observation satellite analyse its own images in orbit. Instead of sending every raw frame to the ground, the onboard pipeline works in four stages: filter (keep frames that are not useful on board), detect (run event models on the useful frames), alert (send a small packet through the first available link) and update (replace models in orbit with small, signed updates). Each model is trained, compressed and measured in this repository before it is considered for flight.

The repository is public because results are published with their method: measured, not claimed. [docs/RESULTS.md](docs/RESULTS.md) is written by hand. Every value names the report file in `reports/` that it was copied from, and the report file records the git commit, configuration and platform. Trained models are not published here.

---

## Status

Milestone L1 is the first stage, the onboard cloud filter: a small network that labels every pixel of a four-band frame as clear, thick cloud, thin cloud or cloud shadow, and decides per frame whether it is worth sending to the ground. Milestone L2 measures model size, a band-flexible model that reads any of the 13 Sentinel-2 Level-1C bands, and a four-band specialist as its control. The code, tests and guides of both are done. Training and evaluation ran on CSC Roihu on 2 and 3 October 2026; the Jetson Orin is not measured yet.

| Component | Code | Measured |
| :--- | :---: | :---: |
| **Milestone L1** | | |
| Data cache (CloudSEN12+, Level-1C, four bands) | done | n/a |
| Training and evaluation on CSC Roihu | done | measured: `l1_base` seeds 0 and 1, `l1_full` seed 0 |
| ONNX export and INT8 quantisation | done | measured; INT8 loses more mean IoU than the one-point limit |
| Model card and checksums | done | draft, v0.1.0 (`l1_base` seed 0) |
| Jetson Orin benchmark | done | not measured |
| **Milestone L2** | | |
| 13-band cache | done | n/a |
| Training and evaluation on CSC Roihu | done | measured: `l2_flex_1m` and `l2_spec_1m`, seed 0 |
| Export of the L2 models | done | not measured |
| Seeds 1 and 2 of the L2 pair | n/a | not run |

On the test split, the four-band specialist `l2_spec_1m` (seed 0) has a mean IoU of 0.720 [0.707, 0.732] and a false discard rate at 50 percent of 0.042 [0.026, 0.059]; `l1_base` (seed 0), the model of the v0.1.0 model card, has 0.635 [0.621, 0.649] and 0.039 [0.024, 0.055]. On four bands, the band-flexible `l2_flex_1m` (seed 0) has a test mean IoU of 0.609. INT8 quantisation lowers the validation mean IoU by 0.060 to 0.154 on the three exported L1 runs. `l1_base` has two seeds (validation mean IoU 0.649 and 0.691); `l1_full` and every L2 run are single seeds. Values, sources and what is still pending: [docs/RESULTS.md](docs/RESULTS.md).

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
| `configs/` | training configurations in TOML: `smoke.toml`, the L1 configs and the L2 family |
| `tests/` | unit tests on synthetic data, text rules and public hygiene |
| `hpc/roihu/` | Slurm jobs, setup and guide for CSC Roihu |
| `jetson/` | benchmark scripts for an NVIDIA Jetson Orin |
| `reports/` | report files written by the scripts, and the test split log |
| `models/cloud-filter/` | model cards and checksums; model files are not distributed here |
| `docs/` | specification, style, data card, assumptions, dependencies and results |

---

## Documentation

- [docs/SPEC.md](docs/SPEC.md): the specification for milestones L1 and L2.
- [docs/DATA.md](docs/DATA.md): the data card for CloudSEN12+, with every dataset fact the code depends on.
- [docs/DATASETS.md](docs/DATASETS.md): every dataset used or considered, its role per split, and how metrics compare with published ones.
- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md): sensor, data, decision and hardware assumptions to revisit.
- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): every requirement and acceptance target, its status and the test or report that verifies it.
- [docs/STANDARDS.md](docs/STANDARDS.md): the standards, handbooks and formats, the clauses read and the status of each.
- [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md): every dependency, why it is needed, and its licence.
- [docs/RESULTS.md](docs/RESULTS.md): measured results, written by hand; every value names the report file it was copied from.
- [docs/LANDSCAPE.md](docs/LANDSCAPE.md): related onboard cloud detection systems, onboard AI platforms and reference algorithms, their published values, and the measurements that would decide a comparison.
- [docs/STYLE.md](docs/STYLE.md): the documentation standard for Tiefer repositories.
- [NOTICE.md](NOTICE.md): what the licence covers and what it does not, third-party data, the typeface and the dependencies.
- [hpc/roihu/plan.md](hpc/roihu/plan.md): what ran on CSC Roihu against the plan, and the next steps.
- [hpc/roihu/README.md](hpc/roihu/README.md), [jetson/README.md](jetson/README.md), [reports/README.md](reports/README.md) and [models/cloud-filter/README.md](models/cloud-filter/README.md): guides for each folder.
- Security policy, contributing guide, code of conduct and support: [tiefer-labs/.github](https://github.com/tiefer-labs/.github).

---

## Principles

1. Measured, not claimed: every number names the report file it comes from, and anything not measured is written as "not measured". The commands for each run are in [docs/RESULTS.md](docs/RESULTS.md), section 19. Not every number can be reproduced from a commit yet: `l1_base s0` ran from a working tree with uncommitted changes, the L2 runs used a batch size and learning rate that are not in their committed configs, and the report files of 2 and 3 October 2026 are still on CSC Roihu (docs/RESULTS.md, section 4).
2. Think like the sensor on board: top-of-atmosphere Level-1C data only; four bands (blue, green, red, near infrared) for L1, and band sets of up to 13 bands for the band-flexible L2 model.
3. Small and friendly to the hardware: at most 1.0 million parameters for L1, a size ladder for L2, and only operators that TensorRT handles well in INT8.
4. Reproducible: fixed seeds, versioned configurations, a locked environment, and the dataset revision and the git commit in every result file, with a flag when the working tree had uncommitted changes.
5. The test split is used only for final evaluation, and every use is logged where it runs. The entries of the test evaluations of 3 October 2026 are on CSC Roihu and pending a copy into [reports/test_log.md](reports/test_log.md), which has no entries yet.

---

## Licence

The repository (code, scripts, configurations, documentation and reports) is licensed under the Mozilla Public License 2.0, see [LICENSE](LICENSE). Trained models are not part of the repository and are not covered by any licence here. The Tiefer name and logo are trademarks and are not licensed.

Data and dependencies: CloudSEN12+ is a third-party dataset under CC0 1.0 and is not included in the repository; every dependency and its licence is listed in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md). Details are in [NOTICE.md](NOTICE.md).

---

## Contact

`hello@tiefer.space`

---

## Changelog

- 7 October 2026: the documentation list adds DATASETS.md, REQUIREMENTS.md, STANDARDS.md, NOTICE.md and hpc/roihu/plan.md; principles 1 and 4 say what holds now and what is pending.
- 7 October 2026: correction: `l1_base` has two seeds; the other runs are single seeds.
- 7 October 2026: correction: the test log entries of 3 October 2026 are on CSC Roihu and pending a copy.
- 7 October 2026: the documentation list links docs/LANDSCAPE.md.
- 7 October 2026: the status describes milestones L1 and L2 as measured on CSC Roihu, with the headline results; principles and layout mention the L2 band sets and sizes.
- 7 October 2026: docs/RESULTS.md is written by hand; the command of the results generator is removed.
