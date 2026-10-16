# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Several training runs on one reserved GPU, the packing measurement and time limits.

    python -m tiefer_lab.packed run <entry> [<entry> ...] [--device auto] [--timing N]
    python -m tiefer_lab.packed report --config <config> --job <job-id> [--samples <csv>]
    python -m tiefer_lab.packed time-limit --report <packing report> --runs N [--epochs E]

An entry is `<config>@<seed>` for a new run, or `resume:<run-id>` to continue one.

`run` starts every entry as its own `python -m tiefer_lab.train` process, at
the same time, on the job's one GPU: each with its own seed, run folder and log
(`<log dir>/<config>-seed<N>.log`). Each run is exactly what it would be alone
(same config, seed handling and metadata), plus `runs_per_gpu` in its
metadata; TIEFER_RUNS_PER_GPU divides the job's cores and memory between the
runs (`tiefer_lab.utils.devices.cores_per_run`, `tiefer_lab.data.cache`).
SIGUSR1 and SIGTERM are passed to every run, which saves last.pt and stops.
The exit status is 0 only when every run ends with status 0. A job that ends
early releases its reservation and is billed on its runtime.

`run --timing N` is the timing step: N runs of one config (seeds 0 to N-1),
each one epoch cut to TIMING_STEPS steps, then validation, marked as timing
runs (never results). hpc/roihu/timing_packed.sbatch runs it with 1, 2, 3 and 4
runs per GPU while nvidia-smi samples the GPU.

`report` reads those timing runs and the samples and writes
`reports/timing/packing_<config>.json`: per packing, the full epoch time of
the slowest run, the data wait share, the peak GPU memory, the mean GPU
utilisation, the slowdown against one run alone and the epochs per GPU-hour.
The chosen packing has the most epochs per GPU-hour among those whose runs all
finished and whose slowest run takes at most MAX_SLOWDOWN times its time alone.

`time-limit` turns a report into the time limit of a packed training job:
epochs x the slowest full epoch time x (1 + TIME_MARGIN), plus the measured data
loading time and STARTUP_SECONDS, never a fixed large value.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any

from tiefer_lab.data import cache
from tiefer_lab.utils import paths

TIMING_STEPS = 50
# The slowest of the packed runs may take at most this many times its time alone.
MAX_SLOWDOWN = 2.0
# Margin on the time limit of a packed training job, over the timing report. GPU time is
# billed on the runtime, so the margin costs nothing, while a run stopped at its limit
# loses the epoch it was in and needs another job (maintainer decision of 16 October 2026).
TIME_MARGIN = 0.5
# Module setup, cache staging and the first checkpoint, on top of the measured data load.
STARTUP_SECONDS = 600
PACKINGS = (1, 2, 3, 4)
FORWARDED = (signal.SIGUSR1, signal.SIGTERM)
REPORT_DIR = "timing"


class PackingError(ValueError):
    """An entry, a report or a time limit cannot be used."""


@dataclass(frozen=True)
class Entry:
    """One run of a packed job: a config with a seed, or a run to resume."""

    config: str | None
    seed: int | None
    resume: str | None

    @classmethod
    def parse(cls, text: str) -> Entry:
        if text.startswith("resume:"):
            run_id = text.removeprefix("resume:")
            if not run_id:
                raise PackingError("resume: needs a run ID")
            return cls(None, None, run_id)
        config, sep, seed = text.rpartition("@")
        if not sep or not config or not seed.isdigit():
            raise PackingError(f"an entry is <config>@<seed> or resume:<run-id>, got {text!r}")
        return cls(config, int(seed), None)

    @property
    def label(self) -> str:
        if self.resume is not None:
            return self.resume
        return f"{Path(self.config or '').stem}-seed{self.seed}"

    def train_args(self) -> list[str]:
        if self.resume is not None:
            return ["--resume", self.resume]
        return ["--config", str(self.config), "--seed", str(self.seed)]


def parse_entries(texts: Sequence[str]) -> list[Entry]:
    entries = [Entry.parse(t) for t in texts]
    labels = [e.label for e in entries]
    if not entries:
        raise PackingError("no entry")
    if len(set(labels)) != len(labels):
        raise PackingError(f"the same run twice in one job: {labels}")
    return entries


