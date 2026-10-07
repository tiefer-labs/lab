# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Acceptance targets: read the reports, write reports/acceptance.md.

    python -m tiefer_lab.acceptance

One row per target with the measured value, its interval, and for the
minimum and the target: "met", "not met" or "not measured". The targets are
goals set by the founder, not predictions. They are written here once and
changed only in a commit that says so; nothing is ever tuned on the test
split to meet one, and a missed target is reported as missed.

Values published in the dataset paper are not written here until they are
checked against its tables (TODO(verify), https://doi.org/10.1038/s41597-022-01878-2).

Reports used: final test evaluations (`final: true`) for accuracy, frame and
flexibility targets; export reports for compression; Jetson reports for the
on-board targets; the fail-safe check of `tiefer_lab.onboard`; and
docs/REQUIREMENTS.md and docs/STANDARDS.md for the two documentation targets.
When several seeds of a configuration have a report, the value is their mean
and the interval spans the lowest and highest bound of their intervals.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tiefer_lab import onboard
from tiefer_lab.data.source import L1C_BAND_NAMES, THIN_CLOUD, USED_BANDS
from tiefer_lab.reports import Report, Reports, load_reports
from tiefer_lab.tables import Group, header_block, markdown_table
from tiefer_lab.utils import paths

REPORT = "acceptance.md"
REPO = Path(__file__).resolve().parents[2]
NOT_MEASURED = "not measured"

ONE_M = ("l2_flex_1m", "l2_flex_1m_zero")
SPECIALIST_1M = ("l2_spec_1m",)
LARGEST = ("l2_flex_22m", "l2_flex_cnx_21m")
RGB = ("B02", "B03", "B04")

# The basis of the throughput targets, as stated by the founder.
THROUGHPUT_BASIS = (
    "A 60 km swath at 10 m is 6000 pixels per line; at about 6.8 km/s ground speed that is "
    "680 lines per second, 6000 x 680 = 4.08 megapixels per second, or 4.08 M / (512 x 512) "
    "= 15.6 tiles of 512 x 512 per second before overlap. Assumptions: the swath, the "
    "sampling and the ground speed above; tiles do not overlap; one model run per tile."
)


@dataclass(frozen=True)
class Measurement:
    value: float | None
    low: float | None = None
    high: float | None = None
    source: str = ""
    note: str = ""


@dataclass(frozen=True)
class Target:
    id: str
    group: str
    description: str
    minimum: float | None
    target: float | None
    # "higher": larger is better; "lower": smaller is better; "report": shown only.
    direction: str
    measure: Callable[[Reports], Measurement | None]
    strict_minimum: bool = False
    minimum_text: str = ""
    target_text: str = ""


# Selection -------------------------------------------------------------------


def _config_name(r: Report) -> str:
    return str(r.data.get("config", {}).get("name", ""))


def finals(
    reports: Reports, configs: Sequence[str], bands: Sequence[str], perturbation: str | None = None
) -> list[Report]:
    """Final test evaluations of the configs on a band set (any order)."""
    return [
        r
        for r in reports.evaluation
        if r.data.get("split") == "test"
        and r.data.get("final")
        and _config_name(r) in configs
        and set(r.data.get("band_set") or USED_BANDS) == set(bands)
        and r.data.get("perturbation") == perturbation
    ]


def _combine(values: Sequence[tuple[Any, Any, Any]], source: str) -> Measurement | None:
    values = [v for v in values if v[0] is not None and math.isfinite(v[0])]
    if not values:
        return None
    lows = [v[1] for v in values if v[1] is not None]
    highs = [v[2] for v in values if v[2] is not None]
    return Measurement(
        statistics.fmean(v[0] for v in values),
        min(lows) if lows else None,
        max(highs) if highs else None,
        source,
        f"mean of {len(values)} seeds" if len(values) > 1 else "",
    )


def _sources(rs: Sequence[Report]) -> str:
    return ", ".join(r.source for r in rs)


def _binary(m: dict[str, Any], problem: str, measure: str = "boa") -> tuple[Any, Any, Any]:
    block = m.get("binary", {}).get(problem, {})
    interval = block.get("intervals", {}).get(f"median_{measure}", {})
    return block.get(f"median_{measure}"), interval.get("low"), interval.get("high")


def boa(
    configs: Sequence[str], bands: Sequence[str], problem: str
) -> Callable[[Reports], Measurement | None]:
    def measure(reports: Reports) -> Measurement | None:
        rs = finals(reports, configs, bands)
        return _combine([_binary(r.data["model"], problem) for r in rs], _sources(rs))

    return measure


def model_value(
    path: Sequence[str], interval: str | None = None
) -> Callable[[Reports], Measurement | None]:
    def measure(reports: Reports) -> Measurement | None:
        rs = finals(reports, ONE_M, USED_BANDS)
        values = []
        for r in rs:
            node: Any = r.data["model"]
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
            bounds = r.data["model"].get("intervals", {}).get(interval or "", {})
            values.append((node, bounds.get("low"), bounds.get("high")))
        return _combine(values, _sources(rs))

    return measure


def references_beaten(reports: Reports) -> Measurement | None:
    """References (except UNetMobV2) whose cloud BOA interval reaches the model's."""
    rs = finals(reports, ONE_M, USED_BANDS)
    if not rs:
        return None
    model_low = min((_binary(r.data["model"], "cloud")[1] for r in rs), default=None)
    with_refs = [r for r in rs if r.data.get("baselines")]
    if model_low is None or not with_refs:
        return None
    refs = {
        name: _binary(m, "cloud")
        for name, m in with_refs[-1].data["baselines"].items()
        if name.startswith("reference_") and "unetmobv2" not in name
    }
    if not refs:
        return Measurement(
            None, source=with_refs[-1].source, note="no reference masks in the report"
        )
    overlapping = sorted(n for n, (_, _, high) in refs.items() if high is None or high >= model_low)
    return Measurement(
        float(len(overlapping)),
        source=with_refs[-1].source,
        note=f"{len(refs)} references; overlapping: {', '.join(overlapping) or 'none'}",
    )


def thin_cloud_reported(reports: Reports) -> Measurement | None:
    rs = finals(reports, ONE_M, USED_BANDS)
    if not rs:
        return None
    pixel = rs[-1].data["model"]["pixel"]
    pa, ua = pixel.get("producers_accuracy"), pixel.get("users_accuracy")
    if not pa or not ua:
        return None
    return Measurement(
        1.0,
        source=rs[-1].source,
        note=f"thin cloud PA {pa[THIN_CLOUD]:.3f}, UA {ua[THIN_CLOUD]:.3f}",
    )


def calibration(reports: Reports) -> Measurement | None:
    rs = finals(reports, ONE_M, USED_BANDS)
    return _combine(
        [(r.data.get("calibration", {}).get("ece"), None, None) for r in rs], _sources(rs)
    )


def seed_spread(reports: Reports) -> Measurement | None:
    rs = finals(reports, ONE_M, USED_BANDS)
    values = [v for v in (_binary(r.data["model"], "cloud")[0] for r in rs) if v is not None]
    if len(values) < 3:
        return (
            Measurement(None, source=_sources(rs), note=f"{len(values)} seeds; 3 are needed")
            if rs
            else None
        )
    return Measurement(statistics.stdev(values), source=_sources(rs), note=f"{len(values)} seeds")


def frame_rate(key: str, invert: bool = False) -> Callable[[Reports], Measurement | None]:
    def measure(reports: Reports) -> Measurement | None:
        rs = finals(reports, ONE_M, USED_BANDS)
        values = []
        for r in rs:
            m = r.data["model"]
            t = f"{m['decision_threshold']:.2f}"
            v = m["frame"]["thresholds"][t].get(key)
            values.append((None if v is None else (1 - v if invert else v), None, None))
        return _combine(values, _sources(rs))

    return measure


def flexible_vs_specialist(reports: Reports) -> Measurement | None:
    flex = boa(ONE_M, USED_BANDS, "cloud")(reports)
    spec = boa(SPECIALIST_1M, USED_BANDS, "cloud")(reports)
    if flex is None or spec is None or flex.value is None or spec.value is None:
        return None
    inside = spec.low is not None and spec.high is not None and spec.low <= flex.value <= spec.high
    return Measurement(
        spec.value - flex.value,
        source=f"{flex.source}; {spec.source}",
        note="within the specialist's interval" if inside else "outside the specialist's interval",
    )


def rescaling_loss(reports: Reports) -> Measurement | None:
    base = boa(ONE_M, USED_BANDS, "cloud")(reports)
    if base is None or base.value is None:
        return None
    losses = []
    for scale in ("rescale=0.5", "rescale=2"):
        rs = finals(reports, ONE_M, USED_BANDS, perturbation=scale)
        m = _combine([_binary(r.data["model"], "cloud") for r in rs], _sources(rs))
        if m is None or m.value is None:
            return None
        losses.append(base.value - m.value)
    return Measurement(max(losses), note="largest loss of rescale=0.5 and rescale=2")


def rgb_reported(reports: Reports) -> Measurement | None:
    return boa(ONE_M, RGB, "cloud")(reports)


def export_value(key: str) -> Callable[[Reports], Measurement | None]:
    def measure(reports: Reports) -> Measurement | None:
        for r in reversed(reports.export):
            if str(r.data.get("run_id", "")).startswith(ONE_M) and set(
                r.data.get("band_set") or []
            ) == set(USED_BANDS):
                if key == "argmax":
                    v = r.data.get("verification", {}).get("fp32", {}).get("argmax_agreement")
                elif key in ("fp16", "int8"):
                    q = r.data.get("quantisation", {}).get("test") or r.data.get(
                        "quantisation", {}
                    ).get("val")
                    if not q:
                        return None
                    change = q.get("fp16_change" if key == "fp16" else "change", {})
                    v = change.get("cloud_boa_change")
                    v = None if v is None else -float(v)
                else:
                    file = r.data.get("files", {}).get(key, {})
                    v = None if not file else file.get("bytes", 0) / 1e6
                return Measurement(v, source=r.source) if v is not None else None
        return None

    return measure


def jetson_value(key: str) -> Callable[[Reports], Measurement | None]:
    def measure(reports: Reports) -> Measurement | None:
        values = []
        for r in reports.jetson:
            if key == "throughput":
                values.append(r.data.get("throughput", {}).get("tiles_per_second"))
            elif key == "latency":
                values.append(r.data.get("latency", {}).get("mean_ms"))
            elif key == "power":
                mw = r.data.get("power", {}).get("run", {}).get("mean_mw")
                values.append(None if mw is None else float(mw) / 1000.0)
        values = [v for v in values if v is not None]
        if not values:
            return None
        best = max(values) if key == "throughput" else min(values)
        return Measurement(float(best), source=_sources(reports.jetson), note="best engine")

    return measure


def worst_stratum(reports: Reports) -> Measurement | None:
    rs = finals(reports, ONE_M, USED_BANDS)
    worst: list[dict[str, Any]] = [
        r.data["worst_stratum"] for r in rs if r.data.get("worst_stratum")
    ]
    if not worst:
        return None
    w = min(worst, key=lambda x: x["cloud_boa"])
    return Measurement(
        w["cloud_boa"],
        source=_sources(rs),
        note=f"{w['field']} = {w['value']}, {w['patches']} patches",
    )


def failsafe(_: Reports) -> Measurement | None:
    out = onboard.failsafe_check()
    return Measurement(
        float(out["discarded"]),
        source="`tiefer_lab.onboard.failsafe_check`",
        note=f"{out['cases']} cases",
    )


def requirements_unverified(_: Reports) -> Measurement | None:
    from tiefer_lab import requirements

    path = REPO / "docs" / "REQUIREMENTS.md"
    if not path.is_file():
        return None
    problems = requirements.check(path, REPO)
    return Measurement(float(len(problems["unverified"])), source="`docs/REQUIREMENTS.md`")


def standards_not_read(_: Reports) -> Measurement | None:
    path = REPO / "docs" / "STANDARDS.md"
    if not path.is_file():
        return None
    rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("| ")]
    return Measurement(
        float(sum(1 for row in rows if row.rstrip().endswith("| not read |"))),
        source="`docs/STANDARDS.md`",
    )


