# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Several runs on one GPU: separate complete run folders, packing report, time limit."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from tiefer_lab import packed, train
from tiefer_lab.data import build_cache
from tiefer_lab.utils import checkpoint

SMOKE = "configs/smoke.toml"


@pytest.fixture
def synthetic_cache(tiefer_env: dict[str, Path]) -> None:
    build_cache.main(
        ["--split", "all", "--synthetic", "--limit", "8", "--patch-size", "64", "--name", "smoke"]
    )


def test_two_runs_launched_together_write_separate_complete_folders(
    synthetic_cache: None, tiefer_env: dict[str, Path], repo_root: Path
) -> None:
    logs = tiefer_env["TIEFER_RUNS_DIR"] / "logs"
    code = packed.main(
        [
            "run",
            str(repo_root / SMOKE) + "@0",
            str(repo_root / SMOKE) + "@1",
            "--device",
            "cpu",
            "--log-dir",
            str(logs),
            "--train-arg=--cache-name",
            "--train-arg=smoke",
            "--train-arg=--allow-synthetic",
            "--train-arg=--epochs",
            "--train-arg=1",
            "--train-arg=--max-steps-per-epoch",
            "--train-arg=2",
        ]
    )
    assert code == 0, [p.read_text()[-2000:] for p in logs.glob("*.log")]
    folders = sorted(p for p in tiefer_env["TIEFER_RUNS_DIR"].glob("smoke-seed*") if p.is_dir())
    assert [f.name.split("-")[1] for f in folders] == ["seed0", "seed1"]
    for seed, folder in enumerate(folders):
        meta = json.loads((folder / train.METADATA_NAME).read_text())
        assert meta["status"] == "completed" and meta["seed"] == seed
        assert meta["seed_from_command_line"] is True
        assert meta["runs_per_gpu"] == 2
        for name in (train.CONFIG_NAME, train.METRICS_NAME, checkpoint.BEST, checkpoint.LAST):
            assert (folder / name).is_file(), (folder.name, name)
    assert sorted(p.name for p in logs.iterdir()) == ["smoke-seed0.log", "smoke-seed1.log"]
    assert "seed1" in (logs / "smoke-seed1.log").read_text()


def test_entries_are_checked() -> None:
    entries = packed.parse_entries(["configs/sieb.toml@0", "resume:sieb-seed1-x"])
    assert entries[0].train_args() == ["--config", "configs/sieb.toml", "--seed", "0"]
    assert entries[1].train_args() == ["--resume", "sieb-seed1-x"]
    for bad in (["configs/sieb.toml"], ["configs/sieb.toml@x"], ["resume:"], []):
        with pytest.raises(packed.PackingError):
            packed.parse_entries(bad)
    with pytest.raises(packed.PackingError, match="twice"):
        packed.parse_entries(["configs/sieb.toml@0", "configs/sieb.toml@0"])
    assert packed.main(["run", "configs/sieb.toml@0", "configs/sieb.toml@1", "--timing", "2"]) == 2


def _timing_run(runs: Path, run_id: str, epoch_seconds: float, start: str, end: str) -> None:
    folder = runs / run_id
    folder.mkdir(parents=True)
    meta = {
        "status": "completed",
        "start_time": start,
        "end_time": end,
        "data": {"ready_seconds": 30.0},
    }
    (folder / "metadata.json").write_text(json.dumps(meta))
    record = {
        "full_epoch_seconds": epoch_seconds,
        "train_seconds": 10.0,
        "data_wait_seconds": 1.0,
        "gpu_memory_peak_bytes": 2**30,
    }
    (folder / "metrics.jsonl").write_text(json.dumps(record) + "\n")


def _sample(utc: str, utilisation: float) -> str:
    """One nvidia-smi line; nvidia-smi writes the node's local time."""
    stamp = dt.datetime.fromisoformat(utc).timestamp()
    local = dt.datetime.fromtimestamp(stamp).strftime("%Y/%m/%d %H:%M:%S.000")
    return f"{local}, {utilisation}, 4000"


