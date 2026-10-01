<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# CSC Roihu guide

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Step by step: how to set up Tiefer Lab on the CSC Roihu supercomputer, build the data cache, train, evaluate and export the cloud filter, and bring the results back.

---

## 1. Facts the scripts depend on

These facts come from the CSC documentation at [docs.csc.fi](https://docs.csc.fi/) as of October 2026. `docs.csc.fi` could not be reached from the environment where these scripts were written, so each line marked `TODO(verify)` must be checked there, or on Roihu itself, before the first job.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Fact</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Used in</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Check</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Nodes and login</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">GPU nodes are ARM (aarch64) with NVIDIA GH200, 4 GPUs per node; one GPU gives up to 72 ARM cores, 95 GiB HBM3 and about 117 GiB CPU memory</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>train.sbatch</code>, <code>evaluate.sbatch</code>, <code>export.sbatch</code>, <code>smoke.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">CPU nodes are x86 (AMD)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>data.sbatch</code>, <code>env.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Login nodes: <code>roihu-gpu.csc.fi</code> (ARM) and <code>roihu-cpu.csc.fi</code> (x86); software for GPU jobs is installed from <code>roihu-gpu.csc.fi</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>setup.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Slurm</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Partitions <code>gputest</code> (15 minutes), <code>gpumedium</code> (up to 36 hours, up to 4 GPUs on one node), <code>gpuinteractive</code> (up to 12 hours)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">all GPU job scripts</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) with <code>sinfo</code> and on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>#SBATCH --account=&lt;project&gt;</code> is mandatory; GPUs are requested with <code>--gres=gpu:gh200:1</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>submit.sh</code>, job scripts</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">CPU partition name <code>small</code> for the data job</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>data.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) with <code>sinfo</code>: a guess, not taken from the documentation</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Local disk of a job is in <code>$TMPDIR</code>, and whether it must be requested</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>env.sh</code> (<code>tiefer_stage_cache</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Software</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">PyTorch comes from a module such as <code>python-pytorch/2.10</code>, with CUDA and cuDNN</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>env.sh</code> (<code>TIEFER_PYTORCH_MODULE</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) with <code>module avail python-pytorch</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">The PyTorch module provides Python 3.12 or newer</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>setup.sh</code>, <code>check_env.py</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) with <code>python3 --version</code> after loading the module</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">A Python 3.12 module for x86 nodes (default guess <code>python-data</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>env.sh</code> (<code>TIEFER_CPU_PYTHON_MODULE</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) with <code>module avail python</code> on <code>roihu-cpu.csc.fi</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Extra packages go into a venv made with <code>python3 -m venv --system-site-packages</code> in <code>/projappl/&lt;project&gt;</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>setup.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Storage and network</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>/projappl/&lt;project&gt;</code> for software, <code>/scratch/&lt;project&gt;</code> for data and runs; files in <code>/scratch</code> unused for 180 days are deleted</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>env.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on <a href="https://docs.csc.fi/">docs.csc.fi</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Whether compute nodes can reach <code>huggingface.co</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">step 4 below</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify): run step 4a; if it fails with a network error, use step 4b</td>
</tr>
</tbody>
</table>
</div>

---

## 2. Requirements

- A CSC project with Roihu GPU access and GPU billing units.
- SSH access to `roihu-gpu.csc.fi` with a MyCSC-signed certificate.
- The project name, written below as `<project>`, and your CSC user name, written as `<user>`.

---

## 3. Steps

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

## 4. Files

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">File</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Purpose</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>env.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">sourced by every job: module, venv, <code>PIP_CACHE_DIR</code> and <code>TIEFER_*</code> paths; stops when <code>TIEFER_CSC_PROJECT</code> is unset</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>setup.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">one-time setup: venv, <code>requirements.txt</code>, the package, environment check</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>check_env.py</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">imports every dependency, prints versions, architecture, GPU, CUDA and bf16 support</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>requirements.txt</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">generated from <code>uv.lock</code> with <code>make requirements</code>, without <code>torch</code> and its own dependencies</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>submit.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sbatch</code> with <code>--account=$TIEFER_CSC_PROJECT</code> and the log location</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>data.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">builds the cache in <code>/scratch</code> on a CPU node</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>smoke.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>gputest</code>, 1 GPU, 15 minutes: check, smoke training, validation evaluation</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>train.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>gpumedium</code>, 1 GPU, 12 hours by default, SIGUSR1 300 s before the limit, resumable</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>evaluate.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">validation with baselines; test only with <code>FINAL=1</code> and <code>REASON</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>export.sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">ONNX export, check against PyTorch, INT8 quantisation</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>usage.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sacct</code> record of a job, written to <code>reports/compute/&lt;job-id&gt;.json</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>collect.sh</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">packs reports, run metadata, best checkpoint and ONNX files, with relative paths only</td>
</tr>
</tbody>
</table>
</div>

Slurm logs go to `$TIEFER_RUNS_DIR/slurm/<job-name>-<job-id>.out`. GPU jobs copy the cache to the job's local disk at start when there is room.

---

## 5. Troubleshooting

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Symptom</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Cause</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Fix</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>TIEFER_CSC_PROJECT is not set</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the project is not exported in this shell</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">add <code>export TIEFER_CSC_PROJECT=&lt;project&gt;</code> to <code>~/.bashrc</code> and log in again</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cannot load python-pytorch/2.10</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the module name or version differs on Roihu</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">find it with <code>module avail python-pytorch</code> and set <code>export TIEFER_PYTORCH_MODULE=&lt;name&gt;</code> before <code>setup.sh</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>Python 3.12 or newer is needed</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the module's Python is older</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">choose a newer PyTorch module and run <code>setup.sh</code> again</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>missing modules</code> in <code>check_env.py</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the venv was built on the other architecture or not at all</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">run <code>bash hpc/roihu/setup.sh</code> on the login node of the same architecture</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">The data job fails with a network error</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">compute nodes cannot reach <code>huggingface.co</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">use step 4b on the login node</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>invalid partition</code> from <code>sbatch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">a partition name differs on Roihu</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">check <code>sinfo</code> and edit the <code>#SBATCH --partition</code> line</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">The training log ends with <code>interrupted</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the time limit was reached</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">submit <code>train.sbatch</code> again with the run ID</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>the test split is only for final evaluation</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">test was requested without <code>FINAL=1</code> and <code>REASON</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">evaluate on validation; use test once, for the final result</td>
</tr>
</tbody>
</table>
</div>

---

## Changelog

- 1 October 2026: first version for milestone L1; CSC facts marked `TODO(verify)`.
