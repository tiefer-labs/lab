# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Latency, throughput and energy of a TensorRT engine on an NVIDIA Jetson Orin.

    python3 jetson/bench.py --engine <file.engine> --label fp16 [--runs 1000]
    python3 jetson/bench.py --engine <file.engine> --label fp16 --dry-run

Standard library only, so it runs with the system Python of JetPack. On a
machine that is not a Jetson, or with --dry-run, it validates the inputs and
prints the plan without running anything.

Measurements:

- device: model, L4T and JetPack, TensorRT, power mode (nvpmodel -q), clocks
  (jetson_clocks --show), from device_info.sh
- latency: trtexec runs the engine after a warm-up, at least 1,000 times,
  with batch 1; per-inference latencies are read from its --exportTimes file;
  p50, p95, p99 and mean are reported
- throughput: tiles per second = 1000 / mean latency in ms (batch 1, one
  stream); square kilometres per second = tiles per second x tile area, with
  tile area = (tile pixels x ground sampling distance)^2; for a 512 x 512
  tile at 10 m that is (512 x 10 m)^2 = (5.12 km)^2 = 26.2144 km2
- power: input rail from tegrastats sampled during the run; energy per tile
  in millijoules = mean input power (W) x mean latency (s) x 1000, both for
  the total board power and for the power above the idle level measured
  before the run
- temperature: tegrastats temperatures at start and end

Radiation, vacuum and thermal effects of the space environment are out of
scope; the Jetson Orin is flight-like reference hardware, not flight hardware.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import fmean
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import power

MIN_RUNS = 1000
OUT_OF_SCOPE = (
    "Radiation, vacuum and thermal effects of the space environment are out of scope. "
    "The Jetson Orin is flight-like reference hardware, not flight hardware."
)
TRTEXEC_PATHS = ("trtexec", "/usr/src/tensorrt/bin/trtexec")
# TODO(verify) on the board: field names of trtexec --exportTimes entries.
LATENCY_FIELDS = ("latencyMs", "endToEndMs", "computeMs")


def is_jetson() -> bool:
    return Path("/etc/nv_tegra_release").is_file()


def find_trtexec(explicit: str | None) -> str | None:
    candidates = (explicit,) if explicit else TRTEXEC_PATHS
    for candidate in candidates:
        if candidate and (shutil.which(candidate) or Path(candidate).is_file()):
            return candidate
    return None


