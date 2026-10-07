<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Dependencies

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Every dependency of Tiefer Lab, why it is needed, its version and its licence. New dependencies need the team's agreement.

---

## 1. Direct dependencies

The range is the one in `pyproject.toml`; the locked version is the one in `uv.lock`. Licences are as declared in each package's metadata for the locked version.

| Package | Why it is needed | Range | Locked | Licence |
| :--- | :---: | :---: | :---: | :---: |
| **Runtime** | | | | |
| `torch` | model, training, evaluation; on CSC Roihu it comes from the CSC module (section 2.1), so the range is wide | `>=2.5` | 2.14.1 | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| `numpy` | arrays and the `.npy` cache files | `>=2.0` | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| `tacoreader` | reads the CloudSEN12+ metadata and patch locations; held below 0.6, because later versions do not read the `tacofoundation:` dataset names ([DATA.md](DATA.md), section 9) | `>=0.5.6,<0.6` | 0.5.6 | MIT |
| `fsspec[http]` | `tacoreader` 0.5 reads `.taco` files over HTTPS through `fsspec`, which needs `aiohttp` for that; the extra installs it | `>=2024.10.0` | 2026.9.0 (`aiohttp` 3.14.3) | BSD-3-Clause (`fsspec`); Apache-2.0 AND MIT (`aiohttp`) |
| `rasterio` | reads the bands and the label of a patch through GDAL virtual files | `>=1.4` | 1.5.2 | BSD-3-Clause |
| `onnx` | the export format, graph checks and FP16 conversion | `>=1.17` | 1.23.1 | Apache-2.0 |
| `onnxruntime` | checks the exported model against PyTorch; INT8 static quantisation | `>=1.20` | 1.30.0 | MIT License |
| **Development** | | | | |
| `pytest` | tests | `>=8.3` | 9.1.1 | MIT |
| `ruff` | lint and format | `>=0.8` | 0.16.9 | MIT |
| `mypy` | strict type check of `src/` | `>=1.13` | 2.3.1 | MIT |
| `regex` | the text rule test (`\p{Extended_Pictographic}`) | `>=2024.11.6` | 2026.9.29 | Apache-2.0 AND CNRI-Python |
| `coverage` | test coverage and its floor in CI | `>=7.6` | 7.16.2 | Apache-2.0 |
| `pandas` | used directly by five tests; not declared, it comes through `tacoreader` (section 5) | not declared | 3.0.6 | BSD License |

---

## 2. Tools and libraries outside the lock

### 2.1 Build, environment and system

| Tool or library | Why it is needed | Version | Licence | Source of the version |
| :--- | :---: | :---: | :---: | :---: |
| `hatchling` | build backend for `pip install -e .`; outside `uv.lock` and the software bill of materials | 1.32.4 | MIT | `pyproject.toml` (`[build-system]`) |
| `uv` | environment and lock | `>=0.8` (`required-version`) | MIT OR Apache-2.0 | `pyproject.toml` (`[tool.uv]`); licence from the PyPI metadata of 0.11.32 |
| CSC module `python-pytorch/2.10` | PyTorch, CUDA and cuDNN on CSC Roihu GPU nodes | torch 2.10.0+cu130, Python 3.12.12 | not read | [hpc/roihu/README.md](../hpc/roihu/README.md), section 6 (observed on Roihu, 1 October 2026) |
| GDAL and PROJ | bundled in the `rasterio` wheel; `rasterio` reads every patch through GDAL | GDAL 3.12.2, PROJ 9.8.1 in `rasterio` 1.5.2 | MIT style licences [1], [2] | `rasterio.__gdal_version__` and `rasterio.__proj_version__` of the locked wheel |
| `tomllib` | configuration files | standard library of Python 3.12 | Python Software Foundation License | Python 3.12 |
| `trtexec`, `tegrastats`, `nvpmodel`, `jetson_clocks` | Jetson benchmark, part of JetPack on the board; not installed by this repository | not measured | NVIDIA licence terms of JetPack | n/a |

`hpc/roihu/requirements.txt` holds the locked runtime packages without the ones the CSC module provides. `make requirements` leaves out `TORCH_ONLY` of the `Makefile`: `torch`, `triton`, `cuda-bindings`, `cuda-pathfinder`, `cuda-toolkit`, `filelock`, `jinja2`, `markupsafe`, `mpmath`, `networkx`, `setuptools`, `sympy` and every `nvidia-*` package of the lock (`nvidia-cublas`, `nvidia-cuda-cupti`, `nvidia-cuda-nvrtc`, `nvidia-cuda-runtime`, `nvidia-cudnn-cu13`, `nvidia-cufft`, `nvidia-cufile`, `nvidia-curand`, `nvidia-cusolver`, `nvidia-cusparse`, `nvidia-cusparselt-cu13`, `nvidia-nccl-cu13`, `nvidia-nvjitlink`, `nvidia-nvshmem-cu13`, `nvidia-nvtx`).

