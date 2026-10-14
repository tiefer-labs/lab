# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The 2022 release masks wait for verified facts and link patches one to one."""

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab.data import cloudsen12_2022 as release
from tiefer_lab.data.source import DataSourceError, MaskEncoding


def test_masks_wait_for_the_licence_decision_and_the_facts() -> None:
    with pytest.raises(DataSourceError, match="LICENCE_DECISION"):
        release.check_ready()
    with pytest.raises(DataSourceError, match="LICENCE_DECISION"):
        release.encode("fmask", np.zeros((2, 2), np.uint8))


def test_link_is_one_to_one_and_counts_the_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "LINK_FIELDS", ("old_roi_id", "product"))
    old = [
        {"old_roi_id": "a", "product": "p1"},
        {"old_roi_id": "b", "product": "p2"},
        {"old_roi_id": "b", "product": "p2"},
    ]
    new = [
        {"old_roi_id": "b", "product": "p2"},
        {"old_roi_id": "a", "product": "p1"},
        {"old_roi_id": "c", "product": "p3"},
    ]
    pairs, counts = release.link(old, new)
    assert pairs == {1: 0}
    assert counts == {"linked": 1, "new_without_old": 1, "ambiguous": 1}


def test_verified_encoding_is_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "LICENCE_DECISION", "allowed for this use")
    monkeypatch.setattr(release, "LINK_FIELDS", ("old_roi_id",))
    monkeypatch.setattr(release, "MASK_FILES", {"fmask": "fmask"})
    monkeypatch.setattr(release, "ENCODINGS", {"fmask": MaskEncoding("cloud", {0: 0, 4: 1})})
    out = release.encode("fmask", np.array([[0, 4]]))
    np.testing.assert_array_equal(out, [[0, 1]])
    with pytest.raises(DataSourceError, match="not in its verified encoding"):
        release.encode("fmask", np.array([[2]]))