def launch(
    entries: Sequence[Entry],
    log_dir: Path,
    extra: Sequence[str] = (),
    run_ids: Sequence[str | None] | None = None,
) -> list[int]:
    """Start every entry at once on this job's GPU; return their exit codes."""
    log_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, cache.RUNS_PER_GPU_ENV: str(len(entries))}
    processes: list[subprocess.Popen[bytes]] = []
    logs = []
    ids = list(run_ids) if run_ids is not None else [None] * len(entries)

    def forward(signum: int, frame: FrameType | None) -> None:
        for p in processes:
            if p.poll() is None:
                p.send_signal(signum)

    previous = {s: signal.signal(s, forward) for s in FORWARDED}
    try:
        for entry, run_id in zip(entries, ids, strict=True):
            command = [sys.executable, "-m", "tiefer_lab.train", *entry.train_args(), *extra]
            if run_id is not None:
                command += ["--run-id", run_id]
            log = (log_dir / f"{entry.label}.log").open("wb")
            logs.append(log)
            processes.append(
                subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
            )
            print(f"started {entry.label} ({len(entries)} runs per GPU)", flush=True)
        codes = [p.wait() for p in processes]
    finally:
        for s, handler in previous.items():
            signal.signal(s, handler)
        for log in logs:
            log.close()
    for entry, code in zip(entries, codes, strict=True):
        print(f"{entry.label}: exit {code}", flush=True)
    return codes


def timing_run_id(config: str, runs: int, seed: int, job: str) -> str:
    return f"timing-{Path(config).stem}-x{runs}-seed{seed}-{job}"


# Report ------------------------------------------------------------------------


def _samples(path: Path | None) -> list[tuple[float, float, float]]:
    """nvidia-smi samples: (time, utilisation percent, memory used MiB)."""
    if path is None or not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            continue
        try:
            stamp = dt.datetime.strptime(parts[0], "%Y/%m/%d %H:%M:%S.%f").timestamp()
            out.append((stamp, float(parts[1]), float(parts[2])))
        except ValueError:
            continue
    return out


def _run_summary(run_dir: Path) -> dict[str, Any] | None:
    meta_path, metrics_path = run_dir / "metadata.json", run_dir / "metrics.jsonl"
    if not meta_path.is_file() or not metrics_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    lines = metrics_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    first = json.loads(lines[0])
    train_seconds = float(first.get("train_seconds") or 0.0)
    return {
        "run_id": run_dir.name,
        "status": meta.get("status"),
        "full_epoch_seconds": first.get("full_epoch_seconds"),
        "train_seconds": train_seconds,
        "data_wait_seconds": first.get("data_wait_seconds"),
        "data_wait_share": (
            round(float(first["data_wait_seconds"]) / train_seconds, 3)
            if first.get("data_wait_seconds") is not None and train_seconds > 0
            else None
        ),
        "gpu_memory_peak_bytes": first.get("gpu_memory_peak_bytes"),
        "ready_seconds": meta.get("data", {}).get("ready_seconds"),
        "start": meta.get("start_time"),
        "end": meta.get("end_time"),
    }


def _stamp(text: str | None) -> float | None:
    return dt.datetime.fromisoformat(text).timestamp() if text else None


