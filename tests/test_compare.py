# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The comparison page, from report values made up for the test."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from tests.test_markdown_style import check_header, check_structure
from tiefer_lab import compare
from tiefer_lab.reports import Report, Reports


def _model(cloud: float, patches: int = 3) -> dict[str, Any]:
    return {
        "patches": patches,
        "binary": {
            "cloud": {
                "median_boa": cloud,
                "intervals": {"median_boa": {"low": cloud - 0.01, "high": cloud + 0.01}},
            },
            "shadow": {"median_boa": 0.8},
        },
        "pixel": {
            "mean_iou": 0.7,
            "iou": [0.9, 0.8, 0.5, 0.6],
            "producers_accuracy": [0.9, 0.9, 0.55, 0.6],
            "users_accuracy": [0.9, 0.9, 0.45, 0.6],
        },
        "frame": {
            "cloud_fraction_mae": 0.05,
            "thresholds": {"0.50": {"false_discard_rate": 0.02, "false_send_rate": 0.1}},
        },
    }


def _report() -> Report:
    data = {
        "kind": "evaluation",
        "split": "val",
        "run_id": "sieb-seed0-x",
        "config": {"name": "sieb"},
        "band_set": ["B02", "B03", "B04", "B08"],
        "run": {"seed": 0, "model": {"parameters": 250000, "macs_512x512": 123456789}},
        "calibration": {"ece": 0.04},
        "model": _model(0.9),
        "baselines": {
            "reference_cloudmask_qa60": {
                "patches": 3,
                "binary": {"cloud": {"median_boa": 0.6}},
            }
        },
    }
    return Report(Path("evaluation/sieb-seed0-x_val.json"), data)


def _export() -> Report:
    data = {
        "run_id": "sieb-seed0-x",
        "band_set": ["B02", "B03", "B04", "B08"],
        "operators": {"fp32": ["Conv", "Clip"], "int8": ["Conv", "QuantizeLinear"]},
        "files": {"fp32": {"bytes": 1000}, "fp16": {"bytes": 500}, "int8": {"bytes": 300}},
    }
    return Report(Path("export/sieb-seed0-x.json"), data)


def test_rows_metrics_and_cost_block() -> None:
    reports = Reports(evaluation=[_report()], export=[_export()])
    text = compare.render(reports, dt.date(2026, 10, 14))
    assert not check_header(Path("reports/comparison.md"), text.split("\n"))
    assert not check_structure(text)
    assert "sieb s0 (B02,B03,B04,B08)" in text
    assert "0.900 [0.890, 0.910]" in text
    # A cloud-only reference has n/a for shadow and the pixel metrics.
    qa60 = [line for line in text.splitlines() if line.startswith("| reference_cloudmask_qa60")]
    assert any("n/a" in line for line in qa60)
    assert "1,000 / 500 / 300" in text
    assert "250,000" in text and "123,456,789" in text
    assert "every row is scored on the same 3 patches" in text


def test_operators_allowed_and_different_pixels_are_named() -> None:
    assert compare.operators_allowed({"operators": {"fp32": ["Conv"], "int8": ["QuantizeLinear"]}})
    assert compare.operators_allowed({"operators": {"fp32": ["Conv", "Softmax"]}}) is False
    other = _report()
    other.data = {**other.data, "model": _model(0.8, patches=4), "baselines": {}}
    text = compare.render(Reports(evaluation=[_report(), other]), dt.date(2026, 10, 14))
    assert "different numbers of patches" in text


def test_page_without_reports() -> None:
    text = compare.render(Reports(), dt.date(2026, 10, 14))
    assert "No evaluation report" in text and not check_structure(text)
