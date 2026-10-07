<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Installation

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For anyone who installs Tiefer Lab for real use: on a workstation, on CSC Roihu, on an NVIDIA Jetson or from a source archive. This document owns the platform matrix, the installation methods and the provenance checks; the first run is in [GETTING-STARTED.md](GETTING-STARTED.md).

---

## 1. Platforms

| Platform | Python and packages | Tested | Evidence |
| :--- | :---: | :---: | :---: |
| Linux x86_64 | uv, locked environment from `uv.lock` | yes, in CI: `lint`, `typecheck`, `test (ubuntu-24.04)` with coverage, `smoke` | `.github/workflows/ci.yml` |
| Linux aarch64 | uv, locked environment from `uv.lock` | yes, in CI: `test (ubuntu-24.04-arm)` | `.github/workflows/ci.yml` |
| macOS, Apple MPS | uv, locked environment | not tested | the code selects MPS when it is available (`src/tiefer_lab/utils/devices.py`) |
| Windows | n/a | not tested | `make` and the shell scripts assume a POSIX shell |
| CSC Roihu GPU nodes (aarch64, NVIDIA GH200) | CSC module `python-pytorch/2.10` and a venv with `hpc/roihu/requirements.txt` | yes, on 2 and 3 October 2026 | [docs/RESULTS.md](docs/RESULTS.md), section 4 |
| CSC Roihu CPU nodes (x86_64) | CSC Python module and a venv | yes, for the data cache | [docs/DATA.md](docs/DATA.md), section 10 |
| NVIDIA Jetson Orin | system Python 3 of JetPack, standard library only; `trtexec` from JetPack | dry-run mode only, in CI through `make smoke`; never on a board | [jetson/README.md](jetson/README.md); [docs/RESULTS.md](docs/RESULTS.md), section 15 |

---

## 2. Methods

### 2.1 From git with uv (the reference method)

```bash
git clone https://github.com/tiefer-labs/lab.git
cd lab
make setup
```

`make setup` runs `uv sync --frozen`: it installs the versions and hashes of `uv.lock`, including the development tools, into `.venv/`, and never updates the lock. Python 3.12 or newer and uv 0.8 or newer are required (`pyproject.toml`). The first run is described in [GETTING-STARTED.md](GETTING-STARTED.md).

### 2.2 From a GitHub source archive

GitHub offers a ZIP or tarball of any commit. The repository has no releases and no tags yet, so an archive is identified only by its commit. Install it as in section 2.1, after unpacking. What is lost without git: every report records `"commit": "unknown"` and `"dirty": null` in `provenance.git`, because `src/tiefer_lab/utils/metadata.py` reads both from `git`. A result made from an archive cannot be traced to a commit; use a git clone for any result.

### 2.3 Container

No container image is provided.

### 2.4 CSC Roihu

Follow [hpc/roihu/README.md](hpc/roihu/README.md), sections 1 to 3. In short, without the commands: the PyTorch of the CSC module replaces the PyPI `torch`, `setup.sh` builds one venv per architecture, and `hpc/roihu/requirements.txt` is generated from `uv.lock` without the packages the module provides ([docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), section 2.1).

### 2.5 NVIDIA Jetson

Follow [jetson/README.md](jetson/README.md). The scripts in `jetson/` use the system Python 3 and its standard library only, so nothing is installed on the board; the ONNX files come from an export on another machine.

---

## 3. Provenance checks

| What | Where | How to check |
| :--- | :---: | :---: |
| Locked packages and their hashes | `uv.lock` | `uv lock --check` (the lock matches `pyproject.toml`); `uv sync --frozen` checks every downloaded file against its hash |
| Software bill of materials | CI artifact `sbom-cdx` of every CI run | `uv run python -m tiefer_lab.sbom --output sbom.cdx.json` writes the same CycloneDX 1.5 file locally |
| Pinned GitHub Actions | `.github/workflows/*.yml` | `grep -h "uses:" .github/workflows/*.yml`: every action is pinned by a full commit SHA |
| Pinned CI tools | `.github/ci-tools/requirements.txt`; the gitleaks SHA-256 in `.github/workflows/ci.yml` | CI installs them with `uv pip install --require-hashes`, which fails on any file whose hash differs |
| Commit and local changes behind a report | `provenance.git` of every report JSON | `python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['provenance']['git'])" <report>.json`; `"dirty": true` means the working tree had uncommitted changes |
| Model files | `SHA256SUMS` of a release folder, for example `models/cloud-filter/v0.1.0/` | in the folder that holds the model files: `sha256sum -c SHA256SUMS` |

The model files are not distributed in this repository ([LICENSING.md](LICENSING.md)); the checksums let a holder of the files check them.

---

## 4. Uninstall and clean up

| Remove | Contents | Default location |
| :--- | :---: | :---: |
| `.venv/` | the locked environment | repository root |
| `runs/` | runs, checkpoints, ONNX files and the smoke run (`runs/smoke/`) | `$TIEFER_RUNS_DIR`, default `./runs` |
| `data/` | data caches | `$TIEFER_DATA_DIR`, default `./data` |
| report files you wrote | evaluation, export and Jetson reports | `$TIEFER_REPORTS_DIR`, default `./reports`; tracked files there stay |

```bash
rm -rf .venv runs data
git status --short reports
```

uv keeps downloaded packages in its own cache; `uv cache clean` removes it. On CSC Roihu, the venvs are in `/projappl/<project>` and the caches and runs in `/scratch/<project>` ([hpc/roihu/README.md](hpc/roihu/README.md)).

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `uv lock --check` fails | `pyproject.toml` was changed without `uv lock` | run `uv lock`, check the diff, commit both files together |
| A hash mismatch during `make setup` | a downloaded file differs from the one in `uv.lock` | do not override it; delete the uv cache entry with `uv cache clean <package>` and retry; report it if it persists ([SECURITY.md](SECURITY.md)) |
| Reports show `"commit": "unknown"` | the code runs from a source archive or a folder without git | install from a git clone (section 2.1) |
| Reports show `"dirty": true` | the working tree had uncommitted changes when the run started | commit or stash the changes and run again; a dirty run cannot be reproduced from a commit |
| `torch` is downloaded again on CSC Roihu | the venv was created without the module's system site packages | follow `setup.sh` in [hpc/roihu/README.md](hpc/roihu/README.md); do not install `uv.lock` directly there |
| The Jetson scripts fail on a workstation | they need JetPack | run them with `--dry-run`, or on the board ([jetson/README.md](jetson/README.md)) |

---

## Changelog

- 7 October 2026: first version: platform matrix with the CI jobs that test it, installation from git, from a source archive and on CSC Roihu and a Jetson, provenance checks, clean-up and troubleshooting.
