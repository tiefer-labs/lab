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
| Storage quota on `/scratch` and `/projappl` | pending maintainer input | pending maintainer input | `csc-projects` |

Stop line: new training stops when the GPU billing units spent on it in Project Schatten reach a limit that is pending maintainer input.

---

## 3. Steps

### 3.1 State

On 16 October 2026 no Project Schatten run, report file, compute report or `test_log.md` entry of a Project Schatten run is in the repository, and Roihu restarts from zero. Until that changes:

- the budget, the storage quota and the stop line are pending maintainer input (section 2), so nothing is submitted;
- the stop line of section 2 holds once it is set: new training stops there, and the order of section 3.3 is the priority;
- every cost below is an upper bound from the job's time limit (200 GPU BU per GPU hour, [billing](https://docs.csc.fi/computing/hpc-billing/)); the first run of every training config is a timing run (`timing.sbatch`, through `sweep.sh --timing`), and the estimate of each later row reads "pending the timing run" until that run's compute report is copied into `reports/compute/`.

### 3.2 Selection rule

Status: frozen on 16 October 2026, before any Project Schatten run exists. It replaces the draft of 14 October 2026 and changes only by a commit that says so before the runs it would affect.

Every value is read from validation reports (`reports/evaluation/<run-id>_val.json`); for a band-flexible model, from its band set B02, B03, B04 and B08. The test split chooses nothing; it is read once per frozen candidate, by the maintainer (step 10). Definitions used below:

- **Validation minimums:** the minimum of every target of `src/tiefer_lab/acceptance.py` that validation measures: `ACC-01`, `ACC-03`, `ACC-05`, `ACC-07`, `ACC-08`, `FRM-01`, `FRM-02` and `STD-01`; for a candidate on three seeds also `ACC-09`.
- **Value of a candidate:** on one seed, the value of seed 0; on three seeds (0, 1, 2), the mean over the seeds, with `ACC-09` taken as the standard deviation of the cloud BOA over them.
- **Tie:** a difference below 0.002.

Rules:

1. **Seeds.** Wandler variants are compared on three seeds, and only after the stability change is selected (rule 3), because a single seed cannot separate their effects from seed spread. Sieb variants are compared on seed 0 only if the standard deviation of the validation cloud BOA over the three reference runs of `sieb` (step 3) is below the `ACC-09` target; otherwise on three seeds. A one-seed variant is compared with seed 0 of its reference, a three-seed variant with the mean of the three reference seeds.
2. **Winner among candidates.** The candidates that meet every validation minimum are eligible. The eligible candidate with the highest validation cloud BOA wins; a tie is broken by the higher mean IoU, and a tie on both by the reference. When no candidate is eligible, the one that misses the fewest minimums wins, then the highest cloud BOA, and each missed minimum is reported. `FRM-01` and `FRM-02` are checked on validation and reported for every candidate.
3. **Stability change.** `wandler_1m`, `wandler_1m_grad_clip`, `wandler_1m_skip_nonfinite` and `wandler_1m_warmup10`, each on three seeds, are compared by rule 2. The setting of the winner is the stability change (none when `wandler_1m` wins), and the winner is the Wandler reference of rules 4 and 5: every later Wandler variant is that config with one setting changed, committed before it is submitted.
4. **Which variants run (step 7).** The variants of a target run only when the family's reference misses that target's target value on validation: `ACC-05` (mean IoU, step 4) with `wandler_1m_lovasz` and `wandler_1m_crop384`, or `sieb_lovasz`; `CMP-05` (the larger cloud BOA loss of `rescale=0.5` and `rescale=2`, step 4) with `wandler_1m_rescale_2x` and `wandler_1m_rescale_3x`, or `sieb_rescale_2x`; `CMP-03` (the INT8 cloud BOA loss of the export of step 8) with the six `int8_` export variants of the family. No other variant runs in this plan.
5. **Family candidate.** Rule 2 among the family's reference and every training variant of rule 4 that ran, on the seeds of rule 1, gives one candidate for Sieb and one for Wandler.
6. **Export setting.** Among the default export and the `int8_` variants of a candidate: the smallest validation INT8 cloud BOA loss whose INT8 file meets the `OBD-03` target; a tie goes to the default MinMax calibration.
7. **Cloud logit bias and soft fraction.** Used only if the maintainer approves their method-change issues; then the bias and the temperature are the ones `python -m tiefer_lab.calibrate` chooses on validation, and the run with them is a separate candidate, compared by rule 2 with the same run without them.
8. **Independent datasets** never choose anything: they are evaluated only for the candidates of rule 5 (step 9).

