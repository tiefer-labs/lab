<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# CSC Roihu guide

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Step by step: how to set up Tiefer Lab on the CSC Roihu supercomputer, build the data cache, train, evaluate and export the cloud filter, and bring the results back. Run Lab once on your own computer first ([GETTING-STARTED.md](../../GETTING-STARTED.md)); other platforms are in [INSTALL.md](../../INSTALL.md). Before a job, add the run with its cost to [plan.md](plan.md), and read the test split only as [POLICY.md](../../POLICY.md), gates 3 and 7, allow.

---

## 1. Requirements

- A CSC project with Roihu GPU access and GPU billing units.
- Access to the x86 login node `roihu-cpu.csc.fi`, by SSH from your own computer with a MyCSC-signed certificate, or as a Roihu-CPU shell in the web interface at [www.roihu.csc.fi](https://www.roihu.csc.fi). Every step of this guide runs from there; the ARM login node `roihu-gpu.csc.fi` is not needed, but GPU jobs submitted from it work the same way.
- The project name, written below as `<project>`, and your CSC user name, written as `<user>`. Replace both with your own values in every command.
- CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. **Confirm with the project PI or the CSC Service Desk before the first job.** This is the founder's decision.

---

## 2. Before you start

1. Check the remaining GPU billing units of the project. One GPU hour costs 200 GPU BU ([billing](https://docs.csc.fi/computing/hpc-billing/)):

   ```bash
   csc-projects
   ```

2. Before each new kind of job, check its request without submitting it (from the repository folder on `roihu-cpu.csc.fi`, after step 1). `submit.sh` passes options written before the job script on to `sbatch`; `--test-only` validates the request and prints when it would start:

   ```bash
   bash hpc/roihu/submit.sh --test-only hpc/roihu/smoke.sbatch
   bash hpc/roihu/submit.sh --test-only hpc/roihu/train.sbatch configs/sieb.toml
   ```

3. Know where things run. Everything is submitted from `roihu-cpu.csc.fi`; the jobs run on the nodes below:

   | Work | Runs on | Environment of the job |
   | :--- | :---: | :---: |
   | CPU setup (`venv-x86_64`, `setup_cpu.sbatch`), the source check, the CPU jobs of evaluation, calibration, export and diagnosis, and the CPU timing (`timing_cpu.sbatch`, `medium`) | x86 CPU nodes | sbatch's default export: the submitting shell's environment |
   | survey and data jobs | x86 CPU nodes | sbatch's default export: the submitting shell's environment |
   | GPU setup (`venv-aarch64`), smoke, timing, training, evaluation and export jobs | ARM GH200 nodes | built on the GPU node |

   CPU nodes are x86 like `roihu-cpu.csc.fi`, so a CPU job can take the login shell's environment. GPU nodes are ARM, so a GPU job must not: `submit.sh` passes it only `HOME`, `CSC_ENV_INIT_NON_INTERACTIVE=yes` and the variables the jobs read, and the job, a login shell, initialises the CSC environment and the module system of its own node. This is CSC's way of submitting across architectures ([submitting jobs across architectures](https://docs.csc.fi/computing/running/submitting-jobs-across-architectures/)). CPU jobs are refused on `roihu-gpu.csc.fi`.

4. Login nodes are for light work only: "one-core jobs that finish in minutes and require less than 1 GiB of memory" ([usage policy](https://docs.csc.fi/computing/usage-policy/)). The data cache is therefore built in a CPU job, never on a login node.

---

## 3. Steps

### Step 0 runbook: from a fresh account to a finished smoke job, device check and source check

Step 0 of [plan.md](plan.md), command by command, in the order to type them on Roihu. `<project>` is the CSC project name and `<user>` the CSC user name: type your own values in their place, and remove both from anything you send back. `<job-id>` is the number `sbatch` prints (`Submitted batch job <job-id>`). The longer explanations are in steps 1, 2 and 4 below.

**Who runs what.** You, the maintainer, type every command on Roihu yourself. Whoever prepares these commands with an AI-assisted system on a third-party service never receives, and never asks for, your CSC password, SSH keys or FirecREST tokens, and nothing in this repository starts an MCP server, a reverse tunnel or any other service on Roihu that would let such a system run commands there ([CSC usage policy](https://docs.csc.fi/computing/usage-policy/), page of 15 October 2026, read 16 October 2026; [AI_ASSISTANCE.md](../../AI_ASSISTANCE.md), section 4). Every command lists only your own jobs and processes (`squeue --me`, `sacct -u "$USER"`); never run `squeue`, `sacct -a`, `who`, `top` or `ps aux` without restriction, and never send other users' names, jobs or processes. Check a job once when you expect it to have ended, not in a loop.

**Login node or job.** The login node is only for editing, submitting jobs, moving data and one-core work of minutes under 1 GiB (same page). Each step below says where it runs: cloning and submitting on the login node; the setup, the smoke job with the device check, the source check and every data step as batch jobs.

**Where files go.** Home is billed at 10 storage BU per TiB-hour, like `/projappl` ([billing](https://docs.csc.fi/computing/hpc-billing/), read 16 October 2026), so nothing but two lines of `~/.bashrc` goes there. The source, the Python environments and the persistent files (the candidates' run folders) live in `/projappl/<project>/tiefer-lab/`; the caches, downloads, run folders, reports, logs, the pip cache and every other cache (`XDG_CACHE_HOME`) in `/scratch/<project>/tiefer-lab/`; temporary files of a job in its local `$TMPDIR`. `env.sh` sets all of these; never move any of them to `$HOME`. Scratch files not accessed for 180 days are deleted by CSC (projects with less than 5 TiB of scratch quota), which is why the candidates' run folders are copied to `/projappl`.

1. On the login node: log in and check its architecture.

   ```bash
   ssh <user>@roihu-cpu.csc.fi
   uname -m
   ```

   Prints `x86_64`.

2. On the login node: read the balance and the cleaning cycle of the project. These numbers stay with you; they are not sent back.

   ```bash
   csc-projects
   csc-workspaces
   ```

   `csc-projects` prints the GPU, CPU, storage and cloud billing units; expected: 10,000 GPU BU, 60,000 CPU BU and 30,000 storage BU (section 2 of [plan.md](plan.md)). `csc-workspaces` prints the quotas and the scratch cleaning cycle.

3. On the login node: set the project once in `~/.bashrc`, and the balance in this shell. `submit.sh` and `sweep.sh` compute the worst case of every job before they submit it and refuse it when it does not fit in what is left minus the reserve (500 GPU BU, the reserve under the stop line); they never fetch the balance themselves. Type the numbers `csc-projects` printed in step 2, and set them again in each new shell:

   ```bash
   echo 'export TIEFER_CSC_PROJECT=<project>' >> ~/.bashrc
   source ~/.bashrc
   echo "${TIEFER_CSC_PROJECT}"
   export TIEFER_GPU_BU_LEFT=<GPU BU left> TIEFER_CPU_BU_LEFT=<CPU BU left> TIEFER_STORAGE_BU_LEFT=<storage BU left>
   ```

   Prints your project name, never the text `<project>` (see the warning in step 1).

4. On the login node: clone into `/projappl` and note the commit.

   ```bash
   mkdir -p /projappl/<project>/tiefer-lab
   git clone https://github.com/tiefer-labs/lab.git /projappl/<project>/tiefer-lab/src
   cd /projappl/<project>/tiefer-lab/src
   git log --oneline -1
   ```

   Prints one line with the commit.

5. As a batch job: set up the CPU side (the package, `hpc/roihu/requirements.txt` and the CPU build of torch, at most 1 hour, at most 3 CPU BU). The `TODO(verify)` of `setup.sh` is resolved here:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch
   squeue --me
   ```

   `submit.sh` prints `worst case 3.0 CPU BU (1 job(s) of 3.0); ... left after it`. When `squeue --me` no longer lists the job:

   ```bash
   tail -n 25 /scratch/<project>/tiefer-lab/runs/slurm/tiefer-setup-cpu-<job-id>.out
   sacct -u "$USER" -j <job-id> --format=JobID,State,ExitCode,Elapsed
   ```

   The log shows `architecture: x86_64`, the pip installs, then from `check_env.py`: `torch 2.10.0+cpu`, `onnxruntime ...`, `CUDA available: False`, `environment ready`, then `installed packages: ...`, `import torch and tiefer_lab: ... s` and last `setup complete: /projappl/<project>/tiefer-lab/venv-x86_64`. The state is `COMPLETED` and the exit code `0:0`. If the PyTorch CPU index cannot be reached, the log ends with a pip error.

6. As a batch job: set up the GPU side with a `gputest` job (at most 15 minutes, at most 50 GPU BU).

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
   squeue --me
   ```

   When it has ended:

   ```bash
   tail -n 25 /scratch/<project>/tiefer-lab/runs/slurm/tiefer-setup-gpu-<job-id>.out
   sacct -u "$USER" -j <job-id> --format=JobID,State,ExitCode,Elapsed
   ```

   The log shows the lines listed in step 2 below, ending with `environment ready`, `import torch and tiefer_lab: ... s` and `setup complete: .../venv-aarch64`; the state is `COMPLETED`, the exit code `0:0`.

7. As a batch job: the smoke job (at most 15 minutes, at most 50 GPU BU). It trains `configs/smoke.toml` for a few steps on a tiny cache, evaluates it, and runs the device check: evaluation on the CPU against evaluation on the GH200, on a fixed input (`tiefer_lab.device_check`).

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
   squeue --me
   ```

   When it has ended:

   ```bash
   grep -E "^(job environment|environment):" /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
   tail -n 40 /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
   sacct -u "$USER" -j <job-id> --format=JobID,State,ExitCode,Elapsed
   ```

   The first command prints `(aarch64)`, `module environment built on this node`, `module python-pytorch/2.10` and a `venv-aarch64` path. The tail ends with `== smoke run finished (outputs are labelled smoke and are never results)` and a JSON summary whose `device_check` shows `"device": "cuda"`, `"precision": "bf16"` and `"passed": true`, with its `agreement` and `max_abs_logit_difference`. The state is `COMPLETED`, the exit code `0:0`. A failed device check ends the job with `CPU and cuda argmax disagree`.

8. As a batch job: the source check, HEAD requests only, without downloading anything or sending a credential (at most 1 hour, at most 0.8 CPU BU).

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/check_sources.sbatch
   squeue --me
   ```

   When it has ended:

   ```bash
   cat /scratch/<project>/tiefer-lab/runs/slurm/tiefer-sources-<job-id>.out
   sacct -u "$USER" -j <job-id> --format=JobID,State,ExitCode,Elapsed
   ```

   Prints one line per source, `<source>: <obtainable> (<files> files, <bytes> bytes); <why>`, and `report: $TIEFER_REPORTS_DIR/data/sources.json`. Expected: `yes` for CloudSEN12+, the Catalogue, KappaSet, L8 Biome, L8 SPARCS, s2cloudless and both CD-FCNN models; `licence not stated` for both KappaMask models and Fmask; `not checked` for UNetMobV2.

9. On the login node: record the usage of the four jobs as report files, and pack the reports.

   ```bash
   bash hpc/roihu/usage.sh <setup-cpu-job-id>
   bash hpc/roihu/usage.sh <setup-gpu-job-id>
   bash hpc/roihu/usage.sh <smoke-job-id>
   bash hpc/roihu/usage.sh <sources-job-id>
   ```

   Each prints the job's own `sacct` record and writes `reports/compute/<job-id>.json`.

**Send back**, with `<project>` and `<user>` removed from every line, and nothing about other users or the project's balance:

- the commit of step 4;
- the four job IDs, each with its `State` and `ExitCode` from `sacct`;
- our own logs: the last 25 lines of the setup logs of steps 5 and 6, and the last 40 lines of the smoke log of step 7 (with its `device_check` block);
- our own reports: the source check log of step 8 with `$TIEFER_REPORTS_DIR/data/sources.json`, and the four `reports/compute/<job-id>.json` of step 9.

With these, the `TODO(verify)` facts of step 0 are resolved (the CPU build of torch and its import time, the device check on GH200), and the plan's revision for the timing step (step 2) can start. The `/projappl` sizes for the storage table come from your own `csc-workspaces` at that revision.

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

GPU nodes are ARM (`aarch64`) and CPU nodes are x86, so `setup.sh` runs once on each side, each time as a batch job: installing packages is not light work, so it never runs on a login node, and `setup.sh` stops outside a Slurm job. It loads the Python module for the architecture, creates `venv-<architecture>` in `/projappl`, installs `hpc/roihu/requirements.txt` and the package (on x86 also the CPU build of torch), runs `check_env.py`, and prints the number of packages and the time to import torch. Both sides are submitted from `roihu-cpu.csc.fi`.

CPU side (`venv-x86_64`), as a short job on the `small` partition (at most 1 hour, at most 3 CPU BU):

```bash
bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch
squeue --me
```

GPU side (`venv-aarch64`), as a short `gputest` job on one GH200 (at most 15 minutes, at most 50 GPU BU). `setup_gpu.sbatch` runs `setup.sh` on the GPU node with `python-pytorch/2.10`, and fails when no GPU is visible:

```bash
bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
squeue --me
```

When the job has ended, read its log and its state:

```bash
cat /scratch/<project>/tiefer-lab/runs/slurm/tiefer-setup-gpu-<job-id>.out
sacct -u "$USER" -j <job-id> --format=JobID,State,Elapsed
```

The log must show, in this order: `job environment: node ... (aarch64), submitted on x86_64, module environment built on this node`; `environment: aarch64, module python-pytorch/2.10, python3 ...`; `architecture: aarch64`; the package versions of `check_env.py`; `CUDA available: True`; `GPU: NVIDIA GH200 ...`; `bf16 supported: True`; `environment ready`; and `setup complete: .../venv-aarch64`. The state is `COMPLETED`. After a change to `hpc/roihu/requirements.txt`, submit the job again.

### Step 3: survey the dataset, then build the data cache

Before a new build, run the survey: a short CPU job that reads the metadata and a few patches of every label type and writes `$TIEFER_REPORTS_DIR/data/survey.json` (counts by label type, patch size and split; locations shared with the validation and test splits; how labels and reference masks are encoded). Facts the code depends on are taken from this report, not assumed. From `roihu-cpu.csc.fi`; no token is needed (the optional token is described below):

```bash
bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch
cat /scratch/<project>/tiefer-lab/reports/data/survey.json
```

From `roihu-cpu.csc.fi`. The build needs no token, login or licence acceptance:

```bash
ssh <user>@roihu-cpu.csc.fi
cd /projappl/<project>/tiefer-lab/src
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
squeue --me
```

A Hugging Face token is optional, not required. Without one the server may answer HTTP 429 (too many requests) more often, and the builder pauses and continues (below). If you choose to use one, it must be a read-only token; it only raises the rate limit. Set it in the submitting shell with `read -rsp "Hugging Face token: " HF_TOKEN && export HF_TOKEN && echo`, which keeps it off the screen and out of the shell history; the job inherits it through sbatch's default export. It is never written to any file, log or report: the builder passes it to GDAL without printing it and redacts it from every error message (`tests/test_cache.py::test_no_report_or_log_of_a_build_contains_the_token`). `check_sources.sbatch` unsets it.

The job runs on the CPU partition `small` with 16 cores, one parallel download worker per core (`SLURM_CPUS_PER_TASK`). It keeps only high quality 509 x 509 patches and prints the kept and dropped counts per split. The build is resumable: if the job stops, submit the same command again and it continues where it stopped.

The log says `Hugging Face token: set` or `not set`, never the token itself. When the server still answers HTTP 429, every reader pauses together and then continues: for the server's `Retry-After` when it is known, otherwise 10 s, 20 s, 40 s and so on up to 300 s, with random jitter. A read that fails part way, which happens when the server answers with an error page instead of data, is treated the same: the log says `read failed (RasterioIOError: ...); all readers pause` and the patch is read again. After 12 attempts the job stops, names the patch and says that the build is resumable. Never write the token into `~/.bashrc`, a file in the repository or any other file.

Its log starts with the metadata columns of the dataset. If it stops because the split field is missing, see the troubleshooting table.

#### All 13 bands, in shards

The band-flexible models read all 13 Level-1C bands from one cache, `cloudsen12-l1c-all`. With all bands a 509 x 509 patch takes about 6.7 MiB, so the cache needs about 6.7 MiB times the number of patches of each split; the merge needs one shard more at its peak. The builder prints its estimate and stops when the file system has less free space, but the project quota on `/scratch` can be lower than that: check it first (`TODO(verify)` the command on [docs.csc.fi](https://docs.csc.fi/computing/disk/)).

Run the 4-band build and the 13-band build one after the other, not at the same time: submit the 13-band jobs only when `data.sbatch all` has finished and its log says every split is complete. All data jobs read from the same server, and several builds at once push it into rate limits and error pages.

The training split is read by four CPU jobs side by side, each into its own folder, and merged afterwards. `--max-rate` caps the reads per minute of the whole split and is shared between the shards; keep the four shards at one shared `--max-rate 120`, and lower it when the log shows HTTP 429:

```bash
for i in 0 1 2 3; do
  bash hpc/roihu/submit.sh hpc/roihu/data.sbatch train --name cloudsen12-l1c-all --bands all --shard "$i/4" --max-rate 120
done
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch val --name cloudsen12-l1c-all --bands all --max-rate 30
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch test --name cloudsen12-l1c-all --bands all --max-rate 30
# when all four shards say "complete":
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch train --name cloudsen12-l1c-all --bands all --merge 4
```

Every shard job is resumable on its own: submit the same line again after a stop. The merge refuses to start until every shard is complete, deletes each shard after copying it, and is resumable too.

#### Check the padding of a cache

The dataset pads each 509 x 509 patch to 512 x 512 ([docs/DATA.md](../../docs/DATA.md), sections 4 and 5). This read-only check shows which sides hold the padding and which label values are there. It reads up to 50 patches memory-mapped and writes nothing, so it runs on the login node; on the synthetic test cache it takes 0.016 s for 50 patches of 512 x 512 (on CSC Roihu: `not measured`). From `roihu-cpu.csc.fi`, after step 2:

```bash
source hpc/roihu/env.sh
python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-high --split val --patches 50
python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-high --split test --patches 50
python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-all --split val --patches 50
python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-all --split test --patches 50
```

Each command ends with `zero sides found: ...` and exits with 1 when those sides differ from `PADDING_SIDES` in `src/tiefer_lab/data/padding.py`. Copy the output into the issue or the pull request that records it.

### Step 4: smoke job on `gputest`

This and every later GPU job is submitted from `roihu-cpu.csc.fi`, like the CPU jobs:

```bash
cd /projappl/<project>/tiefer-lab/src
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
squeue --me
ls /scratch/<project>/tiefer-lab/runs/slurm/
```

Every GPU job log starts with two lines that show its environment. Check them in the first job after a change to the scripts or to Roihu:

```bash
grep -E "^(job environment|environment):" /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
```

They must say `(aarch64)`, `module environment built on this node`, `module python-pytorch/2.10` and a `venv-aarch64` path without `(missing)`. `inherited from the login node` in a GPU job means it was not submitted with `submit.sh`.

The smoke job checks the environment, trains `configs/smoke.toml` for a few steps and evaluates it on validation; its outputs are labelled smoke and are never results. If the train and val splits of the full cache from step 3 are not complete yet (missing, or `data.sbatch` still building them), it builds a tiny cache (32 training and 16 validation patches) in `/scratch/<project>/tiefer-lab/smoke/data/` instead and skips the timing run. Its log names the folder it uses (`full cache: ...` or `tiny smoke cache: ...`). The smoke job only reads the full cache and never writes to it, so it can run while `data.sbatch` is running.

With the full cache, the job ends with a timing run of `configs/sieb_base.toml` (one epoch cut to 50 steps). Its log line `full epoch ... s (estimated)` is the time per epoch of the real training on this GPU; multiply by the number of epochs to plan the `--time` of the training job:

```bash
grep "full epoch" /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
```

### Step 5: train on `gpumedium`

Train `configs/sieb.toml`: `sieb_base` run to the end of its 150-epoch cosine schedule, with a learning rate warm-up and a moving average of the weights (the reasons are in [ASSUMPTIONS.md](../../docs/ASSUMPTIONS.md), section 6). Its time per epoch comes from the timing job of step 4. `configs/sieb_base.toml` stays unchanged.

Each training job uses one GPU. The run ID is printed in the log (`run directory: $TIEFER_RUNS_DIR/<run-id>`) and contains the seed, for example `sieb_base-seed0-<time>-<commit>`. If the time limit is reached, the job saves `last.pt` and stops; submit again with the run ID to continue:

```bash
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/sieb.toml
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/sieb.toml <run-id>
```

The default time is 12 hours; `gpumedium` allows up to 36 hours. Set a longer time from the estimate of step 4:

```bash
bash hpc/roihu/submit.sh --time=24:00:00 hpc/roihu/train.sbatch configs/sieb.toml
```

Optional: two seeds. Submit two separate one-GPU jobs. `SEED` overrides the seed of the configuration and is recorded in the run metadata and the run ID, so the two runs never share a run folder. Each job is billed for its own GPU hours:

```bash
SEED=0 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/sieb.toml
SEED=1 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/sieb.toml
```

To resume one of them, pass its run ID as above; the seed then comes from the run itself.

### Step 6: evaluate, export, final test, usage, collect

Evaluate on validation with the baselines, then export and quantise:

```bash
bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

Both jobs cover every band set of a band-flexible run. For the robustness reports, evaluate the run again under fixed sensor perturbations (by default `rescale=0.5 rescale=2 gain=0.9 gain=1.1 offset=0.01 noise=0.01 blur=1`; set `PERTURBATIONS` to change the list):

```bash
ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

The test split is only for the final evaluation. It needs `FINAL=1` and a reason, and every such run is logged in `test_log.md`:

```bash
FINAL=1 REASON="<why>" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

The protocol options of the jobs, each off unless set: `FULL_METRICS=1` adds the full metric set; `DATA=<cache>` with `REASON` evaluates an independent dataset (logged), and `SUBSTITUTE=1` reads B08 from B8A on Landsat 8; `CLOUD_BIAS=auto` and `FRACTION=soft` use the values of `calibrate.sbatch`; `EXPORT_CONFIG=configs/<name>.toml` takes the export settings of a committed config. The order of the jobs and their commands are in [plan.md](plan.md), section 3.

Record the compute used by each job, then pack the results:

```bash
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
```

On your own computer, copy the archive and unpack it into the repository. There the report files are committed unchanged and their values are copied by hand into [docs/RESULTS.md](../../docs/RESULTS.md):

```bash
scp <user>@roihu-cpu.csc.fi:/scratch/<project>/tiefer-lab/collect/tiefer-<run-id>.tar.gz .
tar -xzf tiefer-<run-id>.tar.gz -C <path-to-lab>
```

---

## 4. Files

| File | Purpose |
| :--- | :---: |
| `job_prelude.sh` | sourced first by every job and by `setup.sh`: initialises the CSC environment when `module` is missing, stops when it is still missing, sets `SLURM_EXPORT_ENV=ALL` in a job, prints the node and how its environment was made, runs `module purge` |
| `shell_options.sh` | turns off `errexit`, `nounset` and `pipefail` around every `module` command, then restores the saved options |
| `env.sh` | sourced after the prelude: module and venv of the node's architecture, `PIP_CACHE_DIR`, `TIEFER_*` paths and, on GPU nodes, `PYTORCH_CUDA_ALLOC_CONF`; prints them in a job; stops when `TIEFER_CSC_PROJECT` is unset or not a project name |
| `setup.sh` | one-time setup per architecture, inside a job only: venv in `/projappl`, `requirements.txt`, the package, the CPU build of torch on x86, environment check, import time |
| `setup_cpu.sbatch` | `small`, 4 cores, 1 hour: runs `setup.sh` on an x86 CPU node, so no setup runs on a login node |
| `budget.sh` | sourced by `submit.sh` and `sweep.sh`: the worst-case cost of a job from its time limit and resources, refused when it does not fit in the balance you typed in minus the reserve |
| `timing_cpu.sbatch` | `medium`, one full node, 1 hour: one cut epoch on the CPU, then CPU BU per epoch against the GPU packing (`reports/timing/cpu_<config>.json`) |
| `setup_gpu.sbatch` | `gputest`, 1 GPU, 15 minutes: runs `setup.sh` on a GPU node, so `venv-aarch64` is set up from `roihu-cpu.csc.fi`; fails when no GPU is visible |
| `check_env.py` | imports every dependency, prints versions, architecture, GPU, CUDA and bf16 support; fails inside a GPU job without a visible GPU |
| `requirements.txt` | generated from `uv.lock` with `make requirements`, without `torch` and its own dependencies |
| `submit.sh` | `sbatch` with `--account`, `--chdir` and the log location; GPU jobs from either login node with a short `--export` list, CPU jobs from `roihu-cpu.csc.fi` with sbatch's default export; `SEED`, `FINAL`, `REASON`, `ROBUSTNESS` and `PERTURBATIONS` reach the job as environment variables |
| `survey.sbatch` | short CPU job: counts, splits, locations and item encodings of the dataset, written to `reports/data/survey.json` |
| `data.sbatch` | builds the cache in `/scratch` on a CPU node; submitted from `roihu-cpu.csc.fi` |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: check, smoke training, validation evaluation, timing run of `configs/sieb_base.toml` |
| `train.sbatch` | `gpumedium`, 1 GPU, 12 hours by default, SIGUSR1 300 s before the limit, resumable, optional `SEED` |
| `evaluate.sbatch` | validation with baselines on every band set of the run; test only with `FINAL=1` and `REASON`; `ROBUSTNESS=1` adds the fixed sensor perturbations in `PERTURBATIONS` |
| `export.sbatch` | ONNX export per band set, check against PyTorch, INT8 quantisation |
| `timing.sbatch` | `gputest`, 1 GPU: one epoch of a config cut to 50 steps; its time per epoch replaces the estimate in `plan.md` |
| `calibrate.sbatch` | `gputest`, 1 GPU: the cloud logit bias and the temperature of a run, on validation only |
| `independent.sbatch` | CPU job: downloads an independent dataset (Zenodo, capped rate, resumable) and caches it; the Landsat 8, Kaggle and GitLab datasets are downloaded by hand into `$TIEFER_DATA_DIR/downloads/<dataset>/` |
| `check_sources.sbatch` | CPU job, `small`, 1 hour: whether every source still allowed or undecided can be obtained; HEAD requests or the first byte only, no download, no credential (it unsets `HF_TOKEN`); writes `reports/data/sources.json`, packed by `collect.sh` |
| `evaluate_all.sh` | submits one `evaluate.sbatch` job per independent dataset recorded as used whose cache is built, for one run, with `DATA`, `FULL_METRICS=1` and `REASON`; lists each one without a cache as `not evaluated: no cache` and then exits non-zero |
| `diagnose.sbatch` | CPU job: `seeds` and `frames` diagnostics, and `int8 <run-id>`, the INT8 sensitivity per Conv node, validation and training only |
| `train_packed.sbatch` | `gpumedium`, 1 GPU: several training runs at once on one reserved GPU (`<config>@<seed>` or `resume:<run-id>` per run), each with its own seed, run folder and log; the job's cores and memory are divided between them; submit with `--time` from `python -m tiefer_lab.packed time-limit` |
| `timing_packed.sbatch` | `gpumedium`, 1 GPU: the timing step of a config with 1, 2, 3 and 4 runs per GPU; time per epoch, GPU utilisation, GPU memory and data wait in `reports/timing/packing_<config>.json`, with the chosen packing |
| `evaluate_cpu.sbatch`, `calibrate_cpu.sbatch`, `export_cpu.sbatch` | CPU jobs, `small`, 32 cores and 64 GiB, submitted from `roihu-cpu.csc.fi`: evaluation, calibration and export of a run with the CPU build of torch; the plan's default, no GPU billing units. INT8 values from ONNX Runtime on the CPU are a proxy for `CMP-03`; the TensorRT values come from the Jetson |
| `model_jobs.sh` | the bodies of evaluation, calibration, export and the INT8 diagnosis, shared by the CPU and the GPU jobs |
| `diagnose_gpu.sbatch` | `gpumedium`, 1 GPU, 1 hour: INT8 sensitivity per Conv node, validation and training only |
| `sweep.sh` | submits configs and seeds as separate one-GPU jobs (`--seeds 0,1,2`, `--timing`, `--test-only`) |
| `plan.md` | the run plan of Project Schatten: budget, stop line and steps |
| `usage.sh` | `sacct` record of a job, written to `reports/compute/<job-id>.json` |
| `collect.sh` | packs reports, run metadata, best checkpoint and ONNX files, with relative paths only |

Every job script starts with `#!/bin/bash --login`, a login shell given by full path. CPU jobs inherit the submitting shell's environment; GPU jobs build their own on the GPU node (section 2, item 3). `job_prelude.sh` and `env.sh` then run `module purge` and load the module and the venv for the node's architecture. GPU jobs stop unless they run on an `aarch64` node. Slurm logs go to `$TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out`. GPU jobs copy the cache to the job's local disk (`$TMPDIR`) at start when there is room.

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `TIEFER_CSC_PROJECT is not set` | the project is not exported in this shell | add the line of step 1 to `~/.bashrc` and run `source ~/.bashrc` |
| `is not a CSC project name` | `~/.bashrc` holds the literal placeholder `<project>` | remove the line as shown in step 1 and add it again with your project name |
| `submit GPU jobs from roihu-gpu.csc.fi` | an older version of `submit.sh` | run `git pull` and submit again from `roihu-cpu.csc.fi` |
| `submit the data job from roihu-cpu.csc.fi` or `submit CPU jobs from roihu-cpu.csc.fi` | a CPU job was submitted from the ARM login node | log in to `roihu-cpu.csc.fi` and submit it there |
| `--export... is set by submit.sh` | `--export` was passed to `submit.sh` | leave `--export` out; `submit.sh` chooses it by the kind of job |
| A job ends within seconds with an empty log | an older version of the scripts, with `--export=NONE` and its profile workarounds | run `git pull` on both login nodes and submit again with `submit.sh`; never run a job script directly on a login node |
| `the 'module' command is not available in this ... job` | the job was not submitted with `submit.sh`, or the CSC initialisation of the node did not run | submit it with `hpc/roihu/submit.sh`; check that the job script starts with `#!/bin/bash --login`; if it persists, contact the CSC Service Desk with the job ID |
| A GPU job log says `module environment inherited from the login node` | the job was submitted with `sbatch` directly, so it took the login node's environment | submit it with `hpc/roihu/submit.sh` |
| `ModuleNotFoundError: No module named 'torch'` in a survey or data job | an older version imported torch in a CPU job; `venv-x86_64` has no torch | run `git pull` and submit the job again |
| `needs an aarch64 GH200 node, but runs on x86_64` | a GPU job ran on an x86 node, for example after a partition override | submit without overriding `--partition`; GPU jobs need a GPU partition |
| `no virtual environment .../venv-aarch64` | the GPU side has not been set up | submit `setup_gpu.sbatch` (step 2, GPU side) |
| `setup_gpu.sbatch` ends `FAILED` with `no GPU visible inside a GPU job` | the job got no GPU, or the PyTorch module does not see it | check the `--gres` line and the `CUDA available` line of the log; submit again, and contact the CSC Service Desk with the job ID if it repeats |
| `no virtual environment .../venv-x86_64` | `setup.sh` has not been run on the CPU side | submit `setup_cpu.sbatch` (step 2, CPU side) |
| `run the setup as a job, not on a login node` | `setup.sh` was started on a login node | submit `setup_cpu.sbatch` or `setup_gpu.sbatch` |
| `set TIEFER_GPU_BU_LEFT` (or `CPU`, `STORAGE`) | the balance is not set in this shell | type the numbers of your `csc-projects` output (runbook, step 3) |
| `worst case ... exceeds the ... left minus the reserve` | the job's time limit times its resources does not fit in what is left | shorten `--time`, or ask the maintainer to revise the plan |
| `missing modules` in `check_env.py` | the venv was built with another module or is incomplete | submit the setup job of that architecture again |
| `cannot load python-pytorch/2.10` | the module was removed or renamed | find it with `module avail python-pytorch`, add `export TIEFER_PYTORCH_MODULE=<name>` to `~/.bashrc`, submit `setup_gpu.sbatch` again; `submit.sh` passes it to jobs |
| `cannot load python-data/3.12-31.03` | the module was removed or renamed | find it with `module avail python-data`, add `export TIEFER_CPU_PYTHON_MODULE=<name>` to `~/.bashrc`, submit `setup_cpu.sbatch` again |
| `the split field 'tortilla:data_split' is not in the metadata` | the dataset uses another name for the split field | find it in the `metadata columns` line of the log, set `SPLIT_FIELD` and `SPLIT_VALUES` in `src/tiefer_lab/data/source.py`, commit, and submit the data job again |
| The data job fails with a network error | compute nodes cannot reach `huggingface.co` | stop and ask the CSC Service Desk; do not build the cache on a login node |
| `rate limited (HTTP 429); all readers pause` in the data log | Hugging Face limits reads without a token | nothing to do, the job continues; an optional read-only `HF_TOKEN` (step 3) raises the limit |
| `RasterioIOError: Read failed` after `rate limited (HTTP 429)`, with GDAL's `not recognized as being in a supported file format` before it | the server answered a read with an error page instead of data while it limited requests; an older version stopped there | run `git pull`: the job now pauses (`read failed (RasterioIOError: ...); all readers pause`) and reads the patch again. If it still stops with `could not be read after 12 attempts`, submit the same data job again, since the build resumes, and run the 4-band and the 13-band builds one after the other, with the 13-band shards at a shared `--max-rate 120` or lower (step 3) |
| `OUT_OF_MEMORY` in the finishing step of the data job, then `FileNotFoundError` on `train_images.partial.npy` | an older version counted class pixels on the whole split at once | run `git pull` and submit the same data job again; it goes straight to the finishing step |
| `stopped after ... of ...` in the data log | the job hit its time limit or a read failed | submit the same data job again; it continues |
| `shard ... is not complete; merge later` | the merge was submitted before every shard finished | wait for the shard jobs (`squeue --me`), resubmit any that stopped, then merge |
| `needs about ... GiB but only ... GiB are free` | the file system is too full for the build | free space in `/scratch/<project>` or ask CSC for more quota |
| `stores bands ...; this build asks for ...` | a 4-band cache name was used for a 13-band build, or the other way round | use `--name cloudsen12-l1c-all` with `--bands all` |
| `invalid partition` from `sbatch` | a partition name differs on Roihu | check `sinfo` and the [partitions page](https://docs.csc.fi/computing/running/batch-job-partitions/), then edit the `#SBATCH --partition` line |
| The training log ends with `interrupted` | the time limit was reached | submit `train.sbatch` again with the run ID |
| `CUDA out of memory` in the training log of a 13-band config | a 13-band model at batch 128 may not fit in the memory of one GH200; expandable segments in the allocator alone may not help | halve the batch size and the learning rate together; the L2 configs use batch 64 and learning rate 0.004 |
| modules or the venv are not found inside a job | the job took an environment made for the other architecture, for example after `sbatch` without `submit.sh` | submit with `submit.sh`; CPU jobs from `roihu-cpu.csc.fi` (section 2, item 3); compare the `job environment` and `environment` lines of the log with step 4 |
| `HTTP 404` in the log of a shard of the data job | the dataset host answered 404 for a read | submit the same shard again; the build resumes where it stopped |
| `pthread_setaffinity_np` messages from ONNX Runtime in the export log | ONNX Runtime could not set the thread affinity it asked for | check that the export report is written; the messages alone do not stop the export |
| `the test split is only for final evaluation` | test was requested without `FINAL=1` and `REASON` | evaluate on validation; use test once, for the final result |

---

## 6. Facts the scripts depend on

Facts from the CSC documentation were checked on 1 October 2026, or on 8 October 2026 where the row names a page date; each row links its page. Facts marked as observed were seen on Roihu on 1 October 2026, before Project Schatten. The scripts keep the values they need to run, but these are not facts confirmed for Project Schatten: step 0 (setup) of [plan.md](plan.md) confirms them, and a row changes when it shows otherwise. Rows marked `TODO(verify)` are still open.

| Fact | Used in | Source |
| :--- | :---: | :---: |
| **Nodes and login** | | |
| GPU nodes are ARM with NVIDIA GH200, 4 GPUs per node; per GPU up to 72 cores, 95 GiB HBM3 and 117 GiB LPDDR5 | GPU job scripts | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| CPU nodes are AMD x86 | `data.sbatch`, `env.sh` | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Login nodes `roihu-gpu.csc.fi` (ARM) and `roihu-cpu.csc.fi` (x86) | `setup.sh`, this guide | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| A GPU job may be submitted from the x86 login node with care: limit `--export` (`HOME` and what the job needs), start the job as a login shell by full path (`/bin/bash --login`), set `CSC_ENV_INIT_NON_INTERACTIVE=yes` so that `/etc/profile.d/zz-csc-env.sh` initialises the CSC environment in a batch job, and set `SLURM_EXPORT_ENV=ALL` inside the script for `srun`. The page adds that CPU jobs are normally submitted from `roihu-cpu.csc.fi` and GPU jobs from `roihu-gpu.csc.fi` | `submit.sh`, `job_prelude.sh`, every job script | [submitting jobs across architectures](https://docs.csc.fi/computing/running/submitting-jobs-across-architectures/), 27 August 2026 |
| The Roihu FAQ says that CPU and GPU jobs "can only be submitted from the x86 and ARM login nodes, respectively"; the page above, which describes how to cross, is followed here | this guide | [Roihu FAQ](https://docs.csc.fi/support/faq/roihu/), 9 September 2026 |
| Login nodes are for light work only: "one-core jobs that finish in minutes and require less than 1 GiB of memory" | `data.sbatch`, this guide | [usage policy](https://docs.csc.fi/computing/usage-policy/) |
| **Slurm** | | |
| `gputest` 15 minutes; `gpumedium` 36 hours, up to 4 GPUs on one node; `gpularge` 36 hours, several nodes; `gpuinteractive` 12 hours | GPU job scripts | [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| CPU partition `small`: 72 hours, 1 node | `data.sbatch` | [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| `--account` is mandatory; GPUs are requested with `--gres=gpu:gh200:<n>`; Slurm adds memory per GPU automatically | `submit.sh`, job scripts | [job scripts on Roihu](https://docs.csc.fi/computing/running/creating-job-scripts-roihu/) |
| 200 GPU BU per GPU hour; up to 72 cores and 212 GiB memory per GPU included, so GPU jobs request `--cpus-per-task=72` | GPU job scripts | [billing](https://docs.csc.fi/computing/hpc-billing/) |
| Slurm was upgraded from 25.05 to 26.05 during the service break of 6 to 8 October 2026 | every job script; a smoke job runs first after the upgrade | CSC notice of the service break |
| `$TMPDIR` is set for every job without a request; its sizes are listed on the partitions page | `env.sh` (`tiefer_stage_cache`) | [Roihu FAQ](https://docs.csc.fi/support/faq/roihu/); sizes: [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
| **Software** | | |
| The PyTorch module `python-pytorch/2.10` | `env.sh` (`TIEFER_PYTORCH_MODULE`) | [GPU and ML guide](https://docs.csc.fi/support/tutorials/gpu-ml/) |
| `module avail python-pytorch` lists `python-pytorch/2.10` and `python-pytorch/2.13` (default) | `env.sh` (`TIEFER_PYTORCH_MODULE`) | observed on Roihu, 1 October 2026; to be confirmed by step 0 |
| On a GPU node, `python-pytorch/2.10` gives Python 3.12.12, torch 2.10.0+cu130, CUDA runtime 13.0, GH200 visible, bf16 supported | `setup.sh`, `check_env.py` | observed before Project Schatten; to be confirmed by step 0 |
| On x86, `python-data/3.12-31.03` gives Python 3.12.13 | `env.sh` (`TIEFER_CPU_PYTHON_MODULE`) | observed on Roihu, 1 October 2026; to be confirmed by step 0 |
| Extra packages go into a venv made with `python3 -m venv --system-site-packages` on top of the loaded module | `setup.sh` | [Python guide](https://docs.csc.fi/support/tutorials/python-usage-guide/) |
| GPU compute nodes reached PyPI during `setup.sh` | `setup.sh`, `setup_gpu.sbatch` | observed before Project Schatten; to be confirmed by step 0 |
| With `--export=NONE`, sourcing `/usr/share/lmod/lmod/init/bash` and `/etc/profile.d/zz-csc-env.sh` in a job still left `MODULEPATH` empty on CPU and GPU nodes; `CSC_ENV_INIT_NON_INTERACTIVE` was not set then | `submit.sh`, job scripts | observed on Roihu, 1 October 2026; to be confirmed by step 0 |
| A GPU job submitted from `roihu-cpu.csc.fi` in this way gets the `aarch64` module environment and `venv-aarch64` | `submit.sh`, `job_prelude.sh` | `TODO(verify)` with the first `setup_gpu.sbatch` job (step 2) |
| A Roihu-CPU shell is available in the web interface | this guide | [www.roihu.csc.fi](https://www.roihu.csc.fi) |
| **Storage and network** | | |
| Files in `/scratch` unused for 180 days are deleted | `env.sh` | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Compute nodes reach `huggingface.co`; without a token the server answered HTTP 429 after a few hundred reads, which the builder pauses through; a token is optional | `data.sbatch`, `src/tiefer_lab/data/http.py` | observed on Roihu before Project Schatten; to be confirmed by step 0 |

---

## Changelog

- 16 October 2026: the step 0 runbook follows the CSC usage policy: the maintainer runs every command, no credentials and no service for an AI-assisted system, only your own jobs, the setup as batch jobs (`setup_cpu.sbatch`), the balance typed in for the cost check of `submit.sh`, and a send-back list of job IDs, exit codes and our own logs and reports; drafted with an AI-assisted system.
- 16 October 2026: the step 0 runbook, command by command, from a fresh account to a finished smoke job, device check and source check, with what each command prints and what to send back; every cache stays out of home; drafted with an AI-assisted system.
- 16 October 2026: packed GPU training (`packed.py`, `train_packed.sbatch`) and the timing step with 1 to 4 runs per GPU (`timing_packed.sbatch`); drafted with an AI-assisted system.
- 16 October 2026: every job that does not train has a CPU job, the default of the plan (`evaluate_cpu.sbatch`, `calibrate_cpu.sbatch`, `export_cpu.sbatch`, `diagnose.sbatch int8`), with its body shared with the GPU job in `model_jobs.sh`; `device_check.py`; drafted with an AI-assisted system.
- 16 October 2026: step 3, the Hugging Face token is optional, read-only, raises the rate limit only and is never written to any file, log or report; drafted with an AI-assisted system.
- 16 October 2026: `check_sources.sbatch` in the files table; drafted with an AI-assisted system.
- 15 October 2026: config names follow the scheme of docs/SPEC.md, section 8 (Sieb, Wandler, Lupe, the CloudScout re-implementation); drafted with an AI-assisted system.
- 15 October 2026: the facts observed on Roihu predate Project Schatten and are to be confirmed by step 0 (setup) of the plan; drafted with an AI-assisted system.
- 15 October 2026: campaign names of withdrawn campaigns replaced by Project Schatten or by what the thing is; drafted with an AI-assisted system.
- 15 October 2026: `evaluate_all.sh` lists each dataset without a cache and exits non-zero; drafted with an AI-assisted system.
- 14 October 2026: the files table lists the calibration, independent dataset and diagnosis jobs and `evaluate_all.sh`; step 6 names the v3 options of the jobs; drafted with an AI-assisted system.
- 8 October 2026: step 3, a read that fails part way pauses every reader and is read again; run the 4-band and the 13-band builds one after the other, with the 13-band shards at a shared `--max-rate 120`; troubleshooting row for `Read failed` after HTTP 429.
- 8 October 2026: everything is done from `roihu-cpu.csc.fi`: GPU jobs follow CSC's way of submitting across architectures and build their environment on the GPU node; the GPU setup is the job `setup_gpu.sbatch`; step 4 and the troubleshooting table say how to check a job's environment in its log.
- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: step 3 adds the read-only padding check of a cache, run on the login node.
- 7 October 2026: item 2 of section 2 points to item 3 below instead of a section 2.3.
- 7 October 2026: the troubleshooting table points to section 2, item 3, which has no section number of its own.
- 7 October 2026: the purpose links GETTING-STARTED.md, INSTALL.md and the gates of POLICY.md for the test split and compute spend.
- 2 October 2026: timing job, sweep script and run plan for milestone L2.
- 2 October 2026: 13-band cache built in shards with a shared rate cap and a disk estimate.
- 2 October 2026: survey job before a data build.
- 2 October 2026: training uses `configs/l1_full.toml`.
- 2 October 2026: Hugging Face token from `HF_TOKEN`, shared backoff on HTTP 429, and the finishing step of a data job resumes on its own.
- 2 October 2026: the smoke job uses the full cache only when its train and val splits are complete, and otherwise builds its tiny cache in its own folder.
- 1 October 2026: back to the standard CSC way of submitting jobs: sbatch's default export, CPU work and the data job from `roihu-cpu.csc.fi`, GPU setup and GPU jobs from `roihu-gpu.csc.fi` (SSH or the web interface); `gpu_shell.sh` and the `--export=NONE` workarounds removed.
- 1 October 2026: troubleshooting row for jobs that end within seconds with an empty log.
- 1 October 2026: source links corrected for `$TMPDIR`, the `/scratch` cleanup, the PyTorch module and the venv rule; `python-data/3.12-31.03` is marked as observed only.
- 1 October 2026: steps reordered (clone and project, setup on both architectures, data job, smoke job, training with optional seeds, evaluation to collection); "Before you start" added; the login node cache path removed; facts checked against the CSC documentation and on Roihu; new troubleshooting cases from a real job failure.
- 1 October 2026: the smoke job measures the time per epoch of `configs/l1_base.toml`.
- 1 October 2026: GPU jobs request 72 cores; data loader workers follow `SLURM_CPUS_PER_TASK`.
- 1 October 2026: sections ordered as Requirements, Steps, Files, Troubleshooting, then the facts to verify.
- 1 October 2026: first version for milestone L1; CSC facts marked `TODO(verify)`.
