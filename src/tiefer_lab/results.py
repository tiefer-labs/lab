# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Build docs/RESULTS.md from the JSON report files, never from typed numbers.

    python -m tiefer_lab.results               # needs real reports in $TIEFER_REPORTS_DIR
    python -m tiefer_lab.results --placeholder # every value "not yet measured"

Reads `evaluation/*.json`, `export/*.json`, `jetson/*.json` and
`compute/*.json` under `$TIEFER_REPORTS_DIR`. Smoke reports (synthetic data
or the smoke configuration) are ignored. Without at least one real
evaluation report it refuses to run, unless `--placeholder` is given.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tiefer_lab.data.source import CLASS_NAMES
from tiefer_lab.tables import Group, header_block, markdown_table
from tiefer_lab.utils import paths

NOT_YET = "not yet measured"
DIGITS = 3


class ResultsError(RuntimeError):
    pass


@dataclass
class Report:
    path: Path
    data: dict[str, Any]

    @property
    def source(self) -> str:
        return f"`reports/{self.path.parent.name}/{self.path.name}`"

    @property
    def commit(self) -> str:
        git = self.data.get("provenance", {}).get("git", {})
        commit = git.get("commit") or self.data.get("git_commit") or "unknown"
        return f"`{str(commit)[:12]}`"

    @property
    def time(self) -> str:
        return str(self.data.get("provenance", {}).get("time", ""))


@dataclass
class Reports:
    evaluation: list[Report] = field(default_factory=list)
    export: list[Report] = field(default_factory=list)
    jetson: list[Report] = field(default_factory=list)
    compute: list[Report] = field(default_factory=list)
    skipped_smoke: int = 0


