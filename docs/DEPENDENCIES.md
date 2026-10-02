<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Dependencies

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Every dependency of Tiefer Lab, why it is needed, and its licence. New dependencies need the team's agreement.

---

## 1. Direct dependencies

Versions are ranges in `pyproject.toml` and exact in `uv.lock`. Licences are as declared in each package's metadata for the locked version.

| Package | Why it is needed | Licence |
| :--- | :---: | :---: |
| **Runtime** | | |
| `torch` | model, training, evaluation; on Roihu it comes from the CSC module, so the range is wide (`>=2.5`) | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| `numpy` | arrays and the `.npy` cache files | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| `tacoreader` | reads the CloudSEN12+ metadata and patch locations; pinned below 0.6 because later versions do not read the `tacofoundation:` dataset names (docs/DATA.md) | MIT |
| `fsspec[http]` | `tacoreader` 0.5 reads `.taco` files over HTTPS through `fsspec`, which needs `aiohttp` for that; the extra installs it | BSD-3-Clause (`fsspec`); Apache-2.0 AND MIT (`aiohttp`) |
| `rasterio` | reads the four bands and the label of a patch through GDAL virtual files | BSD-3-Clause |
| `onnx` | the export format, graph checks and FP16 conversion | Apache-2.0 |
| `onnxruntime` | checks the exported model against PyTorch; INT8 static quantisation | MIT |
| **Development** | | |
| `pytest` | tests | MIT |
| `ruff` | lint and format | MIT |
| `mypy` | strict type check of `src/` | MIT |
| `regex` | the text rule test (`\p{Extended_Pictographic}`) | Apache-2.0 AND CNRI-Python |
| **Build** | | |
| `hatchling` | builds the package for `pip install -e .` | MIT |
| **Standard library and system** | | |
| `tomllib` | configuration files | Python Software Foundation License |
| `trtexec`, `tegrastats`, `nvpmodel`, `jetson_clocks` | Jetson benchmark, part of JetPack on the board; not installed by this repository | NVIDIA licence terms of JetPack |

---

## 2. Decisions

- `fsspec[http]` is the only runtime dependency beyond the agreed list. Without it, `tacoreader` 0.5 cannot read the dataset over HTTPS.
- `onnxscript` is not used. ONNX export uses the TorchScript exporter (`dynamo=False`), which works in PyTorch 2.14 with a deprecation warning. If a later PyTorch removes it, `onnxscript` becomes necessary and needs the team's agreement (docs/ASSUMPTIONS.md, section 5).
- On Linux, `torch` from PyPI installs the NVIDIA CUDA runtime packages (`nvidia-*`, `cuda-toolkit`, `triton`) under NVIDIA's licence terms. They are installed by `uv sync` on the user's machine; this repository does not distribute them. On Roihu they come with the CSC module and are left out of `hpc/roihu/requirements.txt`.

---

## 2A. CI-only tools

Tools that only check the repository in CI. They are not in `uv.lock` and never run inside the project's environment; they are pinned with hashes in `.github/ci-tools/requirements.txt`, generated from `.github/ci-tools/requirements.in` (the command is in its header). Their indirect dependencies are listed in that file.

| Tool | Why it is needed | Licence |
| :--- | :---: | :---: |
| `shellcheck-py` 0.11.0.1 | installs ShellCheck 0.11.0 for `make shellcheck` | MIT (`shellcheck-py`); GPL-3.0 (ShellCheck itself, run in CI, not distributed) |
| `pip-audit` 2.10.1 | audits the locked environment for known vulnerabilities | Apache Software License |

---

## 3. All locked packages

Every package in `uv.lock`, including indirect dependencies, with the licence its metadata declares.

This table is also the licence source of the software bill of materials: `python -m tiefer_lab.sbom` writes CycloneDX 1.5 JSON with every locked package, its version, the SHA-256 of its files and its licence from this table, and stops when a locked package has no row here. CI runs it on every push and shows the result in the job summary.

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

`.github/workflows/audit.yml` runs `pip-audit` on every package of `uv.lock` (all groups, with hashes) on every push and pull request and every Monday, so a new advisory against an unchanged lock is also found. Any finding fails the job. The fix is to update the package (`uv lock --upgrade-package <name>`, then `make requirements`) and commit the new lock.

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

## Changelog

- 2 October 2026: vulnerability audit and its accepted exceptions (section 4).
- 2 October 2026: CI-only tools (section 2A).
- 2 October 2026: section 3 is the licence source of the software bill of materials.
- 1 October 2026: first version for milestone L1.
