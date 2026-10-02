# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Build reports/experiments.md from the run folders: one row per run, nothing typed.

    python -m tiefer_lab.experiments

Reads `metadata.json`, `config.toml` and `metrics.jsonl` of every run in
`$TIEFER_RUNS_DIR`. Smoke and timing runs are left out. GPU hours are the
sum over the run's sessions of (end - start) x GPUs; a session without a
recorded end (for example a job killed at its time limit before it could
save) makes the total "unknown" rather than a guess.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tiefer_lab.config import load_config
from tiefer_lab.tables import Group, header_block, markdown_table
from tiefer_lab.utils import paths

REPORT = "experiments.md"


def _time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


def gpu_hours(meta: dict[str, Any]) -> float | None:
    total = 0.0
    sessions = meta.get("sessions") or []
    if not sessions:
        return None
    for session in sessions:
        if not session.get("end"):
            return None
        seconds = (_time(session["end"]) - _time(session["start"])).total_seconds()
        total += seconds / 3600.0 * int(session.get("gpus") or 0)
    return total


def _records(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "metrics.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def run_row(run_dir: Path) -> dict[str, Any] | None:
    meta_path = run_dir / "metadata.json"
    if not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("smoke") or meta.get("timing_run"):
        return None
    config = load_config(run_dir / "config.toml")
    records = _records(run_dir)
    best_epoch = meta.get("best_epoch")
    best = next((r for r in records if r.get("epoch") == best_epoch), {})
    jobs = [s.get("job_id") for s in meta.get("sessions", []) if s.get("job_id")]
    commit = (meta.get("provenance", {}).get("git", {}).get("commit") or "unknown")[:12]
    return {
        "run_id": str(meta.get("run_id", run_dir.name)),
        "config": config.name,
        "seed": meta.get("seed"),
        "commit": commit,
        "jobs": jobs,
        "status": meta.get("status"),
        "epochs": len(records),
        "best_epoch": best_epoch,
        "best_val_mean_iou": meta.get("best_val_mean_iou"),
        "by_band_set": best.get("val_mean_iou_by_band_set") or {},
        "gpu_hours": gpu_hours(meta),
        "parameters": meta.get("model", {}).get("parameters"),
    }


def collect(runs_dir: Path) -> list[dict[str, Any]]:
    rows = [run_row(d) for d in sorted(runs_dir.iterdir()) if d.is_dir()]
    return [r for r in rows if r is not None]


def _fmt(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render(rows: Sequence[dict[str, Any]], date: dt.date) -> str:
    headers = [
        "Run",
        "Config",
        "Seed",
        "Commit",
        "Jobs",
        "Status",
        "Epochs",
        "Best epoch",
        "Best val mean IoU",
        "Val mean IoU by band set",
        "Parameters",
        "GPU hours",
    ]
    table_rows = [
        [
            f"`{r['run_id']}`",
            r["config"],
            _fmt(r["seed"]),
            f"`{r['commit']}`",
            " ".join(map(str, r["jobs"])) or "none recorded",
            _fmt(r["status"]),
            _fmt(r["epochs"]),
            _fmt(r["best_epoch"]),
            _fmt(r["best_val_mean_iou"]),
            "; ".join(f"{k}: {_fmt(v)}" for k, v in r["by_band_set"].items()) or "n/a",
            _fmt(r["parameters"]),
            _fmt(r["gpu_hours"]),
        ]
        for r in rows
    ]
    total = sum(r["gpu_hours"] for r in rows if r["gpu_hours"] is not None)
    unknown = sum(1 for r in rows if r["gpu_hours"] is None)
    when = f"{date.day} {date:%B %Y}"
    body = markdown_table(headers, [Group("", table_rows)]) if rows else "No runs yet.\n"
    return (
        header_block(
            "Experiments",
            "in use" if rows else "in development",
            "Every training run, one row each, built by `python -m tiefer_lab.experiments` from "
            "the run folders; do not edit it by hand. Smoke and timing runs are left out.",
            "../docs/assets/header.png",
        )
        + "\n## Runs\n\n"
        + body
        + f"\nGPU hours in this table: {total:.2f}"
        + (f", plus {unknown} runs with unknown GPU hours" if unknown else "")
        + ".\n\n---\n\n## Changelog\n\n"
        + f"- {when}: generated from {len(rows)} run folders.\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.experiments")
    parser.parse_args(argv)
    rows = collect(paths.runs_dir())
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, dt.date.today()), encoding="utf-8")
    print(f"{len(rows)} runs: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
