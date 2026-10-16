# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The published reference models: their facts, licences and licence decisions.

The single record of every reference model. `references/run_reference.py`
runs them and `python -m tiefer_lab.data.check_sources` checks that their
files can be obtained; this module imports no torch, so the CPU job of the
check reads it too. No weights are stored here or anywhere in `src/`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from tiefer_lab.data import cache
from tiefer_lab.data.source import (
    NO_DECISION,
    LicenceDecision,
    RemoteFile,
    decided_15_october_2026,
)

Runner = Callable[[cache.SplitData], NDArray[np.uint8]]


@dataclass(frozen=True)
class Reference:
    """A published reference model and what is known about using it."""

    name: str
    source: str
    licence: str | None  # licence of the code, as read on the primary source; None: TODO(verify)
    kind: str  # "four_class", "cloud" or "probability", the output as stored
    runner: Runner | None = None
    note: str = ""
    # The maintainer's licence decision for this use (data/source.py, LicenceDecision).
    decision: LicenceDecision = NO_DECISION
    # Licence of the weights, read separately; None when no source states it, which
    # stops the model (python -m tiefer_lab.data.check_sources: "licence not stated").
    weights_licence: str | None = None
    # How the code and weights are obtained, as the primary source states it.
    obtain: str = ""
    # The files to download, for python -m tiefer_lab.data.check_sources.
    files: tuple[RemoteFile, ...] = ()
    # Why the model is not checked, when it is not (for example its masks ship
    # with CloudSEN12+).
    not_checked: str = ""


READ = "16 October 2026"
CD_FCNN_REPO = "https://raw.githubusercontent.com/IPL-UV/DL-L8S2-UV/main/dl_l8s2_uv/weights"

REFERENCES: dict[str, Reference] = {
    "unetmobv2": Reference(
        "unetmobv2",
        "UNetMobV2 of the CloudSEN12 paper; primary page of the weights TODO(verify)",
        None,
        "four_class",
        note="CloudSEN12+ ships its mask (cloudmask_unetmobv2_v1); this runner is for the "
        "independent datasets",
        not_checked="its masks are already in the CloudSEN12+ extra table "
        "(cloudmask_unetmobv2_v1 and cloudmask_unetmobv2_v2)",
    ),
    "s2cloudless": Reference(
        "s2cloudless",
        "https://github.com/sentinel-hub/sentinel2-cloud-detector, PyPI s2cloudless 1.7.3",
        "CC-BY-SA-4.0",
        "probability",
        note="CloudSEN12+ ships its probability; this runner is for the independent datasets. "
        "CC BY-SA 4.0: it runs from its installed package under references/ and is never "
        "copied into this repository. It reads 10 bands (B01, B02, B04, B05, B08, B8A, B09, "
        "B10, B11, B12) as reflectance, so only the 13-band caches can feed it",
        weights_licence="CC-BY-SA-4.0: the README says 'This work is licensed under a Creative "
        "Commons Attribution-ShareAlike 4.0 International License'; the model file "
        "s2cloudless/models/pixel_s2_cloud_detector_lightGBM_v0.1.txt ships in the package",
        obtain="pip install s2cloudless==1.7.3 from PyPI; no login, token or licence acceptance",
        files=(
            RemoteFile(
                "s2cloudless-1.7.3-py3-none-any.whl",
                "https://files.pythonhosted.org/packages/a5/ed/"
                "1971cd2cd4d1e08940a209308bc1a142618cb7dc84586af7fad69c0db4d9/"
                "s2cloudless-1.7.3-py3-none-any.whl",
                4768896,
                "sha256:bd8ea8f21df724e77ed48592bfce1c49f4093aebe3561f88c9a276cd14c934bf",
                READ,
                "https://pypi.org/pypi/s2cloudless/1.7.3/json",
            ),
        ),
    ),
    "dtacs4bands": Reference(
        "dtacs4bands",
        "https://huggingface.co/isp-uv-es/cloudsen12_models",
        "CC-BY-NC-4.0",
        "four_class",
        note="non-commercial licence",
        decision=decided_15_october_2026(
            "declined, pending legal review", "CC BY-NC 4.0", "non-commercial licence"
        ),
    ),
    "kappamask_l1c": Reference(
        "kappamask_l1c",
        "https://github.com/kappazeta/km_predict",
        "Apache-2.0",
        "four_class",
        note="runs on whole Level-1C SAFE products, which it splits into sub-tiles itself "
        "(cm_vsm), so it cannot run on 509 x 509 patches",
        weights_licence=None,
        obtain="the weights are not in the repository; the public Docker image "
        "kappazeta/kappamask:v2.4 (1,887,346,809 bytes compressed) carries them, and no "
        "licence is stated for them",
    ),
    "kappamask_l2a": Reference(
        "kappamask_l2a",
        "https://github.com/kappazeta/km_predict",
        "Apache-2.0",
        "four_class",
        note="needs whole Level-2A SAFE products; cannot run on 509 x 509 patches",
        weights_licence=None,
        obtain="as kappamask_l1c",
    ),
    "cd_fcnn_rgbi": Reference(
        "cd_fcnn_rgbi",
        "https://github.com/IPL-UV/DL-L8S2-UV",
        "MIT",
        "cloud",
        note="the weights were trained on L8 Biome (file name landsatbiomeRGBI6), so a "
        "result of this model on L8 Biome is not independent",
        weights_licence="MIT, the LICENSE file of the repository that holds the weights; no "
        "separate statement for the weights",
        obtain="git clone or the raw files of the repository; no login",
        files=(
            RemoteFile(
                "landsatbiomeRGBI6.hdf5",
                f"{CD_FCNN_REPO}/landsatbiomeRGBI6.hdf5",
                1418400,
                None,
                READ,
                "git tree of https://github.com/IPL-UV/DL-L8S2-UV, branch main",
            ),
        ),
    ),
    "cd_fcnn_rgbiswir": Reference(
        "cd_fcnn_rgbiswir",
        "https://github.com/IPL-UV/DL-L8S2-UV",
        "MIT",
        "cloud",
        note="as cd_fcnn_rgbi; weights landsatbiomeRGBISWIR7, trained on L8 Biome",
        weights_licence="MIT, the LICENSE file of the repository that holds the weights; no "
        "separate statement for the weights",
        obtain="as cd_fcnn_rgbi",
        files=(
            RemoteFile(
                "landsatbiomeRGBISWIR7.hdf5",
                f"{CD_FCNN_REPO}/landsatbiomeRGBISWIR7.hdf5",
                1418160,
                None,
                READ,
                "git tree of https://github.com/IPL-UV/DL-L8S2-UV, branch main",
            ),
        ),
    ),
    "fmask4": Reference(
        "fmask4",
        "https://github.com/GERSL/Fmask (Fmask 5; the README links the complete package)",
        "MIT",
        "four_class",
        note="runs on a whole Landsat or Sentinel-2 product directory with its metadata "
        "(--imagepath of a .SAFE folder), so it cannot run on 509 x 509 patches; the "
        "MATLAB Fmask 4 of the CloudSEN12 paper is not checked",
        weights_licence=None,
        obtain="the repository holds the code only; the README links the complete package "
        "(about 3 GB, auxiliary data and model files) on a university SharePoint, which "
        "redirected to a login on 16 October 2026; the link holds a personal account name "
        "and is not copied here",
    ),
}
