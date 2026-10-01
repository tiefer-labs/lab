# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""hpc/roihu/requirements.txt must match uv.lock (regenerate with make requirements)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)")


def _torch_only(repo_root: Path) -> list[str]:
    text = (repo_root / "Makefile").read_text().replace("\\\n", " ")
    match = re.search(r"^TORCH_ONLY = (.+)$", text, re.MULTILINE)
    assert match, "TORCH_ONLY not found in Makefile"
    return match.group(1).split()


def _pins(text: str) -> dict[str, str]:
    pins = {}
    for line in text.splitlines():
        match = PIN.match(line)
        if match:
            pins[match.group(1).lower()] = match.group(2)
    return pins


def test_pins_match_lock_and_exclude_torch(repo_root: Path) -> None:
    lock = tomllib.loads((repo_root / "uv.lock").read_text())
    locked = {p["name"]: p["version"] for p in lock["package"]}
    pins = _pins((repo_root / "hpc" / "roihu" / "requirements.txt").read_text())
    assert pins, "no pinned packages"
    for name, version in pins.items():
        assert locked.get(name) == version, f"{name}=={version} differs from uv.lock"
    torch_only = set(_torch_only(repo_root))
    assert "torch" in torch_only
    assert not torch_only & set(pins), "torch and its own dependencies come from the module"
    for needed in ("numpy", "tacoreader", "rasterio", "onnx", "onnxruntime", "fsspec", "aiohttp"):
        assert needed in pins
    for dev in ("pytest", "ruff", "mypy", "regex"):
        assert dev not in pins


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")
def test_file_is_exactly_what_uv_export_writes(repo_root: Path, tmp_path: Path) -> None:
    out = tmp_path / "requirements.txt"
    args = ["uv", "export", "--frozen", "--no-dev", "--no-hashes", "--no-emit-project"]
    for name in _torch_only(repo_root):
        args += ["--no-emit-package", name]
    subprocess.run(
        [*args, "--output-file", str(out)], cwd=repo_root, check=True, capture_output=True
    )
    expected = out.read_text().splitlines()[2:]  # skip the two header lines with the command
    actual = (repo_root / "hpc" / "roihu" / "requirements.txt").read_text().splitlines()[2:]
    assert actual == expected, "run make requirements"
