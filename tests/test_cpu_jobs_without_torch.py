# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The CPU jobs on CSC Roihu run without torch.

hpc/roihu/requirements.txt leaves torch out, so the x86 virtual environment of
the survey and the data cache build has none. Each check runs in a fresh
interpreter where `import torch` fails, as it does there.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

# Every module a CPU job imports, directly or through another module.
CPU_MODULES = (
    "tiefer_lab.data.survey",
    "tiefer_lab.data.build_cache",
    "tiefer_lab.data.cache",
    "tiefer_lab.data.source",
    "tiefer_lab.data.http",
    "tiefer_lab.data.transforms",
    "tiefer_lab.data.richness",
    "tiefer_lab.data.padding",
    "tiefer_lab.utils.metadata",
    "tiefer_lab.utils.paths",
)

BLOCK_TORCH = "import sys\nsys.modules['torch'] = None\n"


def _without_torch(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", BLOCK_TORCH + code], capture_output=True, text=True, check=False
    )


def test_blocking_works() -> None:
    result = _without_torch("import torch")
    assert result.returncode != 0 and "ModuleNotFoundError" in result.stderr


@pytest.mark.parametrize("module", CPU_MODULES)
def test_cpu_module_imports_without_torch(module: str) -> None:
    result = _without_torch(f"import {module}\nassert sys.modules['torch'] is None")
    assert result.returncode == 0, result.stderr


def test_survey_and_build_cache_record_provenance_without_torch() -> None:
    code = (
        "import json\n"
        "import tiefer_lab.data.build_cache\n"
        "import tiefer_lab.data.survey\n"
        "from tiefer_lab.utils import metadata\n"
        "print(json.dumps(metadata.provenance()))\n"
    )
    result = _without_torch(code)
    assert result.returncode == 0, result.stderr
    platform = json.loads(result.stdout)["platform"]
    assert platform["libraries"]["torch"] is None
    assert platform["device"] == "cpu"
    assert platform["cuda_runtime"] is None and platform["cudnn"] is None


def test_provenance_with_torch_keeps_its_fields() -> None:
    import torch

    from tiefer_lab.utils import metadata

    platform = metadata.platform_info(torch.device("cpu"))
    assert platform["libraries"]["torch"] == torch.__version__
    assert platform["device"] == "cpu"
