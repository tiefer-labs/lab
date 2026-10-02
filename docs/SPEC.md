<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Tiefer Lab specification

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The specification for milestone L1 of Tiefer Lab, the onboard cloud filter: what is built, how it is measured and what counts as done.

---

## 1. Context

Tiefer is a space technology startup from Baku, Azerbaijan. It builds AI software that runs on board Earth observation satellites. Instead of sending gigabytes of raw imagery to the ground hours later, the satellite analyses its own images in orbit. The onboard pipeline has four stages:

1. **Filter:** check every frame for cloud and quality as it is captured; frames that are not useful are compressed and kept on board, not sent.
2. **Detect:** run event models (fires, floods, vessels) on the useful frames.
3. **Alert:** send a small packet (location, event, confidence, image chip) through the first available link.
4. **Update:** replace models in orbit with small, signed updates.

This repository, `lab`, is where Tiefer trains, compresses and measures its models before anything flies. It is **public**: results are published with their method, because Tiefer's principle is "measured, not claimed". Milestone L1 builds the first stage, the cloud filter.

Contact for the project: `hello@tiefer.space`. Website: `https://tiefer.space`.

---

## 2. Hard rules (apply to every file and every commit message)

1. **No em dash (U+2014) and no U+2015.** Use commas, colons, full stops or parentheses. Plain hyphens (U+002D) are fine. **The en dash (U+2013) is allowed only where it is strictly required**, rarely, and never as a sentence dash (section 18.2).
2. **No emoji** anywhere, including U+FE0F and decorative symbols.
3. A test (section 15) enforces rules 1 and 2 on every text file in the repository and fails the build.
4. **No invented numbers.** Every metric, latency, power or size figure comes from a script in this repository that was actually run. If something was not measured, write "not measured".
5. **The test split is only for final evaluation.** Tune on validation. Every evaluation on test is logged (section 9).
6. **Public repository hygiene:** no secrets, no personal names other than "Tiefer", no personal email addresses, no CSC project numbers, no usernames, no absolute paths from anyone's machine or from Roihu in committed files (section 15).
7. Data, checkpoints and ONNX files never go into git.
8. Plain, precise English. No hype words ("revolutionary", "cutting-edge", "game-changing", "AI-powered", "seamless", "unlock", "leverage", "empower", "magic").

---

## 3. Goal and definition of done

### Part A: the repository is complete

1. Every component in sections 6 to 13 exists, is tested, and is documented.
2. `make check` passes locally and in GitHub Actions.
3. The full pipeline has run end to end on a tiny subset (a smoke run: data cache, training for a few minutes on CPU, evaluation on validation, ONNX export, INT8 quantisation, Jetson scripts in dry-run mode). Use real CloudSEN12+ patches when the data source is reachable from the build environment; otherwise run the same pipeline on synthetic data and leave the real-data smoke to the first Roihu job. Smoke outputs are clearly labelled as smoke and are never reported as results.
4. Everything the founder needs on Roihu is in `hpc/roihu/` with a step-by-step guide.
5. All work is committed in small, real commits, and CI is green.

### Part B: the results

After the Roihu runs, as described in section 17.

---

## 4. Principles

1. **Measured, not claimed.** Every number is reproducible with one command.
2. **Think like the sensor on board.**
   - Use **only four bands: blue, green, red and near infrared** (Sentinel-2 B02, B03, B04, B08 at 10 m). Very high resolution optical satellites, the kind Tiefer targets, typically carry these four bands plus panchromatic, not the shortwave infrared bands classic cloud algorithms rely on. Record this in `docs/ASSUMPTIONS.md`, to be revisited when a customer's exact sensor is known.
   - Use **Level-1C** (top-of-atmosphere reflectance), not Level-2A. On board there is no atmospheric correction.
3. **Small and friendly to the hardware.** At most 1.0 million parameters. Only operators TensorRT handles well in INT8: convolution, batch norm (folded at export), ReLU or ReLU6, max or average pooling, nearest or bilinear upsampling, transposed convolution, concatenation, addition. No attention, no custom operators.
4. **Reproducible.** Fixed seeds, configurations under version control, a locked environment (`uv.lock`), the dataset revision recorded, the git commit written into every result file.
5. **No synthetic data in metrics.** Synthetic arrays exist only for unit tests and CI, are named as synthetic, and never touch training or evaluation.
6. **Licences tracked** for every dataset and dependency.