def packing_report(
    config: str, job: str, samples: Path | None = None, runs_dir: Path | None = None
) -> dict[str, Any]:
    runs_dir = runs_dir or paths.runs_dir()
    gpu = _samples(samples)
    rows: dict[str, Any] = {}
    for n in PACKINGS:
        runs = [_run_summary(runs_dir / timing_run_id(config, n, s, job)) for s in range(n)]
        found = [r for r in runs if r is not None]
        complete = len(found) == n and all(
            r["status"] in ("completed", "early_stopped") and r["full_epoch_seconds"] for r in found
        )
        row: dict[str, Any] = {"runs": found, "complete": complete}
        if complete:
            slowest = max(float(r["full_epoch_seconds"]) for r in found)
            starts = [_stamp(r["start"]) for r in found]
            ends = [_stamp(r["end"]) for r in found]
            window = [
                g
                for g in gpu
                if None not in starts + ends
                and min(s for s in starts if s is not None) <= g[0]
                and g[0] <= max(e for e in ends if e is not None)
            ]
            row.update(
                {
                    "full_epoch_seconds_slowest": slowest,
                    "epochs_per_gpu_hour": round(n * 3600.0 / slowest, 3),
                    "data_wait_share_max": max(
                        (r["data_wait_share"] for r in found if r["data_wait_share"] is not None),
                        default=None,
                    ),
                    "gpu_memory_peak_bytes_sum": sum(
                        r["gpu_memory_peak_bytes"] or 0 for r in found
                    ),
                    "gpu_utilisation_mean": (
                        round(sum(g[1] for g in window) / len(window), 1) if window else None
                    ),
                    "gpu_memory_used_mib_max": max((g[2] for g in window), default=None),
                    "ready_seconds_max": max(float(r["ready_seconds"] or 0) for r in found),
                }
            )
        rows[str(n)] = row
    alone = rows["1"].get("full_epoch_seconds_slowest")
    eligible = []
    for n in PACKINGS:
        row = rows[str(n)]
        if row["complete"] and alone:
            row["slowdown"] = round(row["full_epoch_seconds_slowest"] / alone, 3)
            if row["slowdown"] <= MAX_SLOWDOWN:
                eligible.append(n)
    chosen = max(eligible, key=lambda n: (rows[str(n)]["epochs_per_gpu_hour"], -n), default=None)
    return {
        "config": Path(config).stem,
        "job": job,
        "timing_steps": TIMING_STEPS,
        "max_slowdown": MAX_SLOWDOWN,
        "packings": rows,
        "chosen_runs_per_gpu": chosen,
        "rule": (
            "the most epochs per GPU-hour among the packings whose runs all finished and "
            f"whose slowest run takes at most {MAX_SLOWDOWN} times its time alone"
        ),
        "smoke": False,
        "timing_run": True,
    }


def time_limit(report: dict[str, Any], runs: int, epochs: int | None = None) -> str:
    """The time limit of a packed job, HH:MM:SS, from a packing report."""
    row = report["packings"].get(str(runs))
    if not row or not row.get("complete"):
        raise PackingError(f"the report has no complete timing with {runs} runs per GPU")
    if epochs is None:
        raise PackingError("give --epochs (train.epochs of the config)")
    seconds = (
        epochs * float(row["full_epoch_seconds_slowest"]) * (1 + TIME_MARGIN)
        + float(row.get("ready_seconds_max") or 0)
        + STARTUP_SECONDS
    )
    total = math.ceil(seconds / 60) * 60
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:00"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.packed")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("entries", nargs="+")
    run.add_argument("--device", default="auto")
    run.add_argument("--log-dir", type=Path)
    run.add_argument("--timing", type=int, choices=PACKINGS, help="timing step with N runs")
    run.add_argument("--job", default=os.environ.get("SLURM_JOB_ID", "local"))
    run.add_argument("--train-arg", action="append", default=[], help=argparse.SUPPRESS)
    rep = sub.add_parser("report")
    rep.add_argument("--config", required=True)
    rep.add_argument("--job", required=True)
    rep.add_argument("--samples", type=Path)
    lim = sub.add_parser("time-limit")
    lim.add_argument("--report", type=Path, required=True)
    lim.add_argument("--runs", type=int, required=True)
    lim.add_argument("--epochs", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            extra = ["--device", args.device, *args.train_arg]
            run_ids: list[str | None] | None = None
            texts = list(args.entries)
            if args.timing:
                if len(texts) != 1 or "@" in texts[0] or texts[0].startswith("resume:"):
                    raise PackingError("--timing takes one config")
                config = texts[0]
                texts = [f"{config}@{s}" for s in range(args.timing)]
                run_ids = [
                    timing_run_id(config, args.timing, s, args.job) for s in range(args.timing)
                ]
                extra += ["--epochs", "1", "--max-steps-per-epoch", str(TIMING_STEPS)]
            entries = parse_entries(texts)
            log_dir = args.log_dir or paths.runs_dir() / "slurm" / f"packed-{args.job}"
            codes = launch(entries, log_dir, extra, run_ids)
            return 0 if all(c == 0 for c in codes) else 1
        if args.command == "report":
            report = packing_report(args.config, args.job, args.samples)
            out = paths.reports_dir() / REPORT_DIR / f"packing_{report['config']}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"{report['config']}: chosen {report['chosen_runs_per_gpu']} runs per GPU")
            print(f"report: {paths.portable(out)}")
            return 0
        report = json.loads(args.report.read_text(encoding="utf-8"))
        print(time_limit(report, args.runs, args.epochs))
        return 0
    except PackingError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