### 3.3 Steps in order of priority

If the budget runs out, the order of the table is the priority: `FRM-01` and stability first. Every command runs from the repository folder on `roihu-cpu.csc.fi`; the commands are in section 3.4. GPU BU columns: the upper bound from the time limit of the jobs, and the estimate.

| Step | What | Configs and seeds | Partition | GPU BU upper bound | GPU BU estimate | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | setup on both architectures and the smoke job, from zero ([README.md](README.md), steps 1, 2 and 4) | `setup.sh`, `setup_gpu.sbatch`, `smoke.sbatch` | `small`, `gputest` | 100 | pending the timing run | not run |
| 0a | source check (CPU): HEAD requests only ([section 3.6](#36-source-check-and-downloads)) | `check_sources.sbatch` | `small` | 0 (CPU BU) | 0 | not run |
| 1 | data (CPU): the survey; the CloudSEN12+ caches `cloudsen12-l1c-high` and `cloudsen12-l1c-all` with the reference masks of the extra table | `survey.sbatch`, `data.sbatch` | `small` | 0 (CPU BU) | 0 | not run |
| 1a | independent caches (CPU): the Sentinel-2 Cloud Mask Catalogue and KappaSet ([section 3.6](#36-source-check-and-downloads)), whose builds drop every product that CloudSEN12+ uses, by product ID and by tile with date. L8 SPARCS and then L8 Biome wait until both have an evaluation report | `independent.sbatch s2_cloud_catalogue`, `independent.sbatch kappaset` | `small` | 0 (CPU BU) | 0 | not run |
| 2 | timing runs | `sieb`, `wandler_1m` | `gputest` | 100 (2 x 15 minutes) | upper bound only | not run |
| 3 | reference runs | `sieb`, `wandler_1m`, seeds 0, 1, 2 | `gpumedium` | 14,400 (6 x 12 hours) | pending the timing run | not run |
| 4 | validation evaluations with references, full metrics and robustness, then the diagnosis, validation and training only: seed stability, false discards (true cloud fraction in bins of 0.05), per-class IoU, INT8 sensitivity per Conv node, cloud BOA loss at `rescale=0.5` and `rescale=2` | the six runs of step 3 | `gpumedium`, `small` | 3,600 (6 evaluations of 2 hours, 6 INT8 diagnoses of 1 hour) | pending the timing run | not run |
| 5 | only if both method-change issues are approved: calibration, then evaluation with the cloud logit bias and the soft fraction; `FRM-01`, `FRM-02`, cloud BOA and mean IoU reported together | the six runs of step 3 | `gputest`, `gpumedium` | 2,700 (6 x 15 minutes, 6 x 2 hours) | pending the timing run | conditional |
| 6 | stability variants: timing, then three seeds each, then their validation evaluations | `wandler_1m_grad_clip`, `wandler_1m_skip_nonfinite`, `wandler_1m_warmup10`, seeds 0, 1, 2 | `gputest`, `gpumedium` | 25,350 (3 x 15 minutes, 9 x 12 hours, 9 x 2 hours) | pending the timing run | not run |
| 7 | the variants rule 4 calls for, on the seeds of rule 1 | `ACC-05`: `wandler_1m_lovasz`, `wandler_1m_crop384`, `sieb_lovasz`; `CMP-05`: `wandler_1m_rescale_2x`, `wandler_1m_rescale_3x`, `sieb_rescale_2x`; `CMP-03`: `*_int8_percentile`, `*_int8_entropy`, `*_int8_calib1024`, `*_int8_calib_stratified`, `*_int8_float_ends`, `*_int8_input_clip` | `gputest`, `gpumedium` | per training config 8,450 on three seeds or 2,850 on one (timing, runs, evaluations); 400 per export variant | pending the timing run and the diagnosis | not run |
| 8 | exports of the reference runs (`CMP-01` to `CMP-03`, `OBD-03`): ONNX per band set, the Wandler four-band export included, check against PyTorch, FP16, INT8 | the six runs of step 3 | `gpumedium` | 2,400 (6 x 2 hours) | pending the timing run | not run |
| 9 | independent evaluations of the candidates of rule 5 | 2 candidates on the Catalogue and on KappaSet | `gpumedium` | 1,600 (4 x 2 hours) | pending the timing run | not run |
| 10 | final test requests, run by the maintainer only (section 3.5) | the 2 frozen candidates | `gpumedium` | 2,400 (per candidate: evaluation, robustness, export check, 3 x 2 hours) | pending the timing run | not run |

Not in this plan: `wandler_1m_frame_loss`, `wandler_1m_crop512`, `sieb_frame_loss`, `wandler_1m_best_by_four_bands`, `sieb_grad_clip`, `wandler_1m_landsat_bandsets`, `lupe_1m`, the CloudScout re-implementation, `wandler_1m_extra_data` and the extra training patches, `wandler_22m`, `wandler_1m_distill_22m` and the `_candidate` configs. They need a later revision of this plan before they are submitted.

### 3.4 Commands

Step 0, from zero on `roihu-cpu.csc.fi` (the full commands and checks are in [README.md](README.md), section 3):

```bash
bash hpc/roihu/setup.sh
bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
```

Steps 1 and 1a: the survey and the CloudSEN12+ caches as [README.md](README.md), step 3, describes them (the 13-band cache with its shards and rate limits as written there), the reference masks once `REFERENCE_*` are set from the survey, then the two independent caches of step 1a, which need the complete CloudSEN12+ cache for their independence check:

```bash
bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch val --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch test --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch s2_cloud_catalogue
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch kappaset
```

Steps 2 and 3, the timing runs, then three seeds of each reference:

```bash
bash hpc/roihu/sweep.sh --timing configs/sieb.toml configs/wandler_1m.toml
bash hpc/roihu/sweep.sh --seeds 0,1,2 configs/sieb.toml configs/wandler_1m.toml
```

Step 4, per run of step 3 (`<run-id>` is the run ID its log prints, `<config>-seed<N>-...`; `<cache>` is `cloudsen12-l1c-high` for Sieb and `cloudsen12-l1c-all` for Wandler):

```bash
FULL_METRICS=1 ROBUSTNESS=1 PERTURBATIONS="rescale=0.5 rescale=2" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch frames /scratch/<project>/tiefer-lab/reports/evaluation/<run-id>_val.json --cache <cache>
bash hpc/roihu/submit.sh hpc/roihu/diagnose_gpu.sbatch <run-id>
```

and once per family, over its three seeds:

```bash
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch seeds /scratch/<project>/tiefer-lab/runs/sieb-seed0-<rest> /scratch/<project>/tiefer-lab/runs/sieb-seed1-<rest> /scratch/<project>/tiefer-lab/runs/sieb-seed2-<rest>
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch seeds /scratch/<project>/tiefer-lab/runs/wandler_1m-seed0-<rest> /scratch/<project>/tiefer-lab/runs/wandler_1m-seed1-<rest> /scratch/<project>/tiefer-lab/runs/wandler_1m-seed2-<rest>
```

Step 5, only after both method-change issues are approved, per run of step 3:

```bash
bash hpc/roihu/submit.sh hpc/roihu/calibrate.sbatch <run-id>
CLOUD_BIAS=auto FRACTION=soft FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

Step 6, timing first, then three seeds, then one validation evaluation per run as in step 4:

```bash
bash hpc/roihu/sweep.sh --timing configs/wandler_1m_grad_clip.toml configs/wandler_1m_skip_nonfinite.toml configs/wandler_1m_warmup10.toml
bash hpc/roihu/sweep.sh --seeds 0,1,2 configs/wandler_1m_grad_clip.toml configs/wandler_1m_skip_nonfinite.toml configs/wandler_1m_warmup10.toml
FULL_METRICS=1 ROBUSTNESS=1 PERTURBATIONS="rescale=0.5 rescale=2" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

Step 7, only the configs rule 4 calls for, each committed first (a Wandler variant on top of the stability change of rule 3); `--seeds 0` for a Sieb variant only when rule 1 allows it:

```bash
bash hpc/roihu/sweep.sh --timing configs/<variant>.toml
bash hpc/roihu/sweep.sh --seeds 0,1,2 configs/<variant>.toml
EXPORT_CONFIG=configs/<family>_int8_<setting>.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

Step 8, per run of step 3:

```bash
bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

Step 9, per candidate of rule 5 and dataset, once its cache exists:

```bash
DATA=s2_cloud_catalogue REASON="independent evaluation of <run-id>, candidate of hpc/roihu/plan.md section 3.2, rule 5" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
DATA=kappaset REASON="independent evaluation of <run-id>, candidate of hpc/roihu/plan.md section 3.2, rule 5" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
```

After every job:

```bash
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
```

### 3.5 Final test requests (step 10)

Written by the assistant from the copied report files after step 9, for the maintainer, who alone runs them. One request per frozen candidate: the config, the run ID, the selection rule and the reason, for example:

```bash
FINAL=1 REASON="final test of <run-id>, frozen by hpc/roihu/plan.md section 3.2 on <date>" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
FINAL=1 REASON="final test of <run-id>, robustness for CMP-05" PERTURBATIONS="rescale=0.5 rescale=2" ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
FINAL=1 REASON="final export check of <run-id>" EXPORT_CONFIG=configs/<selected-export>.toml bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
```

`CMP-05` reads final test evaluations with `rescale=0.5` and `rescale=2`, so each candidate needs those two logged test uses too. Why selection is at risk of adaptive overfitting, and why the independent datasets of step 9 are the clean check, is in [POLICY.md](../../POLICY.md), gate 3.

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

### 3.7 What measures each acceptance target

Per model, which step measures each target of `src/tiefer_lab/acceptance.py`, or why it cannot be measured in this plan. "Validation" values choose (section 3.2); the reported value of a target comes from the final test of step 10 unless the row says otherwise.

| Target | `sieb` | `wandler_1m` |
| :--- | :---: | :---: |
| `ACC-01` | steps 4 and 10, evaluation | steps 4 and 10, evaluation, band set B02 B03 B04 B08 |
| `ACC-02` | not applicable: four bands only | not measured: `wandler_22m` is not in this plan |
| `ACC-03` | steps 4 and 10 | steps 4 and 10 |
| `ACC-04` | step 10, against the reference masks of the extra table (step 1); s2cloudless and CD-FCNN have no runner yet | as `sieb` |
| `ACC-05` | steps 4 and 10 | steps 4 and 10 |
| `ACC-06` | steps 4 and 10, full metrics with the reference masks | as `sieb` |
| `ACC-07` | steps 4 and 10 | steps 4 and 10 |
| `ACC-08` | steps 4 and 10 | steps 4 and 10 |
| `ACC-09` | step 3, three seeds, read in step 4 (`diagnose seeds`) | as `sieb` |
| `IND-01` | step 9: two datasets (the minimum); the target needs four from three sensors, so L8 SPARCS and L8 Biome later | as `sieb` |
| `IND-02` | step 9 on KappaSet, against its shipped Sen2Cor maps; not measured on the Catalogue (its Sen2Cor masks need Level-2A products, which need credentials) | as `sieb` |
| `IND-03` | not measured: no other-sensor dataset is planned yet | as `sieb` |
| `IND-04` | step 9, the worst surface class of the Catalogue and season of KappaSet; biomes only with L8 Biome | as `sieb` |
| `FRM-01` | steps 4, 5 and 10 | steps 4, 5 and 10 |
| `FRM-02` | steps 4, 5 and 10 | steps 4, 5 and 10 |
| `CMP-01` | steps 8 and 10, export | steps 8 and 10, every band set |
| `CMP-02` | steps 8 and 10 | steps 8 and 10 |
| `CMP-03` | steps 8 and 10; export variants in step 7 | as `sieb` |
| `CMP-04` | not applicable: not band-flexible | not measured: the four-band specialist `lupe_1m` is not in this plan |
| `CMP-05` | steps 4 and 10, robustness at `rescale=0.5` and `rescale=2` | as `sieb` |
| `CMP-06` | not measured: no other-sensor dataset is planned yet | as `sieb` |
| `CMP-07` | not applicable: four bands only | steps 4 and 10, band set B02 B03 B04 |
| `OBD-01`, `OBD-02`, `OBD-04`, `OBD-05`, `OBD-06` | not measured on Roihu: they need the Jetson benchmark ([jetson/README.md](../../jetson/README.md)) of the exported files of step 10 | as `sieb` |
| `OBD-03` | step 8, the size of the exported files | as `sieb` (a 1 M model) |
| `STD-01` | steps 4 and 10, worst stratum | steps 4 and 10 |
| `STD-02`, `STD-03`, `STD-04` | measured by the tests and documents, not by runs ([docs/REQUIREMENTS.md](../../docs/REQUIREMENTS.md)) | as `sieb` |

---

## Changelog

- 16 October 2026: the selection rule is frozen, before any Project Schatten run exists, and replaces the draft; section 3.3 plans the first Project Schatten runs in ten steps (data, timing, three reference seeds of `sieb` and `wandler_1m`, diagnosis, the conditional cloud logit bias, the stability variants, the variants the diagnosis calls for, exports, independent evaluations, final test requests); section 3.7, what measures each acceptance target per model; the storage quota is pending maintainer input; drafted with an AI-assisted system.
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