---

## 5. Stack

- Python 3.12. Environment and lockfile with `uv`.
- Runtime: `torch`, `numpy`, `tacoreader`, `rasterio`, `onnx`, `onnxruntime`.
- Development: `pytest`, `ruff` (lint and format), `mypy` (strict on `src/`).
- Configuration: typed dataclasses loaded from TOML (`tomllib`, standard library).
- Text rule test only: `regex` (development dependency), for the Unicode property `\p{Extended_Pictographic}`.
- No other dependency without the team's agreement. Justify every dependency with its licence in `docs/DEPENDENCIES.md`.
- The code runs on CUDA, Apple MPS or CPU, chosen automatically, overridable with `--device`.
- The code accepts any PyTorch version in a declared range (for example `>=2.5`), because on Roihu PyTorch comes from the CSC module (section 12), and records the actual version in every run's metadata.

---

## 6. Data

### Source

**CloudSEN12+** on Hugging Face, dataset `tacofoundation/cloudsen12`, loaded with `tacoreader`. Licence: CC0 1.0. Cite the CloudSEN12 papers in `docs/DATA.md` anyway.

- Use the Level-1C variant and only patches whose labels have quality **high** (expert reviewed).
- Use the dataset's own train, validation and test splits.
- Four semantic classes: clear, thick cloud, thin cloud, cloud shadow.
- The full dataset is about 248 GB. Never download all of it. Read only the four bands and the labels of the needed patches.
- **Before writing the loader**, read the dataset card and the `tacoreader` documentation and record in `docs/DATA.md`, with links: variant names, band order, scale factor, label codes, split field, quality field, patch size, and the dataset revision you used. Do not guess any of these.

### Cache

- `python -m tiefer_lab.data.build_cache --split train|val|test [--limit N]` writes a compact, architecture-independent cache into `$TIEFER_DATA_DIR`: one `numpy` array file per split for images (uint16, four bands), one for labels (uint8), and a JSON index (patch IDs, metadata, dataset revision, build date, counts).
- `--limit N` builds a small subset for smoke runs.
- The builder is resumable and verifies counts at the end.

### Preprocessing

- Convert to top-of-atmosphere reflectance with the documented scale factor. Normalise with per-band mean and standard deviation computed on the **training split only**, stored in the cache index.
- Training: random crops (for example 256 x 256), flips, 90 degree rotations, small brightness and contrast changes within a physically plausible range.
- Evaluation: full patch, reflect padding to a multiple of 32, prediction cropped back. No augmentation.

### Data card

`docs/DATA.md`: source, licence, citation, revision, bands used and why, class definitions, split sizes, known biases (geography, season, land cover), and what the data does **not** represent (very high resolution sensors, onboard radiometry, compression artefacts).

---

## 7. Baselines

Evaluated with the same code and splits as the model:

1. **Always send:** every frame is sent. Shows the cost of doing nothing.
2. **Threshold rule:** a simple brightness and whiteness rule on the four bands, thresholds tuned on validation only.
3. **Reference masks:** masks from established algorithms shipped with the dataset (check the card for which). State clearly that they use more spectral bands, so the comparison favours them.

---

## 8. Model and training

