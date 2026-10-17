# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Runners of the reference models whose licence the maintainer cleared.

Each runner reads the bands it names from a cache split and returns one uint8
mask per patch, 1 cloud and 0 not cloud (kind "cloud"), scored on the cloud
problem only. The models run exactly as published: never trained or tuned,
and never used to choose anything of Tiefer's own models.

- `s2cloudless` 1.7.3 (CC BY-SA 4.0) runs from its package installed under
  references/.packages (references/requirements.txt), never copied into this
  repository: `S2PixelCloudDetector` at its class defaults (threshold 0.4,
  average_over 1, dilation_size 1) on the bands B01, B02, B04, B05, B08, B8A,
  B09, B10, B11, B12 as reflectance, the digital numbers divided by 10,000, as
  its README states (PyPI page of 1.7.3, read 17 October 2026);
- `cd_fcnn_rgbi` and `cd_fcnn_rgbiswir` (MIT) run the network of cd_fcnn.py
  with the published weights, downloaded from their recorded URL into
  references/.weights and checked against the recorded size before use.

The class mapping of each output is docs/ASSUMPTIONS.md, `A-6.14` and `A-6.15`.
"""

from __future__ import annotations

import sys
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import cache
from tiefer_lab.reference_models import REFERENCES

HERE = Path(__file__).resolve().parent
PACKAGES = HERE / ".packages"
WEIGHTS = HERE / ".weights"
REFLECTANCE_SCALE = 10000.0
S2CLOUDLESS_BANDS = ("B01", "B02", "B04", "B05", "B08", "B8A", "B09", "B10", "B11", "B12")


class RunnerError(RuntimeError):
    """A runner cannot run: a package, a file or a band is missing."""


@dataclass(frozen=True)
class Runner:
    """The bands a reference model reads, in its order, and how it runs."""

    bands: tuple[str, ...]
    run: Callable[[cache.SplitData], NDArray[np.uint8]]


def _with_packages() -> None:
    """Make references/.packages importable after the venv's own packages."""
    if not PACKAGES.is_dir():
        raise RunnerError(
            f"no {PACKAGES.name} under references/: install the pinned packages with "
            "python3 -m pip install --no-deps --target references/.packages "
            "-r references/requirements.txt (reference_cpu.sbatch does it)"
        )
    if str(PACKAGES) not in sys.path:
        sys.path.append(str(PACKAGES))


def s2cloudless_masks(data: cache.SplitData) -> NDArray[np.uint8]:
    _with_packages()
    from s2cloudless import S2PixelCloudDetector

    detector = S2PixelCloudDetector()
    out = np.zeros(data.labels.shape, dtype=np.uint8)
    for i in range(len(data)):
        reflectance = np.asarray(data.images[i], dtype=np.float32) / REFLECTANCE_SCALE
        # (bands, height, width) -> (1, height, width, bands), the package's layout
        masks = detector.get_cloud_masks(np.moveaxis(reflectance, 0, -1)[None])
        out[i] = np.asarray(masks[0], dtype=np.uint8)
    return out


def weights_file(name: str) -> Path:
    """The published weights of a CD-FCNN model, downloaded once and size-checked."""
    record = REFERENCES[name].files[0]
    path = WEIGHTS / record.name
    if not path.is_file():
        WEIGHTS.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(".part")
        with urllib.request.urlopen(record.url, timeout=120) as response:  # noqa: S310
            part.write_bytes(response.read())
        part.replace(path)
    size = path.stat().st_size
    if size != record.size:
        raise RunnerError(f"{path.name}: {size} bytes, the record says {record.size}")
    return path


def cd_fcnn_runner(name: str) -> Runner:
    import cd_fcnn

    bands = cd_fcnn.BANDS[name]

    def run(data: cache.SplitData) -> NDArray[np.uint8]:
        _with_packages()
        model = cd_fcnn.load(cd_fcnn.CDFCNN(len(bands)), cd_fcnn.keras_weights(weights_file(name)))
        out = np.zeros(data.labels.shape, dtype=np.uint8)
        for i in range(len(data)):
            out[i] = cd_fcnn.cloud_mask(model, np.asarray(data.images[i]))
        return out

    return Runner(bands, run)


def runners() -> dict[str, Runner]:
    """Every runner, by the name of its record in REFERENCES."""
    return {
        "s2cloudless": Runner(S2CLOUDLESS_BANDS, s2cloudless_masks),
        "cd_fcnn_rgbi": cd_fcnn_runner("cd_fcnn_rgbi"),
        "cd_fcnn_rgbiswir": cd_fcnn_runner("cd_fcnn_rgbiswir"),
    }
