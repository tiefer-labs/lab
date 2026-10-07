<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Tiefer Lab specification

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The specification of Tiefer Lab for milestones L1 and L2, the onboard cloud filter: what is built, how it is measured and what counts as done.

---

## 1. Context

Tiefer is a space technology startup from Baku, Azerbaijan. It builds AI software that runs on board Earth observation satellites. Instead of sending gigabytes of raw imagery to the ground hours later, the satellite analyses its own images in orbit. The onboard pipeline has four stages:

1. **Filter:** check every frame for cloud and quality as it is captured; frames that are not useful are compressed and kept on board, not sent.
2. **Detect:** run event models (fires, floods, vessels) on the useful frames.
3. **Alert:** send a small packet (location, event, confidence, image chip) through the first available link.
4. **Update:** replace models in orbit with small, signed updates.

This repository, `lab`, is where Tiefer trains, compresses and measures its models before anything flies. It is **public**: results are published with their method, because Tiefer's principle is "measured, not claimed". Milestone L1 builds the first stage, the cloud filter, on four bands. Milestone L2 extends it to a band-flexible model family that reads any of the 13 Sentinel-2 Level-1C bands, with four-band specialists as a control (section 8). A Jetson milestone measures the selected model on an NVIDIA Jetson Orin (section 11).

Contact for the project: `hello@tiefer.space`. Website: `https://tiefer.space`.

---

## 2. Hard rules (apply to every file and every commit message)

1. **No em dash (U+2014) and no U+2015.** Use commas, colons, full stops or parentheses. Plain hyphens (U+002D) are fine. The en dash (U+2013) is allowed only where it is strictly required, rarely, and never as a sentence dash ([STYLE.md](STYLE.md), section 3).
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

### Acceptance targets

The acceptance targets of milestone L2, with their minimum and target values, are defined once, in [REQUIREMENTS.md](REQUIREMENTS.md), section 8, from `src/tiefer_lab/acceptance.py`. Other documents link there instead of repeating them.

### Milestone L2: done when

1. Every L2 config of the run plan has run, or is marked `not run` with its reason in [hpc/roihu/plan.md](../hpc/roihu/plan.md).
2. The report files of the L2 runs are in `reports/`, and every acceptance target of REQUIREMENTS.md, section 8, has a status from them.
3. The product decision between the band-flexible model and the four-band specialists is recorded on validation by the rule of [ASSUMPTIONS.md](ASSUMPTIONS.md), section 7. On 7 October 2026 it is provisional: no decision is recorded, because `x-val-4` is pending ([RESULTS.md](RESULTS.md), section 12).
4. The comparisons of [LANDSCAPE.md](LANDSCAPE.md), section 5, name the measurement that decides each of them, and the open measurements are listed in hpc/roihu/plan.md.

### Jetson milestone: done when

1. `jetson/bench.py` has measured the selected model in FP16 and INT8 on a Jetson Orin: latency p50, p95 and p99, throughput, input rail power and energy per tile (section 11).
2. The report files are in `reports/jetson/`, and the targets `OBD-01` to `OBD-06` of REQUIREMENTS.md, section 8, have a status from them.

---

## 4. Principles

1. **Measured, not claimed.** Every number names the report file, configuration and commit behind it, and the commands to reproduce it are in [RESULTS.md](RESULTS.md), section 19. The gates a number, a model card or a public statement must pass are in [POLICY.md](../POLICY.md); the status of every capability Tiefer states in public is in [CLAIMS.md](../CLAIMS.md).
2. **Think like the sensor on board.**
   - Milestone L1 uses **only four bands: blue, green, red and near infrared** (Sentinel-2 B02, B03, B04, B08 at 10 m); milestone L2 also reads the other Level-1C bands (section 8). Very high resolution optical satellites, the kind Tiefer targets, typically carry these four bands plus panchromatic, not the shortwave infrared bands classic cloud algorithms rely on. Record this in `docs/ASSUMPTIONS.md`, to be revisited when a customer's exact sensor is known.
   - Use **Level-1C** (top-of-atmosphere reflectance), not Level-2A. On board there is no atmospheric correction.
3. **Small and friendly to the hardware.** At most 1.0 million parameters in the L1 configs; the L2 size ladder has its own sizes (section 8). Only operators TensorRT handles well in INT8: convolution, batch norm (folded at export), ReLU or ReLU6, max or average pooling, nearest or bilinear upsampling, transposed convolution, concatenation, addition. No attention, no custom operators.
4. **Reproducible.** Fixed seeds, configurations under version control, a locked environment (`uv.lock`), the dataset revision recorded, the git commit written into every result file.
5. **No synthetic data in metrics.** Synthetic arrays exist only for unit tests and CI, are named as synthetic, and never touch training or evaluation.
6. **Licences tracked** for every dataset and dependency.

---

## 5. Stack

- Python 3.12. Environment and lockfile with `uv`.
- Runtime: `torch`, `numpy`, `tacoreader`, `fsspec[http]`, `rasterio`, `onnx`, `onnxruntime`.
- Development: `pytest`, `ruff` (lint and format), `mypy` (strict on `src/`), `coverage`.
- Build backend: `hatchling` 1.32.4, pinned in `pyproject.toml`; `uv` 0.8 or newer (`required-version`).
- Configuration: typed dataclasses loaded from TOML (`tomllib`, standard library).
- Text rule test only: `regex` (development dependency), for the Unicode property `\p{Extended_Pictographic}`.
- No other dependency without the team's agreement. Every dependency, with its range, locked version and licence, is listed in [DEPENDENCIES.md](DEPENDENCIES.md).
- The code runs on CUDA, Apple MPS or CPU, chosen automatically, overridable with `--device`.
- The code accepts any PyTorch version in a declared range (for example `>=2.5`), because on Roihu PyTorch comes from the CSC module (section 12), and records the actual version in every run's metadata.