- `src/tiefer_lab/models/cloud_filter.py`: a compact U-Net style encoder and decoder with depthwise separable convolutions. Input 4 bands, output 4 classes. At most 1.0 million parameters; a test asserts the budget and the allowed operator set (by exporting to ONNX and listing node types).
- Report parameter count and multiply-accumulate operations for a 1 x 4 x 512 x 512 input.
- Loss: cross-entropy plus Dice, class weights from the training split.
- Mixed precision: bf16 autocast when supported (Hopper GPUs on Roihu), otherwise fp16 on CUDA, fp32 on CPU and MPS.
- `channels_last` memory format on CUDA.
- Early stopping on validation mean IoU.
- **Resumable:** checkpoint at the end of every epoch and on SIGTERM or SIGUSR1; `--resume <run-dir>` continues from the last checkpoint. Load checkpoints with `torch.load(..., weights_only=True)`.
- **In-memory data:** load the cached training split into memory once per job when it fits (check size against available memory first), otherwise memory-map it.
- Every run writes to `$TIEFER_RUNS_DIR/<run-id>/`: resolved config, git commit, seed, device and GPU name, CPU architecture, Python and library versions, Slurm job ID, node and partition when present, start and end time, metrics per epoch (JSON lines), best checkpoint.
- From the mask, derive per frame: cloud fraction (thick plus thin), shadow fraction, and a **send or keep decision** at an operator-configurable threshold.
- Commands: `python -m tiefer_lab.train --config configs/<name>.toml [--resume <run-dir>] [--device ...]`.
- Configs: `configs/smoke.toml` (tiny, minutes on CPU) and `configs/l1_base.toml` (full training on one GH200 GPU).

---

## 9. Evaluation

`python -m tiefer_lab.evaluate --run <run-dir> --split val|test [--baselines]`

- Pixel level: IoU and F1 per class, mean IoU, overall accuracy, confusion matrix.
- Frame level: mean absolute error of the cloud fraction; decision accuracy at 30, 50 and 70 percent cloud thresholds.
- **False discard rate:** frames that are actually useful (cloud fraction below the threshold) but would be kept on board. The most important error for an operator; report it prominently.
- 95 percent confidence intervals by bootstrap over patches (1,000 resamples, fixed seed).
- Breakdown by available metadata (for example region or land cover) with sample counts.
- Output: JSON in `$TIEFER_REPORTS_DIR` with all provenance fields from section 8.
- **Test guard:** `--split test` requires the flag `--final` and appends an entry to `reports/test_log.md` (date, run ID, git commit, reason). Without `--final` it refuses to run. A test checks this.

---

## 10. Export and quantisation

`python -m tiefer_lab.export --run <run-dir>`

- ONNX FP32 with a pinned opset and fixed input shape 1 x 4 x 512 x 512 (plus a dynamic batch variant if trivial). Batch norm folded.
- Verify ONNX Runtime against PyTorch: maximum absolute logit difference, and identical argmax on at least 99.9 percent of validation pixels. Fail loudly otherwise.
- FP16 variant.
- INT8: static post-training quantisation with ONNX Runtime, calibration on a few hundred patches from the **training** split. Measure the change in mean IoU and false discard rate on validation (and on test only with `--final`, logged). If mean IoU drops by more than one point, say so and propose quantisation-aware training as future work.
- Release folder `models/cloud-filter/<version>/`: `MODEL_CARD.md`, `SHA256SUMS`, `config.toml` committed. **Trained models are never published from this repository**: checkpoints and `.onnx` files are gitignored, are not attached to GitHub Releases, and stay with Tiefer. The checksums let Tiefer prove which model produced which result.

---

## 11. Jetson benchmark

Folder `jetson/`, scripts meant to run on an NVIDIA Jetson Orin (flight-like reference hardware, not flight hardware):

- Record device model, JetPack and TensorRT versions, power mode (`nvpmodel -q`), whether `jetson_clocks` is active.
- Build TensorRT engines (FP16; INT8 with a calibration cache) with `trtexec`.
- Latency after warm-up over at least 1,000 runs: p50, p95, p99; throughput in tiles per second and square kilometres per second (a 512 x 512 tile at 10 m is 5.12 km x 5.12 km, about 26.2 square kilometres; show the formula).
- Power from `tegrastats` sampled during the run (input power rail); energy per tile in millijoules. Board temperature at start and end.
- JSON output to `reports/jetson/`.
- On a non-Jetson machine the scripts run in **dry-run mode** (validate inputs, print the plan), tested in CI.
- Radiation, vacuum and thermal effects are out of scope; say so in the output.

---

## 12. CSC Roihu