def not_available(reason: str) -> Callable[[Reports], Measurement | None]:
    def measure(_: Reports) -> Measurement | None:
        return Measurement(None, note=reason)

    return measure


def count_independent(reports: Reports) -> Measurement | None:
    sources = {
        r.data.get("data", {}).get("source")
        for r in reports.evaluation
        if r.data.get("data", {}).get("source") not in (None, "cloudsen12", "synthetic")
    }
    return Measurement(float(len(sources)), note="evaluations on datasets other than CloudSEN12+")


# Targets ---------------------------------------------------------------------

GROUP_ACC, GROUP_IND, GROUP_FRM, GROUP_CMP, GROUP_OBD, GROUP_STD = (
    "Accuracy on the 975 test patches, four-band set, 1 M model unless stated",
    "Independent datasets, four-band set, never used for training or selection",
    "Frame decision",
    "Compression and flexibility",
    "On board (Jetson), provisional",
    "Standards alignment",
)

TARGETS: tuple[Target, ...] = (
    Target(
        "ACC-01",
        GROUP_ACC,
        "Cloud against non-cloud, median BOA",
        0.84,
        0.90,
        "higher",
        boa(ONE_M, USED_BANDS, "cloud"),
        strict_minimum=True,
    ),
    Target(
        "ACC-02",
        GROUP_ACC,
        "Same, largest model, all 13 bands",
        0.90,
        0.92,
        "higher",
        boa(LARGEST, L1C_BAND_NAMES, "cloud"),
    ),
    Target(
        "ACC-03",
        GROUP_ACC,
        "Cloud shadow, median BOA",
        0.74,
        0.85,
        "higher",
        boa(ONE_M, USED_BANDS, "shadow"),
        strict_minimum=True,
    ),
    Target(
        "ACC-04",
        GROUP_ACC,
        "Reference algorithms (except UNetMobV2) whose cloud BOA interval overlaps the model's",
        0,
        0,
        "lower",
        references_beaten,
    ),
    Target(
        "ACC-05",
        GROUP_ACC,
        "Mean IoU, four classes",
        0.70,
        0.75,
        "higher",
        model_value(["pixel", "mean_iou"], "mean_iou"),
    ),
    Target(
        "ACC-06",
        GROUP_ACC,
        "Thin cloud producer's and user's accuracy",
        None,
        None,
        "report",
        thin_cloud_reported,
        minimum_text="reported",
        target_text="above every reference except UNetMobV2 (compared in docs/RESULTS.md)",
    ),
    Target(
        "ACC-07",
        GROUP_ACC,
        "Cloud cover per patch, mean absolute error",
        0.08,
        0.05,
        "lower",
        model_value(["frame", "cloud_fraction_mae"], "cloud_fraction_mae"),
    ),
    Target("ACC-08", GROUP_ACC, "Expected calibration error", 0.08, 0.05, "lower", calibration),
    Target(
        "ACC-09",
        GROUP_ACC,
        "Spread over three seeds, cloud BOA (standard deviation)",
        0.02,
        0.01,
        "lower",
        seed_spread,
    ),
    Target(
        "IND-01",
        GROUP_IND,
        "Independent datasets evaluated",
        2,
        4,
        "higher",
        count_independent,
        target_text="4, from at least 3 sensors",
    ),
    Target(
        "IND-02",
        GROUP_IND,
        "Each independent Sentinel-2 dataset, cloud BOA",
        None,
        None,
        "report",
        not_available("no independent dataset evaluated yet"),
        minimum_text="above Sen2Cor on the same pixels",
        target_text="within 0.03 of the CloudSEN12+ test result",
    ),
    Target(
        "IND-03",
        GROUP_IND,
        "Each other-sensor dataset, cloud BOA",
        None,
        None,
        "report",
        not_available("no independent dataset evaluated yet"),
        minimum_text="above the dataset's operational mask, where one exists",
        target_text="within 0.05 of the CloudSEN12+ test result",
    ),
    Target(
        "IND-04",
        GROUP_IND,
        "Worst biome or surface class on any independent dataset, BOA",
        0.75,
        0.85,
        "higher",
        not_available("no independent dataset evaluated yet"),
    ),
    Target(
        "FRM-01",
        GROUP_FRM,
        "Useful frames wrongly discarded",
        0.02,
        0.01,
        "lower",
        frame_rate("false_discard_rate"),
    ),
    Target(
        "FRM-02",
        GROUP_FRM,
        "Cloudy frames detected",
        0.85,
        0.90,
        "higher",
        frame_rate("false_send_rate", invert=True),
    ),
    Target(
        "CMP-01",
        GROUP_CMP,
        "ONNX FP32 against PyTorch, argmax agreement",
        0.999,
        0.999,
        "higher",
        export_value("argmax"),
    ),
    Target(
        "CMP-02",
        GROUP_CMP,
        "FP16 against FP32, cloud BOA loss",
        0.005,
        0.002,
        "lower",
        export_value("fp16"),
    ),
    Target(
        "CMP-03",
        GROUP_CMP,
        "INT8 against FP32, cloud BOA loss",
        0.02,
        0.01,
        "lower",
        export_value("int8"),
    ),
    Target(
        "CMP-04",
        GROUP_CMP,
        "Flexible model against specialist, four bands, cloud BOA loss",
        0.01,
        None,
        "lower",
        flexible_vs_specialist,
        target_text="within the specialist's interval",
    ),
    Target(
        "CMP-05",
        GROUP_CMP,
        "Rescaling 0.5x to 2x, cloud BOA loss",
        0.04,
        0.02,
        "lower",
        rescaling_loss,
    ),
    Target(
        "CMP-06",
        GROUP_CMP,
        "Other sensors against Sentinel-2, cloud BOA loss",
        0.08,
        0.05,
        "lower",
        not_available("no other-sensor dataset evaluated yet"),
    ),
    Target(
        "CMP-07",
        GROUP_CMP,
        "Red, green and blue only, cloud BOA",
        None,
        None,
        "report",
        rgb_reported,
        minimum_text="reported",
        target_text="reported",
    ),
    Target(
        "OBD-01",
        GROUP_OBD,
        "Throughput, 512 x 512 tiles per second",
        20,
        40,
        "higher",
        jetson_value("throughput"),
    ),
    Target(
        "OBD-02",
        GROUP_OBD,
        "Latency per tile, INT8 or FP16, ms",
        50,
        25,
        "lower",
        jetson_value("latency"),
    ),
    Target(
        "OBD-03",
        GROUP_OBD,
        "Model file of the 1 M model, MB",
        4.0,
        1.5,
        "lower",
        export_value("fp32"),
        minimum_text="4 MB FP32",
        target_text="1.5 MB INT8",
    ),
    Target(
        "OBD-04",
        GROUP_OBD,
        "Memory during inference, GB",
        2,
        1,
        "lower",
        not_available("not measured by the Jetson scripts yet"),
    ),
    Target(
        "OBD-05",
        GROUP_OBD,
        "Board power during inference, W",
        25,
        15,
        "lower",
        jetson_value("power"),
    ),
    Target(
        "OBD-06",
        GROUP_OBD,
        "Same input, same output across runs",
        None,
        None,
        "report",
        not_available("not measured by the Jetson scripts yet"),
        minimum_text="bit identical per runtime",
    ),
    Target("STD-01", GROUP_STD, "Worst stratum, cloud BOA", 0.75, 0.85, "higher", worst_stratum),
    Target(
        "STD-02",
        GROUP_STD,
        "Invalid or out-of-domain input that ends in a discarded frame",
        0,
        0,
        "lower",
        failsafe,
    ),
    Target(
        "STD-03",
        GROUP_STD,
        "Requirements without a linked verification",
        0,
        0,
        "lower",
        requirements_unverified,
    ),
    Target(
        "STD-04",
        GROUP_STD,
        'Rows of the standards matrix with status "not read"',
        None,
        0,
        "lower",
        standards_not_read,
        minimum_text="reported",
    ),
)