---

## 6. Data

### Source

**CloudSEN12+** on Hugging Face, dataset `tacofoundation/cloudsen12`, loaded with `tacoreader`. Licence: CC0 1.0. Cite the CloudSEN12 papers in `docs/DATA.md` anyway.

- Use the Level-1C variant and only patches whose labels have quality **high** (expert reviewed).
- Use the dataset's own train, validation and test splits.
- Four semantic classes: clear, thick cloud, thin cloud, cloud shadow.
- The Hugging Face page gives 248 GB for the whole dataset ([DATA.md](DATA.md), section 7). Never download all of it. Read only the bands and the labels of the needed patches.
- **Before writing the loader**, read the dataset card and the `tacoreader` documentation and record in `docs/DATA.md`, with links: variant names, band order, scale factor, label codes, split field, quality field, patch size, and the dataset revision you used. Do not guess any of these.

### Cache

- `python -m tiefer_lab.data.build_cache --split train|val|test|train_extra|all [--bands used|all] [--name <cache>] [--limit N]` writes a compact, architecture-independent cache into `$TIEFER_DATA_DIR`: one `numpy` array file per split for images (uint16, the four L1 bands, or all 13 with `--bands all`), one for labels (uint8), and a JSON index (patch IDs, metadata, dataset revision, build date, counts). The other options (`--shard`, `--merge`, `--max-rate`, `--workers`, `--taco`, `--revision`, `--references`, `--restart`, `--synthetic`) are listed in [DATA.md](DATA.md), section 10.
- `--limit N` builds a small subset for smoke runs.
- The builder is resumable and verifies counts at the end.

### Preprocessing

- Convert to top-of-atmosphere reflectance with the documented scale factor. Normalise with per-band mean and standard deviation computed on the **training split only**, stored in the cache index.
- Training: random crops (for example 256 x 256), flips, 90 degree rotations, small brightness and contrast changes within a physically plausible range.
- Evaluation: full patch, reflect padding to a multiple of 32, prediction cropped back. No augmentation.

### Data card

[DATA.md](DATA.md) answers the datasheet questions (motivation, composition, collection and labelling, preprocessing, uses, distribution, maintenance), then lists the facts the code depends on and the caches built ([STYLE.md](STYLE.md), section 12.5).

---

## 7. Baselines

Evaluated with the same code and splits as the model:

1. **Always send:** every frame is sent. Shows the cost of doing nothing.
2. **Threshold rule:** a brightness and whiteness rule on the four bands, thresholds tuned on validation only.
3. **Reference masks:** masks from established algorithms shipped with the dataset (check the card for which). State clearly that they use more spectral bands, so the comparison favours them.

---

## 8. Model and training

- `src/tiefer_lab/models/cloud_filter.py`: a compact U-Net style encoder and decoder with depthwise separable convolutions. Input 4 bands, output 4 classes. The L1 configs (`configs/l1_*.toml`) stay at most 1.0 million parameters; a test asserts the budget and the allowed operator set (by exporting to ONNX and listing node types). The L2 family below has its own sizes.
- Report parameter count and multiply-accumulate operations for a 1 x 4 x 512 x 512 input.
- Loss: cross-entropy plus Dice. Class weights: the L1 configs use median-frequency weights from the training split (`class_weighting = "median_frequency"`, the default of `src/tiefer_lab/config.py`); the L2 configs set `none`, except `l2_flex_1m_classweights` ([ASSUMPTIONS.md](ASSUMPTIONS.md), section 6).
- Mixed precision: bf16 autocast when supported (Hopper GPUs on Roihu), otherwise fp16 on CUDA, fp32 on CPU and MPS.
- `channels_last` memory format on CUDA.
- Early stopping on validation mean IoU, with the patience of the config (15 for `l1_base`, 150 for `l1_full` and every L2 config, which is the full schedule).
- **Resumable:** checkpoint at the end of every epoch and on SIGTERM or SIGUSR1; `--resume <run-dir>` continues from the last checkpoint. Load checkpoints with `torch.load(..., weights_only=True)`.
- **In-memory data:** load the cached training split into memory once per job when it fits (check size against available memory first), otherwise memory-map it.
- Every run writes to `$TIEFER_RUNS_DIR/<run-id>/`: resolved config, git commit, seed, device and GPU name, CPU architecture, Python and library versions, Slurm job ID, node and partition when present, start and end time, metrics per epoch (JSON lines), best checkpoint.
- From the mask, derive per frame: cloud fraction (thick plus thin), shadow fraction, and a **send or keep decision** at an operator-configurable threshold.
- Commands: `python -m tiefer_lab.train --config configs/<name>.toml [--seed N] [--run-id <name>] [--resume <run-dir>] [--device ...]`; `--cache-name`, `--epochs` and `--max-steps-per-epoch` are for the smoke pipeline and timing runs, which are marked as smoke.
- Configs: `configs/smoke.toml` (tiny, minutes on CPU), `configs/l1_base.toml` (full training on one GH200 GPU) and `configs/l1_full.toml` (`l1_base` to the end of its schedule, with warm-up and a moving average of the weights); the L2 configs are listed in section 14. Batch size, learning rate and the other settings of each family are in [ASSUMPTIONS.md](ASSUMPTIONS.md), section 6.

