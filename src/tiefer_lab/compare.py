# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""One comparison of every model and algorithm, from the report files only.

    python -m tiefer_lab.compare [--split val|test] [--source <dataset>]

Writes `reports/comparison.md`: one row per model (run and band set) and per
baseline or reference algorithm, scored by this repository on the same split
and the same pixels, with the same metrics, followed by a cost block. Rows
are grouped by split, data source and perturbation; a group whose rows were
scored on different numbers of patches says so instead of comparing them.

It never contains a published value of another system: those stay in
docs/LANDSCAPE.md, section 4. A reference that has no shadow class has `n/a`
for the shadow and valid problems; a value that no report holds is
`not measured`. A dataset or a reference mask refused by the maintainer's
licence decision has no row.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from tiefer_lab import paper_models
from tiefer_lab.reports import Report, Reports, load_reports
from tiefer_lab.tables import Group, header_block, markdown_table
from tiefer_lab.utils import paths

REPORT = "comparison.md"
NOT_MEASURED = "not measured"
NA = "n/a"

# ONNX operators of docs/SPEC.md, section 4, as node types (ReLU6 exports as
# Clip and bilinear upsampling as Resize); INT8 files add the explicit
# quantisation nodes that TensorRT reads.
ALLOWED_OPERATORS = frozenset(
    {
        "Conv",
        "ConvTranspose",
        "BatchNormalization",
        "Relu",
        "Clip",
        "MaxPool",
        "AveragePool",
        "Resize",
        "Concat",
        "Add",
        "Constant",
    }
)
QDQ_OPERATORS = frozenset({"QuantizeLinear", "DequantizeLinear"})


@dataclass(frozen=True)
class Row:
    """One model or algorithm in one group."""

    name: str
    kind: str  # "model" or "baseline"
    scores: dict[str, Any]
    report: Report
    binary_only: bool = False


def _num(value: Any) -> str:
    if value is None:
        return NOT_MEASURED
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{float(value):.3f}"


def _interval(value: Any, interval: dict[str, Any] | None) -> str:
    text = _num(value)
    if value is None or not interval or interval.get("low") is None:
        return text
    return f"{text} [{float(interval['low']):.3f}, {float(interval['high']):.3f}]"


def _get(node: Any, *keys: Any) -> Any:
    for key in keys:
        if isinstance(node, dict):
            node = node.get(key)
        elif isinstance(node, list) and isinstance(key, int) and 0 <= key < len(node):
            node = node[key]
        else:
            return None
    return node


def _group_key(r: Report) -> tuple[str, str, str]:
    return (
        str(r.data.get("split")),
        str(_get(r.data, "data", "source") or "cloudsen12"),
        str(r.data.get("perturbation") or "none"),
    )


def _model_name(r: Report) -> str:
    bands = r.data.get("band_set") or []
    seed = _get(r.data, "run", "seed")
    name = str(_get(r.data, "config", "name") or r.data.get("run_id"))
    seed_text = f" s{seed}" if seed is not None else ""
    return f"{name}{seed_text} ({','.join(bands)})" if bands else f"{name}{seed_text}"


def collect_rows(reports: Reports) -> dict[tuple[str, str, str], list[Row]]:
    """Models from every evaluation report, baselines once per group."""
    groups: dict[tuple[str, str, str], list[Row]] = {}
    seen_baselines: dict[tuple[str, str, str], set[str]] = {}
    for r in reports.evaluation:
        key = _group_key(r)
        # A source refused by a licence decision has no row (data/source.py).
        if paper_models.declined_source(key[1]):
            continue
        rows = groups.setdefault(key, [])
        rows.append(Row(_model_name(r), "model", r.data.get("model") or {}, r))
        for name, block in (r.data.get("baselines") or {}).items():
            if name in seen_baselines.setdefault(key, set()) or paper_models.declined_mask(name):
                continue
            seen_baselines[key].add(name)
            rows.append(Row(name, "baseline", block, r, binary_only="pixel" not in block))
    return groups


def _patches(row: Row) -> Any:
    return row.scores.get("patches")


