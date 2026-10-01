<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# CSC Roihu guide

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Step by step: how to set up Tiefer Lab on the CSC Roihu supercomputer, build the data cache, train, evaluate and export the cloud filter, and bring the results back.

---

## 1. Requirements

- A CSC project with Roihu GPU access and GPU billing units.
- SSH access to `roihu-gpu.csc.fi` with a MyCSC-signed certificate.
- The project name, written below as `<project>`, and your CSC user name, written as `<user>`.
- The facts in section 5 checked against the CSC documentation, or on Roihu, before the first job.

---

## 2. Steps

1. Log in to the GPU login node:

   ```bash
   ssh <user>@roihu-gpu.csc.fi
   ```

2. Clone the repository. It is public, so no key is needed:

   ```bash
   mkdir -p /projappl/<project>/tiefer-lab
   git clone https://github.com/tiefer-labs/lab.git /projappl/<project>/tiefer-lab/src
   cd /projappl/<project>/tiefer-lab/src
   ```

3. Set the project once, then install. `setup.sh` loads the PyTorch module, creates the virtual environment, installs `hpc/roihu/requirements.txt` and the package, and runs `check_env.py`:

   ```bash
   echo 'export TIEFER_CSC_PROJECT=<project>' >> ~/.bashrc
   source ~/.bashrc
   bash hpc/roihu/setup.sh
   ```

   For `data.sbatch` on x86 CPU nodes, run the same setup once more on `roihu-cpu.csc.fi`; it creates a second environment for that architecture.

4. Build the data cache in `/scratch`. Data, runs and reports go to `/scratch/<project>/tiefer-lab/`.

   a. As a CPU job, if compute nodes can reach `huggingface.co`:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
   ```

   b. On the login node, if compute nodes have no internet access. The builder reads only the four bands and the label of each patch and can be stopped and started again at any time:

   ```bash
   source hpc/roihu/env.sh
   python3 -m tiefer_lab.data.build_cache --split train
   python3 -m tiefer_lab.data.build_cache --split val
   python3 -m tiefer_lab.data.build_cache --split test
   ```

   Check the CSC rules for long processes on login nodes first (TODO(verify) on [docs.csc.fi](https://docs.csc.fi/)).

5. Run the smoke job (15 minutes on `gputest`) and read its log:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
   squeue --me
   ls /scratch/<project>/tiefer-lab/runs/slurm/
   ```

6. Train. Follow the job with `squeue --me`. The run ID is printed in the log (`run directory: $TIEFER_RUNS_DIR/<run-id>`). If the time limit is reached, the job saves `last.pt` and stops; submit again with the run ID to continue:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml
   bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml <run-id>
   ```

7. Evaluate on validation with the baselines, then export and quantise. The test split is only for the final evaluation; it needs `FINAL=1` and a reason, and is logged in `test_log.md`:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
   FINAL=1 REASON="<why>" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
   ```

8. Record the compute used by each job, then pack the results:

   ```bash
   bash hpc/roihu/usage.sh <job-id>
   bash hpc/roihu/collect.sh <run-id>
   ```

   On your own computer, copy the archive and unpack it into the repository. The results are processed there (`make results`):

   ```bash
   scp <user>@roihu-gpu.csc.fi:/scratch/<project>/tiefer-lab/collect/tiefer-<run-id>.tar.gz .
   tar -xzf tiefer-<run-id>.tar.gz -C <path-to-lab>
   ```

9. CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. **Confirm with the project PI or the CSC Service Desk before the first job.** This is the founder's decision.

---

## 3. Files

| File | Purpose |
| :--- | :---: |
| `env.sh` | sourced by every job: module, venv, `PIP_CACHE_DIR` and `TIEFER_*` paths; stops when `TIEFER_CSC_PROJECT` is unset |
| `setup.sh` | one-time setup: venv, `requirements.txt`, the package, environment check |
| `check_env.py` | imports every dependency, prints versions, architecture, GPU, CUDA and bf16 support |
| `requirements.txt` | generated from `uv.lock` with `make requirements`, without `torch` and its own dependencies |
| `submit.sh` | `sbatch` with `--account=$TIEFER_CSC_PROJECT` and the log location |
| `data.sbatch` | builds the cache in `/scratch` on a CPU node |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: check, smoke training, validation evaluation |
| `train.sbatch` | `gpumedium`, 1 GPU, 12 hours by default, SIGUSR1 300 s before the limit, resumable |
| `evaluate.sbatch` | validation with baselines; test only with `FINAL=1` and `REASON` |
| `export.sbatch` | ONNX export, check against PyTorch, INT8 quantisation |
| `usage.sh` | `sacct` record of a job, written to `reports/compute/<job-id>.json` |
| `collect.sh` | packs reports, run metadata, best checkpoint and ONNX files, with relative paths only |

