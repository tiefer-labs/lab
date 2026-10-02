# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""CSC Roihu helper scripts, run off Roihu with stub sbatch and sacct commands."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tarfile
from pathlib import Path

import pytest

from tiefer_lab.data.sensor import Perturbation

ROIHU = Path(__file__).resolve().parent.parent / "hpc" / "roihu"


@pytest.fixture
def roihu_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # The stub records its arguments and the variables a job would inherit.
    (bin_dir / "sbatch").write_text(
        '#!/bin/sh\necho "$@" > "$STUB_LOG"\n'
        "env | grep -E '^(TIEFER_CSC_PROJECT|SEED|FINAL|REASON)=' | sort > \"$STUB_LOG.env\"\n"
        'echo "Submitted batch job 1"\n'
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
    env["TIEFER_CSC_PROJECT"] = "<project>"
    result = subprocess.run(
        ["bash", "-c", f"source {ROIHU / 'env.sh'}"], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1 and "remove that line" in result.stderr


def test_submit_adds_account_and_log_location(roihu_env: dict[str, str], tmp_path: Path) -> None:
    env = {**roihu_env, "STUB_ARCH": "aarch64"}
    result = _run("submit.sh", ["hpc/roihu/train.sbatch", "configs/l1_base.toml"], env)
    assert result.returncode == 0, result.stderr
    sbatch_args = (tmp_path / "sbatch.log").read_text()
    assert "--account=testproject" in sbatch_args
    assert f"--output={tmp_path}/scratch/runs/slurm/%x-%j.out" in sbatch_args
    assert "--export" not in sbatch_args, "jobs use sbatch's default export"
    assert sbatch_args.strip().endswith("hpc/roihu/train.sbatch configs/l1_base.toml")


def test_submit_passes_seed_final_reason_as_environment_and_sbatch_options(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    env = {**roihu_env, "STUB_ARCH": "aarch64", "SEED": "1", "FINAL": "1"}
    env["REASON"] = "final L1 check, once"
    args = ["--test-only", "--time=24:00:00", "hpc/roihu/train.sbatch", "configs/l1_base.toml"]
    result = _run("submit.sh", args, env)
    assert result.returncode == 0, result.stderr
    assert (
        "--test-only --time=24:00:00 hpc/roihu/train.sbatch"
        in (tmp_path / "sbatch.log").read_text()
    )
    assert (tmp_path / "sbatch.log.env").read_text().splitlines() == [
        "FINAL=1",
        "REASON=final L1 check, once",
        "SEED=1",
        "TIEFER_CSC_PROJECT=testproject",
    ]


@pytest.mark.parametrize(
    "job, arch, message",
    [
        ("train", "x86_64", "submit GPU jobs from roihu-gpu.csc.fi"),
        ("smoke", "x86_64", "submit GPU jobs from roihu-gpu.csc.fi"),
        ("evaluate", "x86_64", "submit GPU jobs from roihu-gpu.csc.fi"),
        ("export", "x86_64", "submit GPU jobs from roihu-gpu.csc.fi"),
        ("data", "aarch64", "submit the data job from roihu-cpu.csc.fi"),
        ("survey", "aarch64", "submit CPU jobs from roihu-cpu.csc.fi"),
    ],
)
def test_submit_refuses_a_job_from_the_wrong_login_node(
    roihu_env: dict[str, str], tmp_path: Path, job: str, arch: str, message: str
) -> None:
    result = _run("submit.sh", [f"hpc/roihu/{job}.sbatch"], {**roihu_env, "STUB_ARCH": arch})
    assert result.returncode == 2 and message in result.stderr
    assert not (tmp_path / "sbatch.log").exists()
    other = "aarch64" if arch == "x86_64" else "x86_64"
    assert (
        _run("submit.sh", [f"hpc/roihu/{job}.sbatch"], {**roihu_env, "STUB_ARCH": other}).returncode
        == 0
    )


@pytest.mark.parametrize(
    "extra, args",
    [
        ({"SEED": "1;rm"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({"FINAL": "yes"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({"TIEFER_CSC_PROJECT": "<project>"}, ["hpc/roihu/train.sbatch", "c.toml"]),
        ({}, ["--account=other", "hpc/roihu/train.sbatch", "c.toml"]),
        ({}, ["--export=NONE", "hpc/roihu/train.sbatch", "c.toml"]),
    ],
)
def test_submit_rejects_unsafe_values(
    roihu_env: dict[str, str], tmp_path: Path, extra: dict[str, str], args: list[str]
) -> None:
    env = {**roihu_env, "STUB_ARCH": "aarch64", **extra}
    result = _run("submit.sh", args, env)
    assert result.returncode != 0 and "error:" in result.stderr
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
        assert "--export" not in text, "jobs use sbatch's default export"
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


def _smoke_env(roihu_env: dict[str, str], tmp_path: Path) -> dict[str, str]:
    """Run smoke.sbatch off Roihu: python3 runs the real cache check and logs every other call."""
    import sys

    log = tmp_path / "python.log"
    (tmp_path / "bin" / "python3").write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-m" ] && [ "$2" = "tiefer_lab.data.cache" ]; then\n'
        f'  exec "{sys.executable}" "$@"\n'
        "fi\n"
        f'echo "$TIEFER_DATA_DIR | $*" >> "{log}"\n'
    )
    (tmp_path / "bin" / "python3").chmod(0o755)
    venv = tmp_path / "projappl" / "venv-aarch64" / "bin"
    venv.mkdir(parents=True)
    (venv / "activate").write_text("")
    return {**roihu_env, "STUB_ARCH": "aarch64", "SLURM_JOB_ID": "7"}


def _full_cache(tmp_path: Path, splits: dict[str, bool], building: tuple[str, ...] = ()) -> Path:
    """A full cache folder as data.sbatch leaves it, possibly while still building."""
    from tiefer_lab.data import cache

    directory = tmp_path / "scratch" / "data" / "cloudsen12-l1c-high"
    entries = {split: {"complete": done, "count": 100} for split, done in splits.items()}
    cache.write_index(directory, {"format": cache.CACHE_FORMAT, "splits": entries})
    (directory / "train_images.npy").write_bytes(b"full cache data")
    for split in building:
        cache.progress_path(directory, split).write_text('{"done": 50}')
    return directory


def _tree(directory: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "state",
    ["missing", "train done, val being built", "train and val done, val rebuilding"],
)
def test_smoke_builds_its_tiny_cache_apart_and_never_touches_the_full_cache(
    roihu_env: dict[str, str], tmp_path: Path, state: str
) -> None:
    env = _smoke_env(roihu_env, tmp_path)
    full = tmp_path / "scratch" / "data"
    if state == "train done, val being built":
        _full_cache(tmp_path, {"train": True}, building=("val",))
    elif state == "train and val done, val rebuilding":
        _full_cache(tmp_path, {"train": True, "val": True}, building=("val",))
    full.mkdir(parents=True, exist_ok=True)
    before = _tree(full)
    result = _run("smoke.sbatch", [], env)
    assert result.returncode == 0, result.stderr
    assert "full cache not ready" in result.stdout and "it is not touched" in result.stdout
    assert _tree(full) == before, "the full cache folder is unchanged"
    calls = (tmp_path / "python.log").read_text().splitlines()
    smoke_dir = str(tmp_path / "scratch" / "smoke" / "data")
    builds = [c for c in calls if "build_cache" in c]
    assert len(builds) == 2 and all(c.startswith(f"{smoke_dir} |") for c in builds)
    assert "--split train --limit 32" in builds[0] and "--split val --limit 16" in builds[1]
    assert all(c.startswith(f"{smoke_dir} |") for c in calls if "tiefer_lab." in c)
    assert not any("l1_base" in c for c in calls), "no timing run on the tiny cache"


def test_smoke_reads_a_complete_full_cache_without_building(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    env = _smoke_env(roihu_env, tmp_path)
    _full_cache(tmp_path, {"train": True, "val": True, "test": False}, building=("test",))
    full = tmp_path / "scratch" / "data"
    before = _tree(full)
    result = _run("smoke.sbatch", [], env)
    assert result.returncode == 0, result.stderr
    calls = (tmp_path / "python.log").read_text().splitlines()
    assert not any("build_cache" in c for c in calls)
    assert any("configs/l1_base.toml" in c for c in calls), "timing run on the full cache"
    assert all(c.startswith(f"{full} |") for c in calls if "tiefer_lab." in c)
    assert _tree(full) == before
    assert not (tmp_path / "scratch" / "smoke").exists()


def test_smoke_stops_when_the_smoke_folder_is_the_full_cache_folder(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    env = _smoke_env(roihu_env, tmp_path)
    env["TIEFER_DATA_DIR"] = str(tmp_path / "scratch" / "smoke" / "data")
    result = _run("smoke.sbatch", [], env)
    assert result.returncode == 1 and "is the full cache folder" in result.stderr
    log = tmp_path / "python.log"
    assert not log.exists() or "build_cache" not in log.read_text()


# 'module' as a shell function, like Lmod: not written for set -euo pipefail.
STUB_MODULE = """\
module() {
  local unset_inside="${TIEFER_TEST_NOT_SET}"
  false | true
  echo "module $*" >> "$STUB_LOG.module"
  [[ "$*" != *broken* ]]
}
"""


@pytest.mark.parametrize("options", ["-euo pipefail", "+euo pipefail"])
def test_env_loads_modules_under_strict_options_and_restores_them(
    roihu_env: dict[str, str], tmp_path: Path, options: str
) -> None:
    (tmp_path / "bin" / "module").unlink()
    script = (
        f"set {options}; {STUB_MODULE}"
        "before=$(set +o; echo $-); "
        f"source {ROIHU / 'env.sh'}; "
        'after=$(set +o; echo $-); echo continued; [[ "$before" == "$after" ]] && echo same'
    )
    result = subprocess.run(["bash", "-c", script], env=roihu_env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["continued", "same"], "options restored exactly"
    calls = Path(roihu_env["STUB_LOG"] + ".module").read_text()
    assert calls == "module purge\nmodule load python-data/3.12-31.03\n"


def test_env_stops_when_module_load_fails(roihu_env: dict[str, str], tmp_path: Path) -> None:
    (tmp_path / "bin" / "module").unlink()
    env = {**roihu_env, "TIEFER_CPU_PYTHON_MODULE": "broken/1.0"}
    script = f"set -euo pipefail; {STUB_MODULE} source {ROIHU / 'env.sh'}; echo continued"
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    assert result.returncode == 1 and "continued" not in result.stdout
    assert "cannot load broken/1.0 (module status 1)" in result.stderr


@pytest.mark.parametrize("options", ["-euo pipefail", "+euo pipefail", "-e +u -o pipefail"])
def test_prelude_purges_modules_under_strict_options_and_restores_them(
    roihu_env: dict[str, str], tmp_path: Path, options: str
) -> None:
    (tmp_path / "bin" / "module").unlink()
    script = (
        f"set {options}; {STUB_MODULE}"
        "before=$(set +o; echo $-); "
        f"source {ROIHU / 'job_prelude.sh'}; "
        'after=$(set +o; echo $-); echo continued; [[ "$before" == "$after" ]] && echo same'
    )
    result = subprocess.run(["bash", "-c", script], env=roihu_env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["continued", "same"], "options restored exactly"
    assert Path(roihu_env["STUB_LOG"] + ".module").read_text() == "module purge\n"


def test_prelude_stops_without_the_module_command(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    (tmp_path / "bin" / "module").unlink()
    script = f"set -euo pipefail; source {ROIHU / 'job_prelude.sh'}; echo continued"
    result = subprocess.run(["bash", "-c", script], env=roihu_env, capture_output=True, text=True)
    assert result.returncode == 1 and "continued" not in result.stdout
    assert "submit it with hpc/roihu/submit.sh from a Roihu login node" in result.stderr


def _appending_sbatch(roihu_env: dict[str, str], tmp_path: Path) -> Path:
    log = tmp_path / "calls.log"
    (tmp_path / "bin" / "sbatch").write_text(
        f'#!/bin/sh\necho "SEED=${{SEED:-}} $*" >> "{log}"\necho "Submitted batch job 1"\n'
    )
    return log


def test_sweep_submits_one_job_per_config_and_seed(
    roihu_env: dict[str, str], tmp_path: Path
) -> None:
    log = _appending_sbatch(roihu_env, tmp_path)
    env = {**roihu_env, "STUB_ARCH": "aarch64"}
    configs = ["configs/l2_flex_1m.toml", "configs/l2_spec_1m.toml"]
    result = _run("sweep.sh", ["--seeds", "0,1,2", *configs], env)
    assert result.returncode == 0, result.stderr
    calls = log.read_text().splitlines()
    assert len(calls) == 6
    assert calls[0].startswith("SEED=0 ") and calls[0].endswith(
        "hpc/roihu/train.sbatch configs/l2_flex_1m.toml"
    )
    assert calls[5].startswith("SEED=2 ") and calls[5].endswith("configs/l2_spec_1m.toml")


def test_sweep_timing_and_test_only(roihu_env: dict[str, str], tmp_path: Path) -> None:
    log = _appending_sbatch(roihu_env, tmp_path)
    env = {**roihu_env, "STUB_ARCH": "aarch64"}
    args = ["--timing", "--test-only", "--seeds", "0,1", "configs/l2_flex_1m.toml"]
    assert _run("sweep.sh", args, env).returncode == 0
    calls = log.read_text().splitlines()
    assert len(calls) == 1 and "--test-only" in calls[0]
    assert calls[0].endswith("hpc/roihu/timing.sbatch configs/l2_flex_1m.toml")


@pytest.mark.parametrize(
    "args",
    [[], ["--seeds", "a", "configs/l2_flex_1m.toml"], ["configs/missing.toml"], ["--bogus", "x"]],
)
def test_sweep_rejects_bad_input(
    roihu_env: dict[str, str], tmp_path: Path, args: list[str]
) -> None:
    log = _appending_sbatch(roihu_env, tmp_path)
    assert _run("sweep.sh", args, {**roihu_env, "STUB_ARCH": "aarch64"}).returncode == 2
    assert not log.exists()


def test_evaluate_and_export_cover_every_band_set() -> None:
    evaluate = (ROIHU / "evaluate.sbatch").read_text()
    export = (ROIHU / "export.sbatch").read_text()
    assert evaluate.count("--band-set all") == 2
    assert export.count("--band-set all") == 2
    default = re.search(r"PERTURBATIONS:-([^}]*)\}", evaluate)
    assert default is not None
    for text in default.group(1).split():
        Perturbation.parse(text)


def test_every_shell_script_is_in_the_shellcheck_list(repo_root: Path) -> None:
    """make shellcheck covers hpc/*.sh, hpc/*.sbatch and jetson/*.sh; no script hides elsewhere."""
    listed = subprocess.run(
        ["git", "ls-files", "hpc", "jetson"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for name in listed:
        path = repo_root / name
        first = path.read_bytes()[:64].split(b"\n", 1)[0]
        is_shell = first.startswith(b"#!") and b"sh" in first.rsplit(b"/", 1)[-1]
        if is_shell or name.endswith((".sh", ".sbatch")):
            assert name.endswith((".sh", ".sbatch")), f"{name}: rename to .sh so shellcheck sees it"
