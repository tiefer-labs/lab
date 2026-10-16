# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Acceptance targets from reports; the report values below are made up for the test."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from tests.test_markdown_style import check_header, check_structure
from tiefer_lab import acceptance, requirements
from tiefer_lab.data.source import USED_BANDS
from tiefer_lab.reports import Report, Reports


def _evaluation(config: str, cloud: float, shadow: float, seed: int = 0) -> Report:
    def binary(value: float) -> dict[str, Any]:
        return {
            "median_boa": value,
            "intervals": {"median_boa": {"low": value - 0.02, "high": value + 0.02}},
        }

    frame = {"0.50": {"false_discard_rate": 0.015, "false_send_rate": 0.12}}
    data = {
        "kind": "evaluation",
        "split": "test",
        "final": True,
        "run_id": f"{config}-seed{seed}",
        "config": {"name": config},
        "band_set": list(USED_BANDS),
        "perturbation": None,
        "provenance": {"git": {"commit": "0" * 40}, "time": f"2026-10-0{seed + 3}"},
        "calibration": {"ece": 0.04},
        "model": {
            "binary": {"cloud": binary(cloud), "shadow": binary(shadow)},
            "pixel": {
                "mean_iou": 0.72,
                "producers_accuracy": [0.9, 0.9, 0.5, 0.6],
                "users_accuracy": [0.9, 0.9, 0.55, 0.6],
            },
            "frame": {"cloud_fraction_mae": 0.06, "thresholds": frame},
            "decision_threshold": 0.5,
            "intervals": {"mean_iou": {"low": 0.70, "high": 0.74}},
        },
    }
    return Report(Path(f"evaluation/{config}-{seed}.json"), data)


def _rows(reports: Reports) -> dict[str, dict[str, Any]]:
    return {r["target"].id: r for r in acceptance.evaluate(reports)}


def test_without_reports_every_measured_target_is_not_measured() -> None:
    rows = _rows(Reports())
    assert rows["ACC-01"]["minimum_status"] == "not measured"
    assert rows["OBD-01"]["target_status"] == "not measured"
    # The fail-safe check runs without reports and must find no discarded frame.
    assert rows["STD-02"]["measurement"].value == 0
    assert rows["STD-02"]["target_status"] == "met"
    assert rows["IND-01"]["minimum_status"] == "not met"  # zero independent datasets


def test_minimum_and_target_are_judged_separately() -> None:
    reports = Reports(evaluation=[_evaluation("wandler_1m", cloud=0.88, shadow=0.84)])
    rows = _rows(reports)
    assert (rows["ACC-01"]["minimum_status"], rows["ACC-01"]["target_status"]) == ("met", "not met")
    assert (rows["ACC-03"]["minimum_status"], rows["ACC-03"]["target_status"]) == ("met", "not met")
    assert (rows["ACC-05"]["minimum_status"], rows["ACC-05"]["target_status"]) == ("met", "not met")
    assert rows["ACC-07"]["minimum_status"] == "met" and rows["ACC-08"]["target_status"] == "met"
    assert (
        rows["FRM-01"]["minimum_status"] == "met" and rows["FRM-01"]["target_status"] == "not met"
    )
    frm2 = rows["FRM-02"]["measurement"].value
    assert abs(frm2 - 0.88) < 1e-9
    assert rows["ACC-09"]["minimum_status"] == "not measured"  # one seed only


def test_a_minimum_written_as_above_is_strict() -> None:
    rows = _rows(Reports(evaluation=[_evaluation("wandler_1m", cloud=0.84, shadow=0.75)]))
    assert rows["ACC-01"]["minimum_status"] == "not met"


def test_three_seeds_give_a_spread_and_a_mean() -> None:
    reports = Reports(
        evaluation=[_evaluation("wandler_1m", 0.90 + 0.01 * s, 0.8, seed=s) for s in range(3)]
    )
    rows = _rows(reports)
    assert abs(rows["ACC-01"]["measurement"].value - 0.91) < 1e-9
    assert abs(rows["ACC-09"]["measurement"].value - 0.01) < 1e-9


def test_flexible_against_specialist() -> None:
    reports = Reports(
        evaluation=[_evaluation("wandler_1m", 0.900, 0.8), _evaluation("lupe_1m", 0.905, 0.8)]
    )
    row = _rows(reports)["CMP-04"]
    assert abs(row["measurement"].value - 0.005) < 1e-9
    assert row["minimum_status"] == "met" and "within" in row["measurement"].note


def test_page_follows_the_markdown_standard() -> None:
    text = acceptance.render(acceptance.evaluate(Reports()), dt.date(2026, 10, 2))
    assert not check_header(Path("reports/acceptance.md"), text.split("\n"))
    assert not check_structure(text)
    assert "ACC-01" in text and "15.6 tiles" in text