### Milestone L2: one band-flexible model family

- **Input:** all 13 Level-1C bands, normalised, plus one availability flag per band (26 input channels). An unavailable band is replaced before the network sees it, so it cannot look like a dark pixel. Two designs are compared on validation and the better one is kept: `placeholder` (a learned value per band) and `zero` (0, the training mean after normalisation).
- **Band sets:** one is drawn per batch from a fixed list in the config (`train.band_sets`); the list matches sensor classes:

  | Band set | Bands |
  | :--- | :---: |
  | blue, green, red | B02, B03, B04 |
  | plus near infrared | B02, B03, B04, B08 |
  | plus short-wave infrared | B02, B03, B04, B08, B11, B12 (B11 and B12 are the short-wave infrared bands of Sentinel-2 MSI, 20 m; B10, the 60 m cirrus band, is not in this set; ESA SentiWiki, S2 Mission, accessed 7 October 2026) |
  | all | B01 to B12 and B8A, 13 bands |

- **Self-distillation:** on a batch that draws a smaller band set, the prediction with all 13 bands (no gradient) is a soft target for the prediction with the drawn set, next to the label loss (`train.distill_weight`).
- **Size ladder:** about 0.5 M, 1 M, 4 M and 20 to 30 M parameters with otherwise identical settings; two architectures at the largest size (the separable U-Net and a U-Net with ConvNeXt-style encoder blocks). No pretrained weights.
- **Control:** four-band specialists (blue, green, red, near infrared) at 1 M and at the largest size, same data and schedule. The decision rule is in [ASSUMPTIONS.md](ASSUMPTIONS.md), section 7; on 7 October 2026 no decision is recorded (section 3).
- **Settings:** every setting in which the L1 and L2 configs differ (batch, learning rate, warm-up, moving average, patience, class weighting and others) is listed in [docs/ASSUMPTIONS.md](ASSUMPTIONS.md), section 6.
- **Loss:** cross-entropy plus Dice without class weights as the baseline; class weights and a focal term as separate runs. Pixels without a label (scribble gaps, nolabel patches) are ignored.
- **Export:** one ONNX file per band set and size, with input 1 x N x 512 x 512 for a band set of N bands; the exported model takes only the bands of its set, with the availability flags fixed. FP32, FP16 and INT8, each checked against PyTorch.

---

## 9. Evaluation

`python -m tiefer_lab.evaluate --run <run-dir> --split val|test [--baselines] [--checkpoint best|last] [--band-set <bands>|all] [--perturb <name>=<value>] [--device ...]`; the test split also needs `--final --reason <text>`.

- Pixel level: IoU and F1 per class, mean IoU, overall accuracy, confusion matrix.
- Frame level: mean absolute error of the cloud fraction; decision accuracy at 30, 50 and 70 percent cloud thresholds.
- **False discard rate:** frames that are actually useful (cloud fraction below the threshold) but would be kept on board. The most important error for an operator; report it prominently.
- 95 percent confidence intervals by bootstrap over patches (1,000 resamples, fixed seed).
- Breakdown by available metadata (for example region or land cover) with sample counts.
- **Padding:** the dataset pads each 509 x 509 patch to 512 x 512 ([DATA.md](DATA.md), section 5). When a split is loaded, every padded label pixel is set to `IGNORE_INDEX` (`src/tiefer_lab/data/padding.py`, since 7 October 2026); the width comes from `real_proj_shape` and the stored size, the sides from `PADDING_SIDES`. Every pixel metric, cloud fraction, frame metric, bootstrap interval, breakdown, baseline, export check, the loss and the class weights then count only labelled pixels of the real image area; the predicted cloud fraction of a frame is taken over the same pixels as the reference. Images are not changed. Values computed before this change count the padded pixels.
- Output: JSON in `$TIEFER_REPORTS_DIR` with all provenance fields from section 8.
- **Test guard:** `--split test` requires the flag `--final` and appends an entry to `reports/test_log.md` (date, run ID, git commit, reason) before the test data is read; `python -m tiefer_lab.export --final` does the same. Without `--final` it refuses to run. A test checks this.

### Operational design domain and fail-safe behaviour

The inputs the filter is designed for (`tiefer_lab.onboard.Domain`). A frame outside them is not classified: it is sent and flagged.

| Property | Inside the domain | Validated so far |
| :--- | :---: | :---: |
| Bands | exactly the bands of the model's band set, in its order | Sentinel-2 Level-1C bands only |
| Values | top-of-atmosphere reflectance in [0, 2] after the reflectance scale (1e-4 for Sentinel-2 digital numbers) | Sentinel-2 Level-1C |
| Ground sampling distance | 0.5 to 20 m; the frame is resampled to 10 m before inference | 10 m, and resolution changes simulated by rescaling Sentinel-2 |
| Invalid pixels | at most 1 percent saturated, empty (all bands 0) or out of range | n/a |
| Frame size | at least 32 pixels per side; large frames run in 512-pixel tiles overlapping by 64 | 509 x 509 patches; tiling tested on synthetic frames |
| Other sensors | outside the validated domain until measured on that sensor's data | none |

