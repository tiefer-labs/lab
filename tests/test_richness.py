# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Richness report: cloud cover bins, shadow, and only verified metadata fields."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tiefer_lab.data import build_cache, richness


def test_patch_statistics_by_hand() -> None:
    labels = np.zeros((4, 10, 10), np.uint8)
    labels[1, :5] = 1  # 50 percent thick cloud
    labels[2] = 2  # all thin cloud
    labels[3, 0, 0] = 3  # clear with one shadow pixel
    labels[3, 1:] = 255  # mostly unlabelled
    bins, shadow = richness.patch_statistics(labels)
    assert bins == [2, 0, 1, 0, 1]
    assert shadow == 1


def test_field_summary_reports_verified_fields_only() -> None:
    metadata = [{"roi_id": "a", "label_type": "high", "season": "x"}, {"roi_id": "b"}]
    out = richness.field_summary(metadata)
    assert out["roi_id"]["distinct"] == 2
    assert out["label_type"]["patches_with_field"] == 1
    assert out["real_proj_shape"] == "not in the metadata"
    assert "season" not in out


def test_cli_on_synthetic_cache(tiefer_env: dict[str, Path]) -> None:
    assert (
        build_cache.main(["--split", "all", "--synthetic", "--limit", "5", "--patch-size", "32"])
        == 0
    )
    assert richness.main([build_cache.SYNTHETIC_NAME]) == 0
    out = tiefer_env["TIEFER_REPORTS_DIR"] / "data" / f"richness_{build_cache.SYNTHETIC_NAME}.json"
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["synthetic"] is True
    train = report["splits"]["train"]
    assert train["patches"] == 5
    assert sum(train["patches_per_cloud_cover"].values()) == 5
    assert abs(sum(train["class_pixel_share"].values()) - 1) < 1e-9


def test_cli_without_cache_fails(tiefer_env: dict[str, Path]) -> None:
    assert richness.main(["missing"]) == 1
