<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Licence notes

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

What is licensed in this repository, under which terms, and what is not.

---

## Repository

Everything in this repository (code, scripts, configurations, documentation and reports) is licensed under the Mozilla Public License 2.0. The full text is in [LICENSE](LICENSE). Every source file starts with the MPL 2.0 notice.

---

## Trained models

Trained models are not part of this repository and are not covered by any licence here. Checkpoints and ONNX files are excluded from git, are not attached to GitHub Releases and stay with Tiefer. Release folders under `models/cloud-filter/` hold only a model card, a configuration and SHA-256 checksums, so that Tiefer can show which model produced which result.

---

## Pretrained weights

No pretrained weights are used. Every model is trained from random initialisation on the data in [docs/DATA.md](docs/DATA.md), so no third-party model licence applies to a trained model.

---

## Trademarks

The Tiefer name and logo (`docs/assets/`) are trademarks of Tiefer and are not licensed. MPL 2.0 section 2.3 grants no rights to trademarks, service marks or logos.

---

## Data

CloudSEN12+ is a third-party dataset published on Hugging Face as [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) under CC0 1.0. It is not included in this repository; the scripts read the needed patches at run time. Citations are in [docs/DATA.md](docs/DATA.md).

---

## Dependencies

Direct dependencies and their licences, as declared in their package metadata for the versions in `uv.lock`. The complete list of locked packages, with the reason for each direct dependency, is in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).

| Package | Use | Licence |
| :--- | :---: | :---: |
| **Runtime** | | |
| `torch` | model, training | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| `numpy` | arrays, cache files | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| `tacoreader` | CloudSEN12+ access | MIT |
| `fsspec` with `aiohttp` | HTTPS reads for `tacoreader` | BSD-3-Clause; Apache-2.0 AND MIT |
| `rasterio` | reading patch rasters | BSD-3-Clause |
| `onnx` | model export format | Apache-2.0 |
| `onnxruntime` | export check and INT8 quantisation | MIT |
| **Development** | | |
| `pytest` | tests | MIT |
| `ruff` | lint and format | MIT |
| `mypy` | type check | MIT |
| `regex` | text rule test | Apache-2.0 AND CNRI-Python |
| **Build** | | |
| `hatchling` | builds the package | MIT |

On Linux, `torch` from PyPI also installs NVIDIA CUDA runtime packages (`nvidia-*`, `cuda-toolkit`) under NVIDIA's proprietary licence terms. They are installed by `uv sync` on the user's machine and are not distributed by this repository.
