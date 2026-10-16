# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Load the JSON report files under `$TIEFER_REPORTS_DIR`.

Reads `evaluation/*.json`, `export/*.json`, `jetson/*.json` and
`compute/*.json`. Smoke reports (synthetic data or the smoke configuration)
are counted and left out. An evaluation or export report without git
provenance is refused.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ReportError(RuntimeError):
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
                raise ReportError(f"{path.name} has no git provenance")
            getattr(reports, kind).append(Report(path, data))
    for items in (reports.evaluation, reports.export, reports.jetson):
        items.sort(key=lambda r: r.time)
    return reports


NOT_RECORDED = "not recorded"


def evaluation_device(report: Report) -> str:
    """The device an evaluation report was computed on: cpu, cuda, mps or not recorded."""
    return str(report.data.get("evaluation_device") or NOT_RECORDED)


def require_one_device(reports: Reports) -> str | None:
    """The one device of every evaluation report, or a ReportError naming the mix.

    A table compares values computed on one device only: the CPU evaluates in fp32,
    a GPU with bf16 or fp16 autocast, so two rows from different devices could
    differ by the device and not by the model. Every reported evaluation runs on
    the CPU (hpc/roihu/plan.md); a report from another device is evaluated again
    with hpc/roihu/evaluate_cpu.sbatch.
    """
    by_device: dict[str, list[str]] = {}
    for report in reports.evaluation:
        by_device.setdefault(evaluation_device(report), []).append(report.path.name)
    if len(by_device) > 1:
        listed = "; ".join(f"{d}: {', '.join(sorted(n))}" for d, n in sorted(by_device.items()))
        raise ReportError(
            "evaluation reports from different devices cannot share one table, because the "
            "CPU evaluates in fp32 and a GPU with mixed precision, so rows could differ by the "
            f"device and not by the model ({listed}); evaluate every run again on the CPU "
            "with hpc/roihu/evaluate_cpu.sbatch"
        )
    return next(iter(by_device), None)
