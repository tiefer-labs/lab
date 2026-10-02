# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Accepted audit findings need a reason and an expiry date, and expire."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "audit_exceptions", ROOT / ".github" / "scripts" / "audit_exceptions.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TODAY = dt.date(2026, 10, 2)


def _entry(**changes: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "id": "PYSEC-2026-1",
        "package": "example",
        "reason": "not reachable from this code",
        "expires": dt.date(2026, 11, 1),
    }
    entry.update(changes)
    return entry


def test_valid_entry_becomes_an_ignore_argument(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "x.toml"
    path.write_text(
        '[[exception]]\nid = "PYSEC-2026-1"\npackage = "example"\n'
        'reason = "not reachable"\nexpires = 2026-11-01\n',
        encoding="utf-8",
    )
    assert _module().main([str(path), "--today", "2026-10-02"]) == 0
    assert capsys.readouterr().out.split() == ["--ignore-vuln", "PYSEC-2026-1"]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"expires": dt.date(2026, 10, 1)}, "expired"),
        ({"expires": dt.date(2027, 6, 1)}, "more than 90 days"),
        ({"reason": " "}, "missing reason"),
        ({"expires": "soon"}, "must be a date"),
    ],
)
def test_invalid_entries_fail(changes: dict[str, object], message: str) -> None:
    assert any(message in p for p in _module().problems([_entry(**changes)], TODAY))


def test_repository_file_is_valid(capsys: pytest.CaptureFixture[str]) -> None:
    assert _module().main([str(ROOT / ".github" / "audit-exceptions.toml")]) == 0