Training and full evaluation run on **CSC Roihu GPU nodes**. Check the current CSC documentation (docs.csc.fi) for every point marked "verify" and record the facts the code depends on, with links, in `hpc/roihu/README.md`.

### Facts (from docs.csc.fi, October 2026)

- CPU nodes are x86 (AMD). **GPU nodes are ARM (aarch64), NVIDIA GH200 Grace Hopper**, 4 GPUs per node; each reserved GPU gives up to 72 ARM cores, 95 GiB HBM3 and about 117 GiB CPU memory.
- Login nodes: `roihu-cpu.csc.fi` (x86) and `roihu-gpu.csc.fi` (ARM). Software for GPU jobs must be installed from `roihu-gpu.csc.fi`.
- GPU partitions: `gputest` (15 minutes), `gpumedium` (up to 36 hours, up to 4 GPUs on one node), `gpularge` (multi-node, not needed), `gpuinteractive` (up to 12 hours).
- Syntax: `#SBATCH --account=<project>` (mandatory), `#SBATCH --partition=gpumedium`, `#SBATCH --gres=gpu:gh200:1`.
- PyTorch comes from the module, for example `module load python-pytorch/2.10`, which includes CUDA and cuDNN. Verify the current name with `module avail python-pytorch`.
- Extra packages: a venv created with `python3 -m venv --system-site-packages` in `/projappl/<project>`, after loading the module. Set the pip cache outside the home directory.
- Storage: `/projappl/<project>` (software), `/scratch/<project>` (data and runs; **files unused for 180 days are deleted**), `$TMPDIR` (fast local NVMe inside a job).
- Verify: whether compute nodes can reach Hugging Face. The guide must handle both cases.

### Rules for the code

- All locations come from environment variables with local defaults: `TIEFER_DATA_DIR` (`./data`), `TIEFER_RUNS_DIR` (`./runs`), `TIEFER_REPORTS_DIR` (`./reports`).
- Two installation modes, one codebase:
  - Local: `uv sync` from `uv.lock`.
  - Roihu: module PyTorch, plus `hpc/roihu/requirements.txt` installed with `pip` into the venv, plus `pip install --no-deps -e .`.
  - `hpc/roihu/requirements.txt` is generated from `uv.lock` with `uv export` (no dev dependencies, no hashes, without `torch` and packages the module provides). A test checks it is in sync with `uv.lock`.

### Files in `hpc/roihu/`

| File | Purpose |
| :--- | :---: |
| `README.md` | Founder guide, plain English, step by step (below) |
| `job_prelude.sh` | Sourced first by every job and by `setup.sh`: stops with a clear message when `module` is missing, runs `module purge` |
| `shell_options.sh` | Turns off `errexit`, `nounset` and `pipefail` around every `module` command, then restores exactly the saved options |
| `env.sh` | Sourced by every job after `job_prelude.sh`: loads the module, activates the venv, sets `PIP_CACHE_DIR` and the `TIEFER_*` paths under `/projappl/$TIEFER_CSC_PROJECT` and `/scratch/$TIEFER_CSC_PROJECT`; fails clearly if `TIEFER_CSC_PROJECT` is unset |
| `setup.sh` | Run once per architecture: on `roihu-cpu.csc.fi` (`venv-x86_64`) and on `roihu-gpu.csc.fi` (`venv-aarch64`); creates the venv, installs, runs the environment check |
| `check_env.py` | Imports every dependency, prints versions, CPU architecture, GPU name, CUDA and bf16 availability; fails with a clear message if anything is missing |
| `data.sbatch` | Builds the full cache in `/scratch` (CPU job on either architecture, parallel downloads, resumable; never on a login node) |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: environment check plus `configs/smoke.toml`; builds a tiny cache in its own folder when the train and val splits of the full cache are not complete, and only reads the full cache |
| `train.sbatch` | `gpumedium`, 1 GPU, default 12 hours (maximum 36), `--signal=B:USR1@300`, resumable, takes a config path and an optional `SEED` |
| `evaluate.sbatch` | Validation evaluation with baselines; test only when `FINAL=1` is set |
| `export.sbatch` | Export and quantisation on Roihu (calibration needs the cached training data) |
| `submit.sh` | Wrapper that passes `--account=$TIEFER_CSC_PROJECT`, `--chdir` and the log location to `sbatch`, since `#SBATCH` lines cannot read environment variables; jobs use sbatch's default export, so `TIEFER_CSC_PROJECT`, `SEED`, `FINAL` and `REASON` reach the job as plain environment variables; GPU jobs are refused unless submitted from an `aarch64` host (`roihu-gpu.csc.fi`) and the data job unless from an `x86_64` host (`roihu-cpu.csc.fi`); `sbatch` options such as `--test-only` go before the job script |
| `usage.sh` | Prints `sacct` usage of a job for the results |
| `collect.sh` | Packs the small result files (reports, run metadata, best checkpoint, ONNX files) into one archive in `/scratch` for copying back, with no absolute paths inside |

