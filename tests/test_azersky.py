# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Azersky: a candidate with no data; its reader stops on the decision and every open fact."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from tiefer_lab.data import azersky, independent
from tiefer_lab.data.source import DataSourceError, LicenceDecision, LicenceRefusedError


def test_a_candidate_without_a_decision_is_never_read(tmp_path: Path) -> None:
    assert azersky.STATUS == "candidate, no data, no licence decision"
    assert not azersky.DECISION.allowed
    with pytest.raises(LicenceRefusedError, match="no licence decision"):
        next(azersky.read_azersky(tmp_path, ["B02"]))
    # Not an independent dataset record: the source check never contacts it, and
    # independent.sbatch stops with its decision before anything is downloaded.
    assert "azersky" not in independent.DATASETS
    with pytest.raises(LicenceRefusedError, match="azersky: no licence decision"):
        independent.require_dataset_allowed("azersky")


def test_every_fact_is_open_and_names_what_resolves_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert set(azersky.FACTS) == {"product_format", "bands", "toa_scaling", "gsd_m", "labels"}
    assert all(fact.value is None and fact.resolves for fact in azersky.FACTS.values())
    used = LicenceDecision("used", "data agreement (test value)", "1 January 2027")
    monkeypatch.setattr(azersky, "DECISION", used)
    facts = dict(azersky.FACTS)
    for name in azersky.FACTS:
        with pytest.raises(DataSourceError, match=f"{name} is not verified yet") as stop:
            next(azersky.read_azersky(tmp_path, ["B02"]))
        assert azersky.FACTS[name].resolves in str(stop.value)
        facts[name] = dataclasses.replace(facts[name], value="verified (test value)")
        monkeypatch.setattr(azersky, "FACTS", dict(facts))
    with pytest.raises(DataSourceError, match="write the scene read"):
        next(azersky.read_azersky(tmp_path, ["B02"]))


def test_nothing_is_fetched_and_the_labels_follow_cloudsen12(repo_root: Path) -> None:
    text = (repo_root / "src" / "tiefer_lab" / "data" / "azersky.py").read_text()
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert not re.search(r"https?://", code)
    assert "RemoteFile" not in code and "http" not in code.split('"""', 2)[2]
    assert list(azersky.LABEL_CLASSES) == ["clear", "thick cloud", "thin cloud", "cloud shadow"]