def test_requirements_traceability(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    rows = [f"| `{t.id}` | x | `tiefer_lab.acceptance` |" for t in acceptance.TARGETS]
    this = "tests/test_acceptance.py"
    doc = tmp_path / "REQUIREMENTS.md"
    doc.write_text(
        "\n".join(
            [
                *rows,
                f"| `REQ-TST-01` | verified | `{this}::test_requirements_traceability` |",
                "| `REQ-TST-02` | no verification |  |",
                f"| `REQ-TST-03` | broken | `{this}::no_such_test`, `missing/file.py` |",
                "| `REQ-TST-01` | duplicate | `src/tiefer_lab/acceptance.py` |",
            ]
        )
    )
    result = requirements.check(doc, repo)
    assert result["unverified"] == ["REQ-TST-02"]
    assert result["broken_links"] == [
        "REQ-TST-03: missing/file.py",
        "REQ-TST-03: tests/test_acceptance.py::no_such_test",
    ]
    assert result["duplicates"] == ["REQ-TST-01"]
    assert result["missing_acceptance_targets"] == []


def _independent(
    config: str,
    source: str,
    sensor: str,
    cloud: float,
    reference: tuple[str, float] | None = None,
    strata: dict[str, float] | None = None,
) -> Report:
    report = _evaluation(config, cloud=cloud, shadow=0.8)
    report.data.update(
        {
            "split": "all",
            "final": False,
            "data": {"source": source},
            "independent": {
                "sensor": sensor,
                "four_band_equivalent": True,
                "operational_mask": None if sensor.startswith("Sentinel") else "reference_qa",
                "strata_fields": ["biome"],
            },
            "breakdown": {
                "biome": {
                    name: {"patches": 12, "cloud_boa": value}
                    for name, value in (strata or {}).items()
                }
            },
        }
    )
    if reference is not None:
        name, value = reference
        report.data["baselines"] = {name: {"binary": {"cloud": {"median_boa": value}}}}
    report.path = Path(f"evaluation/{config}-{source}.json")
    return report


def test_independent_targets_by_hand() -> None:
    reports = Reports(
        evaluation=[
            _evaluation("wandler_1m", cloud=0.90, shadow=0.8),
            _independent(
                "wandler_1m",
                "s2_cloud_catalogue",
                "Sentinel-2 MSI",
                0.89,
                ("reference_sen2cor", 0.80),
            ),
            _independent(
                "wandler_1m", "kappaset", "Sentinel-2 MSI", 0.85, ("reference_sen2cor", 0.70)
            ),
            _independent(
                "wandler_1m",
                "landsat8_biome",
                "Landsat 8 OLI",
                0.86,
                ("reference_qa", 0.80),
                strata={"snow": 0.74, "forest": 0.9},
            ),
        ]
    )
    rows = _rows(reports)
    assert rows["IND-01"]["measurement"].value == 3
    assert rows["IND-01"]["minimum_status"] == "met"
    # Three datasets from two sensors: the target needs four from three.
    assert rows["IND-01"]["target_status"] == "not met"
    ind2 = rows["IND-02"]
    # Smallest margin over Sen2Cor: 0.89 - 0.80 = 0.09 and 0.85 - 0.70 = 0.15.
    assert abs(ind2["measurement"].value - 0.09) < 1e-9 and ind2["minimum_status"] == "met"
    # Within 0.03 of the test value 0.90: 0.89 yes, 0.85 no.
    assert ind2["target_status"] == "not met"
    ind3 = rows["IND-03"]
    assert abs(ind3["measurement"].value - 0.06) < 1e-9
    # 0.86 is within 0.05 of 0.90.
    assert ind3["target_status"] == "met"
    assert rows["IND-04"]["measurement"].value == 0.74
    assert rows["IND-04"]["minimum_status"] == "not met"
    # CMP-06: 0.90 - 0.86 = 0.04, below the minimum 0.08 and the target 0.05.
    assert abs(rows["CMP-06"]["measurement"].value - 0.04) < 1e-9
    assert rows["CMP-06"]["target_status"] == "met"


def test_per_model_targets_read_only_that_config() -> None:
    reports = Reports(
        evaluation=[
            _evaluation("wandler_1m", cloud=0.86, shadow=0.8),
            _evaluation("sieb", cloud=0.92, shadow=0.8),
        ]
    )
    rows = {
        r["target"].id: r
        for r in acceptance.evaluate(reports, acceptance.build_targets(("sieb",), strict=True))
    }
    assert rows["ACC-01"]["measurement"].value == 0.92
    assert "largest" in rows["ACC-02"]["measurement"].note
    assert "lupe_1m" in rows["CMP-04"]["measurement"].note
    # The default table still reads the 1 M band-flexible model only.
    assert _rows(reports)["ACC-01"]["measurement"].value == 0.86


def test_export_match_is_strict_only_in_per_model_tables() -> None:
    assert acceptance._export_matches("wandler_1m_rescale_2x-seed0-x", ("wandler_1m",), False)
    assert not acceptance._export_matches("wandler_1m_rescale_2x-seed0-x", ("wandler_1m",), True)
    assert acceptance._export_matches("wandler_1m-seed0-x", ("wandler_1m",), True)


def test_jetson_memory_and_determinism() -> None:
    jetson = Report(
        Path("jetson/int8.json"),
        {
            "memory": {"peak_gb": 0.8},
            "determinism": {"identical": True, "runs": 20},
            "throughput": {"tiles_per_second": 30.0},
        },
    )
    rows = _rows(Reports(jetson=[jetson]))
    assert rows["OBD-04"]["target_status"] == "met"
    assert rows["OBD-06"]["minimum_status"] == "reported"
    assert rows["OBD-06"]["target_status"] == "met"


def test_per_model_page_follows_the_markdown_standard() -> None:
    rows = acceptance.evaluate(Reports(), acceptance.build_targets(("sieb",), strict=True))
    text = acceptance.render(rows, dt.date(2026, 10, 14), "sieb")
    assert not check_header(Path("reports/acceptance_l1_full.md"), text.split("\n"))
    assert "Acceptance of sieb" in text


def test_int8_is_marked_as_a_proxy() -> None:
    export = Report(
        Path("export/wandler_1m-seed0-x.json"),
        {
            "run_id": "wandler_1m-seed0-x",
            "band_set": list(USED_BANDS),
            "quantisation": {"val": {"change": {"cloud_boa_change": -0.004}}},
        },
    )
    rows = _rows(Reports(export=[export]))
    measurement = rows["CMP-03"]["measurement"]
    assert measurement.value == 0.004
    assert "proxy" in measurement.note and "Jetson" in measurement.note