Every job script starts with `#!/bin/bash -l` and uses sbatch's default export; GPU jobs stop unless `uname -m` is `aarch64`. Slurm output goes to `$TIEFER_RUNS_DIR/slurm/%x-%j.out`. Jobs copy the cache to `$TMPDIR` at start when it is read from disk.

### Founder guide (content of `hpc/roihu/README.md`)

1. Requirements: a CSC project with Roihu GPU access and GPU billing units; SSH access to `roihu-cpu.csc.fi` and `roihu-gpu.csc.fi` with a MyCSC-signed certificate; the CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. Confirm with the project PI or CSC Service Desk before the first job. This is the founder's decision.
2. Before you start: `csc-projects` for the remaining GPU billing units; `bash hpc/roihu/submit.sh --test-only <job>` to check a request; login nodes are for light work only, so the cache is never built there.
3. Clone with `git clone https://github.com/tiefer-labs/lab.git` into `/projappl/<project>/tiefer-lab/src` (public, no key) and set `export TIEFER_CSC_PROJECT=<project>` in `~/.bashrc`, with a warning never to paste the literal `<project>` and how to remove such a line.
4. `bash hpc/roihu/setup.sh` on the CPU side (`venv-x86_64`, on `roihu-cpu.csc.fi`) and on the GPU side (`venv-aarch64`, on `roihu-gpu.csc.fi`).
5. Build the data cache with `data.sbatch`.
6. `bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch` on `gputest`, check the log; when the train and val splits of the full cache are not complete, it builds a tiny cache in its own folder and never touches the full cache.
7. `bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/l1_base.toml` on `gpumedium`, one GPU per job, optionally two seeds as two jobs with `SEED`; follow with `squeue --me`; resubmit with the run ID if the time limit is reached.
8. `evaluate.sbatch`, then `export.sbatch`, the final test with `FINAL=1` and `REASON`, `usage.sh` per job, and `bash hpc/roihu/collect.sh <run-id>`; copy the archive to the founder's computer (for example with `scp` from the computer) and unpack it into the repository, where the results are processed.

---

## 13. Results document

`python -m tiefer_lab.results` builds `docs/RESULTS.md` **only from JSON files in `reports/`**, never from typed numbers. Sections: summary (three sentences, no adjectives), environment, data, model, baselines, pixel and frame metrics with confidence intervals, quantisation impact, Jetson measurements (or "not yet measured"), compute used on Roihu, limitations, how to reproduce, changelog.

Limitations must include: 10 m training data versus very high resolution target sensors, four bands only, public Level-1C data versus onboard raw data, no space environment effects.

In Part A, `docs/RESULTS.md` exists with every value "not yet measured". Smoke outputs never appear in it.

---

## 14. Repository layout (complete file tree)

This is the complete list of committed files at the end of Part A. Create every one of them. A file that turns out to be needed but is not listed is added to the repository and to this tree in the same commit. Directories end with `/`.