def test_packing_report_chooses_by_epochs_per_gpu_hour_within_the_slowdown(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    # Full epoch of the slowest run by packing: 100 s alone, 120, 150 and 250 s, each
    # packing in its own ten minutes, with its mean GPU utilisation.
    seconds = {1: 100.0, 2: 120.0, 3: 150.0, 4: 250.0}
    utilisation = {1: 30.0, 2: 60.0, 3: 85.0, 4: 95.0}
    lines = ["not a sample"]
    for n, value in seconds.items():
        start, end = f"2026-10-16T10:{n}0:00+00:00", f"2026-10-16T10:{n}5:00+00:00"
        for s in range(n):
            _timing_run(
                runs, packed.timing_run_id("configs/sieb.toml", n, s, "7"), value, start, end
            )
        lines.append(_sample(f"2026-10-16T10:{n}2:00+00:00", utilisation[n]))
    samples = tmp_path / "gpu.csv"
    samples.write_text("\n".join(lines) + "\n")
    report = packed.packing_report("configs/sieb.toml", "7", samples, runs)
    rows = report["packings"]
    assert rows["1"]["epochs_per_gpu_hour"] == 36.0 and rows["3"]["epochs_per_gpu_hour"] == 72.0
    assert rows["3"]["gpu_utilisation_mean"] == 85.0
    # One run alone leaves the GPU underused; four are too slow.
    assert "below 50.0" in rows["1"]["not_chosen_because"]
    assert rows["4"]["slowdown"] == 2.5 and "slower" in rows["4"]["not_chosen_because"]
    assert report["chosen_runs_per_gpu"] == 3
    assert rows["2"]["data_wait_share_max"] == 0.1
    # Time limit: 100 epochs x 150 s x 1.5 + 30 s load + 600 s start, rounded up to minutes.
    assert packed.time_limit(report, 3, 100) == "06:26:00"
    with pytest.raises(packed.PackingError):
        packed.time_limit(report, 3, None)
    # Without GPU samples no packing is chosen.
    unmeasured = packed.packing_report("configs/sieb.toml", "7", None, runs)
    assert unmeasured["chosen_runs_per_gpu"] is None
    assert "not measured" in unmeasured["packings"]["3"]["not_chosen_because"]
    missing = packed.packing_report("configs/wandler_1m.toml", "7", None, runs)
    assert missing["chosen_runs_per_gpu"] is None
    with pytest.raises(packed.PackingError, match="no complete timing"):
        packed.time_limit(missing, 2, 10)

    # A full medium CPU node against the chosen GPU packing, in BU per epoch.
    cpu_run = "timing-cpu-sieb-8"
    _timing_run(runs, cpu_run, 900.0, "2026-10-16T11:00:00+00:00", "2026-10-16T11:20:00+00:00")
    comparison = packed.cpu_comparison("configs/sieb.toml", runs / cpu_run, report)
    # CPU: 900 s x 288 / 3600 = 72; GPU: 150 s / 3 runs x 200 / 3600 = 2.78.
    assert comparison["cpu_bu_per_epoch"] == 72.0 and comparison["gpu_bu_per_epoch"] == 2.78
    assert comparison["cheaper"] == "gpu"
    assert packed.cpu_comparison("configs/sieb.toml", runs / cpu_run, None)["cheaper"] is None
    with pytest.raises(packed.PackingError, match="no finished CPU timing run"):
        packed.cpu_comparison("configs/sieb.toml", runs / "absent", report)


def test_below_the_utilisation_rule_the_highest_measured_packing_goes_to_the_gate(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    seconds = {1: 100.0, 2: 120.0, 3: 150.0, 4: 250.0}
    # No packing reaches 50 percent; four would be the highest but is too slow.
    utilisation = {1: 20.0, 2: 40.0, 3: 45.0, 4: 48.0}
    lines = []
    for n, value in seconds.items():
        start, end = f"2026-10-16T10:{n}0:00+00:00", f"2026-10-16T10:{n}5:00+00:00"
        for s in range(n):
            _timing_run(
                runs, packed.timing_run_id("configs/sieb.toml", n, s, "7"), value, start, end
            )
        lines.append(_sample(f"2026-10-16T10:{n}2:00+00:00", utilisation[n]))
    samples = tmp_path / "gpu.csv"
    samples.write_text("\n".join(lines) + "\n")
    report = packed.packing_report("configs/sieb.toml", "7", samples, runs)
    rows = report["packings"]
    assert report["chosen_runs_per_gpu"] == 3
    assert report["chosen_below_utilisation_rule"] is True
    assert rows["3"]["flag"] == packed.BELOW_RULE == "below the 50 percent rule"
    assert "not_chosen_because" not in rows["3"]
    assert "below 50.0" in rows["2"]["not_chosen_because"] and "flag" not in rows["2"]
    assert "packing 3" in report["for_the_gate"] and "gate" in report["for_the_gate"]
    # A packing with no measurement is still never chosen.
    unmeasured = packed.packing_report("configs/sieb.toml", "7", None, runs)
    assert unmeasured["chosen_runs_per_gpu"] is None
    assert unmeasured["chosen_below_utilisation_rule"] is False


def test_a_timing_stopped_by_its_time_limit_says_so(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    # Only one run alone finished before the limit; nothing was measured on the GPU.
    _timing_run(
        runs,
        packed.timing_run_id("configs/cloudscout_reimpl_step1_th30.toml", 1, 0, "5"),
        600.0,
        "2026-10-16T10:00:00+00:00",
        "2026-10-16T10:12:00+00:00",
    )
    report = packed.packing_report(
        "configs/cloudscout_reimpl_step1_th30.toml", "5", None, runs, time_limit_reached=True
    )
    assert report["time_limit_reached"] is True
    assert report["chosen_runs_per_gpu"] is None
    assert "time limit stopped it" in report["packings"]["2"]["not_chosen_because"]


def test_report_and_time_limit_commands(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    runs = tiefer_env["TIEFER_RUNS_DIR"]
    run_id = packed.timing_run_id("configs/sieb.toml", 1, 0, "9")
    _timing_run(runs, run_id, 60.0, "2026-10-16T10:00:00+00:00", "2026-10-16T10:01:00+00:00")
    samples = tmp_path / "gpu.csv"
    samples.write_text(_sample("2026-10-16T10:00:30+00:00", 70.0) + "\n")
    args = ["report", "--config", "configs/sieb.toml", "--job", "9", "--samples", str(samples)]
    assert packed.main(args) == 0
    out = tiefer_env["TIEFER_REPORTS_DIR"] / "timing" / "packing_sieb.json"
    report = json.loads(out.read_text())
    assert report["chosen_runs_per_gpu"] == 1
    assert packed.main(["time-limit", "--report", str(out), "--runs", "1", "--epochs", "10"]) == 0
    assert capsys.readouterr().out.strip().endswith("00:26:00")
    _timing_run(
        runs, "timing-cpu-sieb-9", 600.0, "2026-10-16T11:00:00+00:00", "2026-10-16T11:10:00+00:00"
    )
    compare = ["cpu-compare", "--config", "configs/sieb.toml", "--cpu-run", "timing-cpu-sieb-9"]
    assert packed.main([*compare, "--gpu-report", str(out)]) == 0
    cpu = json.loads((tiefer_env["TIEFER_REPORTS_DIR"] / "timing" / "cpu_sieb.json").read_text())
    assert cpu["cpu_bu_per_epoch"] == 48.0 and cpu["cheaper"] == "gpu"


def test_signals_reach_every_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    import signal

    received: list[tuple[str, int]] = []

    class FakeProcess:
        def __init__(self, command: list[str], **kwargs: object) -> None:
            self.label = command[command.index("--seed") + 1]
            self.done = False

        def poll(self) -> int | None:
            return 0 if self.done else None

        def send_signal(self, signum: int) -> None:
            received.append((self.label, signum))

        def wait(self) -> int:
            if not received:
                # Slurm's warning before the time limit reaches the launcher.
                os.kill(os.getpid(), signal.SIGUSR1)
            self.done = True
            return 0

    monkeypatch.setattr(packed.subprocess, "Popen", FakeProcess)
    before = signal.getsignal(signal.SIGUSR1)
    entries = packed.parse_entries(["configs/sieb.toml@0", "configs/sieb.toml@1"])
    assert packed.launch(entries, tmp_path) == [0, 0]
    assert sorted(received) == [("0", signal.SIGUSR1), ("1", signal.SIGUSR1)]
    assert signal.getsignal(signal.SIGUSR1) == before
