<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Notices and attributions

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The attributions of third-party work used by this repository: data, the Copernicus notice, the typeface and the dependencies.

---

## Licences and marks

The licence of every part of this repository, and what is not licensed (trained models, the images in `docs/assets/`, the Tiefer name and logo), is in [LICENSING.md](LICENSING.md). The use of the name and logo is in [TRADEMARK.md](TRADEMARK.md). This file holds the attributions only.

No pretrained weights are used. Every model is trained from random initialisation on the data in [docs/DATA.md](docs/DATA.md), so no third-party model needs attribution.

---

## Third-party data

CloudSEN12+ is a third-party dataset published by the TACO Foundation on Hugging Face as [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) under CC0 1.0. It is not included in this repository; the scripts read the needed patches at run time and cache them outside git. Its dataset card asks for no attribution, and the work behind it is cited as the card lists it:

- Scientific Data, 2022: [10.1038/s41597-022-01878-2](https://doi.org/10.1038/s41597-022-01878-2)
- Data in Brief, 2024: [10.1016/j.dib.2024.110852](https://doi.org/10.1016/j.dib.2024.110852)
- IGARSS 2023: [10.1109/IGARSS52108.2023.10282381](https://doi.org/10.1109/IGARSS52108.2023.10282381)

The extra variant of the dataset ships cloud masks made by third-party algorithms (QA60, Sen2Cor, s2cloudless, CloudScore+, UNetMobV2 and SEnSeI v2). The card publishes them as part of the dataset, under the dataset's CC0 1.0 terms, and names the source of each; this repository does not include them.

The independent test datasets recorded as used ([docs/DATASETS.md](docs/DATASETS.md), section 1.1) are third-party datasets under CC BY 4.0. They are not included in this repository; the scripts download them at run time and cache them outside git, cut into tiles, resampled to 10 m and with their labels mapped to the four classes of this repository ([docs/INDEPENDENT.md](docs/INDEPENDENT.md), section 4):

- Sentinel-2 Cloud Mask Catalogue, by A. Francis, J. Mrziglod, P. Sidiropoulos and J.-P. Muller, Zenodo, 2020, [10.5281/zenodo.4172871](https://doi.org/10.5281/zenodo.4172871), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the authors as the CloudSEN12 paper cites the record (reference 32).
- KappaSet: Sentinel-2 KappaZeta Cloud and Cloud Shadow Masks, by the creators named on the record, Zenodo, 2022, [10.5281/zenodo.7100327](https://doi.org/10.5281/zenodo.7100327), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Both contain Copernicus Sentinel-2 data, so a result on them carries the Copernicus notice below.

Third-party datasets and models that the maintainer's licence decisions refuse ([docs/DATASETS.md](docs/DATASETS.md), section 1.1) are not used, so this file carries no attribution for them. Attributions are added here only for material actually used.

The patches are Copernicus Sentinel-2 data. The legal notice on the use of Copernicus Sentinel data asks that adapted or modified data communicated to the public carries the notice "Contains modified Copernicus Sentinel data [Year]" ([legal notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice), accessed 7 October 2026). For the values derived from CloudSEN12+ in this repository:

Contains modified Copernicus Sentinel data 2018–2020.

The years are those of the 2022 release, as its paper states for the Sentinel-2 images (2018 to 2020); the CloudSEN12+ card, version 1.1.2, does not state the years of the patches it added.

---

## Typeface

The header image uses the typeface Mozilla Headline, Copyright 2025 The Mozilla Headline Project Authors, licensed under the SIL Open Font License, Version 1.1 ([Google Fonts](https://fonts.google.com/specimen/Mozilla+Headline/license), accessed 7 October 2026). The font files are not part of this repository.

---

## Dependencies

The dependencies are not distributed with this repository; `uv sync` installs them from PyPI on the user's machine. Their versions and licences, as declared in their package metadata, are listed in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), which is the source of truth: the direct dependencies, the tools outside the lock, and every locked package. The licences of the direct runtime dependencies (`torch`, `numpy`, `tacoreader`, `fsspec` with `aiohttp`, `rasterio`, `onnx`, `onnxruntime`) combine Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, MIT, 0BSD, Zlib and CC0-1.0, as listed there.

On Linux, `torch` from PyPI also installs the NVIDIA CUDA runtime packages (`nvidia-*`, `cuda-toolkit`, `cuda-bindings`, `cuda-pathfinder`) and `triton`, under their own licence terms, some of them proprietary NVIDIA terms. They are installed by `uv sync` on the user's machine and are not distributed by this repository.

---

## Changelog

- 15 October 2026: attribution of the Sentinel-2 Cloud Mask Catalogue and KappaSet, the independent test datasets recorded as used; drafted with an AI-assisted system.
- 15 October 2026: attributions only for material actually used; the sources refused by the licence decisions of 15 October 2026 carry none; drafted with an AI-assisted system.
- 7 October 2026: the licence of each part, what is not licensed and the trademarks move to LICENSING.md and TRADEMARK.md; this file keeps the attributions and links both.
- 7 October 2026: this changelog added. The images of `docs/assets/` are excluded from the MPL 2.0 licence, all rights reserved by Tiefer; the header typeface Mozilla Headline is named with its licence, SIL Open Font License 1.1.
- 7 October 2026: the Copernicus Sentinel data notice and the years of the imagery; the CloudSEN12+ citations; the reference masks of the extra variant are third-party products under the dataset's terms.
- 7 October 2026: the dependency table is replaced by a summary and a link to docs/DEPENDENCIES.md; the packages that `torch` installs on Linux include `cuda-bindings`, `cuda-pathfinder` and `triton`; no licence is granted for model weights.
- 1 October 2026: first version.