- **Fail-safe:** wrong band count, non-finite values, too many invalid pixels, a resolution or size outside the domain, a model file whose SHA-256 is not the expected one, or any error during inference end in "send" with a status and a flag. A doubtful frame costs downlink, never a lost frame.
- `tiefer_lab.onboard.failsafe_check` runs nine such cases and a valid cloudy control; the acceptance target is that none of them is discarded (`tests/test_onboard.py`, `reports/acceptance.md`).

---

## 10. Export and quantisation

`python -m tiefer_lab.export --run <run-dir> [--checkpoint best|last] [--band-set <bands>|all] [--skip-int8] [--final --reason <text>]`

- ONNX FP32 with a pinned opset (17) and a fixed input shape: 1 x 4 x 512 x 512 for the L1 models and the four-band specialists, 1 x N x 512 x 512 per band set of the band-flexible model (plus a dynamic batch variant if trivial). Batch norm folded.
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

The facts the scripts depend on, each with its source, are in the table of [hpc/roihu/README.md](../hpc/roihu/README.md), section 6; that table is the reference, and this list summarises it.

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
| `survey.sbatch` | Short CPU job: counts, splits, locations and item encodings of the dataset, in `reports/data/survey.json` |
| `data.sbatch` | Builds the full cache in `/scratch` (CPU job on either architecture, parallel downloads, resumable; never on a login node) |
| `smoke.sbatch` | `gputest`, 1 GPU, 15 minutes: environment check plus `configs/smoke.toml`; builds a tiny cache in its own folder when the train and val splits of the full cache are not complete, and only reads the full cache |
| `train.sbatch` | `gpumedium`, 1 GPU, default 12 hours (maximum 36), `--signal=B:USR1@300`, resumable, takes a config path and an optional `SEED` |
| `evaluate.sbatch` | Validation evaluation with baselines; test only when `FINAL=1` is set |
| `export.sbatch` | Export and quantisation on Roihu (calibration needs the cached training data) |
| `submit.sh` | Wrapper that passes `--account=$TIEFER_CSC_PROJECT`, `--chdir` and the log location to `sbatch`, since `#SBATCH` lines cannot read environment variables; jobs use sbatch's default export, so `TIEFER_CSC_PROJECT`, `SEED`, `FINAL` and `REASON` reach the job as plain environment variables; GPU jobs are refused unless submitted from an `aarch64` host (`roihu-gpu.csc.fi`) and the data job unless from an `x86_64` host (`roihu-cpu.csc.fi`); `sbatch` options such as `--test-only` go before the job script |
| `usage.sh` | Prints `sacct` usage of a job for the results |
| `timing.sbatch` | One cut epoch on `gputest`: the real cost of a config |
| `sweep.sh` | Submits configs and seeds as separate one-GPU jobs |
| `plan.md` | The run plan of 2 October 2026, what ran, and the open measurements |
| `requirements.txt` | Generated from `uv.lock` with `uv export`, without the packages of the CSC module |
| `collect.sh` | Packs the small result files (reports, run metadata, best checkpoint, ONNX files) into one archive in `/scratch` for copying back, with no absolute paths inside |

Every job script starts with `#!/bin/bash -l` and uses sbatch's default export; GPU jobs stop unless `uname -m` is `aarch64`. Slurm output goes to `$TIEFER_RUNS_DIR/slurm/%x-%j.out`. Jobs copy the cache to `$TMPDIR` at start when it is read from disk.

### Founder guide (content of `hpc/roihu/README.md`)

The guide follows docs/STYLE.md, section 12.14, and its steps are:

1. Requirements: a CSC project with Roihu GPU access and GPU billing units; SSH access to `roihu-cpu.csc.fi` and `roihu-gpu.csc.fi` with a MyCSC-signed certificate; the CSC terms of use. Free CSC computing is for research and education by people affiliated with Finnish research organisations, and may not serve an organisation's own service production; commercial work needs a paid project. Confirm with the project PI or CSC Service Desk before the first job. This is the founder's decision.
2. Before you start: the remaining GPU billing units; `bash hpc/roihu/submit.sh --test-only <job>` to check a request; which login node submits which job; login nodes are for light work only, so the cache is never built there.
3. Step 1, clone and set the project: `git clone https://github.com/tiefer-labs/lab.git` into `/projappl/<project>/tiefer-lab/src` and `export TIEFER_CSC_PROJECT=<project>` in `~/.bashrc`, with a warning never to paste the literal `<project>`.
4. Step 2, set up both architectures: `bash hpc/roihu/setup.sh` on `roihu-cpu.csc.fi` (`venv-x86_64`) and on `roihu-gpu.csc.fi` (`venv-aarch64`).
5. Step 3, survey the dataset with `survey.sbatch`, then build the data cache with `data.sbatch`.
6. Step 4, the smoke job on `gputest`; when the train and val splits of the full cache are not complete, it builds a tiny cache in its own folder and never touches the full cache.
7. Step 5, train on `gpumedium`, one GPU per job, seeds as separate jobs with `SEED`; `timing.sbatch` and `sweep.sh` for the cost of a config and for several configs.
8. Step 6, evaluate, export, the final test with `FINAL=1` and `REASON`, `usage.sh` per job, and `bash hpc/roihu/collect.sh <run-id>`; copy the archive to the founder's computer and unpack it into the repository.

---

## 13. Results document

