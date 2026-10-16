<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Run plan on CSC Roihu

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The plan of Project Schatten on CSC Roihu: its basis, the budget it starts from, the stop line for new training and its steps. GPU BU are GPU billing units of CSC.

---

## 1. Basis

Project Schatten is the only campaign. Every campaign before it is withdrawn: its results, checkpoints, timing and compute reports are not used for anything, neither as a value, a cost estimate, a selection, a starting point, a diagnosis nor a comparison. Roihu restarts from zero: no environment, cache, checkpoint, report or log is assumed to exist there, and every step starts from the setup of [README.md](README.md), section 3. Every run starts from one tagged, clean commit. Before a run is submitted, its config is committed and it is added to section 3 with its estimated cost ([POLICY.md](../../POLICY.md), gate 7).

---

## 2. Budget

From the `csc-projects` output of the day the first Project Schatten job is submitted:

| Resource | Remaining | Granted | Source |
| :--- | :---: | :---: | :---: |
| GPU billing units | pending maintainer input | pending maintainer input | `csc-projects` |
| CPU billing units | pending maintainer input | pending maintainer input | `csc-projects` |
| Storage billing units | pending maintainer input | pending maintainer input | `csc-projects` |

Stop line: new training stops when the GPU billing units spent on it in Project Schatten reach a limit that is pending maintainer input.

---

## 3. Steps

### 3.1 State

No Project Schatten run, report file, compute report or `test_log.md` entry of a Project Schatten run is in the repository. Until there is:

- the remaining budget is pending maintainer input (section 2), so no run is submitted;
- every cost below is an upper bound from the job's time limit (200 GPU BU per GPU hour, [billing](https://docs.csc.fi/computing/hpc-billing/)); the estimate is pending a Project Schatten timing run (`timing.sbatch`) of each config and its compute report in `reports/compute/`;
- the stop line of section 2 holds.

### 3.2 Selection rule

Status: draft, not frozen; replaced in Package 5.

Written on 14 October 2026, before any run of these steps, and changed only by a commit that says so before the runs it would affect. Every choice uses the validation split; the test split is read once per frozen candidate (step 9).

1. **Validation minimums.** A candidate is eligible when, on validation with the four bands B02, B03, B04 and B08, it meets every minimum of `src/tiefer_lab/acceptance.py` that validation can measure: `ACC-01`, `ACC-03`, `ACC-05`, `ACC-07`, `ACC-08`, `FRM-01`, `FRM-02` and `STD-01`; with three seeds also `ACC-09`.
2. **A variant wins** when it improves the metric of the target it is made for (table of step 3) over its reference by more than the larger of 0.005 and the standard deviation over the seeds of the reference on validation, and no validation minimum that the reference met becomes missed. The metric is the false discard rate at 50 percent for `FRM-01` variants, mean IoU for `ACC-05` variants, the cloud BOA loss at `rescale=0.5` and `rescale=2` for `CMP-05` variants, and the INT8 cloud BOA loss for `CMP-03` export variants.
3. **Candidate references.** `sieb_candidate` and `wandler_1m_candidate` are their drafts plus every winner of their family; when two winners change the same setting, the larger gain is kept. The completed configs are committed before step 5.
4. **Final candidate per family.** Among the eligible seeds and options of the candidate reference: the highest validation cloud BOA; a difference below 0.002 is a tie, broken by the higher mean IoU.
5. **Export setting.** Among the export variants of the selected run: the smallest validation INT8 cloud BOA loss whose INT8 file meets the `OBD-03` target; ties go to the default MinMax calibration.
6. **Cloud logit bias and soft fraction.** Used only if the maintainer agrees to their method-change issues; then the bias is the one `python -m tiefer_lab.calibrate` chooses on validation, and the run with the bias is a separate candidate under rule 4.
7. **Independent datasets** never choose anything: they are evaluated only for the frozen candidates (step 8).

### 3.3 Steps in order of priority

The targets come first in this order, in case the budget runs out: `FRM-01`, stability and `ACC-09`, `ACC-05`, `CMP-03`, `CMP-05`, then the runs never made, then the largest model. Every command runs from the repository folder on `roihu-cpu.csc.fi`. GPU BU columns: the upper bound of the job's time limit, and the estimate, which is pending a Project Schatten timing run until its compute report is in `reports/compute/`.