def load_reports(directory: Path) -> Reports:
    reports = Reports()
    for kind in ("evaluation", "export", "jetson", "compute"):
        for path in sorted((directory / kind).glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("smoke"):
                reports.skipped_smoke += 1
                continue
            if kind in ("evaluation", "export") and not data.get("provenance", {}).get("git"):
                raise ResultsError(f"{path.name} has no git provenance")
            getattr(reports, kind).append(Report(path, data))
    for items in (reports.evaluation, reports.export, reports.jetson):
        items.sort(key=lambda r: r.time)
    return reports


def fmt(value: Any, digits: int = DIGITS) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def with_interval(value: Any, interval: dict[str, Any] | None) -> str:
    if value is None:
        return "n/a"
    if not interval or interval.get("low") is None:
        return fmt(value)
    return f"{fmt(value)} [{fmt(interval['low'])}, {fmt(interval['high'])}]"


def _latest(reports: list[Report], split: str) -> Report | None:
    matching = [r for r in reports if r.data.get("split") == split]
    return matching[-1] if matching else None


# Sections ------------------------------------------------------------------


def summary(reports: Reports) -> list[str]:
    if not reports.evaluation:
        return [
            "No results have been measured yet.",
            "Training and evaluation run on CSC Roihu in Part B of milestone L1.",
            "Every value on this page is written by `python -m tiefer_lab.results` "
            "from report files.",
        ]
    main = _latest(reports.evaluation, "test") or reports.evaluation[-1]
    model = main.data["model"]
    t = model["decision_threshold"]
    fdr_interval = model.get("intervals", {}).get(f"false_discard_rate@{t:.2f}")
    lines = [
        f"On the {main.data['split']} split, the cloud filter has a mean IoU of "
        f"{with_interval(model['pixel']['mean_iou'], model.get('intervals', {}).get('mean_iou'))} "
        f"over {model['patches']} patches ({main.source}).",
        f"At a cloud threshold of {round(t * 100)} percent, its false discard rate is "
        f"{with_interval(model['false_discard_rate'], fdr_interval)}.",
    ]
    quant = reports.export[-1].data.get("quantisation", {}).get("val") if reports.export else None
    if quant:
        lines.append(
            f"INT8 quantisation changes the validation mean IoU by "
            f"{fmt(quant['change']['mean_iou_change'])} ({reports.export[-1].source})."
        )
    else:
        lines.append(f"INT8 quantisation is {NOT_YET}.")
    return lines


def environment_section(reports: Reports) -> str:
    rows = []
    for r in reports.evaluation:
        run = r.data.get("run", {}).get("provenance") or {}
        plat = run.get("platform", {})
        slurm = run.get("slurm", {})
        rows.append(
            [
                f"`{r.data['run_id']}`",
                str(plat.get("gpu", plat.get("device", "n/a"))),
                str(plat.get("machine", "n/a")),
                str(plat.get("libraries", {}).get("torch", "n/a")),
                str(slurm.get("partition", "n/a")),
                r.source,
                r.commit,
            ]
        )
    if not rows:
        rows = [[NOT_YET] * 7]
    return markdown_table(
        ["Training run", "Device", "CPU architecture", "PyTorch", "Partition", "Source", "Commit"],
        [Group("", rows)],
    )


def data_section(reports: Reports) -> str:
    rows = []
    for r in reports.evaluation:
        d = r.data.get("data", {})
        dataset = d.get("dataset") or {}
        rows.append(
            [
                r.data["split"],
                fmt(d.get("split_count")),
                f"`{dataset.get('revision', 'unknown')}`",
                r.source,
                r.commit,
            ]
        )
    if not rows:
        rows = [["validation"] + [NOT_YET] * 4, ["test"] + [NOT_YET] * 4]
    return markdown_table(
        ["Split", "Patches", "Dataset revision", "Source", "Commit"], [Group("", rows)]
    )


def model_section(reports: Reports) -> str:
    if reports.export:
        r = reports.export[-1]
        rows = [
            ["Parameters", fmt(r.data.get("parameters")), r.source, r.commit],
            [
                "Multiply-accumulates, 1 x 4 x 512 x 512",
                fmt(r.data.get("macs_1x4x512x512")),
                r.source,
                r.commit,
            ],
            ["ONNX opset", fmt(r.data.get("opset")), r.source, r.commit],
        ]
    else:
        rows = [
            ["Parameters", NOT_YET, NOT_YET, NOT_YET],
            ["Multiply-accumulates, 1 x 4 x 512 x 512", NOT_YET, NOT_YET, NOT_YET],
        ]
    return markdown_table(["", "Value", "Source", "Commit"], [Group("", rows)])


def _method_rows(r: Report) -> list[list[str]]:
    t = r.data["model"]["decision_threshold"]
    key = f"{t:.2f}"
    rows = []
    entries = [("Cloud filter", r.data["model"])]
    for name, values in r.data.get("baselines", {}).items():
        entries.append((name.replace("_", " "), values))
    for name, m in entries:
        intervals = m.get("intervals", {})
        rows.append(
            [
                name,
                with_interval(m["pixel"]["mean_iou"], intervals.get("mean_iou")),
                with_interval(m["false_discard_rate"], intervals.get(f"false_discard_rate@{key}")),
                with_interval(
                    m["frame"]["thresholds"][key]["decision_accuracy"],
                    intervals.get(f"decision_accuracy@{key}"),
                ),
                r.source,
                r.commit,
            ]
        )
    return rows


def comparison_section(reports: Reports) -> str:
    headers = [
        "",
        "Mean IoU",
        "False discard rate at 50 percent",
        "Decision accuracy at 50 percent",
        "Source",
        "Commit",
    ]
    groups = []
    for split in ("val", "test"):
        r = _latest(reports.evaluation, split)
        if r is not None:
            groups.append(
                Group(f"{'Validation' if split == 'val' else 'Test'} split", _method_rows(r))
            )
    if not groups:
        names = ["Cloud filter", "always send", "threshold rule"]
        groups = [
            Group(
                "Validation split",
                [[n, NOT_YET, NOT_YET, NOT_YET, NOT_YET, NOT_YET] for n in names],
            )
        ]
    return markdown_table(headers, groups)


def pixel_frame_section(reports: Reports) -> str:
    groups = []
    for split in ("val", "test"):
        r = _latest(reports.evaluation, split)
        if r is None:
            continue
        m = r.data["model"]
        intervals = m.get("intervals", {})

        def row(
            name: str, value: Any, key: str, r: Report = r, intervals: dict[str, Any] = intervals
        ) -> list[str]:
            return [name, with_interval(value, intervals.get(key)), r.source, r.commit]

        rows = [
            row(f"IoU, {name}", m["pixel"]["iou"][i], f"iou_class_{i}")
            for i, name in enumerate(CLASS_NAMES)
        ]
        rows.append(row("Overall accuracy", m["pixel"]["overall_accuracy"], "overall_accuracy"))
        rows.append(
            row(
                "Cloud fraction mean absolute error",
                m["frame"]["cloud_fraction_mae"],
                "cloud_fraction_mae",
            )
        )
        for key, values in sorted(m["frame"]["thresholds"].items()):
            pct = round(float(key) * 100)
            rows.append(
                row(
                    f"False discard rate at {pct} percent",
                    values["false_discard_rate"],
                    f"false_discard_rate@{key}",
                )
            )
            rows.append(
                row(
                    f"Decision accuracy at {pct} percent",
                    values["decision_accuracy"],
                    f"decision_accuracy@{key}",
                )
            )
        groups.append(Group(f"{'Validation' if split == 'val' else 'Test'} split", rows))
    if not groups:
        names = [f"IoU, {name}" for name in CLASS_NAMES]
        names += [f"False discard rate at {p} percent" for p in (30, 50, 70)]
        names += [f"Decision accuracy at {p} percent" for p in (30, 50, 70)]
        groups = [Group("Validation split", [[n, NOT_YET, NOT_YET, NOT_YET] for n in names])]
    return markdown_table(["", "Value [95 percent interval]", "Source", "Commit"], groups)


def quantisation_section(reports: Reports) -> str:
    rows = []
    for r in reports.export:
        for split, q in sorted(r.data.get("quantisation", {}).items()):
            c = q["change"]
            rows.append(
                [
                    f"`{r.data['run_id']}`, {split}",
                    fmt(c["mean_iou_fp32"]),
                    fmt(c["mean_iou_int8"]),
                    fmt(c["false_discard_rate_fp32"]),
                    fmt(c["false_discard_rate_int8"]),
                    r.source,
                    r.commit,
                ]
            )
    if not rows:
        rows = [[NOT_YET] * 7]
    headers = [
        "Run and split",
        "Mean IoU FP32",
        "Mean IoU INT8",
        "False discard rate FP32",
        "False discard rate INT8",
        "Source",
        "Commit",
    ]
    return markdown_table(headers, [Group("", rows)])


def hardware_section(reports: Reports) -> str:
    rows = []
    for r in reports.jetson:
        lat = r.data["latency"]
        rows.append(
            [
                f"{r.data.get('label')} ({r.data.get('device', {}).get('model', 'Jetson')})",
                f"{fmt(lat['p50_ms'], 2)} ms",
                f"{fmt(lat['p99_ms'], 2)} ms",
                fmt(r.data["throughput"]["tiles_per_second"], 1),
                f"{fmt(r.data['energy_per_tile_mj']['total'], 1)} mJ",
                r.source,
                r.commit,
            ]
        )
    if not rows:
        rows = [
            ["Jetson Orin, FP16"] + [NOT_YET] * 6,
            ["Jetson Orin, INT8"] + [NOT_YET] * 6,
        ]
    headers = [
        "Engine",
        "Latency p50",
        "Latency p99",
        "Tiles per second",
        "Energy per tile",
        "Source",
        "Commit",
    ]
    return markdown_table(headers, [Group("", rows)])


def compute_section(reports: Reports) -> str:
    rows = []
    for r in reports.compute:
        for step in r.data.get("steps", [])[:1]:
            rows.append(
                [
                    f"`{r.data.get('job_id')}` {step.get('JobName', '')}",
                    step.get("Partition", "n/a"),
                    step.get("Elapsed", "n/a"),
                    step.get("AllocTRES", "n/a"),
                    f"`reports/compute/{r.path.name}`",
                    "n/a",
                ]
            )
    if not rows:
        rows = [[NOT_YET] * 6]
    headers = ["Job", "Partition", "Elapsed", "Allocated resources", "Source", "Commit"]
    return markdown_table(headers, [Group("", rows)])


LIMITATIONS = [
    "Training data is Sentinel-2 at 10 m ground sampling; Tiefer's target sensors are very "
    "high resolution, where clouds and shadows look different.",
    "Only four bands are used (blue, green, red, near infrared); classic cloud algorithms "
    "also use shortwave infrared, which the target sensors lack.",
    "The data is public Level-1C top-of-atmosphere reflectance, not raw onboard data with "
    "its own calibration, noise and compression.",
    "No space environment effects are covered: radiation, vacuum and thermal behaviour of "
    "the onboard computer are not tested.",
    "Hardware measurements, when present, come from an NVIDIA Jetson Orin, which is "
    "flight-like reference hardware, not flight hardware.",
]

REPRODUCE = """```bash
python -m tiefer_lab.data.build_cache --split all
python -m tiefer_lab.train --config configs/l1_base.toml
python -m tiefer_lab.evaluate --run <run-id> --split val --baselines
python -m tiefer_lab.export --run <run-id>
python -m tiefer_lab.results
```

On CSC Roihu, the same steps run as Slurm jobs; see
[hpc/roihu/README.md](../hpc/roihu/README.md)."""


def render(reports: Reports, date: dt.date) -> str:
    when = f"{date.day} {date:%B %Y}"
    parts = [
        header_block(
            "Results",
            "in use" if reports.evaluation else "in development",
            "Results of milestone L1, the onboard cloud filter. This page is generated by "
            "`python -m tiefer_lab.results` from the report files in `reports/`; "
            "do not edit it by hand.",
            "assets/header.png",
        ),
        "## 1. Summary\n\n" + " ".join(summary(reports)) + "\n\n"
        f"Numbers are rounded to {DIGITS} decimals unless a unit says otherwise. Intervals are "
        "95 percent bootstrap intervals over patches. A value is written `n/a` where it is "
        "undefined and `not yet measured` where no report exists.",
        "## 2. Environment\n\n" + environment_section(reports),
        "## 3. Data\n\nCloudSEN12+, Level-1C, high quality labels, four bands; see "
        "[DATA.md](DATA.md).\n\n" + data_section(reports),
        "## 4. Model\n\n" + model_section(reports),
        "## 5. Baselines and model\n\nReference masks, when shipped with the dataset, use more "
        "spectral bands than the four used here, so the comparison favours them.\n\n"
        + comparison_section(reports),
        "## 6. Pixel and frame metrics\n\nThe false discard rate is the share of useful frames "
        "(true cloud fraction below the threshold) that would be kept on board.\n\n"
        + pixel_frame_section(reports),
        "## 7. Quantisation\n\n" + quantisation_section(reports),
        "## 8. Hardware\n\n" + hardware_section(reports),
        "## 9. Compute used\n\n" + compute_section(reports),
        "## 10. Limitations\n\n" + "\n".join(f"- {line}" for line in LIMITATIONS),
        "## 11. How to reproduce\n\n" + REPRODUCE,
        "## Changelog\n\n" + f"- {when}: generated from {len(reports.evaluation)} evaluation, "
        f"{len(reports.export)} export, {len(reports.jetson)} Jetson and "
        f"{len(reports.compute)} compute report files.",
    ]
    head, rest = parts[0], parts[1:]
    body = "\n\n---\n\n".join(p.rstrip("\n") for p in rest)
    return head.rstrip("\n") + "\n\n" + body + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.results", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("--placeholder", action="store_true", help="write the page with no results")
    parser.add_argument("--output", type=Path, default=None, help="default: docs/RESULTS.md")
    parser.add_argument("--date", type=dt.date.fromisoformat, default=None, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        reports = Reports() if args.placeholder else load_reports(paths.reports_dir())
    except ResultsError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    if not args.placeholder and not reports.evaluation:
        print(
            "error: no real evaluation reports in $TIEFER_REPORTS_DIR/evaluation "
            f"({reports.skipped_smoke} smoke reports ignored); refusing to write results. "
            "Use --placeholder for a page without results.",
            file=sys.stderr,
        )
        return 2
    output = args.output or paths.repo_root() / "docs" / "RESULTS.md"
    date = args.date or dt.datetime.now(dt.UTC).date()
    output.write_text(render(reports, date), encoding="utf-8")
    print(f"written: {paths.portable(output)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