```text
lab/
  .github/
    dependabot.yml                weekly updates: pip (uv) and github-actions
    workflows/
      ci.yml                      lint, type check, tests on CPU with synthetic data
      codeql.yml                  CodeQL for python and actions
  configs/
    smoke.toml                    tiny run, minutes on CPU or MPS
    l1_base.toml                  full training on one GH200 GPU
    l1_full.toml                  l1_base to the end of its schedule, with warm-up and moving average
  docs/
    SPEC.md                       sections 1 to 17 of the build brief, unchanged
    STYLE.md                      the Markdown standard (section 18), for every Tiefer repository
    assets/                       provided by the founder, never edited
      header.png                  header image at the top of every Markdown file
      tiefer-logo.svg             the logo in brand blue
      tiefer-logo-white.svg       the logo in white, for dark backgrounds
    DATA.md                       data card with verified dataset facts and links
    ASSUMPTIONS.md                sensor and data assumptions to revisit
    DEPENDENCIES.md               every dependency, why it is needed, its licence
    RESULTS.md                    generated by tiefer_lab.results ("not yet measured" in Part A)
  hpc/
    roihu/
      README.md                   founder guide for CSC Roihu (section 12)
      job_prelude.sh              module check and module purge for every job
      shell_options.sh            relax and restore set -euo pipefail around module commands
      env.sh                      module, venv and TIEFER_* paths for every job
      setup.sh                    one-time setup per architecture (x86 and ARM)
      check_env.py                environment and GPU check
      requirements.txt            generated from uv.lock, without torch
      submit.sh                   sbatch wrapper: --account, log location, login node check
      usage.sh                    sacct usage of a job
      collect.sh                  packs results for copying back, no absolute paths
      data.sbatch                 builds the data cache in /scratch
      smoke.sbatch                gputest, 15 minutes
      train.sbatch                gpumedium, resumable
      evaluate.sbatch             validation, or test with FINAL=1
      export.sbatch               ONNX export and INT8 quantisation
  jetson/
    README.md                     how to run the benchmark on a Jetson Orin
    device_info.sh                device, JetPack, TensorRT, power mode, clocks
    build_engines.sh              trtexec FP16 and INT8 engines
    bench.py                      latency, throughput, energy; dry-run mode off-device
    power.py                      tegrastats sampler and parser
  models/
    cloud-filter/
      README.md                   what release folders contain (filled in Part B)
  reports/
    README.md                     what each report file is and which script writes it
    test_log.md                   log of every test split evaluation (header only in Part A)
    jetson/
      README.md                   where Jetson results land
  src/
    tiefer_lab/
      __init__.py                 package version
      py.typed
      config.py                   typed dataclasses, TOML loading and validation
      metrics.py                  IoU, F1, confusion, frame metrics, false discard rate
      bootstrap.py                confidence intervals
      decisions.py                cloud fraction and send or keep decision
      baselines.py                always send, threshold rule, reference masks
      train.py                    python -m tiefer_lab.train
      evaluate.py                 python -m tiefer_lab.evaluate, with the test guard
      results.py                  python -m tiefer_lab.results, builds docs/RESULTS.md
      smoke.py                    python -m tiefer_lab.smoke, the full local smoke pipeline
      tables.py                   Markdown table helper for every generated table
      data/
        __init__.py
        source.py                 CloudSEN12+ access with tacoreader
        build_cache.py            python -m tiefer_lab.data.build_cache
        http.py                   backoff on HTTP 429 and the Hugging Face token
        cache.py                  cache reading, in memory or memory-mapped
        dataset.py                PyTorch datasets for train and evaluation
        transforms.py             reflectance, normalisation, crops, augmentation, padding
      models/
        __init__.py
        cloud_filter.py           the compact network
        losses.py                 cross-entropy plus Dice
      export/
        __init__.py
        __main__.py               python -m tiefer_lab.export
        onnx_export.py            FP32 and FP16 export with folded batch norm
        verify.py                 ONNX Runtime against PyTorch
        quantise.py               INT8 static quantisation and its evaluation
      utils/
        __init__.py
        paths.py                  TIEFER_* variables and defaults
        devices.py                CUDA, MPS, CPU selection, precision choice
        seeding.py
        metadata.py               run provenance, Slurm fields, relative paths only
        signals.py                SIGTERM and SIGUSR1 handling
        checkpoint.py             save, load (weights_only), resume
        ema.py                    exponential moving average of the weights
  tests/
    __init__.py
    conftest.py                   synthetic fixtures, temporary TIEFER_* paths
    test_text_rules.py
    test_public_hygiene.py
    test_paths.py
    test_config.py
    test_requirements_sync.py
    test_transforms.py
    test_bands_and_labels.py
    test_cache.py                 cache build, resume and reading on synthetic data
    test_http.py                  backoff on HTTP 429, token never printed
    test_metrics.py
    test_bootstrap.py
    test_decisions.py
    test_baselines.py
    test_test_guard.py
    test_checkpoint_resume.py
    test_model_budget.py          parameter budget and allowed ONNX operators
    test_export.py
    test_quantise.py
    test_jetson_dry_run.py
    test_markdown_style.py        every Markdown file follows docs/STYLE.md
    test_results.py
    test_roihu_scripts.py         CSC Roihu helper scripts with stub sbatch and sacct
    test_tables.py                Markdown table helper
  .editorconfig
  .env.example                    TIEFER_* variables with comments, no secrets
  .gitattributes                  line endings, *.sh and *.sbatch as LF
  .gitignore                      data/, runs/, .venv/, *.onnx, *.pt, *.engine, .env, caches
  .python-version                 3.12
  CITATION.cff                    how to cite Tiefer Lab (author: Tiefer)
  LICENSE                         MPL 2.0, official text
  Makefile
  NOTICE.md                       licence notes: repository MPL 2.0, data, dependencies, trademarks
  README.md                       public README in English
  pyproject.toml                  project metadata (license MPL-2.0), dependencies, ruff, mypy, pytest
  uv.lock
```

