# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""CSC Roihu helper scripts, run off Roihu with stub sbatch and sacct commands."""

from __future__ import annotations

import json
import os
import subprocess
import tarfile
from pathlib import Path

import pytest

ROIHU = Path(__file__).resolve().parent.parent / "hpc" / "roihu"


@pytest.fixture
def roihu_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "sbatch").write_text(
        '#!/bin/sh\necho "$@" > "$STUB_LOG"\necho "Submitted batch job 1"\n'
    )
    (bin_dir / "srun").write_text('#!/bin/sh\nfor a in "$@"; do echo "$a"; done > "$STUB_LOG"\n')
    (bin_dir / "module").write_text('#!/bin/sh\necho "module $*" >> "$STUB_LOG.module"\n')
    # The test machine reports this architecture; STUB_ARCH overrides it.
    (bin_dir / "uname").write_text('#!/bin/sh\necho "${STUB_ARCH:-x86_64}"\n')
    # Synthetic sacct output in the --parsable2 format, not a real job record.
    (bin_dir / "sacct").write_text(
        "#!/bin/sh\n"
        "echo 'JobID|JobName|Partition|State|Elapsed|AllocTRES'\n"
        "echo '1|tiefer-train|gpumedium|COMPLETED|01:00:00|billing=1,gres/gpu=1'\n"
    )
    for stub in bin_dir.iterdir():
        stub.chmod(0o755)
    env = {
        k: v for k, v in os.environ.items() if not k.startswith("TIEFER_") and k != "SLURM_JOB_ID"
    }
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "TIEFER_CSC_PROJECT": "testproject",
            "TIEFER_PROJAPPL": str(tmp_path / "projappl"),
            "TIEFER_SCRATCH": str(tmp_path / "scratch"),
            "STUB_LOG": str(tmp_path / "sbatch.log"),
        }
    )
    return env


def _run(script: str, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROIHU / script), *args], env=env, capture_output=True, text=True
    )