Until 7 October 2026, a results generator built `docs/RESULTS.md` only from the JSON files in `reports/`. In Part A the page existed with every value not measured, and smoke outputs never appeared in it. The generator was removed on 7 October 2026: the generated page was hard to read, and the results of milestones L1 and L2 had to be combined in tables it could not lay out.

Since then the step is: write `docs/RESULTS.md` by hand, by the results page type of [STYLE.md](STYLE.md), section 12.2.

- Every value names the report file in `reports/` that it was copied from, and the report file records the git commit, configuration and platform. No value without a report file, the dataset revision and a commit behind it.
- A value from the session notes (`notes`) or a value that is `pending` is allowed for a time. Each such value is listed in the section of values to verify, with its exit condition: the report file is copied into the repository and the value is checked against it.
- Missing values use the words of STYLE.md, section 4: `not measured`, `pending`, `n/a`.
- Sections: summary (three sentences, no adjectives), how to read the page, runs, environment and provenance, data, results by topic with a source column, quantisation, hardware, compute used on Roihu, training notes, limitations, how to reproduce, values to verify, report files, changelog.

Limitations must include: 10 m training data versus very high resolution target sensors, the band set of each result, public Level-1C data versus onboard raw data, no space environment effects.

---

## 14. Repository layout (complete file tree)

This is the complete list of committed files at the end of Part A. Create every one of them. A file that turns out to be needed but is not listed is added to the repository and to this tree in the same commit. Directories end with `/`.