Created at runtime and never committed: `data/`, `runs/`, `.venv/`, `*.onnx`, `*.pt`, `*.engine`, `.env`.

`SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `SUPPORT.md` are not repeated here: GitHub shows the organisation-wide versions from `tiefer-labs/.github` automatically. Link to them from `README.md`.

`Makefile` targets: `setup`, `lint`, `typecheck`, `test`, `check` (lint, typecheck, test), `smoke` (the full local smoke pipeline on a tiny subset), `requirements` (regenerate `hpc/roihu/requirements.txt`), `results`.

`README.md` (English, public) follows section 18: header image, one sentence, link row, then what Tiefer Lab is (two paragraphs, plain), a status table for milestone L1, milestone L1 and its status, how to run locally, how to run on CSC Roihu (link to `hpc/roihu/README.md`), data and licences, results (link to `docs/RESULTS.md`), licence, contact `hello@tiefer.space`. No badges that call third-party services, no emoji.

Never committed: local working notes, editor and tool settings folders, `data/`, `runs/` and `.env`. Local tool folders are excluded through `.git/info/exclude`, not listed in `.gitignore`.

---

## 15. Quality, security and public repository hygiene

- `ruff`, `mypy --strict` on `src/`, `pytest` pass on every commit.
- Every Markdown file follows `docs/STYLE.md` (section 18): the header image, the standard header block, heading levels, copy-ready commands, sources for every number. `LICENSE` and `docs/assets/` are provided by the founder and are never edited.
- Tests cover: paths from `TIEFER_*` variables; `requirements.txt` in sync with `uv.lock`; data transforms and normalisation; exactly four bands in the right order; label mapping; metrics against hand-computed examples; frame decisions; bootstrap reproducibility; the test-split guard; checkpoint save and resume; parameter budget and operator set; ONNX export round trip on a tiny untrained model; quantisation on synthetic data; Jetson scripts in dry-run mode; results generator refusing to run without real report files.
- **Text rule test:** fails if any tracked text file (`.py`, `.md`, `.toml`, `.yaml`, `.yml`, `.txt`, `.sh`, `.sbatch`, `.json`, `.cff`, `.cfg`) contains U+2014, U+2015, U+FE0F or a character with the Unicode property Extended_Pictographic (checked with the `regex` package), or an en dash (U+2013) that has a space or line boundary on either side (an en dash is only accepted directly between two characters, as in a range). `LICENSE` is checked too.
- **Public hygiene test:** fails if a tracked file contains an absolute home or scratch path (for example `/home/`, `/Users/`, `/users/`, `/scratch/project_`, `/projappl/project_`), a CSC project identifier pattern (`project_` followed by digits), an email address other than `hello@tiefer.space`, something that looks like a key or token, or the name of any AI coding tool or its vendor in tracked content or paths (patterns built from string pieces so the test does not match itself). Report JSON stores paths relative to the repository or as `$TIEFER_*` placeholders.
- Both tests write their patterns with escape sequences or string concatenation (for example the Python escape sequence for U+2014 instead of the character itself), never as literal characters, so they do not flag themselves. Placeholders such as `<project>` in documentation are allowed.
- `ci.yml`: push and pull request, CPU only, synthetic data only: lint, type check, tests. Top-level `permissions: contents: read`. Actions pinned by full commit SHA with the tag in a comment; resolve SHAs with `git ls-remote`, never invent one. `persist-credentials: false`. No `pull_request_target`.
- `codeql.yml`: CodeQL for Python and GitHub Actions on push, pull request and weekly.
- `dependabot.yml`: weekly for Python dependencies and GitHub Actions.
- No secrets anywhere. `.env.example` documents the `TIEFER_*` variables; `.env` is gitignored.
- Never use `pickle` on files from outside this repository's own runs.

---

## 16. Licence

- **The whole repository is licensed under the Mozilla Public License 2.0**: code, scripts, configurations, documentation and reports. This is the same licence as Tiefer's other public repositories. Set `license = "MPL-2.0"` in `pyproject.toml` and `license: MPL-2.0` in `CITATION.cff`.
- Trained models are not part of the repository and are not covered by any licence here (section 10). `LICENSE` is added by the founder from GitHub's licence template ("Mozilla Public License 2.0") and contains the official, unmodified text. Never edit it. If it is missing, stop and ask the founder to add it; never type the licence from memory.
- Every source file (`.py`, `.sh`, `.sbatch`, `.toml` configs) starts with the MPL 2.0 notice in a comment:

  ```text
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at https://mozilla.org/MPL/2.0/.
  ```

- `NOTICE.md`: the repository is MPL 2.0; trained models are not distributed here; the Tiefer name and logo are trademarks and are not licensed (MPL 2.0 section 2.3 grants no trademark rights); CloudSEN12+ is a third-party dataset under CC0 1.0 (with citation) and is not included in the repository; every dependency with its licence.

---

---

## 17. Part B: results after the Roihu runs

1. Unpack the returned files into `reports/`, `runs/` and `models/` and check their provenance (commit, config, platform). Flag anything inconsistent.
2. Check that test evaluations are logged in `reports/test_log.md` and that no tuning happened on test.
3. Write `MODEL_CARD.md` and `SHA256SUMS` for the release folder.
4. Generate `docs/RESULTS.md` with `make results`.
5. If Jetson numbers are missing, leave them as "not yet measured".
6. Commit in small, real commits.

---

## Changelog

- 1 October 2026: `hpc/roihu/gpu_shell.sh` removed; GPU setup and GPU jobs run from `roihu-gpu.csc.fi`.
- 1 October 2026: job scripts no longer use `--export=NONE`; `job_prelude.sh` keeps only the module check and `module purge`.
- 1 October 2026: `submit.sh` uses sbatch's default export again and checks the architecture of the submitting host.
- 1 October 2026: `hpc/roihu/shell_options.sh` added to the table and the tree.
- 1 October 2026: the founder guide in section 12 follows the new order of `hpc/roihu/README.md`: before you start, clone and project, setup on both architectures, data, smoke, training with optional seeds, evaluation to collection; the login node cache path is removed.
- 1 October 2026: `hpc/roihu/job_prelude.sh` and `hpc/roihu/gpu_shell.sh` added to the table and the tree; job scripts use a login shell and `--export=NONE`.
- 1 October 2026: the table of files in `hpc/roihu/` follows the table format of docs/STYLE.md, section 9 (first column left, other columns centred); content unchanged.
- 1 October 2026: sections 1 to 17 added for milestone L1, Part A.
