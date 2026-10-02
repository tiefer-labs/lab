# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The coverage floor may rise, never fall."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coverage_floor", ROOT / ".github" / "scripts" / "coverage_floor.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: int | None) -> str:
    text = "" if value is None else f"[tool.coverage.report]\nfail_under = {value}\n"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_floor_may_rise_or_stay(tmp_path: Path) -> None:
    module = _module()
    assert module.main([_write(tmp_path / "a", 80), _write(tmp_path / "b", 80)]) == 0
    assert module.main([_write(tmp_path / "a", 80), _write(tmp_path / "b", 85)]) == 0
    assert module.main([_write(tmp_path / "a", None), _write(tmp_path / "b", 85)]) == 0


def test_lowering_the_floor_fails(tmp_path: Path) -> None:
    assert _module().main([_write(tmp_path / "a", 87), _write(tmp_path / "b", 86)]) == 1


def test_repository_has_a_floor() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    value = _module().floor(text)
    assert value is not None and value > 0