```text
lab/
  .github/
    dependabot.yml                weekly updates: uv and github-actions; tacoreader held below 0.6
    audit-exceptions.toml         accepted vulnerability findings, each with a reason and an expiry
    ci-tools/
      requirements.in             CI-only tools: pip-audit, shellcheck-py
      requirements.txt            the same, pinned with hashes
    scripts/
      audit_exceptions.py         checks the accepted findings and turns them into pip-audit arguments
      coverage_floor.py           fails when the coverage floor is lower than in the base commit
    workflows/
      ci.yml                      lint, type check, tests (x86, ARM, coverage), shellcheck, smoke, SBOM, secret scan
      audit.yml                   vulnerability audit of uv.lock on push and weekly
      codeql.yml                  CodeQL for python and actions
  configs/
    smoke.toml                    tiny run, minutes on CPU or MPS
    l1_base.toml                  full training on one GH200 GPU
    l1_full.toml                  l1_base to the end of its schedule, with warm-up and moving average
    l2_flex_1m.toml               band-flexible, about 1 M parameters: reference run of the family
    l2_flex_1m_zero.toml          as l2_flex_1m with the zero input design
    l2_flex_0p5m.toml             size ladder, about 0.5 M parameters
    l2_flex_4m.toml               size ladder, about 4 M parameters
    l2_flex_22m.toml              size ladder, about 22 M parameters, separable U-Net
    l2_flex_cnx_21m.toml          size ladder, about 21 M parameters, ConvNeXt-style U-Net
    l2_spec_1m.toml               four-band specialist, about 1 M parameters (control)
    l2_spec_22m.toml              four-band specialist, about 22 M parameters (control)
    l2_flex_1m_classweights.toml  as l2_flex_1m with class weights
    l2_flex_1m_focal.toml         as l2_flex_1m with a focal term
    l2_flex_1m_nodistill.toml     as l2_flex_1m without self-distillation
    l2_flex_1m_rescale.toml       as l2_flex_1m with random rescaling, 0.5 to 2
    l2_flex_1m_gainoffset.toml    as l2_flex_1m with per-band gain and offset jitter
    l2_flex_1m_noiseblur.toml     as l2_flex_1m with sensor noise and mild blur
  docs/
    SPEC.md                       this specification
    STYLE.md                      the documentation standard, for every Tiefer repository
    assets/                       provided by the founder, never edited
      header.png                  header image at the top of every Markdown file
      tiefer-logo.svg             the logo in brand blue
      tiefer-logo-white.svg       the logo in white, for dark backgrounds
    DATA.md                       data card with verified dataset facts and links
    DATASETS.md                   dataset catalogue, roles per split, harmonisation, comparison metrics
    LANDSCAPE.md                  related systems, their published values, what decides each comparison
    ASSUMPTIONS.md                sensor and data assumptions to revisit
    REQUIREMENTS.md               every requirement and acceptance target with its verification
    STANDARDS.md                  standards matrix: area, document and clause, evidence, status
    DEPENDENCIES.md               every dependency, why it is needed, its licence
    RESULTS.md                    measured results, written by hand from reports/ (generated until 7 October 2026)
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
      survey.sbatch               survey of the dataset metadata and item encodings
      timing.sbatch               one cut epoch on gputest: the real cost of a config
      sweep.sh                    configs and seeds as separate one-GPU jobs
      plan.md                     run plan of 2 October 2026, what ran, open measurements
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
      MODEL_CARD_TEMPLATE.md      model card to copy into each release folder
      v0.1.0/
        MODEL_CARD.md             model card of l1_base s0 (draft)
        SHA256SUMS                SHA-256 of the model files, which are not in the repository
        config.toml               resolved configuration of the run
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
      metrics.py                  IoU, F1, producer's and user's accuracy, frame metrics
      binary_metrics.py           cloud and shadow BOA, PA, UA, OA per patch, median
      bootstrap.py                confidence intervals
      decisions.py                cloud fraction and send or keep decision
      baselines.py                always send, threshold rule, reference masks
      train.py                    python -m tiefer_lab.train
      evaluate.py                 python -m tiefer_lab.evaluate, with the test guard
      reports.py                  loads the report files for tiefer_lab.acceptance (results.py until 7 October 2026)
      experiments.py              python -m tiefer_lab.experiments: one row per run
      onboard.py                  fail-safe decision per frame, model hash check, tiled large frames
      acceptance.py               python -m tiefer_lab.acceptance: reports/acceptance.md
      requirements.py             traceability check of docs/REQUIREMENTS.md
      sbom.py                     CycloneDX software bill of materials from uv.lock, run in CI
      smoke.py                    python -m tiefer_lab.smoke, the full local smoke pipeline
      tables.py                   Markdown table helper for every generated table
      data/
        __init__.py
        source.py                 CloudSEN12+ access with tacoreader
        build_cache.py            python -m tiefer_lab.data.build_cache
        http.py                   backoff on HTTP 429 and the Hugging Face token
        sensor.py                 sensor robustness augmentations and evaluation perturbations
        survey.py                 python -m tiefer_lab.data.survey: counts, splits, encodings
        richness.py               python -m tiefer_lab.data.richness: classes, cloud cover, verified fields
        cache.py                  cache reading, in memory or memory-mapped; the padding check
        padding.py                where the dataset padded each patch (PADDING_SIDES, real_proj_shape)
        dataset.py                PyTorch datasets for train and evaluation
        transforms.py             reflectance, normalisation, crops, augmentation, padding
      models/
        __init__.py
        cloud_filter.py           the compact network
        convnext_unet.py          U-Net with ConvNeXt-style encoder blocks, for the largest size
        flexible.py               band-flexible input: 13 bands, availability flags, two designs
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
    test_padding.py               padding of cached patches and the read-only check, on synthetic data
    test_http.py                  backoff on HTTP 429, token never printed
    test_survey.py                survey on a synthetic table with real GeoTIFF items
    test_extra_patches.py         scribble and nolabel patches, location exclusion, overlap proof
    test_richness.py              richness report: cloud cover bins, verified fields only
    test_references.py            reference masks: verification stop, encodings, coverage, resume
    test_metrics.py
    test_binary_metrics.py        BOA, PA, UA and OA per patch, by hand
    test_flexible_model.py        band-flexible models, ConvNeXt-style U-Net, loss terms
    test_flexible_pipeline.py     train, evaluate and export a flexible model and a specialist
    test_experiments.py           reports/experiments.md from the run folders
    test_sensor.py                rescaling, gain, offset, noise and blur
    test_onboard.py               tiled inference, fail-safe decisions, corrupted model files
    test_acceptance.py            acceptance targets, minimum and target judged separately
    test_requirements_doc.py      no requirement without verification, no broken link
    test_sbom.py                  SBOM covers every locked package with licence and hashes
    test_wording.py               no compliance claims, valid standards matrix statuses
    test_audit_exceptions.py      accepted findings need a reason and expire
    test_coverage_floor.py        the coverage floor may rise, never fall
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
    test_docs_index.py            INDEX.md lists every Markdown file, and every listed file exists
    test_reports.py               report loading: smoke reports left out, provenance required
    test_roihu_scripts.py         CSC Roihu helper scripts with stub sbatch and sacct
    test_tables.py                Markdown table helper
  .editorconfig
  .env.example                    TIEFER_* variables with comments, no secrets
  .gitattributes                  line endings, *.sh and *.sbatch as LF
  .gitignore                      data/, runs/, .venv/, *.onnx, *.pt, *.engine, *.calib, *.npy, *.tar.gz, .env, caches
  .python-version                 3.12
  ACCEPTABLE_USE.md               Lab copy of the organisation's acceptable use policy
  BENCHMARK-AUTHORITY.md          which result answers which question; how to cite
  CITATION.cff                    how to cite Tiefer Lab (author: Tiefer)
  CLA.md                          contributor licence agreement, a draft not in force
  CLAIMS.md                       ledger of every public capability statement
  CODE_OF_CONDUCT.md              Lab copy of the organisation's code of conduct
  CONTRIBUTING.md                 Lab contributor contract
  EXTENDING.md                    golden paths to extend Lab
  GETTING-STARTED.md              first run and the offline proof
  GOVERNANCE.md                   roles, decision classes, versions, continuity
  INDEX.md                        every Markdown file with purpose, owner topic and status
  INSTALL.md                      every way to install, and provenance checks
  LEARNING-PATH.md                concepts in prerequisite order
  LICENSE                         MPL 2.0, official text
  LICENSING.md                    the licence of every part of the repository
  Makefile
  NOTICE.md                       attributions: data, Copernicus notice, typeface, dependencies
  POLICY.md                       measurement and release gates
  README.md                       public README in English
  SECURITY.md                     Lab security policy and private reporting
  START-HERE.md                   route from a task to the document that owns it
  SUPPORT.md                      Lab copy of the organisation's support page
  TRADEMARK.md                    use of the Tiefer name and logo
  pyproject.toml                  project metadata (license MPL-2.0), dependencies, ruff, mypy, pytest
  uv.lock
```

Created at runtime and never committed: `data/`, `runs/`, `.venv/`, `*.onnx`, `*.pt`, `*.engine`, `*.calib`, `*.npy`, `*.tar.gz`, `.env`. Written at run time and committed only when copied in from CSC Roihu or a Jetson: `reports/acceptance.md`, `reports/experiments.md`, `reports/data/survey.json`, and the report files under `reports/`.

`SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md` and `ACCEPTABLE_USE.md` at the repository root override the organisation-wide versions of `tiefer-labs/.github` for this repository; they keep the organisation's process, addresses and times and add what is specific to Lab. Every Markdown file is listed in [INDEX.md](../INDEX.md).

`Makefile` targets: `setup`, `lint`, `typecheck`, `test`, `coverage` (the tests under coverage, with the report and its floor), `check` (lint, typecheck, test), `smoke` (the full local smoke pipeline on a tiny subset), `requirements` (regenerate `hpc/roihu/requirements.txt`), `shellcheck` (every script under `hpc/` and `jetson/`). The `results` target was removed with the generator on 7 October 2026.

`README.md` (English, public) follows [STYLE.md](STYLE.md), section 12.14: header image, one sentence, link row, then what Tiefer Lab is (two paragraphs, plain), a status table for milestone L1, milestone L1 and its status, how to run locally, how to run on CSC Roihu (link to `hpc/roihu/README.md`), data and licences, results (link to `docs/RESULTS.md`), licence, contact `hello@tiefer.space`. No badges that call third-party services, no emoji.

Never committed: local working notes, editor and tool settings folders, `data/`, `runs/` and `.env`. Local tool folders are excluded through `.git/info/exclude`, not listed in `.gitignore`.

---

## 15. Quality, security and public repository hygiene

- `ruff`, `mypy --strict` on `src/`, `pytest` pass on every commit.
- Every Markdown file follows [STYLE.md](STYLE.md): the header image, the standard header block, heading levels, copy-ready commands, sources for every number. `LICENSE` and `docs/assets/` are provided by the founder and are never edited.
- Tests cover: paths from `TIEFER_*` variables; `requirements.txt` in sync with `uv.lock`; data transforms and normalisation; exactly four bands in the right order; label mapping; metrics against hand-computed examples; frame decisions; bootstrap reproducibility; the test-split guard; checkpoint save and resume; parameter budget and operator set; ONNX export round trip on a tiny untrained model; quantisation on synthetic data; Jetson scripts in dry-run mode; report loading that leaves smoke reports out and refuses reports without git provenance (until 7 October 2026: the results generator refusing to run without real report files).
- **Text rule test:** fails if any tracked text file (`.py`, `.md`, `.toml`, `.yaml`, `.yml`, `.txt`, `.sh`, `.sbatch`, `.json`, `.cff`, `.cfg`) contains U+2014, U+2015, U+FE0F or a character with the Unicode property Extended_Pictographic (checked with the `regex` package), or an en dash (U+2013) that has a space or line boundary on either side (an en dash is only accepted directly between two characters, as in a range). `LICENSE` is checked too.
- **Public hygiene test:** fails if a tracked file contains an absolute home or scratch path (for example `/home/`, `/Users/`, `/users/`, `/scratch/project_`, `/projappl/project_`), a CSC project identifier pattern (`project_` followed by digits), an email address other than `hello@tiefer.space`, something that looks like a key or token, or the name of any AI coding tool or its vendor in tracked content or paths (patterns built from string pieces so the test does not match itself). Report JSON stores paths relative to the repository or as `$TIEFER_*` placeholders.
- Both tests write their patterns with escape sequences or string concatenation (for example the Python escape sequence for U+2014 instead of the character itself), never as literal characters, so they do not flag themselves. Placeholders such as `<project>` in documentation are allowed.
- `ci.yml`: push and pull request, CPU only, synthetic data only. Each check is its own job: `lint`, `typecheck`, `test (ubuntu-24.04)` with coverage, `test (ubuntu-24.04-arm)`, `shellcheck` (every script under `hpc/` and `jetson/`, including the batch files), `smoke` (the synthetic smoke pipeline end to end, 10-minute limit), `sbom` (CycloneDX file attached to the run as an artifact) and `secrets` (gitleaks over the full history, binary checked against its SHA-256).
- **Coverage floor:** `fail_under` in `pyproject.toml` is the measured total rounded down; CI fails below it and fails when a commit lowers it against the base commit. Raise it when coverage rises.
- **Permissions and pinning:** workflow-level `permissions: {}`, and each job asks only for what it needs (`contents: read`; CodeQL also `security-events: write`). Actions pinned by full commit SHA with the tag in a comment; resolve SHAs with `git ls-remote`, never invent one. Downloaded tools are checked against a recorded SHA-256 or installed from a hashed requirements file. `persist-credentials: false`. No `pull_request_target`.
- `audit.yml`: `pip-audit` over every package of `uv.lock` on push, pull request, weekly and on demand; a finding fails unless accepted in `.github/audit-exceptions.toml` with a reason and an expiry at most 90 days ahead (docs/DEPENDENCIES.md, section 4).
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

- [LICENSING.md](../LICENSING.md) states the licence of every part of the repository and what is not licensed (trained models, `docs/assets/`, the Tiefer name and logo); [TRADEMARK.md](../TRADEMARK.md) the use of the name and logo; [NOTICE.md](../NOTICE.md) the attributions (CloudSEN12+ with its citations and the Copernicus notice, the typeface, the dependencies).

---

## 17. Part B: results after the Roihu runs