Slurm logs go to `$TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out`. GPU jobs copy the cache to the job's local disk at start when there is room.

---

## 4. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `TIEFER_CSC_PROJECT is not set` | the project is not exported in this shell | add `export TIEFER_CSC_PROJECT=<project>` to `~/.bashrc` and log in again |
| `cannot load python-pytorch/2.10` | the module name or version differs on Roihu | find it with `module avail python-pytorch` and set `export TIEFER_PYTORCH_MODULE=<name>` before `setup.sh` |
| `Python 3.12 or newer is needed` | the module's Python is older | choose a newer PyTorch module and run `setup.sh` again |
| `missing modules` in `check_env.py` | the venv was built on the other architecture or not at all | run `bash hpc/roihu/setup.sh` on the login node of the same architecture |
| The data job fails with a network error | compute nodes cannot reach `huggingface.co` | use step 4b on the login node |
| `invalid partition` from `sbatch` | a partition name differs on Roihu | check `sinfo` and edit the `#SBATCH --partition` line |
| The training log ends with `interrupted` | the time limit was reached | submit `train.sbatch` again with the run ID |
| `the test split is only for final evaluation` | test was requested without `FINAL=1` and `REASON` | evaluate on validation; use test once, for the final result |

---

## 5. Facts the scripts depend on

These facts come from the CSC documentation at [docs.csc.fi](https://docs.csc.fi/) as of October 2026. `docs.csc.fi` could not be reached from the environment where these scripts were written, so each line marked `TODO(verify)` must be checked there, or on Roihu itself, before the first job.

| Fact | Used in | Check |
| :--- | :---: | :---: |
| **Nodes and login** | | |
| GPU nodes are ARM (aarch64) with NVIDIA GH200, 4 GPUs per node; one GPU gives up to 72 ARM cores, 95 GiB HBM3 and about 117 GiB CPU memory | `train.sbatch`, `evaluate.sbatch`, `export.sbatch`, `smoke.sbatch` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| CPU nodes are x86 (AMD) | `data.sbatch`, `env.sh` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| Login nodes: `roihu-gpu.csc.fi` (ARM) and `roihu-cpu.csc.fi` (x86); software for GPU jobs is installed from `roihu-gpu.csc.fi` | `setup.sh` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| **Slurm** | | |
| Partitions `gputest` (15 minutes), `gpumedium` (up to 36 hours, up to 4 GPUs on one node), `gpuinteractive` (up to 12 hours) | all GPU job scripts | TODO(verify) with `sinfo` and on [docs.csc.fi](https://docs.csc.fi/) |
| `#SBATCH --account=<project>` is mandatory; GPUs are requested with `--gres=gpu:gh200:1` | `submit.sh`, job scripts | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| GPU jobs are billed in GPU hours, and up to 72 cores per reserved GPU are included, so GPU jobs request `--cpus-per-task=72`; data loader workers are set from `SLURM_CPUS_PER_TASK` | `train.sbatch`, `evaluate.sbatch`, `export.sbatch`, `smoke.sbatch` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/computing/hpc-billing/) |
| CPU partition name `small` for the data job | `data.sbatch` | TODO(verify) with `sinfo`: a guess, not taken from the documentation |
| Local disk of a job is in `$TMPDIR`, and whether it must be requested | `env.sh` (`tiefer_stage_cache`) | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| **Software** | | |
| PyTorch comes from a module such as `python-pytorch/2.10`, with CUDA and cuDNN | `env.sh` (`TIEFER_PYTORCH_MODULE`) | TODO(verify) with `module avail python-pytorch` |
| The PyTorch module provides Python 3.12 or newer | `setup.sh`, `check_env.py` | TODO(verify) with `python3 --version` after loading the module |
| A Python 3.12 module for x86 nodes (default guess `python-data`) | `env.sh` (`TIEFER_CPU_PYTHON_MODULE`) | TODO(verify) with `module avail python` on `roihu-cpu.csc.fi` |
| Extra packages go into a venv made with `python3 -m venv --system-site-packages` in `/projappl/<project>` | `setup.sh` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| **Storage and network** | | |
| `/projappl/<project>` for software, `/scratch/<project>` for data and runs; files in `/scratch` unused for 180 days are deleted | `env.sh` | TODO(verify) on [docs.csc.fi](https://docs.csc.fi/) |
| Whether compute nodes can reach `huggingface.co` | step 4 below | TODO(verify): run step 4a; if it fails with a network error, use step 4b |

---

## Changelog

- 1 October 2026: GPU jobs request 72 cores; data loader workers follow `SLURM_CPUS_PER_TASK`.
- 1 October 2026: sections ordered as Requirements, Steps, Files, Troubleshooting, then the facts to verify.
- 1 October 2026: first version for milestone L1; CSC facts marked `TODO(verify)`.