def test_env_requires_project(roihu_env: dict[str, str]) -> None:
    env = {k: v for k, v in roihu_env.items() if k != "TIEFER_CSC_PROJECT"}
    result = subprocess.run(
        ["bash", "-c", f"source {ROIHU / 'env.sh'}"], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1 and "TIEFER_CSC_PROJECT" in result.stderr


def test_submit_adds_account_and_log_location(roihu_env: dict[str, str], tmp_path: Path) -> None:
    result = _run("submit.sh", ["hpc/roihu/train.sbatch", "configs/l1_base.toml"], roihu_env)
    assert result.returncode == 0, result.stderr
    sbatch_args = (tmp_path / "sbatch.log").read_text()
    assert "--account=testproject" in sbatch_args
    assert f"--output={tmp_path}/scratch/runs/slurm/%x-%j.out" in sbatch_args
    assert "--export=NONE,TIEFER_CSC_PROJECT=testproject " in sbatch_args
    assert sbatch_args.strip().endswith("hpc/roihu/train.sbatch configs/l1_base.toml")


def test_submit_forwards_seed_final_reason_and_sbatch_options(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    env = {**roihu_env, "SEED": "1", "FINAL": "1", "REASON": "final L1 check"}
    args = ["--test-only", "--time=24:00:00", "hpc/roihu/train.sbatch", "configs/l1_base.toml"]
    result = _run("submit.sh", args, env)
    assert result.returncode == 0, result.stderr
    sbatch_args = (tmp_path / "sbatch.log").read_text()
    assert (
        "--export=NONE,TIEFER_CSC_PROJECT=testproject,SEED=1,FINAL=1,REASON=final L1 check"
        in sbatch_args
    )
    assert "--test-only --time=24:00:00 hpc/roihu/train.sbatch" in sbatch_args


@pytest.mark.parametrize(
    "extra, args",
    [
        ({"REASON": "a,b"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({"SEED": "1;rm"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({"FINAL": "yes"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({"TIEFER_CSC_PROJECT": "<project>"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({}, ["--account=other", "hpc/roihu/train.sbatch", "c.toml"]),
        ({}, ["--export=ALL", "hpc/roihu/train.sbatch", "c.toml"]),
    ],
)
def test_submit_rejects_unsafe_values(
    roihu_env: dict[str, str], tmp_path: Path, extra: dict[str, str], args: list[str]
) -> None:
    result = _run("submit.sh", args, {**roihu_env, **extra})
    assert result.returncode == 2
    assert not (tmp_path / "sbatch.log").exists()


def test_usage_writes_compute_report(roihu_env: dict[str, str], tmp_path: Path) -> None:
    result = _run("usage.sh", ["1"], roihu_env)
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "scratch" / "reports" / "compute" / "1.json").read_text())
    assert report["steps"][0]["Partition"] == "gpumedium"
    assert "Account" not in report["steps"][0]
    assert _run("usage.sh", ["1;rm"], roihu_env).returncode == 2


def test_collect_packs_relative_paths_only(roihu_env: dict[str, str], tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    run = scratch / "runs" / "r1"
    (run / "export").mkdir(parents=True)
    for name in ("config.toml", "metadata.json", "metrics.jsonl", "best.pt", "export/m.onnx"):
        (run / name).write_text("synthetic placeholder")
    (run / "last.pt").write_text("not collected")
    (scratch / "reports" / "evaluation").mkdir(parents=True)
    (scratch / "reports" / "evaluation" / "r1_val.json").write_text("{}")
    result = _run("collect.sh", ["r1"], roihu_env)
    assert result.returncode == 0, result.stderr
    with tarfile.open(scratch / "collect" / "tiefer-r1.tar.gz") as archive:
        names = archive.getnames()
    assert "runs/r1/best.pt" in names and "runs/r1/export/m.onnx" in names
    assert "reports/evaluation/r1_val.json" in names
    assert "runs/r1/last.pt" not in names
    assert all(not n.startswith("/") and ".." not in n for n in names)
    assert _run("collect.sh", ["missing"], roihu_env).returncode == 2


def test_job_scripts_request_documented_resources() -> None:
    train = (ROIHU / "train.sbatch").read_text()
    assert "#SBATCH --partition=gpumedium" in train
    assert "#SBATCH --gres=gpu:gh200:1" in train
    assert "#SBATCH --signal=B:USR1@300" in train
    assert "#SBATCH --time=12:00:00" in train
    assert "#SBATCH --partition=gputest" in (ROIHU / "smoke.sbatch").read_text()
    for name in ("train", "evaluate", "export", "smoke"):
        assert "#SBATCH --cpus-per-task=72" in (ROIHU / f"{name}.sbatch").read_text()
    for script in ROIHU.glob("*.sbatch"):
        text = script.read_text()
        assert "#SBATCH --account" not in text, "the account is passed by submit.sh"
        assert text.startswith("#!/bin/bash -l\n"), script.name
        assert "#SBATCH --export=NONE\n" in text and "--export=ALL" not in text, script.name
        prelude = text.index("source hpc/roihu/job_prelude.sh")
        assert prelude < text.index("source hpc/roihu/env.sh"), script.name
        assert text.index("uname -m") < prelude, "architecture is checked before loading"


@pytest.mark.parametrize("name", ["train", "evaluate", "export", "smoke"])
def test_gpu_jobs_stop_on_a_non_arm_node(roihu_env: dict[str, str], name: str) -> None:
    result = _run(f"{name}.sbatch", ["configs/l1_base.toml"], roihu_env)
    assert result.returncode == 1
    assert "needs an aarch64 GH200 node, but runs on x86_64" in result.stderr
    assert not Path(roihu_env["STUB_LOG"] + ".module").exists(), "nothing loaded"


def test_data_job_accepts_both_architectures_only(roihu_env: dict[str, str]) -> None:
    result = _run("data.sbatch", [], {**roihu_env, "STUB_ARCH": "riscv64"})
    assert result.returncode == 1 and "expected aarch64 or x86_64" in result.stderr
    text = (ROIHU / "data.sbatch").read_text()
    assert "aarch64 | x86_64) ;;" in text and "gh200" not in text


def test_prelude_sets_home_and_user_and_purges_modules(roihu_env: dict[str, str]) -> None:
    import pwd

    env = {k: v for k, v in roihu_env.items() if k not in ("HOME", "USER")}
    script = f'set -euo pipefail; source {ROIHU / "job_prelude.sh"}; echo "$HOME|$USER"'
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    entry = pwd.getpwuid(os.getuid())
    assert result.stdout.strip() == f"{entry.pw_dir}|{entry.pw_name}"
    assert Path(roihu_env["STUB_LOG"] + ".module").read_text() == "module purge\n"


def test_smoke_builds_a_tiny_cache_when_the_index_is_missing() -> None:
    smoke = (ROIHU / "smoke.sbatch").read_text()
    assert 'if [[ ! -f "${TIEFER_DATA_DIR}/${cache_name}/index.json" ]]' in smoke
    assert 'export TIEFER_DATA_DIR="${TIEFER_SCRATCH}/smoke/data"' in smoke
    assert "--split train --limit 32" in smoke and "--split val --limit 16" in smoke
    # The tiny cache must be built before the first training command.
    assert smoke.index("--limit 32") < smoke.index("tiefer_lab.train")