# Evaluation ------------------------------------------------------------------


def status(value: float | None, bound: float | None, direction: str, strict: bool = False) -> str:
    if value is None or not math.isfinite(value):
        return NOT_MEASURED
    if bound is None:
        return "reported"
    if direction == "higher":
        return "met" if (value > bound if strict else value >= bound) else "not met"
    return "met" if value <= bound else "not met"


def evaluate(reports: Reports) -> list[dict[str, Any]]:
    rows = []
    for t in TARGETS:
        m = t.measure(reports) or Measurement(None)
        rows.append(
            {
                "target": t,
                "measurement": m,
                "minimum_status": status(m.value, t.minimum, t.direction, t.strict_minimum)
                if t.direction != "report"
                else ("reported" if m.value is not None else NOT_MEASURED),
                "target_status": status(m.value, t.target, t.direction)
                if t.direction != "report"
                else NOT_MEASURED,
            }
        )
    return rows


def _num(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4g}"


def render(rows: Sequence[dict[str, Any]], date: dt.date) -> str:
    headers = [
        "",
        "Target",
        "Minimum",
        "Target value",
        "Measured",
        "Interval",
        "Minimum",
        "Target",
        "Source",
    ]
    groups: dict[str, list[list[str]]] = {}
    for row in rows:
        t: Target = row["target"]
        m: Measurement = row["measurement"]
        minimum = t.minimum_text or (
            ("above " if t.strict_minimum else "") + _num(t.minimum)
            if t.minimum is not None
            else "n/a"
        )
        target = t.target_text or _num(t.target)
        interval = f"[{_num(m.low)}, {_num(m.high)}]" if m.low is not None else "n/a"
        measured = _num(m.value) + (f" ({m.note})" if m.note else "")
        groups.setdefault(t.group, []).append(
            [
                t.id,
                t.description,
                minimum,
                target,
                measured,
                interval,
                row["minimum_status"],
                row["target_status"],
                m.source or "n/a",
            ]
        )
    table = markdown_table(headers, [Group(title, rs) for title, rs in groups.items()])
    when = f"{date.day} {date:%B %Y}"
    return (
        header_block(
            "Acceptance",
            "in development",
            "Acceptance targets of milestone L2 against the measured values, built by "
            "`python -m tiefer_lab.acceptance` from the report files; do not edit it by hand. "
            "Targets are goals set by the founder, not predictions; a missed target is reported "
            "as missed.",
            "../docs/assets/header.png",
        )
        + "\n## Targets\n\n"
        + table
        + "\nPublished reference values of the dataset paper are not written here until they are "
        "checked against its tables (TODO(verify), https://doi.org/10.1038/s41597-022-01878-2).\n\n"
        + "## Basis of the on-board targets\n\n"
        + THROUGHPUT_BASIS
        + " The on-board targets are provisional and are reviewed after the first measurement.\n\n"
        + "---\n\n## Changelog\n\n"
        + f"- {when}: generated from {len(rows)} targets.\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.acceptance")
    parser.parse_args(argv)
    reports = load_reports(paths.reports_dir())
    rows = evaluate(reports)
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, dt.date.today()), encoding="utf-8")
    met = sum(r["target_status"] == "met" for r in rows)
    unmeasured = sum(r["minimum_status"] == NOT_MEASURED for r in rows)
    print(f"{len(rows)} targets: {met} target met, {unmeasured} not measured", flush=True)
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