1. Unpack the returned files into `reports/`, `runs/` and `models/` and check their provenance (commit, config, platform). Flag anything inconsistent.
2. Check that test evaluations are logged in `reports/test_log.md` and that no tuning happened on test.
3. Write `MODEL_CARD.md` and `SHA256SUMS` for the release folder.
4. Until 7 October 2026, `docs/RESULTS.md` was generated with `make results`; since then it is written by hand from the report files, naming the file of every value (section 13).
5. If Jetson numbers are missing, write `not measured`.
6. Commit in small, real commits.

---

## Changelog

- 7 October 2026: section 9, the dataset's padding is masked in the labels at load time, and every metric and fraction counts only the real image area.
- 7 October 2026: section 14 lists `data/padding.py` and `tests/test_padding.py`.
- 7 October 2026: section 16 names LICENSING.md, TRADEMARK.md and NOTICE.md for what each states.
- 7 October 2026: section 14 lists the root documents added on 7 October 2026 and `tests/test_docs_index.py`; the community files of this repository override the organisation versions; principle 1 points to POLICY.md and CLAIMS.md.
- 7 October 2026: the purpose names milestones L1 and L2 and a Jetson milestone; section 3 names REQUIREMENTS.md, section 8, as the single source of the acceptance targets, and says when milestone L2 and the Jetson milestone are done, with the provisional product decision.
- 7 October 2026: the principles of four bands and of at most 1.0 million parameters apply to milestone L1; section 8 gives the class weights of L1 (median frequency) and L2 (none by default), the patience per config, the complete configs and options of `train`, and the input 1 x N x 512 x 512 of the L2 exports.
- 7 October 2026: the options of `build_cache`, `evaluate` and `export` are complete; `export --final` also writes to the test log.
- 7 October 2026: section 5 adds `fsspec[http]`, `coverage`, `hatchling` 1.32.4 and the `uv` version, and points to DEPENDENCIES.md.
- 7 October 2026: section 12 adds `timing.sbatch`, `sweep.sh`, `plan.md` and `requirements.txt`, points to the sourced facts of hpc/roihu/README.md, and the founder guide follows its steps.
- 7 October 2026: section 13 is in the past tense for the removed generator and states the hand-written rule, with `notes` and `pending` allowed until their report file is copied in.
- 7 October 2026: section 14: `richness.py`, `cache.py`, `dataset.py` and `transforms.py` are under `data/`; LANDSCAPE.md and the v0.1.0 release folder are listed; the run-time report files, the `.gitignore` patterns, the dependabot rule and the `coverage` and `shellcheck` targets are complete.
- 7 October 2026: references to "section 18" point to docs/STYLE.md; one bold phrase per item; `n/a` instead of "not applicable"; one separator before section 17.
- 7 October 2026: section 8 links the table of every L1 and L2 setting difference in docs/ASSUMPTIONS.md, section 6.
- 7 October 2026: section 8, the band set table names B02, B03, B04 as blue, green, red, and B11 and B12 as the short-wave infrared bands, from ESA SentiWiki; a `TODO(verify)` resolved.
- 7 October 2026: the results generator, its test and the `make results` target are removed; `docs/RESULTS.md` is written by hand from the report files (note in section 13). Reasons: readability, and the page had to combine the results of milestones L1 and L2 in tables the generator could not lay out. The report loader used by `tiefer_lab.acceptance` moves to `src/tiefer_lab/reports.py`. Sections 13, 14, 15 and 17 keep their original text next to the change.
- 2 October 2026: section 15 and the tree describe the new CI: separate jobs, tests on x86 and ARM, coverage with a floor, shellcheck, the smoke job, the SBOM artifact, the secret scan and the weekly vulnerability audit. Before, one CI job ran lint, type check and tests, with `permissions: contents: read` at the workflow level.
- 2 October 2026: section 9 adds the operational design domain and the fail-safe behaviour of `tiefer_lab.onboard`. Before, the specification did not say which inputs the filter is designed for or what happens outside them.
- 2 October 2026: section 8 adds milestone L2, one band-flexible model family (input with availability flags in two designs, band sets drawn per batch, self-distillation, a size ladder from 0.5 M to about 22 M parameters, four-band specialists as control, export per band set). The 1.0 million parameter budget now applies to the L1 configs only. Before, the model took four bands only and the budget applied to every model.
- 1 October 2026: `hpc/roihu/gpu_shell.sh` removed; GPU setup and GPU jobs run from `roihu-gpu.csc.fi`.
- 1 October 2026: job scripts no longer use `--export=NONE`; `job_prelude.sh` keeps only the module check and `module purge`.
- 1 October 2026: `submit.sh` uses sbatch's default export again and checks the architecture of the submitting host.
- 1 October 2026: `hpc/roihu/shell_options.sh` added to the table and the tree.
- 1 October 2026: the founder guide in section 12 follows the new order of `hpc/roihu/README.md`: before you start, clone and project, setup on both architectures, data, smoke, training with optional seeds, evaluation to collection; the login node cache path is removed.
- 1 October 2026: `hpc/roihu/job_prelude.sh` and `hpc/roihu/gpu_shell.sh` added to the table and the tree; job scripts use a login shell and `--export=NONE`.
- 1 October 2026: the table of files in `hpc/roihu/` follows the table format of docs/STYLE.md, section 9 (first column left, other columns centred); content unchanged.
- 1 October 2026: sections 1 to 17 added for milestone L1, Part A.
