<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Tiefer Lab

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Tiefer Lab is where Tiefer trains, compresses and measures the models that run on board Earth observation satellites. It is not flight software: nothing here has flown, the trained models are not distributed, and no hardware measurement has been made yet.

[Website](https://tiefer.space) | [Specification](docs/SPEC.md) | [Results](docs/RESULTS.md) | [Licence](LICENSE)

---

## About

Tiefer builds software that lets an Earth observation satellite analyse its own images in orbit. The onboard pipeline Tiefer describes has four stages: filter (keep frames that are not useful on board), detect (run event models on the useful frames), alert (send a small packet through the first available link) and update (replace models in orbit with small, signed updates). Tiefer Lab builds and measures the first stage, the cloud filter; what exists of each stage is recorded in [CLAIMS.md](CLAIMS.md).

The repository is public because results are published with their method: measured, not claimed. [docs/RESULTS.md](docs/RESULTS.md) is written by hand; every value names the report file it was copied from, and the report file records the git commit, configuration and platform.

### What Lab is not

- Not flight software, and not flight-proven: every model ran on GPUs on CSC Roihu, never on a satellite.
- Not a model distribution: trained models are not published here and no licence is granted for them ([LICENSING.md](LICENSING.md)).
- Not measured on hardware: the Jetson Orin scripts exist, but no latency, power or energy has been measured ([docs/RESULTS.md](docs/RESULTS.md), section 15).
- Not measured on a target sensor: every result is on Sentinel-2 Level-1C data from CloudSEN12+.
- Not a detector, alert system or update system: those stages have no code in this repository ([CLAIMS.md](CLAIMS.md)).

---

## Status

| Milestone or component | Status | Evidence |
| :--- | :---: | :---: |
| **Milestone L1: four-band cloud filter** | | |
| Data cache (CloudSEN12+, Level-1C, four bands) | done | [docs/DATA.md](docs/DATA.md), section 10 |
| Training and evaluation on CSC Roihu (`l1_base` seeds 0 and 1, `l1_full` seed 0) | measured | [docs/RESULTS.md](docs/RESULTS.md), section 6 |
| ONNX export and INT8 quantisation | measured | [docs/RESULTS.md](docs/RESULTS.md), section 14 |
| Model card and checksums (v0.1.0, `l1_base` seed 0) | draft | [models/cloud-filter/v0.1.0/MODEL_CARD.md](models/cloud-filter/v0.1.0/MODEL_CARD.md) |
| **Milestone L2: band-flexible model and four-band specialist** | | |
| 13-band data cache | done | [docs/DATA.md](docs/DATA.md), section 10 |
| Training and evaluation on CSC Roihu (`l2_flex_1m` and `l2_spec_1m`, seed 0) | measured | [docs/RESULTS.md](docs/RESULTS.md), sections 6 and 12 |
| Export of the L2 models | not measured | [docs/RESULTS.md](docs/RESULTS.md), section 14 |
| Seeds 1 and 2 of the L2 pair | not run | [hpc/roihu/plan.md](hpc/roihu/plan.md), section 1 |
| Product decision between the two L2 models | pending | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 7 |
| **Jetson milestone** | | |
| Benchmark scripts, dry-run mode | done | [jetson/README.md](jetson/README.md) |
| Latency, power and energy on a Jetson Orin | not measured | [docs/RESULTS.md](docs/RESULTS.md), section 15 |

Headline numbers, as [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md) lists them: on the test split, the four-band specialist `l2_spec_1m` seed 0 has a mean IoU of 0.720 [0.707, 0.732] and a false discard rate at 50 percent of 0.042 [0.026, 0.059]; INT8 quantisation lowers the validation mean IoU by 0.060 to 0.154 on the three exported L1 runs. Caveats: single seeds, L2 settings not in the committed configs, report files still on CSC Roihu, and padded pixels counted in every metric ([BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), section 3).

---

## Where to go next

| You want to | Read |
| :--- | :---: |
| Find the one document that answers your question | [START-HERE.md](START-HERE.md) |
| Run Lab on your computer in minutes, offline | [GETTING-STARTED.md](GETTING-STARTED.md) |
| Check what is real before anything else | [CLAIMS.md](CLAIMS.md) |
| Find the number to quote and how to cite it | [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md) |

---

## Quick start

```bash
git clone https://github.com/tiefer-labs/lab.git
cd lab
make setup
make check
make smoke SMOKE_SOURCE=synthetic
```

Requirements, durations, the expected output and troubleshooting are in [GETTING-STARTED.md](GETTING-STARTED.md). Installation on CSC Roihu, on a Jetson and from a source archive is in [INSTALL.md](INSTALL.md); training on CSC Roihu is in [hpc/roihu/README.md](hpc/roihu/README.md).

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

Every Markdown file of the repository, with its purpose, audience and status, is listed in [INDEX.md](INDEX.md); [START-HERE.md](START-HERE.md) routes a task to the document that owns it. The five most used:

- [docs/RESULTS.md](docs/RESULTS.md): measured results; every value names the report file it was copied from.
- [docs/SPEC.md](docs/SPEC.md): the specification for milestones L1 and L2.
- [docs/DATA.md](docs/DATA.md): the data card for CloudSEN12+.
- [hpc/roihu/README.md](hpc/roihu/README.md): the guide for training on CSC Roihu.
- [CONTRIBUTING.md](CONTRIBUTING.md): how to contribute.

---

## Principles

1. Measured, not claimed: every number names the report file it comes from, and anything not measured is written as "not measured". The gates a number must pass are in [POLICY.md](POLICY.md). The commands for each run are in [docs/RESULTS.md](docs/RESULTS.md), section 19. Not every number can be reproduced from a commit yet: `l1_base s0` ran from a working tree with uncommitted changes, the L2 runs used a batch size and learning rate that are not in their committed configs, and the report files of 2 and 3 October 2026 are still on CSC Roihu (docs/RESULTS.md, section 4).
2. Think like the sensor on board: top-of-atmosphere Level-1C data only; four bands (blue, green, red, near infrared) for L1, and band sets of up to 13 bands for the band-flexible L2 model.
3. Small and friendly to the hardware: at most 1.0 million parameters for L1, a size ladder for L2, and only operators that TensorRT handles well in INT8.
4. Reproducible: fixed seeds, versioned configurations, a locked environment, and the dataset revision and the git commit in every result file, with a flag when the working tree had uncommitted changes.
5. The test split is used only for final evaluation, and every use is logged where it runs. The entries of the test evaluations of 3 October 2026 are on CSC Roihu and pending a copy into [reports/test_log.md](reports/test_log.md), which has no entries yet.

---

## Licence

The repository is licensed under the Mozilla Public License 2.0, see [LICENSE](LICENSE). What each part is licensed under, and what is not licensed (trained models, the images in `docs/assets/`, the Tiefer name and logo), is in [LICENSING.md](LICENSING.md); attributions are in [NOTICE.md](NOTICE.md), and the use of the name and logo in [TRADEMARK.md](TRADEMARK.md).

---

## Contact

`hello@tiefer.space`. Security reports follow [SECURITY.md](SECURITY.md); help is described in [SUPPORT.md](SUPPORT.md).

---

## Changelog

- 7 October 2026: the first screen says what Lab is and what it is not; "What Lab is not", a status table with evidence, "Where to go next", a minimal quick start that defers to GETTING-STARTED.md and INSTALL.md, and a documentation section that points to INDEX.md and START-HERE.md; the community files of this repository replace the links to tiefer-labs/.github.
- 7 October 2026: the documentation list adds DATASETS.md, REQUIREMENTS.md, STANDARDS.md, NOTICE.md and hpc/roihu/plan.md; principles 1 and 4 say what holds now and what is pending.
- 7 October 2026: correction: `l1_base` has two seeds; the other runs are single seeds.
- 7 October 2026: correction: the test log entries of 3 October 2026 are on CSC Roihu and pending a copy.
- 7 October 2026: the documentation list links docs/LANDSCAPE.md.
- 7 October 2026: the status describes milestones L1 and L2 as measured on CSC Roihu, with the headline results; principles and layout mention the L2 band sets and sizes.
- 7 October 2026: docs/RESULTS.md is written by hand; the command of the results generator is removed.
