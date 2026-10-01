# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""tegrastats sampler and parser for NVIDIA Jetson boards.

Standard library only, so it runs with the system Python of JetPack.

    python3 jetson/power.py --parse <tegrastats-log> [--rail VDD_IN]
    python3 jetson/power.py --dry-run

tegrastats prints one line per interval with power rails as
`NAME <current>mW/<average>mW` and temperatures as `name@<value>C`. The name
of the input power rail depends on the module (TODO(verify) on the target
board with `tegrastats --interval 1000`); the first rail found from
INPUT_RAILS is used unless `--rail` is given.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import fmean
from types import TracebackType

INPUT_RAILS = ("VDD_IN", "VIN_SYS_5V0", "POM_5V_IN")
RAIL = re.compile(r"\b([A-Z][A-Z0-9_]*) (\d+)mW/(\d+)mW")
TEMPERATURE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)@(-?\d+(?:\.\d+)?)C\b")


@dataclass
class Sample:
    time: float
    rails_mw: dict[str, int] = field(default_factory=dict)
    temperatures_c: dict[str, float] = field(default_factory=dict)


def parse_line(line: str, timestamp: float = 0.0) -> Sample:
    """Instantaneous rail power (mW) and temperatures (degrees C) of one tegrastats line."""
    sample = Sample(time=timestamp)
    for name, current, _average in RAIL.findall(line):
        sample.rails_mw[name] = int(current)
    for name, value in TEMPERATURE.findall(line):
        sample.temperatures_c[name] = float(value)
    return sample


def input_rail(samples: list[Sample], requested: str | None = None) -> str:
    names = set().union(*(s.rails_mw for s in samples)) if samples else set()
    if requested:
        if requested not in names:
            raise ValueError(f"rail {requested} not in tegrastats output: {sorted(names)}")
        return requested
    for name in INPUT_RAILS:
        if name in names:
            return name
    raise ValueError(f"no known input rail in tegrastats output: {sorted(names)}")


def summarise(samples: list[Sample], rail: str) -> dict[str, float | int | str]:
    values = [s.rails_mw[rail] for s in samples if rail in s.rails_mw]
    if not values:
        raise ValueError(f"no samples for rail {rail}")
    return {
        "rail": rail,
        "samples": len(values),
        "mean_mw": fmean(values),
        "max_mw": max(values),
        "min_mw": min(values),
    }


def board_temperature(sample: Sample) -> dict[str, float]:
    return dict(sorted(sample.temperatures_c.items()))


class Sampler:
    """Runs `tegrastats --interval <ms>` in the background and collects samples."""

    def __init__(self, interval_ms: int = 100, command: str = "tegrastats") -> None:
        self.interval_ms = interval_ms
        self.command = command
        self.samples: list[Sample] = []
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None

    def _read(self) -> None:
        assert self._process is not None and self._process.stdout is not None
        for line in self._process.stdout:
            sample = parse_line(line, time.monotonic())
            if sample.rails_mw:
                self.samples.append(sample)

    def __enter__(self) -> Sampler:
        if shutil.which(self.command) is None:
            raise FileNotFoundError(f"{self.command} not found; run this on a Jetson board")
        self._process = subprocess.Popen(
            [self.command, "--interval", str(self.interval_ms)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process.wait(timeout=10)
        if self._thread is not None:
            self._thread.join(timeout=10)


def sample_for(seconds: float, interval_ms: int = 100) -> list[Sample]:
    with Sampler(interval_ms) as sampler:
        time.sleep(seconds)
    return sampler.samples


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse or sample tegrastats power readings.")
    parser.add_argument("--parse", type=Path, help="tegrastats log file to summarise")
    parser.add_argument("--rail", help="input power rail name (default: first known)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = parser.parse_args(argv)
    if args.dry_run or not args.parse:
        print("dry run: power.py would parse tegrastats lines of the form")
        print("  'VDD_IN 4936mW/4936mW ... tj@46.2C' and report the input rail power")
        print(f"  known input rails: {', '.join(INPUT_RAILS)}")
        return 0
    lines = args.parse.read_text(encoding="utf-8").splitlines()
    samples = [parse_line(line, float(i)) for i, line in enumerate(lines)]
    samples = [s for s in samples if s.rails_mw]
    rail = input_rail(samples, args.rail)
    print(json.dumps(summarise(samples, rail), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
