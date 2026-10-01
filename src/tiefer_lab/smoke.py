# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The full local smoke pipeline on a tiny subset.

    python -m tiefer_lab.smoke [--source auto|cloudsen12|synthetic] [--device ...]

Steps: data cache, training with configs/smoke.toml (minutes on CPU),
evaluation on validation with the baselines, ONNX export with the check
against PyTorch, INT8 quantisation, the Jetson scripts in dry-run mode, and a
check that the results generator ignores smoke reports.

Everything is written to `$TIEFER_RUNS_DIR/smoke/` (its own data, runs and
reports folders), never to `data/` or `reports/`. Every report is marked
`"smoke": true`. Smoke outputs are never results.

`--source auto` uses real CloudSEN12+ patches when the dataset is reachable
and synthetic scenes otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tiefer_lab import evaluate, results, train
from tiefer_lab.data import build_cache, cache, source
from tiefer_lab.export import __main__ as export_cli
from tiefer_lab.utils import paths

SMOKE_CONFIG = Path("configs") / "smoke.toml"
SYNTHETIC_COUNTS = {"train": 32, "val": 8, "test": 8}
SYNTHETIC_PATCH = 384
REAL_CACHE = "cloudsen12-l1c-smoke"


class SmokeError(RuntimeError):
    pass


def _step(name: str) -> float:
    print(f"\n== smoke: {name}", flush=True)
    return time.monotonic()


def _isolate(base: Path) -> dict[str, Path]:
    """Point every TIEFER_* location at the smoke folder for this process."""
    dirs = {
        paths.DATA_ENV: base / "data",
        paths.RUNS_ENV: base / "runs",
        paths.REPORTS_ENV: base / "reports",
    }
    for env, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[env] = str(path)
    return dirs


def build_data(source_name: str) -> tuple[str, str]:
    """Build the smoke cache; returns (cache name, source actually used)."""
    if source_name == "auto":
        source_name = "cloudsen12" if source.dataset_revision() else "synthetic"
        print(f"dataset reachable: {source_name == 'cloudsen12'}; using {source_name}", flush=True)
    if source_name == "synthetic":
        directory = cache.cache_dir(build_cache.SYNTHETIC_NAME)
        for split, count in SYNTHETIC_COUNTS.items():
            build_cache.build_synthetic_split(directory, split, count, SYNTHETIC_PATCH, seed=0)
        return build_cache.SYNTHETIC_NAME, "synthetic"
    revision = source.dataset_revision()
    directory = cache.cache_dir(REAL_CACHE)
    for split, count in SYNTHETIC_COUNTS.items():
        build_cache.build_real_split(directory, split, count, [source.TACO_NAME_L1C], revision)
    return REAL_CACHE, "cloudsen12"


def jetson_dry_runs(export_dir: Path) -> list[dict[str, Any]]:
    root = paths.repo_root() / "jetson"
    commands = [
        ["bash", str(root / "device_info.sh"), "--dry-run"],
        [
            "bash",
            str(root / "build_engines.sh"),
            "--fp32",
            str(export_dir / export_cli.FILES["fp32"]),
            "--int8",
            str(export_dir / export_cli.FILES["int8"]),
            "--out",
            str(export_dir / "engines"),
            "--dry-run",
        ],
        [
            sys.executable,
            str(root / "bench.py"),
            "--engine",
            "cloud_filter_fp16.engine",
            "--label",
            "fp16",
            "--dry-run",
        ],
        [sys.executable, str(root / "power.py"), "--dry-run"],
    ]
    outcomes = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout.rstrip(), flush=True)
        if result.returncode != 0:
            raise SmokeError(f"{Path(command[1]).name} failed: {result.stderr.strip()}")
        outcomes.append({"script": Path(command[1]).name, "exit_code": result.returncode})
    return outcomes


def run(source_name: str, device: str) -> dict[str, Any]:
    started = time.monotonic()
    base = paths.runs_dir() / "smoke"
    dirs = _isolate(base)
    summary: dict[str, Any] = {"smoke": True, "steps": {}}

    t = _step("data cache")
    cache_name, used = build_data(source_name)
    summary["data_source"] = used
    summary["steps"]["data"] = round(time.monotonic() - t, 1)

    t = _step("training")
    run_id = f"smoke-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
    args = ["--config", str(paths.repo_root() / SMOKE_CONFIG), "--cache-name", cache_name]
    args += ["--run-id", run_id, "--device", device]
    if used == "synthetic":
        args.append("--allow-synthetic")
    if train.main(args) != 0:
        raise SmokeError("training failed")
    summary["steps"]["train"] = round(time.monotonic() - t, 1)

    t = _step("evaluation on validation with baselines")
    eval_args = ["--run", run_id, "--split", "val", "--baselines", "--device", device]
    if used == "synthetic":
        eval_args.append("--allow-synthetic")
    if evaluate.main(eval_args) != 0:
        raise SmokeError("evaluation failed")
    report = json.loads((dirs[paths.REPORTS_ENV] / "evaluation" / f"{run_id}_val.json").read_text())
    summary["steps"]["evaluate"] = round(time.monotonic() - t, 1)

    t = _step("ONNX export, check against PyTorch, INT8 quantisation")
    export_args = ["--run", run_id] + (["--allow-synthetic"] if used == "synthetic" else [])
    if export_cli.main(export_args) != 0:
        raise SmokeError("export failed")
    export_report = json.loads((dirs[paths.REPORTS_ENV] / "export" / f"{run_id}.json").read_text())
    summary["steps"]["export"] = round(time.monotonic() - t, 1)

    t = _step("Jetson scripts in dry-run mode")
    summary["jetson_dry_runs"] = jetson_dry_runs(dirs[paths.RUNS_ENV] / run_id / "export")
    summary["steps"]["jetson"] = round(time.monotonic() - t, 1)

    t = _step("results generator ignores smoke reports")
    code = results.main(["--output", str(base / "RESULTS.smoke.md")])
    if code == 0:
        raise SmokeError("the results generator accepted smoke reports")
    summary["results_generator_refused"] = True
    summary["steps"]["results"] = round(time.monotonic() - t, 1)

    summary.update(
        {
            "run_id": run_id,
            "all_reports_marked_smoke": bool(report["smoke"] and export_report["smoke"]),
            "export_files": sorted(f["name"] for f in export_report["files"].values()),
            "fp32_argmax_agreement": export_report["verification"]["fp32"]["argmax_agreement"],
            "seconds": round(time.monotonic() - started, 1),
        }
    )
    (base / "smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.smoke", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("--source", default="auto", choices=["auto", "cloudsen12", "synthetic"])
    parser.add_argument("--device", default="auto")
    args = parser.parse_args(argv)
    try:
        summary = run(args.source, args.device)
    except (SmokeError, train.TrainingError, cache.CacheError, source.DataSourceError) as err:
        print(f"smoke run failed: {err}", file=sys.stderr)
        return 1
    print("\n== smoke run finished (outputs are labelled smoke and are never results)")
    print(
        json.dumps({k: summary[k] for k in ("data_source", "run_id", "seconds", "steps")}, indent=2)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
