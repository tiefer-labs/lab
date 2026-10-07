<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Getting started

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For a first-time user who wants to run Tiefer Lab on one computer in minutes. This document owns the first run and the offline proof: the whole pipeline on synthetic data, with no network, no GPU, no dataset and no account.

---

## 1. What you need

| Requirement | Version | Source |
| :--- | :---: | :---: |
| Linux or macOS with `git` and `make` | n/a | `Makefile` |
| Python | 3.12 or newer | `pyproject.toml` (`requires-python`), `.python-version` |
| uv | 0.8 or newer | `pyproject.toml` (`required-version`) |
| Network access | for `make setup` only, to download the locked packages | `uv.lock` |
| Disk | 5.8 GiB for `.venv` on Linux x86_64, measured on 7 October 2026 | `du -sh .venv` |

What you do not need: a GPU (the code chooses CUDA, Apple MPS or CPU, in that order, `src/tiefer_lab/utils/devices.py`), the CloudSEN12+ dataset, a Hugging Face account or token, or access to CSC Roihu. Installation on other platforms, on CSC Roihu and on a Jetson is in [INSTALL.md](INSTALL.md).

---

## 2. Steps

Durations were measured on 7 October 2026 on a Linux x86_64 machine with 4 CPU cores and no GPU, with the packages already downloaded. They are not laptop measurements; a laptop CPU is `not measured`.

| Step | Command | Duration | Writes | It worked when you see |
| :--- | :---: | :---: | :---: | :---: |
| 1. Clone | `git clone https://github.com/tiefer-labs/lab.git` | not measured | `lab/` | the folder `lab/` |
| 2. Install | `make setup` | not measured (download time depends on the network) | `.venv/` | no error from `uv sync --frozen` |
| 3. Check | `make check` | 25 s | caches of ruff, mypy and pytest | `All checks passed!`, `Success: no issues found`, `... passed` |
| 4. Smoke run | `make smoke` | 24 s | `runs/smoke/` | `== smoke run finished (outputs are labelled smoke and are never results)` |

```bash
git clone https://github.com/tiefer-labs/lab.git
cd lab
make setup
make check
make smoke
```

`make check` runs `ruff check`, `ruff format --check`, `mypy` and `pytest` (`Makefile`). The tests use small synthetic arrays and run on CPU.

`make smoke` runs `python -m tiefer_lab.smoke` (`src/tiefer_lab/smoke.py`): a data cache, training with `configs/smoke.toml` for 2 epochs, evaluation on validation with the baselines, ONNX export with the check against PyTorch, INT8 quantisation, the Jetson scripts in dry-run mode, and a check that the report loader leaves smoke reports out. It prints one `== smoke: <step>` line per step and a JSON summary at the end.

---

## 3. The offline proof

The smoke pipeline can be forced to use synthetic scenes, so that it needs no network and no dataset:

```bash
make smoke SMOKE_SOURCE=synthetic
```

`SMOKE_SOURCE` is passed to `python -m tiefer_lab.smoke --source`; its values are `auto` (the default), `cloudsen12` and `synthetic` (`Makefile`, `src/tiefer_lab/smoke.py`). With `auto`, the pipeline asks the Hugging Face API for the dataset revision; when that fails, it prints `dataset reachable: False; using synthetic` and continues with synthetic scenes. With `synthetic`, it never contacts the network.

How it was proved on 7 October 2026, with the packages installed and the network removed by a Linux network namespace:

```bash
unshare -rn env UV_OFFLINE=1 make smoke SMOKE_SOURCE=synthetic
```

| Run | Exit code | Wall time | Summary (`seconds`) | Data source in the summary |
| :--- | :---: | :---: | :---: | :---: |
| `SMOKE_SOURCE=synthetic`, no network | 0 | 25 s | 22.4 | `synthetic` |
| `SMOKE_SOURCE=auto`, no network | 0 | 24 s | not recorded | `synthetic` (`dataset reachable: False; using synthetic`) |

Time per step of the first run, from `smoke_summary.json`: data 2.0 s, training 5.7 s, evaluation 1.5 s, export and INT8 13.1 s, Jetson dry runs 0.1 s, report check 0.0 s. `unshare -rn` needs a Linux kernel with user namespaces; on other systems, disconnect the network instead.

---

## 4. What the smoke run writes

Everything goes to `runs/smoke/` (or `$TIEFER_RUNS_DIR/smoke/`), never to `data/` or `reports/`:

| Path | Contents |
| :--- | :---: |
| `runs/smoke/data/synthetic/` | the synthetic cache: 32 training, 8 validation and 8 test scenes of 384 x 384 pixels |
| `runs/smoke/runs/smoke-<UTC time>/` | `config.toml`, `metadata.json`, `metrics.jsonl`, `best.pt`, `last.pt` and `export/` with four ONNX files |
| `runs/smoke/reports/evaluation/` and `runs/smoke/reports/export/` | one evaluation and one export report, each marked `"smoke": true` |
| `runs/smoke/smoke_summary.json` | the steps, their times, the data source and the result of each check |

The smoke run took 68 MiB on disk (`du -sh`).

---

## 5. What smoke outputs are not

Smoke outputs are never results. Every smoke report is marked `"smoke": true`, and the report loader leaves it out (`src/tiefer_lab/reports.py`; the last smoke step checks this). The mean IoU printed during a smoke run measures a 2-epoch model on synthetic scenes and says nothing about cloud detection. Measured results are in [docs/RESULTS.md](docs/RESULTS.md); the rules for using a number are in [POLICY.md](POLICY.md).

---

## 6. Next steps

| You want to | Go to |
| :--- | :---: |
| Install for real use, on CSC Roihu or on a Jetson | [INSTALL.md](INSTALL.md) |
| Build the real data cache and train | [docs/DATA.md](docs/DATA.md), section 10; [hpc/roihu/README.md](hpc/roihu/README.md) |
| Reproduce a published number | [docs/RESULTS.md](docs/RESULTS.md), section 19 |
| Find the document for any other task | [START-HERE.md](START-HERE.md) |

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `uv: command not found` | uv is not installed | install uv from its documentation, then run `make setup` again |
| `make setup` fails with a network error | the packages cannot be downloaded | `make setup` needs the network once; the smoke run does not |
| uv reports that no matching Python interpreter is found | Python 3.12 or newer is not available | let uv install it (`uv python install 3.12`) or install it with the system package manager |
| `dataset reachable: True; using cloudsen12` and a slow data step | `SMOKE_SOURCE=auto` reached the dataset and reads real patches | run `make smoke SMOKE_SOURCE=synthetic` for the offline proof |
| `smoke run failed: ...` with `the report loader accepted smoke reports` | a report without the smoke mark reached the loader | open an issue with the log; this is a bug |
| `device must be one of ('auto', 'cuda', 'mps', 'cpu')` | an unknown value for `--device` | use one of the listed values, or `cuda:<n>` |
| `make check` fails in `test_markdown_style.py` or `test_text_rules.py` | a Markdown or text file breaks [docs/STYLE.md](docs/STYLE.md) | read the line numbers in the message and fix the file |

---

## Changelog

- 7 October 2026: first version: requirements, the first run with measured durations, the offline proof with `SMOKE_SOURCE=synthetic` and without network, the smoke outputs, and troubleshooting.