def percentile(values: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (same as numpy's default)."""
    if not values:
        raise ValueError("no values")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q / 100.0
    low, high = math.floor(pos), math.ceil(pos)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def latency_summary(latencies_ms: list[float]) -> dict[str, float | int]:
    return {
        "runs": len(latencies_ms),
        "mean_ms": fmean(latencies_ms),
        "p50_ms": percentile(latencies_ms, 50),
        "p95_ms": percentile(latencies_ms, 95),
        "p99_ms": percentile(latencies_ms, 99),
        "min_ms": min(latencies_ms),
        "max_ms": max(latencies_ms),
    }


def tile_area_km2(tile_pixels: int, gsd_m: float) -> float:
    side_km = tile_pixels * gsd_m / 1000.0
    return side_km * side_km


def throughput(mean_latency_ms: float, tile_pixels: int, gsd_m: float) -> dict[str, Any]:
    tiles_per_s = 1000.0 / mean_latency_ms
    area = tile_area_km2(tile_pixels, gsd_m)
    return {
        "tiles_per_second": tiles_per_s,
        "km2_per_second": tiles_per_s * area,
        "tile_area_km2": area,
        "formula": (
            f"tiles/s = 1000 / mean latency (ms); km2/s = tiles/s x ({tile_pixels} px x "
            f"{gsd_m} m)^2 = tiles/s x {area:.4f} km2"
        ),
    }


def energy_per_tile_mj(mean_power_mw: float, mean_latency_ms: float) -> float:
    """Millijoules per tile: power (W) x time per tile (s) x 1000 = mW x ms / 1000."""
    return mean_power_mw * mean_latency_ms / 1000.0


def read_latencies(times_file: Path) -> list[float]:
    entries = json.loads(times_file.read_text(encoding="utf-8"))
    for name in LATENCY_FIELDS:
        if entries and name in entries[0]:
            return [float(e[name]) for e in entries]
    keys = sorted(entries[0]) if entries else []
    raise ValueError(f"no latency field {LATENCY_FIELDS} in trtexec times; found {keys}")


def git_commit() -> str:
    """Commit of the repository checkout on the board, recorded in the report."""
    root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def device_info() -> dict[str, str]:
    script = Path(__file__).resolve().parent / "device_info.sh"
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True, check=True)
    info = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            info[key.strip()] = value.strip()
    return info


def plan(args: argparse.Namespace, trtexec: str) -> list[str]:
    times = "<temporary>/times.json"
    return [
        "bash jetson/device_info.sh",
        f"tegrastats --interval {args.interval_ms} for {args.idle_seconds} s (idle power)",
        f"tegrastats --interval {args.interval_ms} in the background during the run",
        f"{trtexec} --loadEngine={args.engine} --iterations={args.runs} "
        f"--warmUp={args.warmup_ms} --duration=0 --exportTimes={times}",
        f"write {args.output_dir}/<label>_<UTC time>.json",
    ]


def validate(args: argparse.Namespace) -> list[str]:
    problems = []
    if args.runs < MIN_RUNS:
        problems.append(f"--runs must be at least {MIN_RUNS}")
    if not args.engine.name.endswith(".engine"):
        problems.append("--engine must be a TensorRT .engine file")
    if not args.label.replace("-", "").replace("_", "").isalnum():
        problems.append("--label may contain letters, digits, - and _ only")
    if args.tile_pixels <= 0 or args.gsd_m <= 0:
        problems.append("--tile-pixels and --gsd-m must be positive")
    return problems


def run(args: argparse.Namespace, trtexec: str) -> dict[str, Any]:
    if not args.engine.is_file():
        raise FileNotFoundError(f"engine not found: {args.engine}")
    info = device_info()
    idle = power.sample_for(args.idle_seconds, args.interval_ms)
    with tempfile.TemporaryDirectory() as tmp:
        times = Path(tmp) / "times.json"
        with power.Sampler(args.interval_ms) as sampler:
            subprocess.run(
                [
                    trtexec,
                    f"--loadEngine={args.engine}",
                    f"--iterations={args.runs}",
                    f"--warmUp={args.warmup_ms}",
                    "--duration=0",
                    f"--exportTimes={times}",
                ],
                check=True,
            )
        latencies = read_latencies(times)
    samples = sampler.samples
    rail = power.input_rail(samples, args.rail)
    run_power = power.summarise(samples, rail)
    idle_power = power.summarise(idle, rail)
    lat = latency_summary(latencies)
    above_idle = max(float(run_power["mean_mw"]) - float(idle_power["mean_mw"]), 0.0)
    return {
        "kind": "jetson",
        "label": args.label,
        "engine": args.engine.name,
        "git_commit": git_commit(),
        "time": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "device": info,
        "latency": lat,
        "warmup_ms": args.warmup_ms,
        "throughput": throughput(float(lat["mean_ms"]), args.tile_pixels, args.gsd_m),
        "power": {"run": run_power, "idle": idle_power, "interval_ms": args.interval_ms},
        "energy_per_tile_mj": {
            "total": energy_per_tile_mj(float(run_power["mean_mw"]), float(lat["mean_ms"])),
            "above_idle": energy_per_tile_mj(above_idle, float(lat["mean_ms"])),
        },
        "temperature_c": {
            "start": power.board_temperature(samples[0]) if samples else {},
            "end": power.board_temperature(samples[-1]) if samples else {},
        },
        "out_of_scope": OUT_OF_SCOPE,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a TensorRT engine on a Jetson Orin.")
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--label", required=True, help="for example fp16 or int8")
    parser.add_argument("--runs", type=int, default=MIN_RUNS)
    parser.add_argument("--warmup-ms", type=int, default=2000)
    parser.add_argument("--interval-ms", type=int, default=100, help="tegrastats interval")
    parser.add_argument("--idle-seconds", type=float, default=10.0)
    parser.add_argument("--rail", help="input power rail (default: first known)")
    parser.add_argument("--tile-pixels", type=int, default=512)
    parser.add_argument("--gsd-m", type=float, default=10.0, help="ground sampling distance")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/jetson"))
    parser.add_argument("--trtexec", help="path to trtexec")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    problems = validate(args)
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        return 2
    trtexec = find_trtexec(args.trtexec)
    if args.dry_run or not is_jetson() or trtexec is None:
        reason = "requested" if args.dry_run else "not a Jetson board or trtexec not found"
        print(f"dry run ({reason}); inputs are valid. Plan:")
        for step in plan(args, trtexec or "trtexec"):
            print(f"  {step}")
        print(OUT_OF_SCOPE)
        return 0
    report = run(args, trtexec)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out = args.output_dir / f"{args.label}_{stamp}.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["latency"], indent=2))
    print(f"report: {out.name} in {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
