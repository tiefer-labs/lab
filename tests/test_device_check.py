# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Evaluation on the CPU gives the argmax of the training device (hpc/roihu/plan.md)."""

from __future__ import annotations

import pytest
import torch

from tiefer_lab import device_check


def test_cpu_against_cpu_is_identical() -> None:
    result = device_check.compare("cpu")
    assert result["passed"] and result["agreement"] == 1.0
    assert result["max_abs_logit_difference"] == 0.0
    assert result["decisive_pixels"] > 0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no GPU here; the smoke job runs it")
def test_cpu_against_the_training_gpu_within_the_tolerance() -> None:
    result = device_check.compare("cuda")
    assert result["passed"], result
    assert result["decisive_agreement"] == 1.0


def test_main_reports_and_fails_on_disagreement(monkeypatch: pytest.MonkeyPatch) -> None:
    assert device_check.main(["--device", "cpu"]) == 0
    monkeypatch.setattr(device_check, "compare", lambda name: {"passed": False})
    assert device_check.main(["--device", "cpu"]) == 1