| Step | What | Configs and seeds | Partition | GPU BU upper bound | GPU BU estimate | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | setup on both architectures and the smoke job, from zero ([README.md](README.md), steps 1, 2 and 4) | `setup.sh`, `setup_gpu.sbatch`, `smoke.sbatch` | `small`, `gputest` | 100 | estimate pending a Project Schatten timing run | not run |
| 0a | source check (CPU): can every source still allowed or undecided be obtained; HEAD requests only ([section 3.6](#36-source-check-and-downloads)) | `check_sources.sbatch` | `small` | 0 (CPU BU) | 0 | not run |
| 1 | survey and CloudSEN12+ caches (CPU), from zero ([README.md](README.md), step 3) | `cloudsen12-l1c-high` and `cloudsen12-l1c-all`, every split | `small` | 0 (CPU BU) | 0 | not run |
| 1a | independent dataset caches (CPU): the Sentinel-2 Cloud Mask Catalogue and KappaSet ([section 3.6](#36-source-check-and-downloads)); L8 SPARCS and then L8 Biome only after both have an evaluation report | `independent.sbatch s2_cloud_catalogue`, `independent.sbatch kappaset` | `small` | 0 (CPU BU) | 0 | not run |
| 1b | reference masks of the extra table (CPU) | `cloudsen12-l1c-all` val and test, after `REFERENCE_*` are set from the survey | `small` | 0 (CPU BU) | 0 | not run |
| 1c | extra training patches (CPU) | `train_extra` of `cloudsen12-l1c-all`, after `LOCATION_FIELD` and `SCRIBBLE_UNLABELLED_CODE` | `small` | 0 (CPU BU) | 0 | not run |
| 3a | timing of every new training config | 12 configs below and `cloudscout_reimpl_step1_th30` | `gputest` | 650 | estimate pending a Project Schatten timing run | not run |
| 3b | `FRM-01` variants, seed 0 | `wandler_1m_frame_loss`, `wandler_1m_crop512`, `sieb_frame_loss` | `gpumedium` | 7,200 | estimate pending a Project Schatten timing run | not run |
| 3c | stability variants, seed 0 | `wandler_1m_grad_clip`, `wandler_1m_skip_nonfinite`, `wandler_1m_warmup10`, `wandler_1m_best_by_four_bands`, `sieb_grad_clip` | `gpumedium` | 12,000 | estimate pending a Project Schatten timing run | not run |
| 3d | `ACC-05` variants, seed 0 | `wandler_1m_lovasz`, `wandler_1m_crop384`, `sieb_lovasz` | `gpumedium` | 7,200 | estimate pending a Project Schatten timing run | not run |
| 3e | `CMP-03` export variants of a Project Schatten run of `sieb` and of `wandler_1m`, no training; those runs are not yet a step of this plan | `*_int8_percentile`, `*_int8_entropy`, `*_int8_calib1024`, `*_int8_calib_stratified`, `*_int8_float_ends`, `*_int8_input_clip` of `sieb` and `wandler_1m` | `gpumedium` | 4,800 | estimate pending a Project Schatten timing run | not run |
| 3f | `CMP-05` and `CMP-06` variants, seed 0 | `wandler_1m_rescale_3x`, `sieb_rescale_2x`, `wandler_1m_landsat_bandsets` | `gpumedium` | 7,200 | estimate pending a Project Schatten timing run | not run |
| 3g | runs never made | `lupe_1m` seed 0 (`CMP-04`); `cloudscout_reimpl_step1_th30`, then `cloudscout_reimpl_th70` and `cloudscout_reimpl_th50` | `gpumedium` | 9,600 | estimate pending a Project Schatten timing run | not run |
| 3h | extra training data, seed 0 | `wandler_1m_extra_data`, after step 1c | `gpumedium` | 2,400 | estimate pending a Project Schatten timing run | not run |
| 4a | largest model, all 13 bands (`ACC-02`, teacher) | `wandler_22m` seed 0 | `gpumedium` | 7,200 (36 hours) | estimate pending a Project Schatten timing run | not run |
| 4b | distillation from it | `wandler_1m_distill_22m` seed 0 | `gpumedium` | 2,400 | estimate pending a Project Schatten timing run | not run |
| 5 | candidate references, three seeds; then the fine-tune stage | `sieb_candidate`, `wandler_1m_candidate` seeds 0, 1, 2; `wandler_1m_candidate_finetune` seed 0 | `gpumedium` | 16,800 | estimate pending a Project Schatten timing run | not run |
| 6 | exports of every candidate, with the export setting of rule 5 and `CLOUD_BIAS=auto` where agreed | the runs of steps 3 to 5 | `gpumedium` | 400 per run | estimate pending a Project Schatten timing run | not run |
| 7 | validation evaluations with references, full metrics and robustness; calibration; selection by section 3.2 | the runs of steps 3 to 5 | `gpumedium`, `gputest` | 850 per run (two evaluations, one calibration) | estimate pending a Project Schatten timing run | not run |
| 8 | independent dataset evaluations of the frozen candidates | the candidates of rule 4, each verified dataset | `gpumedium` | 400 per candidate and dataset | estimate pending a Project Schatten timing run | not run |
| 9 | final test, by the maintainer only | the frozen candidates, see section 3.5 | `gpumedium` | 400 per evaluation | estimate pending a Project Schatten timing run | not run |

The upper bounds above add up to far more than any budget a stop line is likely to allow. The order of the table is the order of submission; the estimate of each step from the Project Schatten compute reports decides how far down the table the stop line allows.

### 3.4 Commands

Step 0, from zero on `roihu-cpu.csc.fi` (the full commands and checks are in [README.md](README.md), section 3):

```bash
bash hpc/roihu/setup.sh
bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
```

Step 1, the survey and the CloudSEN12+ caches, as [README.md](README.md), step 3, describes them (the 13-band cache with its shards and rate limits as written there):

```bash
bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
```

Steps 1a, 1b and 1c, further CPU jobs (no GPU BU):

```bash
# step 1a: the Catalogue and KappaSet, after step 1 (their builds drop the products CloudSEN12+ uses)
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch s2_cloud_catalogue
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch kappaset
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch val --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch test --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch train_extra --name cloudsen12-l1c-all --bands all
```

Step 3, timing first, then one seed of each variant, in the order of the table:

```bash
bash hpc/roihu/sweep.sh --timing configs/wandler_1m_frame_loss.toml configs/wandler_1m_crop512.toml configs/sieb_frame_loss.toml configs/wandler_1m_grad_clip.toml configs/wandler_1m_skip_nonfinite.toml configs/wandler_1m_warmup10.toml configs/wandler_1m_best_by_four_bands.toml configs/sieb_grad_clip.toml configs/wandler_1m_lovasz.toml configs/wandler_1m_crop384.toml configs/sieb_lovasz.toml configs/wandler_1m_rescale_3x.toml configs/cloudscout_reimpl_step1_th30.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_frame_loss.toml configs/wandler_1m_crop512.toml configs/sieb_frame_loss.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_grad_clip.toml configs/wandler_1m_skip_nonfinite.toml configs/wandler_1m_warmup10.toml configs/wandler_1m_best_by_four_bands.toml configs/sieb_grad_clip.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_lovasz.toml configs/wandler_1m_crop384.toml configs/sieb_lovasz.toml
EXPORT_CONFIG=configs/sieb_int8_percentile.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <sieb-run-id>
EXPORT_CONFIG=configs/wandler_1m_int8_percentile.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <wandler_1m-run-id>
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_rescale_3x.toml configs/sieb_rescale_2x.toml configs/wandler_1m_landsat_bandsets.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/lupe_1m.toml configs/cloudscout_reimpl_step1_th30.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/cloudscout_reimpl_th70.toml configs/cloudscout_reimpl_th50.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_extra_data.toml
```

The other export variants run like the `int8_percentile` lines, one job per config (`int8_entropy`, `int8_calib1024`, `int8_calib_stratified`, `int8_float_ends`, `int8_input_clip`). `cloudscout_reimpl_th70` and `cloudscout_reimpl_th50` start only after `cloudscout_reimpl_step1_th30-seed0` has finished.

Step 4, the largest model, then distillation once it has finished:

```bash
bash hpc/roihu/submit.sh --time=36:00:00 hpc/roihu/train.sbatch configs/wandler_22m.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_distill_22m.toml
```

Step 5, after the completed candidate configs are committed (rule 3):

```bash
bash hpc/roihu/sweep.sh --seeds 0,1,2 configs/sieb_candidate.toml configs/wandler_1m_candidate.toml
bash hpc/roihu/sweep.sh --seeds 0 configs/wandler_1m_candidate_finetune.toml
```

Steps 6 and 7, per run:

```bash
bash hpc/roihu/submit.sh hpc/roihu/calibrate.sbatch <run-id>
FULL_METRICS=1 ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
CLOUD_BIAS=auto FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
EXPORT_CONFIG=configs/<export-variant>.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
```

Step 8, per frozen candidate and dataset recorded as used ([docs/DATASETS.md](../../docs/DATASETS.md), section 1.1), once its cache exists:

```bash
DATA=s2_cloud_catalogue REASON="<reason of section 3.5>" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

### 3.5 Final test requests (step 9)

Written by the assistant from the copied report files after step 7, for the maintainer, who alone runs them. One request per frozen candidate: the config, the run ID, the selection rule and the reason, for example:

```bash
FINAL=1 REASON="final test of <run-id>, frozen by hpc/roihu/plan.md section 3.2 on <date>" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
FINAL=1 REASON="final test of <run-id>, robustness for CMP-05" PERTURBATIONS="rescale=0.5 rescale=2" ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
FINAL=1 REASON="final export check of <run-id>" EXPORT_CONFIG=configs/<selected-export>.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

`CMP-05` reads final test evaluations with `rescale=0.5` and `rescale=2`, so each candidate needs those two logged test uses too. Why selection is at risk of adaptive overfitting, and why the independent datasets of step 8 are the clean check, is in [POLICY.md](../../POLICY.md), gate 3.

### 3.6 Source check and downloads

Step 0a needs no data and no credential: it sends HEAD requests, or asks for the first byte, of every recorded file and writes `reports/data/sources.json` ([docs/DATASETS.md](../../docs/DATASETS.md), section 1.2). From `roihu-cpu.csc.fi`, after step 0:

```bash
bash hpc/roihu/submit.sh hpc/roihu/check_sources.sbatch
cat /scratch/<project>/tiefer-lab/reports/data/sources.json
```

One row per download. Sizes are the recorded sizes of `files` in `src/tiefer_lab/data/source.py` and `src/tiefer_lab/data/independent.py`. The duration is the size divided by the rate cap of `independent.sbatch` (`TIEFER_DOWNLOAD_RATE`, default 20 MiB per second), a lower bound; unpacking and caching come on top. Step 1a plans the Catalogue and KappaSet (decision of 16 October 2026). L8 Biome and L8 SPARCS are used, but their downloads stay not planned until the Catalogue and KappaSet both have an evaluation report; then SPARCS comes before Biome, downloaded by hand into `$TIEFER_DATA_DIR/downloads/<dataset>/` as [README.md](README.md) says, since `independent.sbatch` downloads Zenodo records only.

| Download | Decision | Size | Storage BU | Duration at the cap | Command | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| CloudSEN12+ parts (Hugging Face) | used | 136,865,704,637 bytes in 8 parts; never downloaded whole, the cache build of step 1 reads byte ranges | pending maintainer input | not derived from the facts; the build log of step 1 gives it | step 1 | not run |
| Sentinel-2 Cloud Mask Catalogue (Zenodo 4172871) | used | 15,206,407,392 bytes in 4 files | pending maintainer input | at least 12 minutes | `bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch s2_cloud_catalogue` | planned in step 1a, not run |
| KappaSet (Zenodo 7100327) | used | 56,186,540,640 bytes in 2 files | pending maintainer input | at least 45 minutes | `bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch kappaset` | planned in step 1a, not run |
| Landsat 8 SPARCS (USGS) | used | 1,555,733,976 bytes in 1 archive | pending maintainer input | at least 2 minutes | by hand, first of the two, after the Catalogue and KappaSet both have an evaluation report | not planned |
| Landsat 8 Biome (USGS) | used | 94,130,145,717 bytes in 96 archives | pending maintainer input | at least 75 minutes | by hand, after L8 SPARCS | not planned |

---

## Changelog

- 16 October 2026: step 1a plans the Catalogue and KappaSet downloads; L8 SPARCS and then L8 Biome stay not planned until both have an evaluation report (decisions of 16 October 2026); drafted with an AI-assisted system.
- 16 October 2026: step 0a, the source check, and section 3.6, one row per download with its size and the duration at the rate cap; storage billing units pending maintainer input; drafted with an AI-assisted system.
- 15 October 2026: config names follow the scheme of docs/SPEC.md, section 8 (Sieb, Wandler, Lupe, the CloudScout re-implementation); drafted with an AI-assisted system.
- 15 October 2026: the stop line is pending maintainer input; the selection rule is marked as a draft, not frozen; drafted with an AI-assisted system.
- 15 October 2026: the plan of Project Schatten: earlier campaigns withdrawn; Roihu restarts from zero, with a setup step and a CloudSEN12+ cache step; the budget is pending maintainer input; the steps that used withdrawn runs are removed, and every estimate is pending a Project Schatten timing run; the stop line is kept; drafted with an AI-assisted system.
- 15 October 2026: step 1a plans no download, and its download and evaluation commands are removed from section 3.4; WHUS2-CD is a candidate without a licence decision and has no row; drafted with an AI-assisted system.
- 15 October 2026: step 1a lists only the datasets that the licence decisions of 15 October 2026 allow; no row downloads, caches or evaluates S2-Hollstein, L8-38Cloud, L8-95Cloud, S2-CESBIO, the Copernicus imagery for them, dtacs4bands or the 2022 release; drafted with an AI-assisted system.
- 14 October 2026: section 3: the state of the v2 campaign, the selection rule frozen before any v3 run, the v3 steps in order of priority with upper bounds of their cost, the commands and the final test requests; drafted with an AI-assisted system.
- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: links to docs/DATA.md follow its new section numbers.
