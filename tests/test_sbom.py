# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The SBOM covers every locked package with a licence, and stops when one is missing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tiefer_lab import sbom


def _inputs(repo_root: Path) -> tuple[str, str]:
    return (
        (repo_root / "uv.lock").read_text(encoding="utf-8"),
        (repo_root / "docs" / "DEPENDENCIES.md").read_text(encoding="utf-8"),
    )


def test_every_locked_package_is_a_component_with_licence_and_hash(repo_root: Path) -> None:
    lock, deps = _inputs(repo_root)
    bom = sbom.build(lock, deps)
    assert bom["bomFormat"] == "CycloneDX" and bom["specVersion"] == "1.5"
    names = {c["name"] for c in bom["components"]}
    assert lock.count("[[package]]") == len(names) + 1  # plus the project itself
    for component in bom["components"]:
        assert component["licenses"], component["name"]
        assert component["purl"].startswith("pkg:pypi/")
        hashes = [h for ref in component["externalReferences"] for h in ref.get("hashes", [])]
        assert hashes and all(h["alg"] == "SHA-256" for h in hashes), component["name"]
    scopes = {c["name"]: c["scope"] for c in bom["components"]}
    assert scopes["torch"] == "required" and scopes["aiohttp"] == "required"
    assert scopes["pytest"] == "excluded" and scopes["ruff"] == "excluded"


def test_output_is_deterministic(repo_root: Path) -> None:
    lock, deps = _inputs(repo_root)
    assert json.dumps(sbom.build(lock, deps)) == json.dumps(sbom.build(lock, deps))


def test_missing_licence_row_stops(repo_root: Path) -> None:
    lock, deps = _inputs(repo_root)
    without_torch = "\n".join(
        line for line in deps.splitlines() if not line.startswith("| `torch` |")
    )
    with pytest.raises(sbom.SbomError, match="torch"):
        sbom.build(lock, without_torch)


def test_licence_entries() -> None:
    assert sbom.licence_entry("MIT") == {"expression": "MIT"}
    assert sbom.licence_entry("Apache-2.0 AND MIT") == {"expression": "Apache-2.0 AND MIT"}
    assert sbom.licence_entry("BSD License") == {"license": {"name": "BSD License"}}


def test_cli_writes_the_file(tmp_path: Path) -> None:
    out = tmp_path / "sbom.cdx.json"
    assert sbom.main(["--output", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["components"]
