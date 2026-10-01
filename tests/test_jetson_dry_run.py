# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Jetson scripts off-device: dry runs, input validation, parsing and formulas."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

JETSON = Path(__file__).resolve().parent.parent / "jetson"


def _load(name: str) -> ModuleType:
    sys.path.insert(0, str(JETSON))
    spec = importlib.util.spec_from_file_location(f"jetson_{name}", JETSON / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bench = _load("bench")
power = _load("power")

# Synthetic tegrastats line in the documented format, not a measurement.
LINE = (
    "RAM 2000/7000MB SWAP 0/3500MB CPU [5%@729,3%@729] cpu@45.5C soc2@44.25C tj@46.2C "
    "VDD_IN 4936mW/4900mW VDD_CPU_GPU_CV 554mW/550mW VDD_SOC 1426mW/1400mW"
)


def test_bench_dry_run_off_device() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(JETSON / "bench.py"),
            "--engine",
            "x.engine",
            "--label",
            "fp16",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "dry run" in result.stdout and "--iterations=1000" in result.stdout
    assert "out of scope" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ["--engine", "x.engine", "--label", "fp16", "--runs", "999"],
        ["--engine", "model.onnx", "--label", "fp16"],
        ["--engine", "x.engine", "--label", "a b"],
    ],
)
def test_bench_rejects_invalid_inputs(args: list[str]) -> None:
    assert bench.main([*args, "--dry-run"]) == 2


def test_device_info_dry_run() -> None:
    result = subprocess.run(
        ["bash", str(JETSON / "device_info.sh"), "--dry-run"], capture_output=True, text=True
    )
    assert result.returncode == 0 and "nvpmodel -q" in result.stdout


def test_build_engines_validates_and_plans(tmp_path: Path) -> None:
    fp32 = tmp_path / "cloud_filter_fp32.onnx"
    int8 = tmp_path / "cloud_filter_int8.onnx"
    fp32.write_bytes(b"synthetic placeholder")
    int8.write_bytes(b"synthetic placeholder")
    script = str(JETSON / "build_engines.sh")
    ok = subprocess.run(
        [
            "bash",
            script,
            "--fp32",
            str(fp32),
            "--int8",
            str(int8),
            "--out",
            str(tmp_path / "e"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0
    assert "--fp16" in ok.stdout and "--int8" in ok.stdout
    missing = subprocess.run(
        ["bash", script, "--fp32", str(tmp_path / "none.onnx"), "--out", "e", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert missing.returncode == 2 and "not found" in missing.stderr


def test_power_parser_and_summary() -> None:
    sample = power.parse_line(LINE)
    assert sample.rails_mw == {"VDD_IN": 4936, "VDD_CPU_GPU_CV": 554, "VDD_SOC": 1426}
    assert sample.temperatures_c["tj"] == pytest.approx(46.2)
    assert power.input_rail([sample]) == "VDD_IN"
    other = power.parse_line(LINE.replace("4936mW", "5064mW"))
    summary = power.summarise([sample, other], "VDD_IN")
    assert summary["mean_mw"] == pytest.approx(5000.0) and summary["samples"] == 2
    with pytest.raises(ValueError):
        power.input_rail([sample], "VDD_GPU")


def test_latency_throughput_and_energy_formulas(tmp_path: Path) -> None:
    latencies = [float(v) for v in range(1, 101)]
    summary = bench.latency_summary(latencies)
    assert summary["p50_ms"] == pytest.approx(50.5)
    assert summary["p99_ms"] == pytest.approx(99.01)
    assert bench.tile_area_km2(512, 10.0) == pytest.approx(26.2144)
    tput = bench.throughput(4.0, 512, 10.0)
    assert tput["tiles_per_second"] == pytest.approx(250.0)
    assert tput["km2_per_second"] == pytest.approx(250.0 * 26.2144)
    # 5000 mW for 4 ms is 20 mJ.
    assert bench.energy_per_tile_mj(5000.0, 4.0) == pytest.approx(20.0)
    times = tmp_path / "times.json"
    times.write_text(json.dumps([{"latencyMs": 1.5}, {"latencyMs": 2.5}]))
    assert bench.read_latencies(times) == [1.5, 2.5]
    times.write_text(json.dumps([{"other": 1.0}]))
    with pytest.raises(ValueError):
        bench.read_latencies(times)
