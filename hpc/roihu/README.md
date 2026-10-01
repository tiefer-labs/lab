<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# CSC Roihu guide

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Step by step: how to set up Tiefer Lab on the CSC Roihu supercomputer, build the data cache, train, evaluate and export the cloud filter, and bring the results back.

---

## 1. Requirements

- A CSC project with Roihu GPU access and GPU billing units.
- SSH access to `roihu-cpu.csc.fi` (x86) and `roihu-gpu.csc.fi` (ARM) with a MyCSC-signed certificate.
- The project name, written below as `<project>`, and your CSC user name, written as `<user>`. Replace both with your own values in every command.
- CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. **Confirm with the project PI or the CSC Service Desk before the first job.** This is the founder's decision.

---

## 2. Before you start

1. Check the remaining GPU billing units of the project. One GPU hour costs 200 GPU BU ([billing](https://docs.csc.fi/computing/hpc-billing/)):

   ```bash
   csc-projects
   ```

2. Before each new kind of job, check its request without submitting it (from the repository folder, after step 1). `submit.sh` passes options written before the job script on to `sbatch`; `--test-only` validates the request and prints when it would start:

   ```bash
   bash hpc/roihu/submit.sh --test-only hpc/roihu/smoke.sbatch
   bash hpc/roihu/submit.sh --test-only hpc/roihu/train.sbatch configs/l1_base.toml
   ```

3. Know where things run. Login nodes are for light work only: "one-core jobs that finish in minutes and require less than 1 GiB of memory" ([usage policy](https://docs.csc.fi/computing/usage-policy/)). The data cache is therefore built in a CPU job, never on a login node.

---

## 3. Steps

### Step 1: clone and set the project

Log in to the x86 login node, clone into `/projappl`, and set the project once in `~/.bashrc`:

```bash
ssh <user>@roihu-cpu.csc.fi
mkdir -p /projappl/<project>/tiefer-lab
git clone https://github.com/tiefer-labs/lab.git /projappl/<project>/tiefer-lab/src
cd /projappl/<project>/tiefer-lab/src
echo 'export TIEFER_CSC_PROJECT=<project>' >> ~/.bashrc
source ~/.bashrc
echo "${TIEFER_CSC_PROJECT}"
```

> [!WARNING]
> Never paste the literal text `<project>` into `~/.bashrc`: type your project name in its place before you press Enter. The scripts stop with `is not a CSC project name` when they find the placeholder. To remove such a line, find it, delete it, and add the correct one:
>
> ```bash
> grep -n 'TIEFER_CSC_PROJECT' ~/.bashrc
> sed -i '/TIEFER_CSC_PROJECT=<project>/d' ~/.bashrc
> ```

Data, runs and reports go to `/scratch/<project>/tiefer-lab/`; the code and the virtual environments stay in `/projappl/<project>/tiefer-lab/`.

### Step 2: set up both architectures

GPU nodes are ARM (`aarch64`) and CPU nodes are x86, so `setup.sh` runs once on each side. It loads the Python module for the architecture, creates `venv-<architecture>`, installs `hpc/roihu/requirements.txt` and the package, and runs `check_env.py`.

CPU side (`venv-x86_64`), on `roihu-cpu.csc.fi`:

```bash
bash hpc/roihu/setup.sh
```

GPU side (`venv-aarch64`). From the x86 login shell, open a 15 minute shell on one GH200 GPU with `gpu_shell.sh` and run setup there; the environment check then also sees the GPU:

```bash
bash hpc/roihu/gpu_shell.sh
bash hpc/roihu/setup.sh
exit
```

Or log in to the ARM login node and run setup there:

```bash
ssh <user>@roihu-gpu.csc.fi
cd /projappl/<project>/tiefer-lab/src
bash hpc/roihu/setup.sh
```

### Step 3: build the data cache

```bash
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
squeue --me
```

The job runs on the CPU partition `small` with 16 cores, one parallel download worker per core (`SLURM_CPUS_PER_TASK`). It keeps only high quality 509 x 509 patches and prints the kept and dropped counts per split. The build is resumable: if the job stops, submit the same command again and it continues where it stopped.

Its log starts with the metadata columns of the dataset. If it stops because the split field is missing, see the troubleshooting table.

### Step 4: smoke job on `gputest`

```bash
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
squeue --me
ls /scratch/<project>/tiefer-lab/runs/slurm/
```

The smoke job checks the environment, trains `configs/smoke.toml` for a few steps and evaluates it on validation; its outputs are labelled smoke and are never results. If the full cache from step 3 does not exist yet, it first builds a tiny cache (32 training and 16 validation patches) under `/scratch/<project>/tiefer-lab/smoke/` and skips the timing run.

With the full cache, the job ends with a timing run of `configs/l1_base.toml` (one epoch cut to 50 steps). Its log line `full epoch ... s (estimated)` is the time per epoch of the real training on this GPU; multiply by the number of epochs to plan the `--time` of the training job:

```bash
grep "full epoch" /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
```

### Step 5: train on `gpumedium`

Each training job uses one GPU. The run ID is printed in the log (`run directory: $TIEFER_RUNS_DIR/<run-id>`) and contains the seed, for example `l1_base-seed0-<time>-<commit>`. If the time limit is reached, the job saves `last.pt` and stops; submit again with the run ID to continue:

```bash
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml <run-id>
```

The default time is 12 hours; `gpumedium` allows up to 36 hours. Set a longer time from the estimate of step 4:

```bash
bash hpc/roihu/submit.sh --time=24:00:00 hpc/roihu/train.sbatch configs/l1_base.toml
```

Optional: two seeds. Submit two separate one-GPU jobs. `SEED` overrides the seed of the configuration and is recorded in the run metadata and the run ID, so the two runs never share a run folder. Each job is billed for its own GPU hours:

```bash
SEED=0 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml
SEED=1 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml
```

To resume one of them, pass its run ID as above; the seed then comes from the run itself.

### Step 6: evaluate, export, final test, usage, collect

Evaluate on validation with the baselines, then export and quantise:

```bash
bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

The test split is only for the final evaluation. It needs `FINAL=1` and a reason without commas or quotes, and every such run is logged in `test_log.md`:

```bash
FINAL=1 REASON="<why>" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

Record the compute used by each job, then pack the results:

```bash
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
```

On your own computer, copy the archive and unpack it into the repository. The results are processed there (`make results`):

```bash
scp <user>@roihu-cpu.csc.fi:/scratch/<project>/tiefer-lab/collect/tiefer-<run-id>.tar.gz .
tar -xzf tiefer-<run-id>.tar.gz -C <path-to-lab>
```

---

## 4. Files

| File | Purpose |
| :--- | :---: |
| `job_prelude.sh` | sourced first by every job and by `setup.sh`: `HOME` and `USER` from `getent passwd` when empty, `/etc/profile` when `module` is missing, `module purge` |
| `shell_options.sh` | turns off `errexit`, `nounset` and `pipefail` around `/etc/profile` and every `module` command, then restores the saved options |
| `env.sh` | sourced after the prelude: module, venv, `PIP_CACHE_DIR` and `TIEFER_*` paths; stops when `TIEFER_CSC_PROJECT` is unset or not a project name |
| `setup.sh` | one-time setup per architecture: venv, `requirements.txt`, the package, environment check |
| `gpu_shell.sh` | interactive shell on one GH200 GPU in `gputest` for 15 minutes, to run `setup.sh` for the GPU side |
| `check_env.py` | imports every dependency, prints versions, architecture, GPU, CUDA and bf16 support |
| `requirements.txt` | generated from `uv.lock` with `make requirements`, without `torch` and its own dependencies |
| `submit.sh` | `sbatch` with `--account`, `--export=NONE,TIEFER_CSC_PROJECT=...` and the log location; passes `SEED`, `FINAL`, `REASON` and module overrides when set |
| `data.sbatch` | builds the cache in `/scratch` on a CPU node, on either architecture |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: check, smoke training, validation evaluation, timing run of `configs/l1_base.toml` |
| `train.sbatch` | `gpumedium`, 1 GPU, 12 hours by default, SIGUSR1 300 s before the limit, resumable, optional `SEED` |
| `evaluate.sbatch` | validation with baselines; test only with `FINAL=1` and `REASON` |
| `export.sbatch` | ONNX export, check against PyTorch, INT8 quantisation |
| `usage.sh` | `sacct` record of a job, written to `reports/compute/<job-id>.json` |
| `collect.sh` | packs reports, run metadata, best checkpoint and ONNX files, with relative paths only |

Every job script starts with `#!/bin/bash -l` and `#SBATCH --export=NONE`, so nothing leaks in from the submitting shell. GPU jobs stop unless they run on an `aarch64` node. Slurm logs go to `$TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out`. GPU jobs copy the cache to the job's local disk (`$TMPDIR`) at start when there is room.

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `TIEFER_CSC_PROJECT is not set` | the project is not exported in this shell | add the line of step 1 to `~/.bashrc` and run `source ~/.bashrc` |
| `is not a CSC project name` | `~/.bashrc` holds the literal placeholder `<project>` | remove the line as shown in step 1 and add it again with your project name |
| `the 'module' command is not available` | the job or shell started without the system profile, even after `/etc/profile` | start from a login shell on `roihu-cpu.csc.fi` or `roihu-gpu.csc.fi`; if it persists, contact the CSC Service Desk |
| `needs an aarch64 GH200 node, but runs on x86_64` | a GPU job ran on an x86 node, for example after a partition override | submit without overriding `--partition`; GPU jobs need a GPU partition |
| `no virtual environment .../venv-aarch64` | `setup.sh` has not been run on the GPU side | run step 2, GPU side, with `gpu_shell.sh` |
| `no virtual environment .../venv-x86_64` | `setup.sh` has not been run on the CPU side | run step 2, CPU side, on `roihu-cpu.csc.fi` |
| `missing modules` in `check_env.py` | the venv was built with another module or is incomplete | run `setup.sh` again on the same architecture |
| `cannot load python-pytorch/2.10` | the module was removed or renamed | find it with `module avail python-pytorch`, add `export TIEFER_PYTORCH_MODULE=<name>` to `~/.bashrc`, run `setup.sh` again on the GPU side; `submit.sh` passes it to jobs |
| `cannot load python-data/3.12-31.03` | the module was removed or renamed | find it with `module avail python-data`, add `export TIEFER_CPU_PYTHON_MODULE=<name>` to `~/.bashrc`, run `setup.sh` again on the CPU side |
| `the split field 'tortilla:data_split' is not in the metadata` | the dataset uses another name for the split field | find it in the `metadata columns` line of the log, set `SPLIT_FIELD` and `SPLIT_VALUES` in `src/tiefer_lab/data/source.py`, commit, and submit the data job again |
| The data job fails with a network error | compute nodes cannot reach `huggingface.co` | stop and ask the CSC Service Desk; do not build the cache on a login node |
| `stopped after ... of ...` in the data log | the job hit its time limit or a read failed | submit the same data job again; it continues |
| `REASON cannot contain commas or quotes` | `sbatch --export` splits its list on commas | write the reason without commas or quotes |
| `invalid partition` from `sbatch` | a partition name differs on Roihu | check `sinfo` and the [partitions page](https://docs.csc.fi/computing/running/batch-job-partitions/), then edit the `#SBATCH --partition` line |
| The training log ends with `interrupted` | the time limit was reached | submit `train.sbatch` again with the run ID |
| `the test split is only for final evaluation` | test was requested without `FINAL=1` and `REASON` | evaluate on validation; use test once, for the final result |

---

## 6. Facts the scripts depend on

Facts from the CSC documentation were checked on 1 October 2026; each row links its page. Facts marked as observed were seen on Roihu on 1 October 2026. Rows marked `TODO(verify)` are still open.

| Fact | Used in | Source |
| :--- | :---: | :---: |
| **Nodes and login** | | |
| GPU nodes are ARM with NVIDIA GH200, 4 GPUs per node; per GPU up to 72 cores, 95 GiB HBM3 and 117 GiB LPDDR5 | GPU job scripts | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| CPU nodes are AMD x86 | `data.sbatch`, `env.sh` | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Login nodes `roihu-gpu.csc.fi` (ARM) and `roihu-cpu.csc.fi` (x86) | `setup.sh`, this guide | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Login nodes are for light work only: "one-core jobs that finish in minutes and require less than 1 GiB of memory" | `data.sbatch`, this guide | [usage policy](https://docs.csc.fi/computing/usage-policy/) |
| **Slurm** | | |
| `gputest` 15 minutes; `gpumedium` 36 hours, up to 4 GPUs on one node; `gpularge` 36 hours, several nodes; `gpuinteractive` 12 hours | GPU job scripts, `gpu_shell.sh` | [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| CPU partition `small`: 72 hours, 1 node | `data.sbatch` | [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| `--account` is mandatory; GPUs are requested with `--gres=gpu:gh200:<n>`; Slurm adds memory per GPU automatically | `submit.sh`, job scripts | [job scripts on Roihu](https://docs.csc.fi/computing/running/creating-job-scripts-roihu/) |
| 200 GPU BU per GPU hour; up to 72 cores and 212 GiB memory per GPU included, so GPU jobs request `--cpus-per-task=72` | GPU job scripts | [billing](https://docs.csc.fi/computing/hpc-billing/) |
| `$TMPDIR` is set for every job without a request; its sizes are listed on the partitions page | `env.sh` (`tiefer_stage_cache`) | [Roihu FAQ](https://docs.csc.fi/support/faq/roihu/); sizes: [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| **Software** | | |
| The PyTorch module `python-pytorch/2.10` | `env.sh` (`TIEFER_PYTORCH_MODULE`) | [GPU and ML guide](https://docs.csc.fi/support/tutorials/gpu-ml/) |
| `module avail python-pytorch` lists `python-pytorch/2.10` and `python-pytorch/2.13` (default) | `env.sh` (`TIEFER_PYTORCH_MODULE`) | observed on Roihu, 1 October 2026 |
| On a GPU node, `python-pytorch/2.10` gives Python 3.12.12, torch 2.10.0+cu130, CUDA runtime 13.0, GH200 visible, bf16 supported | `setup.sh`, `check_env.py` | observed |
| On x86, `python-data/3.12-31.03` gives Python 3.12.13 | `env.sh` (`TIEFER_CPU_PYTHON_MODULE`) | observed on Roihu, 1 October 2026 |
| Extra packages go into a venv made with `python3 -m venv --system-site-packages` on top of the loaded module | `setup.sh` | [Python guide](https://docs.csc.fi/support/tutorials/python-usage-guide/) |
| GPU compute nodes reach PyPI, so `setup.sh` installs from a `gpu_shell.sh` session | `setup.sh`, `gpu_shell.sh` | observed |
| **Storage and network** | | |
| Files in `/scratch` unused for 180 days are deleted | `env.sh` | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Whether compute nodes can reach `huggingface.co` | `data.sbatch`, `smoke.sbatch` | TODO(verify): the first data job shows it |

---

## Changelog

- 1 October 2026: source links corrected for `$TMPDIR`, the `/scratch` cleanup, the PyTorch module and the venv rule; `python-data/3.12-31.03` is marked as observed only.
- 1 October 2026: steps reordered (clone and project, setup on both architectures, data job, smoke job, training with optional seeds, evaluation to collection); "Before you start" added; the login node cache path removed; facts checked against the CSC documentation and on Roihu; new troubleshooting cases from a real job failure.
- 1 October 2026: the smoke job measures the time per epoch of `configs/l1_base.toml`.
- 1 October 2026: GPU jobs request 72 cores; data loader workers follow `SLURM_CPUS_PER_TASK`.
- 1 October 2026: sections ordered as Requirements, Steps, Files, Troubleshooting, then the facts to verify.
- 1 October 2026: first version for milestone L1; CSC facts marked `TODO(verify)`.