### 2.2 CI-only tools

Tools that only check the repository in CI. They are not in `uv.lock` and never run inside the project's environment.

| Tool | Why it is needed | Version | Licence | How it is pinned |
| :--- | :---: | :---: | :---: | :---: |
| `pip-audit` | audits the locked environment for known vulnerabilities (section 4) | 2.10.1 | Apache Software License | hashes in `.github/ci-tools/requirements.txt` |
| `shellcheck-py` | installs ShellCheck 0.11.0 for `make shellcheck` | 0.11.0.1 | MIT (`shellcheck-py`); GPL-3.0 (ShellCheck itself, run in CI, not distributed) | hashes in `.github/ci-tools/requirements.txt` |
| gitleaks | scans the full history for secrets | 8.30.1 | not read | SHA-256 of the release archive in `.github/workflows/ci.yml` |
| CodeQL | code scanning of Python and GitHub Actions | `github/codeql-action` v4.38.2 | not read | commit SHA in `.github/workflows/codeql.yml` |

`.github/ci-tools/requirements.txt` is generated from `.github/ci-tools/requirements.in` (the command is in its header). Its indirect packages, with the licence of their PyPI metadata (read on 7 October 2026):

| Package | Version | Licence |
| :--- | :---: | :---: |
| `boolean-py` | 5.0 | BSD-2-Clause |
| `cachecontrol` | 0.14.4 | Apache-2.0 |
| `certifi` | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0) (PyPI classifier) |
| `charset-normalizer` | 3.5.2 | MIT |
| `cyclonedx-python-lib` | 11.12.0 | Apache Software License (PyPI classifier) |
| `defusedxml` | 0.7.1 | Python Software Foundation License (PyPI classifier) |
| `filelock` | 4.0.9 | MIT |
| `idna` | 3.20 | BSD-3-Clause |
| `license-expression` | 30.4.4 | Apache-2.0 |
| `markdown-it-py` | 4.2.0 | MIT License (PyPI classifier) |
| `mdurl` | 0.1.2 | MIT License (PyPI classifier) |
| `msgpack` | 1.2.3 | Apache-2.0 |
| `packageurl-python` | 0.17.6 | MIT License (PyPI classifier) |
| `packaging` | 26.3 | Apache-2.0 OR BSD-2-Clause |
| `pip` | 26.2.1 | MIT |
| `pip-api` | 0.0.35 | Apache Software License (PyPI classifier) |
| `pip-requirements-parser` | 32.0.1 | MIT |
| `platformdirs` | 4.12.2 | MIT |
| `py-serializable` | 2.1.0 | Apache Software License (PyPI classifier) |
| `pygments` | 2.21.0 | BSD-2-Clause |
| `pyparsing` | 3.3.3 | MIT |
| `requests` | 2.34.2 | Apache Software License (PyPI classifier) |
| `rich` | 15.0.0 | MIT License (PyPI classifier) |
| `sortedcontainers` | 2.4.0 | Apache Software License (PyPI classifier) |
| `tomli` | 2.4.1 | MIT |
| `tomli-w` | 1.2.0 | MIT License (PyPI classifier) |
| `typing-extensions` | 4.16.0 | PSF-2.0 |
| `urllib3` | 2.8.0 | MIT |

### 2.3 GitHub Actions

Every action is pinned by its full commit SHA, with the tag in a comment.

| Action | Tag | Commit | Used in |
| :--- | :---: | :---: | :---: |
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | every workflow |
| `actions/upload-artifact` | v7.0.1 | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | `ci.yml` (software bill of materials) |
| `astral-sh/setup-uv` | v10.2.0 | `c18668ad3cf93ea998bef934396af7bb5c839dc7` | `ci.yml`, `audit.yml` |
| `github/codeql-action/init` and `analyze` | v4.38.2 | `2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2` | `codeql.yml` |

`.github/dependabot.yml` proposes weekly updates of `uv.lock` and of the actions, and ignores `tacoreader` 0.6 and later (section 1).

---

## 3. All locked packages

Every package in `uv.lock`, including indirect dependencies, with the licence its metadata declares. `src/tiefer_lab/sbom.py` parses this section by its heading and its three columns.

