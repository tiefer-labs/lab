<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# CSC Roihu guide

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Step by step: how to set up Tiefer Lab on the CSC Roihu supercomputer, build the data cache, train, evaluate and export the cloud filter, and bring the results back.

---

## 1. Requirements

- A CSC project with Roihu GPU access and GPU billing units.
- Access to both login nodes: `roihu-cpu.csc.fi` (x86) and `roihu-gpu.csc.fi` (ARM), by SSH from your own computer with a MyCSC-signed certificate, or as a Roihu-CPU or Roihu-GPU shell in the web interface at [www.roihu.csc.fi](https://www.roihu.csc.fi).
- The project name, written below as `<project>`, and your CSC user name, written as `<user>`. Replace both with your own values in every command.
- CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. **Confirm with the project PI or the CSC Service Desk before the first job.** This is the founder's decision.

---

## 2. Before you start

1. Check the remaining GPU billing units of the project. One GPU hour costs 200 GPU BU ([billing](https://docs.csc.fi/computing/hpc-billing/)):

   ```bash
   csc-projects
   ```

2. Before each new kind of job, check its request without submitting it (from the repository folder, after step 1, on the login node of section 2.3). `submit.sh` passes options written before the job script on to `sbatch`; `--test-only` validates the request and prints when it would start:

   ```bash
   bash hpc/roihu/submit.sh --test-only hpc/roihu/smoke.sbatch
   bash hpc/roihu/submit.sh --test-only hpc/roihu/train.sbatch configs/l1_full.toml
   ```

3. Know where things run. Jobs use sbatch's default export, the standard CSC way: a job inherits the environment of the shell that submitted it, including the `module` command. So each job is submitted from the login node of its own architecture, and `submit.sh` refuses it otherwise:

   | Work | Login node |
   | :--- | :---: |
   | CPU setup (`venv-x86_64`) and the data job | `roihu-cpu.csc.fi` |
   | GPU setup (`venv-aarch64`), smoke, training, evaluation and export jobs | `roihu-gpu.csc.fi` |

   Reach each one by SSH from your own computer, or open a Roihu-CPU or Roihu-GPU shell in the web interface at [www.roihu.csc.fi](https://www.roihu.csc.fi).

4. Login nodes are for light work only: "one-core jobs that finish in minutes and require less than 1 GiB of memory" ([usage policy](https://docs.csc.fi/computing/usage-policy/)). The data cache is therefore built in a CPU job, never on a login node.

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

GPU side (`venv-aarch64`), on `roihu-gpu.csc.fi`, by SSH from your own computer or in a Roihu-GPU shell at [www.roihu.csc.fi](https://www.roihu.csc.fi). If `check_env.py` sees no GPU on the login node, it says so and still passes; the smoke job checks the GPU:

```bash
ssh <user>@roihu-gpu.csc.fi
cd /projappl/<project>/tiefer-lab/src
bash hpc/roihu/setup.sh
```

### Step 3: survey the dataset, then build the data cache

Before a new build, run the survey: a short CPU job that reads the metadata and a few patches of every label type and writes `$TIEFER_REPORTS_DIR/data/survey.json` (counts by label type, patch size and split; locations shared with the validation and test splits; how labels and reference masks are encoded). Facts the code depends on are taken from this report, not assumed. From `roihu-cpu.csc.fi`, with the token set as below:

```bash
bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch
cat /scratch/<project>/tiefer-lab/reports/data/survey.json
```

From `roihu-cpu.csc.fi`. Without a Hugging Face token the server answers HTTP 429 (too many requests) after a few hundred patches, so set a read token in the shell first. `read -rs` keeps it out of the screen, the shell history and every file; the job inherits it through sbatch's default export, and the builder passes it to GDAL without printing it:

```bash
ssh <user>@roihu-cpu.csc.fi
cd /projappl/<project>/tiefer-lab/src
read -rsp "Hugging Face token: " HF_TOKEN && export HF_TOKEN && echo
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
squeue --me
```

The job runs on the CPU partition `small` with 16 cores, one parallel download worker per core (`SLURM_CPUS_PER_TASK`). It keeps only high quality 509 x 509 patches and prints the kept and dropped counts per split. The build is resumable: if the job stops, submit the same command again and it continues where it stopped.

The log says `Hugging Face token: set` or `not set`, never the token itself. When the server still answers HTTP 429, every reader pauses together and then continues: for the server's `Retry-After` when it is known, otherwise 10 s, 20 s, 40 s and so on up to 300 s, with random jitter. Never write the token into `~/.bashrc` or a file in the repository.

Its log starts with the metadata columns of the dataset. If it stops because the split field is missing, see the troubleshooting table.

#### All 13 bands, in shards

The band-flexible models read all 13 Level-1C bands from one cache, `cloudsen12-l1c-all`. With all bands a 509 x 509 patch takes about 6.7 MiB, so the high quality train, val and test splits (8490, 535 and 975 patches on 2 October 2026) need about 55.3, 3.5 and 6.4 GiB, 65.1 GiB in all; the merge needs one shard more at its peak. The builder prints its estimate and stops when the file system has less free space, but the project quota on `/scratch` can be lower than that: check it first (`TODO(verify)` the command on [docs.csc.fi](https://docs.csc.fi/computing/disk/)).

The training split is read by four CPU jobs side by side, each into its own folder, and merged afterwards. `--max-rate` caps the reads per minute of the whole split and is shared between the shards; 120 is the highest rate observed with a token without HTTP 429 (2 October 2026):

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

### Step 4: smoke job on `gputest`

This and every later job is submitted from `roihu-gpu.csc.fi`:

```bash
ssh <user>@roihu-gpu.csc.fi
cd /projappl/<project>/tiefer-lab/src
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
squeue --me
ls /scratch/<project>/tiefer-lab/runs/slurm/
```

The smoke job checks the environment, trains `configs/smoke.toml` for a few steps and evaluates it on validation; its outputs are labelled smoke and are never results. If the train and val splits of the full cache from step 3 are not complete yet (missing, or `data.sbatch` still building them), it builds a tiny cache (32 training and 16 validation patches) in `/scratch/<project>/tiefer-lab/smoke/data/` instead and skips the timing run. Its log names the folder it uses (`full cache: ...` or `tiny smoke cache: ...`). The smoke job only reads the full cache and never writes to it, so it can run while `data.sbatch` is running.

With the full cache, the job ends with a timing run of `configs/l1_base.toml` (one epoch cut to 50 steps). Its log line `full epoch ... s (estimated)` is the time per epoch of the real training on this GPU; multiply by the number of epochs to plan the `--time` of the training job:

```bash
grep "full epoch" /scratch/<project>/tiefer-lab/runs/slurm/tiefer-smoke-<job-id>.out
```

### Step 5: train on `gpumedium`

Train `configs/l1_full.toml`: `l1_base` run to the end of its 150-epoch cosine schedule, with a learning rate warm-up and a moving average of the weights (the reasons are in [ASSUMPTIONS.md](../../docs/ASSUMPTIONS.md), section 6). At the measured 8.6 s per epoch on one GH200 (2 October 2026), 150 epochs take about 22 minutes, about 0.4 GPU hours. `configs/l1_base.toml` stays as it was measured.

Each training job uses one GPU. The run ID is printed in the log (`run directory: $TIEFER_RUNS_DIR/<run-id>`) and contains the seed, for example `l1_base-seed0-<time>-<commit>`. If the time limit is reached, the job saves `last.pt` and stops; submit again with the run ID to continue:

```bash
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_full.toml
bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_full.toml <run-id>
```

The default time is 12 hours; `gpumedium` allows up to 36 hours. Set a longer time from the estimate of step 4:

```bash
bash hpc/roihu/submit.sh --time=24:00:00 hpc/roihu/train.sbatch configs/l1_full.toml
```

Optional: two seeds. Submit two separate one-GPU jobs. `SEED` overrides the seed of the configuration and is recorded in the run metadata and the run ID, so the two runs never share a run folder. Each job is billed for its own GPU hours:

```bash
SEED=0 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_full.toml
SEED=1 bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_full.toml
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
| `job_prelude.sh` | sourced first by every job and by `setup.sh`: stops when `module` is missing, runs `module purge` |
| `shell_options.sh` | turns off `errexit`, `nounset` and `pipefail` around every `module` command, then restores the saved options |
| `env.sh` | sourced after the prelude: module, venv, `PIP_CACHE_DIR`, `TIEFER_*` paths and, on GPU nodes, `PYTORCH_CUDA_ALLOC_CONF`; stops when `TIEFER_CSC_PROJECT` is unset or not a project name |
| `setup.sh` | one-time setup per architecture: venv, `requirements.txt`, the package, environment check |
| `check_env.py` | imports every dependency, prints versions, architecture, GPU, CUDA and bf16 support |
| `requirements.txt` | generated from `uv.lock` with `make requirements`, without `torch` and its own dependencies |
| `submit.sh` | `sbatch` with `--account`, `--chdir` and the log location; refuses GPU jobs unless run on `roihu-gpu.csc.fi` and the data job unless run on `roihu-cpu.csc.fi`; `SEED`, `FINAL`, `REASON`, `ROBUSTNESS` and `PERTURBATIONS` reach the job as plain environment variables |
| `survey.sbatch` | short CPU job: counts, splits, locations and item encodings of the dataset, written to `reports/data/survey.json` |
| `data.sbatch` | builds the cache in `/scratch` on a CPU node; submitted from `roihu-cpu.csc.fi` |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: check, smoke training, validation evaluation, timing run of `configs/l1_base.toml` |
| `train.sbatch` | `gpumedium`, 1 GPU, 12 hours by default, SIGUSR1 300 s before the limit, resumable, optional `SEED` |
| `evaluate.sbatch` | validation with baselines on every band set of the run; test only with `FINAL=1` and `REASON`; `ROBUSTNESS=1` adds the fixed sensor perturbations in `PERTURBATIONS` |
| `export.sbatch` | ONNX export per band set, check against PyTorch, INT8 quantisation |
| `timing.sbatch` | `gputest`, 1 GPU: one epoch of a config cut to 50 steps; its time per epoch replaces the estimate in `plan.md` |
| `sweep.sh` | submits configs and seeds as separate one-GPU jobs (`--seeds 0,1,2`, `--timing`, `--test-only`) |
| `plan.md` | the run order with costs, under 5000 GPU BU |
| `usage.sh` | `sacct` record of a job, written to `reports/compute/<job-id>.json` |
| `collect.sh` | packs reports, run metadata, best checkpoint and ONNX files, with relative paths only |

Every job script starts with `#!/bin/bash -l` and uses sbatch's default export, so it inherits the submitting shell's environment; `job_prelude.sh` and `env.sh` then run `module purge` and load the module for the node's architecture. GPU jobs stop unless they run on an `aarch64` node. Slurm logs go to `$TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out`. GPU jobs copy the cache to the job's local disk (`$TMPDIR`) at start when there is room.

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `TIEFER_CSC_PROJECT is not set` | the project is not exported in this shell | add the line of step 1 to `~/.bashrc` and run `source ~/.bashrc` |
| `is not a CSC project name` | `~/.bashrc` holds the literal placeholder `<project>` | remove the line as shown in step 1 and add it again with your project name |
| `submit GPU jobs from roihu-gpu.csc.fi` | a GPU job was submitted from the x86 login node | log in to `roihu-gpu.csc.fi` (SSH, or a Roihu-GPU shell at [www.roihu.csc.fi](https://www.roihu.csc.fi)) and submit it there |
| `submit the data job from roihu-cpu.csc.fi` | the data job was submitted from the ARM login node | log in to `roihu-cpu.csc.fi` and submit it there |
| `jobs need sbatch's default export` | `--export` was passed to `submit.sh` | leave `--export` out; with `--export=NONE` the `module` command and `MODULEPATH` cannot be restored inside a job |
| A job ends within seconds with an empty log | an older version of the scripts, with `--export=NONE` and its profile workarounds | run `git pull` on both login nodes and submit again with `submit.sh`; never run a job script directly on a login node |
| `the 'module' command is not available in this job` | the job was not submitted from a Roihu login shell | submit it with `hpc/roihu/submit.sh` from `roihu-cpu.csc.fi` or `roihu-gpu.csc.fi`; if it persists, contact the CSC Service Desk |
| `needs an aarch64 GH200 node, but runs on x86_64` | a GPU job ran on an x86 node, for example after a partition override | submit without overriding `--partition`; GPU jobs need a GPU partition |
| `no virtual environment .../venv-aarch64` | `setup.sh` has not been run on the GPU side | run step 2, GPU side, on `roihu-gpu.csc.fi` |
| `no virtual environment .../venv-x86_64` | `setup.sh` has not been run on the CPU side | run step 2, CPU side, on `roihu-cpu.csc.fi` |
| `missing modules` in `check_env.py` | the venv was built with another module or is incomplete | run `setup.sh` again on the same architecture |
| `cannot load python-pytorch/2.10` | the module was removed or renamed | find it with `module avail python-pytorch`, add `export TIEFER_PYTORCH_MODULE=<name>` to `~/.bashrc`, run `setup.sh` again on the GPU side; `submit.sh` passes it to jobs |
| `cannot load python-data/3.12-31.03` | the module was removed or renamed | find it with `module avail python-data`, add `export TIEFER_CPU_PYTHON_MODULE=<name>` to `~/.bashrc`, run `setup.sh` again on the CPU side |
| `the split field 'tortilla:data_split' is not in the metadata` | the dataset uses another name for the split field | find it in the `metadata columns` line of the log, set `SPLIT_FIELD` and `SPLIT_VALUES` in `src/tiefer_lab/data/source.py`, commit, and submit the data job again |
| The data job fails with a network error | compute nodes cannot reach `huggingface.co` | stop and ask the CSC Service Desk; do not build the cache on a login node |
| `rate limited (HTTP 429); all readers pause` in the data log | Hugging Face limits reads without a token | nothing to do, the job continues; set `HF_TOKEN` as in step 3 before the next data job |
| `OUT_OF_MEMORY` in the finishing step of the data job, then `FileNotFoundError` on `train_images.partial.npy` | an older version counted class pixels on the whole split at once | run `git pull` and submit the same data job again; it goes straight to the finishing step |
| `stopped after ... of ...` in the data log | the job hit its time limit or a read failed | submit the same data job again; it continues |
| `shard ... is not complete; merge later` | the merge was submitted before every shard finished | wait for the shard jobs (`squeue --me`), resubmit any that stopped, then merge |
| `needs about ... GiB but only ... GiB are free` | the file system is too full for the build | free space in `/scratch/<project>` or ask CSC for more quota |
| `stores bands ...; this build asks for ...` | a 4-band cache name was used for a 13-band build, or the other way round | use `--name cloudsen12-l1c-all` with `--bands all` |
| `invalid partition` from `sbatch` | a partition name differs on Roihu | check `sinfo` and the [partitions page](https://docs.csc.fi/computing/running/batch-job-partitions/), then edit the `#SBATCH --partition` line |
| The training log ends with `interrupted` | the time limit was reached | submit `train.sbatch` again with the run ID |
| `CUDA out of memory` in the training log of a 13-band config | batch 128 with all 13 bands does not fit on one GH200; expandable segments in the allocator alone did not help (jobs 2000912 and 2000941, 3 October 2026) | halve the batch size and the learning rate together, as the L2 configs do since 7 October 2026 (batch 64, learning rate 0.004; job 2000949 ran to the end) |
| modules or the venv are not found inside a job | the job was submitted from the login host of the other architecture, so it inherited the wrong environment | submit GPU jobs from `roihu-gpu.csc.fi` and CPU jobs from `roihu-cpu.csc.fi` (section 2.3) |
| `HTTP 404` in the log of a shard of the data job | the dataset host answered 404 for a read (job 1999649) | submit the same shard again; the build resumes where it stopped (job 2000731) |
| `pthread_setaffinity_np` messages from ONNX Runtime in the export log | ONNX Runtime could not set the thread affinity it asked for; the cause is not investigated | nothing; the exports completed; the effect on timing has not been investigated |
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
| `gputest` 15 minutes; `gpumedium` 36 hours, up to 4 GPUs on one node; `gpularge` 36 hours, several nodes; `gpuinteractive` 12 hours | GPU job scripts | [partitions](https://docs.csc.fi/computing/running/batch-job-partitions/) |
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
| GPU compute nodes reached PyPI during `setup.sh` | `setup.sh` | observed |
| With `--export=NONE`, sourcing `/usr/share/lmod/lmod/init/bash` and `/etc/profile.d/zz-csc-env.sh` in a job still left `MODULEPATH` empty on CPU and GPU nodes, so jobs use sbatch's default export | `submit.sh`, job scripts | observed on Roihu, 1 October 2026 |
| A Roihu-CPU or Roihu-GPU shell is available in the web interface | this guide | [www.roihu.csc.fi](https://www.roihu.csc.fi) |
| **Storage and network** | | |
| Files in `/scratch` unused for 180 days are deleted | `env.sh` | [Roihu system](https://docs.csc.fi/computing/systems-roihu/) |
| Compute nodes reach `huggingface.co`; without a token the server answered HTTP 429 after about 415 patches per window, and with a bearer token reads ran at 55 to 120 patches per minute without 429 | `data.sbatch`, `src/tiefer_lab/data/http.py` | observed on Roihu, 2 October 2026 |

---

## Changelog

- 7 October 2026: troubleshooting rows for out of GPU memory with 13 bands, jobs submitted from the wrong login host, HTTP 404 in a shard and ONNX Runtime affinity messages; GPU jobs set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in `env.sh`.
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