def _binary_cells(row: Row, problem: str) -> list[str]:
    if row.binary_only and problem != "cloud":
        return [NA] * 4
    block = _get(row.scores, "binary", problem)
    if block is None and problem == "valid":
        block = _get(row.scores, "paper", "valid")
        return [_num(_get(block, "median_boa")), NOT_MEASURED, NOT_MEASURED, NOT_MEASURED]
    intervals = _get(block, "intervals") or {}
    return [
        _interval(_get(block, f"median_{m}"), intervals.get(f"median_{m}"))
        for m in ("boa", "pa", "ua", "oa")
    ]


def _share_cells(row: Row, problem: str, measure: str) -> list[str]:
    if row.binary_only and problem != "cloud":
        return [NA] * 3
    shares = _get(row.scores, "paper", problem, f"{measure}_shares")
    return [_num(_get(shares, k)) for k in ("low", "middle", "high")]


def _pixel_cells(row: Row) -> list[str]:
    if row.binary_only:
        return [NA] * 7
    pixel = row.scores.get("pixel") or {}
    iou = pixel.get("iou") or [None] * 4
    ece = _get(row.report.data, "calibration", "ece") if row.kind == "model" else None
    return [
        _interval(pixel.get("mean_iou"), _get(row.scores, "intervals", "mean_iou")),
        *(_num(v) for v in iou[:4]),
        f"{_num(_get(pixel, 'producers_accuracy', 2))} / {_num(_get(pixel, 'users_accuracy', 2))}",
        _num(ece) if row.kind == "model" else NA,
    ]


def _frame_cells(row: Row) -> list[str]:
    if row.binary_only:
        return [NA] * 7
    frame = row.scores.get("frame") or {}
    t = frame.get("thresholds") or {}
    sweep = _get(row.scores, "frame_sweep", "lowest_false_send_rate_at_false_discard_rate") or {}
    return [
        _num(frame.get("cloud_fraction_mae")),
        _num(_get(t, "0.30", "false_discard_rate")),
        _num(_get(t, "0.50", "false_discard_rate")),
        _num(_get(t, "0.50", "false_send_rate")),
        f"{_num(_get(t, '0.70', 'false_discard_rate'))} / "
        f"{_num(_get(t, '0.70', 'decision_accuracy'))}",
        _num(_get(sweep, "0.01", "false_send_rate")),
        _num(_get(sweep, "0.02", "false_send_rate")),
    ]


def _export_for(reports: Reports, run_id: str, bands: Sequence[str]) -> Report | None:
    for r in reversed(reports.export):
        if r.data.get("run_id") == run_id and set(r.data.get("band_set") or []) == set(bands):
            return r
    return None


def _jetson_for(reports: Reports, run_id: str) -> list[Report]:
    return [r for r in reports.jetson if r.data.get("run_id") == run_id]


def operators_allowed(export: dict[str, Any]) -> bool | None:
    """Whether every ONNX file of an export uses only the allowed operators."""
    ops = export.get("operators") or {}
    if not ops:
        return None
    for name, types in ops.items():
        allowed = ALLOWED_OPERATORS | (QDQ_OPERATORS if name == "int8" else frozenset())
        if not set(types) <= allowed:
            return False
    return True


def _cost_cells(row: Row, reports: Reports) -> list[str]:
    if row.kind != "model":
        return ["see docs/LANDSCAPE.md, section 4", *([NA] * 6)]
    data = row.report.data
    bands = data.get("band_set") or []
    model = _get(data, "run", "model") or {}
    export = _export_for(reports, str(data.get("run_id")), bands)
    files = (export.data.get("files") or {}) if export else {}
    jetson = _jetson_for(reports, str(data.get("run_id")))
    latency = min(
        (v for r in jetson if (v := _get(r.data, "latency", "mean_ms")) is not None),
        default=None,
    )
    return [
        str(len(bands)) if bands else NOT_MEASURED,
        _num(model.get("parameters")),
        _num(model.get("macs_512x512")),
        " / ".join(_num(_get(files, k, "bytes")) for k in ("fp32", "fp16", "int8")),
        _num(operators_allowed(export.data)) if export else NOT_MEASURED,
        f"{latency:.3f} ms" if latency is not None else NOT_MEASURED,
        export.source if export else NOT_MEASURED,
    ]


def _same_pixels(rows: Sequence[Row]) -> str:
    counts = sorted({p for r in rows if (p := _patches(r)) is not None})
    if len(counts) <= 1:
        return f"every row is scored on the same {counts[0] if counts else 0:,} patches"
    return (
        "rows were scored on different numbers of patches "
        f"({', '.join(f'{c:,}' for c in counts)}); compare only rows with the same count"
    )


