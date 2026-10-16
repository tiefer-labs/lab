# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Config names follow the scheme of docs/SPEC.md, section 8."""

from __future__ import annotations

import re
from pathlib import Path

from tiefer_lab.config import config_to_dict, load_config

FAMILIES = ("sieb", "wandler", "lupe", "cloudscout_reimpl", "smoke")
SCHEME = re.compile(r"^(sieb|wandler|lupe|cloudscout_reimpl|smoke)(_[a-z0-9]+)*$")
SIZE = re.compile(r"^\d+(k|m)$")


def _configs(repo_root: Path) -> dict[str, Path]:
    return {p.stem: p for p in sorted((repo_root / "configs").glob("*.toml"))}


def test_every_config_name_follows_the_scheme(repo_root: Path) -> None:
    for stem, path in _configs(repo_root).items():
        assert SCHEME.match(stem), stem
        assert load_config(path).name == stem, stem
        parts = stem.split("_")
        if parts[0] == "sieb":
            # Sieb has one size and carries none.
            assert not any(SIZE.match(p) for p in parts[1:]), stem
        if parts[0] in ("wandler", "lupe"):
            assert any(SIZE.match(p) for p in parts[1:]), stem
        if "finetune" in parts:
            assert stem.endswith("_candidate_finetune"), stem


def test_int8_names_change_the_export_only(repo_root: Path) -> None:
    configs = _configs(repo_root)
    for stem in configs:
        if "_int8_" not in stem:
            continue
        reference = stem.split("_int8_")[0]
        a = config_to_dict(load_config(configs[reference]))
        b = config_to_dict(load_config(configs[stem]))
        changed = {s for s in a if s != "name" and a[s] != b[s]}
        assert changed == {"export"}, (stem, changed)


def test_every_family_is_explained_in_the_spec(repo_root: Path) -> None:
    spec = (repo_root / "docs" / "SPEC.md").read_text(encoding="utf-8")
    section = spec.split("### Model names", 1)[1].split("\n### ", 1)[0]
    for family in FAMILIES:
        assert re.search(rf"^\| `{family}` \| [^|]+ \| [^|]+ \|$", section, re.M), family
    for german in ("sieve", "converter", "magnifying glass"):
        assert german in section, german
