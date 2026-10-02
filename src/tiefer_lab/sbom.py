# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Software bill of materials: CycloneDX 1.5 JSON from `uv.lock`.

    python -m tiefer_lab.sbom --output sbom.cdx.json

Every locked package becomes a component with its exact version, package URL,
the SHA-256 of each distribution file in the lock, and the licence listed in
docs/DEPENDENCIES.md, section 3. Packages reached only through the development
group get the scope "excluded" (used for tests, not at run time). A locked
package without a licence row stops the build with a clear message, so the
SBOM and the licence list cannot drift apart. The output is deterministic: no
timestamp, and the serial number is derived from the lock file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import uuid
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SPEC_VERSION = "1.5"
_ROW = re.compile(r"^\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|$")
_SPDX = re.compile(r"^[A-Za-z0-9.+-]+( (AND|OR|WITH) [A-Za-z0-9.+-]+)*$")
_SPDX_PLAIN = {"MIT", "ISC", "0BSD", "Zlib", "Unlicense"}


class SbomError(RuntimeError):
    """The lock and the licence list disagree."""


def licences(dependencies_md: str) -> dict[str, str]:
    """Package name to licence text, from section 3 of docs/DEPENDENCIES.md."""
    section = dependencies_md.split("## 3. All locked packages", 1)
    if len(section) != 2:
        raise SbomError("docs/DEPENDENCIES.md has no section '3. All locked packages'")
    out: dict[str, str] = {}
    for line in section[1].split("\n## ", 1)[0].splitlines():
        match = _ROW.match(line.strip())
        if match:
            out[match.group(1)] = match.group(3).strip()
    return out


def licence_entry(text: str) -> dict[str, Any]:
    """An SPDX expression when the text is one, otherwise a named licence."""
    is_expression = _SPDX.match(text) is not None and (
        text in _SPDX_PLAIN or all("-" in t or t in _SPDX_PLAIN for t in _ids(text))
    )
    return {"expression": text} if is_expression else {"license": {"name": text}}


def _ids(expression: str) -> list[str]:
    return [t for t in expression.split() if t not in {"AND", "OR", "WITH"}]


def purl(name: str, version: str) -> str:
    return f"pkg:pypi/{name.lower().replace('_', '-')}@{version}"


def _references(package: Mapping[str, Any]) -> list[dict[str, Any]]:
    files = ([package["sdist"]] if "sdist" in package else []) + list(package.get("wheels", []))
    refs = []
    for item in files:
        algorithm, _, digest = str(item.get("hash", "")).partition(":")
        ref: dict[str, Any] = {"type": "distribution", "url": item["url"]}
        if algorithm == "sha256" and digest:
            ref["hashes"] = [{"alg": "SHA-256", "content": digest}]
        refs.append(ref)
    return refs


def _edges(
    package: Mapping[str, Any], extras: Iterable[str] = (), dev: bool = False
) -> list[tuple[str, list[str]]]:
    """(dependency name, its requested extras) of a package with the given extras."""
    deps = list(package.get("dependencies", []))
    for extra in extras:
        deps += package.get("optional-dependencies", {}).get(extra, [])
    if dev:
        for group in package.get("dev-dependencies", {}).values():
            deps += group
    return [(d["name"], list(d.get("extra", []))) for d in deps]


def runtime_names(packages: Mapping[str, Mapping[str, Any]], root: Mapping[str, Any]) -> set[str]:
    """Names of the packages reached from the project's run-time dependencies."""
    seen: set[tuple[str, str]] = set()
    names: set[str] = set()
    stack = _edges(root)
    while stack:
        name, extras = stack.pop()
        names.add(name)
        for extra in ["", *extras]:
            if (name, extra) in seen:
                continue
            seen.add((name, extra))
            stack += _edges(packages[name], [extra] if extra else [])
    return names


def build(lock_text: str, dependencies_md: str) -> dict[str, Any]:
    lock = tomllib.loads(lock_text)
    packages = {p["name"]: p for p in lock["package"]}
    roots = [p for p in lock["package"] if "editable" in p["source"]]
    if len(roots) != 1:
        raise SbomError(f"expected one editable project in uv.lock, found {len(roots)}")
    root = roots[0]
    known = licences(dependencies_md)
    missing = sorted(n for n in packages if n != root["name"] and n not in known)
    if missing:
        raise SbomError(
            "locked packages without a licence row in docs/DEPENDENCIES.md, section 3: "
            + ", ".join(missing)
        )
    runtime = runtime_names(packages, root)
    requested: dict[str, set[str]] = {name: set() for name in packages}
    for package in packages.values():
        for dep, extras in _edges(package, package.get("optional-dependencies", {})):
            requested[dep].update(extras)
    for group in root.get("dev-dependencies", {}).values():
        for dep in group:
            requested[dep["name"]].update(dep.get("extra", []))
    components = []
    dependencies = []
    for name in sorted(packages):
        package = packages[name]
        ref = purl(name, package["version"])
        children = sorted(
            {
                purl(dep, packages[dep]["version"])
                for dep, _ in _edges(package, requested[name], dev=package is root)
            }
        )
        dependencies.append({"ref": ref, "dependsOn": children})
        if package is root:
            continue
        components.append(
            {
                "type": "library",
                "bom-ref": ref,
                "name": name,
                "version": package["version"],
                "purl": ref,
                "scope": "required" if name in runtime else "excluded",
                "licenses": [licence_entry(known[name])],
                "externalReferences": _references(package),
            }
        )
    digest = hashlib.sha256(lock_text.encode("utf-8")).digest()
    return {
        "bomFormat": "CycloneDX",
        "specVersion": SPEC_VERSION,
        "serialNumber": f"urn:uuid:{uuid.UUID(bytes=digest[:16], version=4)}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": purl(root["name"], root["version"]),
                "name": root["name"],
                "version": root["version"],
                "licenses": [{"license": {"id": "MPL-2.0"}}],
            }
        },
        "components": components,
        "dependencies": dependencies,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lock", type=Path, default=REPO / "uv.lock")
    parser.add_argument("--licences", type=Path, default=REPO / "docs" / "DEPENDENCIES.md")
    parser.add_argument("--output", type=Path, default=Path("sbom.cdx.json"))
    args = parser.parse_args(argv)
    try:
        bom = build(
            args.lock.read_text(encoding="utf-8"), args.licences.read_text(encoding="utf-8")
        )
    except SbomError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(bom, indent=2) + "\n", encoding="utf-8")
    required = sum(c["scope"] == "required" for c in bom["components"])
    print(
        f"{args.output}: {len(bom['components'])} components, {required} at run time, "
        f"CycloneDX {SPEC_VERSION}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