SPDX: a licence string that is a valid SPDX expression (for example `MIT` or `Apache-2.0 AND MIT`) goes into the software bill of materials as an SPDX expression; any other string (for example the PyPI classifier name `BSD License`) goes in as a licence name. The strings are copied from the package metadata and are not rewritten here.

This table is also the licence source of the software bill of materials: `python -m tiefer_lab.sbom` writes CycloneDX 1.5 JSON with every locked package, its version, the SHA-256 of its files and its licence from this table, and stops when a locked package has no row here. CI runs it on every push and pull request and attaches the file to the run as the artifact `sbom-cdx` (kept 90 days).

| Package | Locked version | Licence (package metadata) |
| :--- | :---: | :---: |
| `affine` | 3.0.1 | BSD-3-Clause |
| `aiohappyeyeballs` | 2.7.1 | Python Software Foundation License |
| `aiohttp` | 3.14.3 | Apache-2.0 AND MIT |
| `aiosignal` | 1.4.0 | Apache Software License |
| `ast-serialize` | 0.11.2 | MIT |
| `attrs` | 26.1.0 | MIT |
| `certifi` | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0) |
| `charset-normalizer` | 3.5.2 | MIT |
| `click` | 8.5.0 | BSD-3-Clause |
| `colorama` | 0.4.6 | BSD License (PyPI classifier) |
| `coverage` | 7.16.2 | Apache-2.0 |
| `cuda-bindings` | 13.4.3 | Apache-2.0 |
| `cuda-pathfinder` | 1.8.2 | Apache-2.0 |
| `cuda-toolkit` | 13.0.3.0 | not declared in package metadata; NVIDIA CUDA package |
| `filelock` | 4.0.8 | MIT |
| `flatbuffers` | 25.12.19 | Apache Software License |
| `frozenlist` | 1.8.0 | Apache-2.0 |
| `fsspec` | 2026.9.0 | BSD-3-Clause |
| `idna` | 3.20 | BSD-3-Clause |
| `iniconfig` | 2.3.0 | MIT |
| `jinja2` | 3.1.6 | BSD License |
| `librt` | 0.16.0 | MIT |
| `markupsafe` | 3.0.3 | BSD-3-Clause |
| `ml-dtypes` | 0.6.0 | Apache-2.0 |
| `mpmath` | 1.3.0 | BSD License |
| `multidict` | 6.9.1 | Apache License 2.0 |
| `mypy` | 2.3.1 | MIT |
| `mypy-extensions` | 1.1.0 | MIT |
| `networkx` | 3.7 | BSD-3-Clause |
| `numpy` | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| `nvidia-cublas` | 13.1.1.3 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cuda-cupti` | 13.0.85 | Other/Proprietary License |
| `nvidia-cuda-nvrtc` | 13.0.88 | Other/Proprietary License |
| `nvidia-cuda-runtime` | 13.0.96 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cudnn-cu13` | 9.24.0.43 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-cufft` | 12.0.0.61 | Other/Proprietary License |
| `nvidia-cufile` | 1.15.1.6 | Other/Proprietary License |
| `nvidia-curand` | 10.4.0.35 | Other/Proprietary License |
| `nvidia-cusolver` | 12.0.4.66 | Other/Proprietary License |
| `nvidia-cusparse` | 12.6.3.3 | Other/Proprietary License |
| `nvidia-cusparselt-cu13` | 0.8.1 | NVIDIA Proprietary Software |
| `nvidia-nccl-cu13` | 2.30.7 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-nvjitlink` | 13.4.92 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-nvshmem-cu13` | 3.4.5 | LicenseRef-NVIDIA-Proprietary |
| `nvidia-nvtx` | 13.0.85 | Other/Proprietary License |
| `onnx` | 1.23.1 | Apache-2.0 |
| `onnxruntime` | 1.30.0 | MIT License |
| `packaging` | 26.3 | Apache-2.0 OR BSD-2-Clause |
| `pandas` | 3.0.6 | BSD License |
| `pathspec` | 1.1.1 | Mozilla Public License 2.0 (MPL 2.0) |
| `pluggy` | 1.6.0 | MIT License |
| `propcache` | 0.5.4 | Apache-2.0 |
| `protobuf` | 7.36.2 | 3-Clause BSD License |
| `pyarrow` | 25.0.1 | Apache-2.0 |
| `pygments` | 2.21.0 | BSD-2-Clause |
| `pyparsing` | 3.3.3 | MIT |
| `pytest` | 9.1.1 | MIT |
| `python-dateutil` | 2.9.0.post0 | BSD License; Apache Software License |
| `rasterio` | 1.5.2 | BSD-3-Clause |
| `regex` | 2026.9.29 | Apache-2.0 AND CNRI-Python |
| `requests` | 2.34.2 | Apache Software License |
| `ruff` | 0.16.9 | MIT |
| `setuptools` | 84.0.0 | MIT |
| `six` | 1.17.0 | MIT License |
| `sympy` | 1.14.0 | BSD License |
| `tacoreader` | 0.5.6 | MIT (LICENSE file in the package) |
| `torch` | 2.14.1 | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| `tqdm` | 4.70.1 | MPL-2.0 AND MIT |
| `triton` | 3.8.0 | MIT |
| `typing-extensions` | 4.16.0 | PSF-2.0 |
| `tzdata` | 2026.4 | Apache-2.0 (PyPI metadata) |
| `urllib3` | 2.8.0 | MIT |
| `yarl` | 1.25.1 | Apache-2.0 |

---

## 4. Vulnerability audit

`.github/workflows/audit.yml` runs `pip-audit` on every package of `uv.lock` (all groups, with hashes) on every push and pull request, every Monday and on demand (`workflow_dispatch`), so a new advisory against an unchanged lock is also found. Any finding fails the job. The fix is to update the package (`uv lock --upgrade-package <name>`, then `make requirements`) and commit the new lock.

When a finding cannot be fixed yet or does not apply, it is accepted in `.github/audit-exceptions.toml`, never by turning the audit off:

```toml
[[exception]]
id = "PYSEC-2026-1"
package = "example"
reason = "the vulnerable function is never called; no fixed version exists yet"
expires = 2026-12-31
```

`id` is the advisory ID as `pip-audit` prints it. `reason` says why the finding is accepted. `expires` is at most 90 days ahead; after that date the audit fails again until the entry is renewed with a new reason or removed. `.github/scripts/audit_exceptions.py` checks every entry before the audit runs and stops on a missing field, an expired date or one too far ahead, and the job log lists every accepted finding with its reason and expiry.

---

## 5. Decisions

- `fsspec[http]` is the only runtime dependency beyond the agreed list. Without it, `tacoreader` 0.5 cannot read the dataset over HTTPS.
- `pandas` is used directly by five tests (`tests/test_bands_and_labels.py`, `tests/test_cache.py`, `tests/test_extra_patches.py`, `tests/test_references.py`, `tests/test_survey.py`) and is not declared: it is installed as a dependency of `tacoreader`. Declaring it in the development group would make the tests independent of that; re-locking with the local `uv` also rewrites the environment markers of unrelated packages, so it is left for a lock update.
- `onnxscript` is not used. ONNX export uses the TorchScript exporter (`dynamo=False`), which works in PyTorch 2.14 with a deprecation warning. If a later PyTorch removes it, `onnxscript` becomes necessary and needs the team's agreement ([ASSUMPTIONS.md](ASSUMPTIONS.md), `A-5.4`).
- On Linux, `torch` from PyPI installs the NVIDIA CUDA runtime packages (`nvidia-*`, `cuda-toolkit`, `cuda-bindings`, `cuda-pathfinder`, `triton`) under their own licence terms. They are installed by `uv sync` on the user's machine; this repository does not distribute them. On Roihu they come with the CSC module and are left out of `hpc/roihu/requirements.txt` (section 2.1).

---

## 6. Sources

1. GDAL/OGR Licensing, `LICENSE.TXT` of the GDAL repository, https://raw.githubusercontent.com/OSGeo/gdal/master/LICENSE.TXT, accessed 7 October 2026.
2. PROJ `COPYING`, https://raw.githubusercontent.com/OSGeo/PROJ/master/COPYING, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: section 1 gives the range in `pyproject.toml` and the locked version of every direct dependency, and lists `pandas`, which five tests import and which comes through `tacoreader`.
- 7 October 2026: section 2 lists what is outside the lock: `hatchling`, `uv`, the CSC module `python-pytorch/2.10`, GDAL and PROJ in the `rasterio` wheel, the CI-only tools with their indirect packages and licences, gitleaks, CodeQL and the GitHub Actions by tag and commit; the former section 2A is section 2.2.
- 7 October 2026: section 2.1 lists every package that `make requirements` leaves out for CSC Roihu.
- 7 October 2026: section 3 says how licence strings become SPDX expressions or licence names in the software bill of materials.
- 7 October 2026: the audit also runs on demand (`workflow_dispatch`); the dependabot rule for `tacoreader` is described; decisions moved to section 5.
- 2 October 2026: vulnerability audit and its accepted exceptions (section 4).
- 2 October 2026: CI-only tools (section 2A); `coverage` in the development group.
- 2 October 2026: section 3 is the licence source of the software bill of materials.
- 1 October 2026: first version for milestone L1.
