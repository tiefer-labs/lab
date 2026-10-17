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
    for name in set(ref.REFERENCES) - set(ref.runners()):
        with pytest.raises(ref.ReferenceError):
            ref.run(name, "any", "val")
    dtacs = ref.REFERENCES["dtacs4bands"]
    assert dtacs.licence == "CC-BY-NC-4.0"
    assert dtacs.decision.status == "declined, pending legal review"
    with pytest.raises(ref.ReferenceError, match="declined, pending legal review"):
        ref.run("dtacs4bands", "any", "val")
    # A declined reference leaves the command's choices.
    assert "dtacs4bands" not in ref.allowed_references()
    with pytest.raises(SystemExit):
        ref.main(["--model", "dtacs4bands", "--cache", "x", "--split", "val"])


def test_a_model_whose_weights_have_no_stated_licence_stops(repo_root: Path) -> None:
    ref = _module(repo_root)
    import dataclasses

    from tiefer_lab.data.source import LicenceDecision

    kappamask = dataclasses.replace(
        ref.REFERENCES["kappamask_l1c"],
        decision=LicenceDecision("used", "test"),
    )
    assert kappamask.licence == "Apache-2.0" and kappamask.weights_licence is None
    with pytest.raises(ref.ReferenceError, match="no licence is stated for its weights"):
        ref.ready(kappamask)
    with pytest.raises(ref.ReferenceError, match="no runner yet"):
        ref.ready(dataclasses.replace(kappamask, weights_licence="test"))


def test_the_decisions_of_16_october_2026_are_recorded(repo_root: Path) -> None:
    ref = _module(repo_root)
    for name in ("s2cloudless", "cd_fcnn_rgbi", "cd_fcnn_rgbiswir"):
        reference = ref.REFERENCES[name]
        assert reference.decision.status == "used"
        assert reference.decision.date == "16 October 2026"
        assert "issuecomment" in (reference.decision.issue or "")
        # Cleared, and their runners are added (references/runners.py).
        assert ref.ready(reference).bands
    s2cloudless = ref.ready(ref.REFERENCES["s2cloudless"])
    assert s2cloudless.bands == (
        "B01",
        "B02",
        "B04",
        "B05",
        "B08",
        "B8A",
        "B09",
        "B10",
        "B11",
        "B12",
    )
    assert "repository-wide MIT LICENSE" in ref.REFERENCES["cd_fcnn_rgbi"].weights_licence
    assert "never copied" in ref.REFERENCES["s2cloudless"].decision.reason
    for name in ("kappamask_l1c", "kappamask_l2a", "fmask4"):
        with pytest.raises(ref.ReferenceError, match="no licence is stated for its weights"):
            ref.run(name, "any", "val")


def test_release_2022_script_stops_with_its_decision(repo_root: Path, tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "add_release_2022", repo_root / "references" / "add_release_2022.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = ["--root", str(tmp_path), "--cache", "x", "--split", "val"]
    assert module.main(args) == 2


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