def render(reports: Reports, date: dt.date, split: str | None = None) -> str:
    groups = collect_rows(reports)
    parts = [
        header_block(
            "Comparison",
            "in development",
            "Every model and algorithm scored by this repository, row by row on the same split "
            "and pixels, built by `python -m tiefer_lab.compare` from the report files; do not "
            "edit it by hand. Published values of other systems are not on this page; they are "
            "in docs/LANDSCAPE.md, section 4.",
            "../docs/assets/header.png",
        )
    ]
    if not groups:
        parts.append("\n## 1. Rows\n\nNo evaluation report is in `reports/evaluation/` yet.\n")
    section = 0
    for (group_split, source, perturbation), rows in sorted(groups.items()):
        if split is not None and group_split != split:
            continue
        section += 1
        title = f"{source}, {group_split} split, perturbation {perturbation}"
        sources = sorted({r.report.source for r in rows})
        blocks = [
            f"\n## {section}. {title}\n",
            f"Rounded to 3 decimals, half up; intervals are 95 percent bootstrap intervals. "
            f"{_same_pixels(rows)}. Reports: {', '.join(sources)}.\n",
        ]
        sub = 0
        for problem in ("cloud", "shadow", "valid"):
            table = markdown_table(
                ["", "Kind", "Patches", "BOA", "PA", "UA", "OA"],
                [
                    Group(
                        "",
                        [
                            [r.name, r.kind, _num(_patches(r)), *_binary_cells(r, problem)]
                            for r in rows
                        ],
                    )
                ],
            )
            sub += 1
            blocks.append(f"\n### {section}.{sub} {problem.capitalize()} problem\n\n")
            blocks.append(table + "\n")
        shares = markdown_table(
            ["", "Problem", "PA low", "PA middle", "PA high", "UA low", "UA middle", "UA high"],
            [
                Group(
                    "",
                    [
                        [
                            r.name,
                            problem,
                            *_share_cells(r, problem, "pa"),
                            *_share_cells(r, problem, "ua"),
                        ]
                        for r in rows
                        for problem in ("cloud", "shadow")
                    ],
                )
            ],
        )
        pixel = markdown_table(
            [
                "",
                "Mean IoU",
                "IoU clear",
                "IoU thick",
                "IoU thin",
                "IoU shadow",
                "Thin PA / UA",
                "ECE",
            ],
            [Group("", [[r.name, *_pixel_cells(r)] for r in rows])],
        )
        frame = markdown_table(
            [
                "",
                "Fraction MAE",
                "FDR 0.3",
                "FDR 0.5",
                "FSR 0.5",
                "FDR / accuracy 0.7",
                "FSR at FDR 0.01",
                "FSR at FDR 0.02",
            ],
            [Group("", [[r.name, *_frame_cells(r)] for r in rows])],
        )
        cost = markdown_table(
            [
                "",
                "Bands",
                "Parameters",
                "MACs per 512 x 512",
                "Bytes FP32 / FP16 / INT8",
                "Operators allowed",
                "Jetson latency",
                "Export report",
            ],
            [Group("", [[r.name, *_cost_cells(r, reports)] for r in rows])],
        )
        for heading, table in (
            ("Paper summary: share of patches with PA or UA low, middle, high", shares),
            ("Pixel metrics", pixel),
            ("Frame metrics (FDR false discard rate, FSR false send rate)", frame),
            ("Cost", cost),
        ):
            sub += 1
            blocks.append(f"\n### {section}.{sub} {heading}\n\n{table}\n")
        parts.append("".join(blocks))
    when = f"{date.day} {date:%B %Y}"
    parts.append(
        "\nJetson throughput and power, and the latency of a run without a Jetson report, are "
        "`not measured` until a report from `jetson/bench.py --run-id` exists.\n"
        f"\n---\n\n## Changelog\n\n- {when}: generated from "
        f"{len(reports.evaluation)} evaluation reports.\n"
    )
    return "".join(parts)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.compare")
    parser.add_argument("--split", choices=["val", "test", "all"], default=None)
    args = parser.parse_args(argv)
    reports = load_reports(paths.reports_dir())
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(reports, dt.date.today(), args.split), encoding="utf-8")
    print(f"{len(reports.evaluation)} evaluation reports", flush=True)
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
