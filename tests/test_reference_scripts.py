# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Reference models outside src/ stop until their licence is cleared; masks append to a cache."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from tiefer_lab.data import build_cache, cache


def _module(repo_root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "run_reference", repo_root / "references" / "run_reference.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_reference"] = module
    spec.loader.exec_module(module)
    return module


def test_every_reference_stops_before_its_licence_is_cleared(repo_root: Path) -> None:
    ref = _module(repo_root)
    for name in ref.REFERENCES:
        with pytest.raises(ref.ReferenceError):
            ref.run(name, "any", "val")
    dtacs = ref.REFERENCES["dtacs4bands"]
    assert dtacs.licence == "CC-BY-NC-4.0" and dtacs.decision is None
    assert ref.main(["--model", "dtacs4bands", "--cache", "x", "--split", "val"]) == 2


def test_the_test_split_needs_final_and_a_reason(repo_root: Path) -> None:
    ref = _module(repo_root)
    assert ref.main(["--model", "fmask4", "--cache", "x", "--split", "test"]) == 2


def test_masks_are_added_next_to_existing_ones(
    repo_root: Path, tiefer_env: dict[str, Path]
) -> None:
    build_cache.main(["--split", "val", "--synthetic", "--limit", "3", "--patch-size", "32"])
    directory = cache.cache_dir("synthetic")
    masks = np.zeros((3, 32, 32), np.uint8)
    cache.add_reference_masks(directory, "val", {"a": masks}, {"a": "cloud"})
    cache.add_reference_masks(directory, "val", {"b": masks + 1}, {"b": "four_class"})
    data = cache.load_split(directory, "val")
    assert sorted(data.reference) == ["a", "b"]
    assert data.reference_kinds == {"a": "cloud", "b": "four_class"}
    with pytest.raises(cache.CacheError, match="already holds"):
        cache.add_reference_masks(directory, "val", {"a": masks}, {"a": "cloud"})
    with pytest.raises(cache.CacheError, match="expected uint8"):
        cache.add_reference_masks(directory, "val", {"c": masks[:2]}, {"c": "cloud"})
