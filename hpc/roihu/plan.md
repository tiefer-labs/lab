<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Run plan on CSC Roihu

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The plan of Project Schatten on CSC Roihu: its basis, the budget it starts from, the stop line for new training and its steps. GPU BU are GPU billing units of CSC.

---

## 1. Basis

Project Schatten is the only campaign. Every campaign before it is withdrawn: its results, checkpoints, timing and compute reports are not used for anything, neither as a value, a cost estimate, a selection, a starting point, a diagnosis nor a comparison. Roihu restarts from zero: no environment, cache, checkpoint, report or log is assumed to exist there, and every step starts from the setup of [README.md](README.md), section 3. Every run starts from one tagged, clean commit. Before a run is submitted, its config is committed and it is added to section 3 with its estimated cost ([POLICY.md](../../POLICY.md), gate 7).

---

## 2. Budget

The allocation is fixed: maintainer input of 16 October 2026; no further allocation will be granted, so every step of section 3 has to fit it.

| Resource | Allocation | Used by Project Schatten |
| :--- | :---: | :---: |
| GPU billing units | 10,000 | training only (steps 0, 2, 3, 6, 7 and 7b) |
| CPU billing units | 60,000 | every job that does not train |
| Storage billing units | 30,000 | `/scratch` and `/projappl` |
| Cloud billing units | 30,000 | not used |
| Disk quota on `/scratch` and `/projappl` | pending maintainer input | the sizes of section 3.8 |

Billing, from [docs.csc.fi/computing/hpc-billing](https://docs.csc.fi/computing/hpc-billing/) (page of 15 October 2026, read 16 October 2026):

- **GPU partitions:** 200 GPU BU per reserved GPU and hour of runtime; cores (72 per GPU) and memory (212 GiB per GPU) are included. Local storage reserved with `--gres` adds 0.02 BU per GiB-hour; `$TMPDIR` is free. The GPU allocation is therefore 50 GPU-hours. The bill follows the runtime, not the time limit, so a job that ends early releases its GPU and pays only for what it used.
- **CPU partitions `small`, `test`, `interactive`, `longrun`:** the larger of 0.75 BU per core-hour and 0.375 BU per GiB-hour of reserved memory, times the runtime. A job with 2 GiB per core pays the same for both; every CPU job of this plan is sized so. `medium` and `large`: 288 BU per full node-hour.
- **Storage:** `/scratch` 6 BU per TiB-hour of used space, `/projappl` and home 10 BU per TiB-hour.

**Stop line:** no new GPU job is submitted once the GPU BU used by Project Schatten reach 9,500. The last 500 GPU BU cover reruns of failed jobs. The final test (step 10) needs no GPU.

**Running out of BUs** ([usage policy](https://docs.csc.fi/computing/usage-policy/) (page of 15 October 2026, read 16 October 2026)): a running job finishes even past a zero balance, and a project whose balance of any type stays negative is closed after 60 days. When the storage BUs run out, no job can be submitted to any partition, and access to `/scratch` and `/projappl` ends after 30 days. So `submit.sh` and `sweep.sh` compute the worst case of every job before they submit it (time limit x GPUs x 200 for a GPU job; the CPU formula above for a CPU job) and refuse it when it does not fit in the balance left minus the reserve: 500 GPU BU, the reserve under the stop line, and 0 CPU BU (`hpc/roihu/budget.sh`). The balance is the one the maintainer reads in their own `csc-projects` output and types in (`TIEFER_GPU_BU_LEFT`, `TIEFER_CPU_BU_LEFT`, `TIEFER_STORAGE_BU_LEFT`); it is never fetched with credentials.

**Gate:** after the timing step (step 2), this plan is revised with the real costs of the packing reports, in its own pull request, before step 3 is submitted. If the real total of every planned step exceeds 9,500 GPU BU even with packing, that revision cuts in this order, says so, and the maintainer decides:

1. the Wandler variants (step 7);
2. the Wandler stability step (step 6);
3. the `wandler_1m_candidate` combination (step 7b);
4. the Sieb variants beyond the first two targets that rule 4 calls for.

Never cut: the timing runs, the three Sieb seeds, the three `wandler_1m` seeds, the calibration (CPU) and the Sieb combination.

---

## 3. Steps

### 3.1 State

On 16 October 2026 no Project Schatten run, report file, compute report or `test_log.md` entry of a Project Schatten run is in the repository, and Roihu restarts from zero. Until that changes:

- steps 0, 0a, 1, 1a and 2 are approved first; step 3 waits for the revision of the gate (section 2), and steps 4 to 10 are revised with the costs of the timing reports before any of them is submitted;
- every GPU job trains; every job that does not train runs on a CPU partition (evaluation of validation, perturbations, independent datasets and the final test, calibration, diagnosis, ONNX export with FP16 and INT8 conversion and the ONNX Runtime INT8 measurement, acceptance, comparison, the source check and the caches). INT8 values from ONNX Runtime on the CPU are a proxy for `CMP-03`; the TensorRT values come from the Jetson. Every reported evaluation (validation, perturbations, independent datasets, final test) runs on the CPU; each evaluation report records its device (`evaluation_device`), and `acceptance` and `compare` refuse a table that mixes devices, because the CPU evaluates in fp32 and a GPU with mixed precision (`reports.require_one_device`);
- training runs are packed: several runs share one reserved GPU (`train_packed.sbatch`), the seeds of one config or one-change variants of one reference, at the packing that the timing step chooses: the most epochs per GPU-hour whose slowest run takes at most twice its time alone (`tiefer_lab.packed`, `MAX_SLOWDOWN`) and whose mean GPU utilisation is at least 50 percent (`MIN_GPU_UTILISATION`). CSC can terminate jobs whose GPUs are severely underused ([usage policy](https://docs.csc.fi/computing/usage-policy/) (page of 15 October 2026, read 16 October 2026)), so the timing report states the utilisation of each packing, and no packing below that share is chosen;
- CPU training is a measured option. CSC asks to use whichever of CPU or GPU costs fewer BU, and one CPU BU equals one GPU BU (same page). The timing step also trains `sieb` and `cloudscout_reimpl_step1_th30` for one cut epoch on one full `medium` node (`timing_cpu.sbatch`, 288 CPU BU per node-hour) and reports the CPU BU per epoch against the GPU BU per epoch of the chosen packing (`reports/timing/cpu_<config>.json`). The gate revision may move whole comparison groups (a reference and its variants together, never mixed) to CPU training; a CPU-trained run and a GPU-trained run are never compared as one-change variants of each other;
- the time limit of every training job is the packing report's slowest full epoch time times the epochs, plus 50 percent and the measured start-up (`python -m tiefer_lab.packed time-limit`), never a fixed large value. GPU time is billed on the runtime, so the margin costs nothing, while a run stopped at its limit loses the epoch it was in and needs another job (maintainer decision of 16 October 2026). A stopped run resumes from its `last.pt` with `resume:<run-id>`: warned 300 s before the limit (SIGUSR1) it saves and stops; killed without warning it keeps `last.pt` of its last finished epoch, and either way the resumed run ends with the weights of a run that was never stopped (`tests/test_checkpoint_resume.py`);
- a variant whose one change leaves the work per step as it is (loss, gradient clipping, the skip of non-finite steps, warm-up) uses its reference's packing report; a variant that changes the crop or the rescaling (`wandler_1m_crop384`, `*_rescale_*`) gets one 15-minute timing job (`timing.sbatch`, `gputest`) before its runs. This departs from the rule that every first run of a config is a timing run (maintainer decision of 16 October 2026): the full timing step costs up to 200 GPU BU per config, so the up to 11 variant and combination configs would take about 2,200 of the 10,000 GPU BU, while a one-change variant that keeps the work per step runs at its reference's measured speed, and a crop or rescaling change is measured by one 15-minute job for 50 GPU BU;
- the GPU BU, GPU-hours and hours per run of the training steps read "pending the timing report" until `reports/timing/packing_<config>.json` of the timing step is copied into the repository.

### 3.2 Selection rule

Status: frozen on 16 October 2026, before any Project Schatten run exists; revised the same day, before any run, on the maintainer's review (conditional stability step, tie margin from the measured spread, fallback by false discard rate, combination step 7b). It replaces the draft of 14 October 2026 and changes only by a commit that says so before the runs it would affect.

Every value is read from validation reports (`reports/evaluation/<run-id>_val.json`); for a band-flexible model, from its band set B02, B03, B04 and B08. The test split chooses nothing; it is read once per frozen candidate, by the maintainer (step 10). Definitions used below:

- **Validation minimums:** the minimum of every target of `src/tiefer_lab/acceptance.py` that validation measures: `ACC-01`, `ACC-03`, `ACC-05`, `ACC-07`, `ACC-08`, `FRM-01`, `FRM-02` and `STD-01`; for a candidate on three seeds also `ACC-09`.
- **Value of a candidate:** on one seed, the value of seed 0; on three seeds (0, 1, 2), the mean over the seeds, with `ACC-09` taken as the standard deviation of the cloud BOA over them.
- **Reference spread:** the standard deviation of a metric on validation over the three seeds of the family's reference runs of step 3 (`sieb` or `wandler_1m`); for the INT8 cloud BOA loss, over the exports of those runs (step 8).
- **Tie:** a difference smaller than the reference spread of that metric, and at least 0.002.

Rules:

1. **Seeds.** Wandler variants are compared on three seeds, and only after step 6 is settled (rule 3), because a single seed cannot separate their effects from seed spread. Sieb variants are compared on seed 0 only if the reference spread of the validation cloud BOA of `sieb` is below the `ACC-09` target; otherwise on three seeds. A one-seed variant is compared with seed 0 of its reference, a three-seed variant with the mean of the three reference seeds.
2. **Winner among candidates.** The candidates that meet every validation minimum are eligible. The eligible candidate with the highest validation cloud BOA wins; a tie is broken by the higher mean IoU, and a tie on both by the reference. When no candidate is eligible, the one that misses the fewest minimums wins, then the lowest validation false discard rate (`FRM-01`), then the highest cloud BOA, and each missed minimum is reported. `FRM-01` and `FRM-02` are checked on validation and reported for every candidate.
3. **Stability (step 6), conditional.** Step 6 runs only if the three seeds of `wandler_1m` (step 3) miss the `ACC-09` minimum on validation, or any of them records a non-finite step (`diagnose seeds`, step 4). If it runs, `wandler_1m_grad_clip`, `wandler_1m_skip_nonfinite` and `wandler_1m_warmup10` run on three seeds each; among those that meet the `ACC-09` minimum, the one with the smallest seed spread of the validation cloud BOA wins, a tie broken by the higher cloud BOA. Its setting is the stability change, and it becomes the Wandler reference of rules 4 to 6. If step 6 does not run, or no variant meets the `ACC-09` minimum, there is no stability change, `wandler_1m` stays the Wandler reference, and the plan says so in a commit before step 7. Every later Wandler variant is the Wandler reference with one setting changed, committed before it is submitted.
4. **Which variants run (step 7).** The variants of a target run only when the family's reference misses that target's target value on validation: `ACC-05` (mean IoU, step 4) with `wandler_1m_lovasz` and `wandler_1m_crop384`, or `sieb_lovasz`; `CMP-05` (the larger cloud BOA loss of `rescale=0.5` and `rescale=2`, step 4) with `wandler_1m_rescale_2x` and `wandler_1m_rescale_3x`, or `sieb_rescale_2x`; `CMP-03` (the INT8 cloud BOA loss of the export of step 8) with the six `int8_` export variants of the family. No other variant runs in this plan. The winner of each target is chosen by rule 2 among the reference and that target's variants; a winner is a variant that beats the reference.
5. **Combination (step 7b).** When the training winners of step 7 of a family change different settings, they are combined into `sieb_candidate` or `wandler_1m_candidate`: the family's reference with the settings of those winners, nothing else; when two winners change the same setting, the one with the higher validation cloud BOA keeps it. Each combination runs on three seeds. It is selected only if it is not worse than any single winner on any validation minimum by more than the tie margin of that metric; otherwise the best single winner by rule 2 is kept. With fewer than two winners, step 7b does not run for that family.
6. **Family candidate.** The combination of rule 5 when it is selected; otherwise rule 2 among the family's reference and its single winners. This gives one candidate for Sieb and one for Wandler.
7. **Export setting.** Among the default export and the `int8_` variants of a candidate: the smallest validation INT8 cloud BOA loss whose INT8 file meets the `OBD-03` target; a tie goes to the default MinMax calibration.
8. **Cloud logit bias and soft fraction.** Used only if the maintainer approves their method-change issues, [issue 21](https://github.com/tiefer-labs/lab/issues/21) and [issue 22](https://github.com/tiefer-labs/lab/issues/22); then the bias and the temperature are the ones `python -m tiefer_lab.calibrate` chooses on validation, and the run with them is a separate candidate, compared by rule 2 with the same run without them. Validation values after the bias are optimistic, because the bias is chosen on validation; the independent datasets of step 9 are the clean check.
9. **Independent datasets** never choose anything: they are evaluated only for the candidates of rule 6 (step 9).

### 3.3 Steps in order of priority

If the budget runs out, the order of the table is the priority: `FRM-01` and stability first. Every command runs from the repository folder on `roihu-cpu.csc.fi`; the commands are in section 3.4 and the costs in section 3.8.

| Step | What | Configs and seeds | Partition | Cost (section 3.8) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 0 | setup on both architectures as batch jobs, the CPU build of torch on the x86 side, and the smoke job with the CPU against GPU check, from zero ([README.md](README.md), the step 0 runbook) | `setup_cpu.sbatch`, `setup_gpu.sbatch`, `smoke.sbatch` | `small`, `gputest` | at most 100 GPU BU | not run |
| 0a | source check: HEAD requests only ([section 3.6](#36-source-check-and-downloads)) | `check_sources.sbatch` | `small` | CPU | not run |
| 1 | data: the survey; the CloudSEN12+ caches `cloudsen12-l1c-high` and `cloudsen12-l1c-all` with the reference masks of the extra table | `survey.sbatch`, `data.sbatch` | `small` | CPU | not run |
| 1a | independent caches: the Sentinel-2 Cloud Mask Catalogue and KappaSet ([section 3.6](#36-source-check-and-downloads)), whose builds drop every product that CloudSEN12+ uses, by product ID and by tile with date; their downloads are deleted once the cache is complete. L8 SPARCS and then L8 Biome wait until both have an evaluation report | `independent.sbatch s2_cloud_catalogue`, `independent.sbatch kappaset` | `small` | CPU | not run |
| 2 | timing step: each config with 1, 2, 3 and 4 runs per GPU; time per epoch, GPU utilisation, GPU memory and data wait; the chosen packing. Then one cut epoch on a full CPU node, against the GPU in BU per epoch. Then the gate (section 2) | GPU: `sieb`, `wandler_1m`; CPU: `sieb`, `cloudscout_reimpl_step1_th30` | `gpumedium`, `medium` | at most 400 GPU BU | not run |
| 3 | reference runs, packed | `sieb` seeds 0, 1, 2; `wandler_1m` seeds 0, 1, 2 | `gpumedium` | pending the timing report | not run |
| 4 | validation evaluations with references, full metrics and robustness, then the diagnosis, validation and training only: seed stability, false discards (true cloud fraction in bins of 0.05), per-class IoU, INT8 sensitivity per Conv node, cloud BOA loss at `rescale=0.5` and `rescale=2` | the six runs of step 3 | `small` | CPU | not run |
| 5 | only if both method-change issues, [issue 21](https://github.com/tiefer-labs/lab/issues/21) (cloud logit bias) and [issue 22](https://github.com/tiefer-labs/lab/issues/22) (soft cloud fraction), are approved: calibration on the CPU, then evaluation with the cloud logit bias and the soft fraction; `FRM-01`, `FRM-02`, cloud BOA and mean IoU reported together | the six runs of step 3 | `small` | CPU | conditional |
| 6 | stability variants, only if rule 3 calls for them (`wandler_1m` misses `ACC-09` or records a non-finite step): three seeds each, packed, then their validation evaluations | `wandler_1m_grad_clip`, `wandler_1m_skip_nonfinite`, `wandler_1m_warmup10`, seeds 0, 1, 2 | `gpumedium`, `small` | pending the timing report; 0 if it does not run | conditional |
| 7 | the variants rule 4 calls for, on the seeds of rule 1, packed; the export variants on the CPU | `ACC-05`: `wandler_1m_lovasz`, `wandler_1m_crop384`, `sieb_lovasz`; `CMP-05`: `wandler_1m_rescale_2x`, `wandler_1m_rescale_3x`, `sieb_rescale_2x`; `CMP-03`: `*_int8_percentile`, `*_int8_entropy`, `*_int8_calib1024`, `*_int8_calib_stratified`, `*_int8_float_ends`, `*_int8_input_clip` | `gputest`, `gpumedium`, `small` | pending the timing report and the diagnosis | not run |
| 7b | combination of the step 7 winners of each family, only if rule 5 calls for it: three seeds, packed, then validation evaluations | `sieb_candidate`, `wandler_1m_candidate`, seeds 0, 1, 2, filled from the step 7 winners | `gpumedium`, `small` | pending the timing report; 0 if it does not run | conditional |
| 8 | exports of the reference runs on the CPU (`CMP-01` to `CMP-03`, `OBD-03`): ONNX per band set, the Wandler four-band export included, check against PyTorch, FP16, INT8 with ONNX Runtime (a proxy for `CMP-03`) | the six runs of step 3 | `small` | CPU | not run |
| 9 | independent evaluations of the candidates of rule 6 | 2 candidates on the Catalogue and on KappaSet | `small` | CPU | not run |
| 10 | final test requests, run by the maintainer only (section 3.5), on the CPU | the 2 frozen candidates | `small` | CPU | not run |

Not in this plan: `wandler_1m_frame_loss`, `wandler_1m_crop512`, `sieb_frame_loss`, `wandler_1m_best_by_four_bands`, `sieb_grad_clip`, `wandler_1m_landsat_bandsets`, `lupe_1m`, the CloudScout re-implementation, `wandler_1m_extra_data` and the extra training patches, `wandler_22m` and `wandler_1m_distill_22m`. They need a later revision of this plan before they are submitted.

### 3.4 Commands

Step 0, from zero on `roihu-cpu.csc.fi` (the full commands and checks are in [README.md](README.md), section 3); the smoke job runs `tiefer_lab.device_check` on the GPU:

```bash
bash hpc/roihu/submit.sh hpc/roihu/setup_cpu.sbatch
bash hpc/roihu/submit.sh hpc/roihu/setup_gpu.sbatch
bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
```

Steps 0a, 1 and 1a: the source check, the survey and the CloudSEN12+ caches as [README.md](README.md), step 3, describes them (the 13-band cache with its shards and rate limits as written there), the reference masks once `REFERENCE_*` are set from the survey, then the two independent caches of step 1a, which need the complete CloudSEN12+ cache for their independence check:

```bash
bash hpc/roihu/submit.sh hpc/roihu/check_sources.sbatch
bash hpc/roihu/submit.sh hpc/roihu/survey.sbatch
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch all
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch val --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/data.sbatch test --name cloudsen12-l1c-all --references
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch s2_cloud_catalogue
bash hpc/roihu/submit.sh hpc/roihu/independent.sbatch kappaset
```

Step 2, the timing step, then the packing reports are copied into `reports/timing/` and the plan is revised (the gate):

```bash
bash hpc/roihu/submit.sh hpc/roihu/timing_packed.sbatch configs/sieb.toml
bash hpc/roihu/submit.sh hpc/roihu/timing_packed.sbatch configs/wandler_1m.toml
bash hpc/roihu/submit.sh hpc/roihu/timing_cpu.sbatch configs/sieb.toml
bash hpc/roihu/submit.sh hpc/roihu/timing_cpu.sbatch configs/cloudscout_reimpl_step1_th30.toml
```

Step 3, after the gate, with the chosen packing `<n>` and the time limit from the report (`<epochs>` is `train.epochs` of the config). With `<n>` of 3, one job per config; with fewer, the seeds split over more jobs:

```bash
python3 -m tiefer_lab.packed time-limit --report reports/timing/packing_sieb.json --runs <n> --epochs <epochs>
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/sieb.toml@0 configs/sieb.toml@1 configs/sieb.toml@2
python3 -m tiefer_lab.packed time-limit --report reports/timing/packing_wandler_1m.json --runs <n> --epochs <epochs>
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/wandler_1m.toml@0 configs/wandler_1m.toml@1 configs/wandler_1m.toml@2
```

A job that stops at its time limit is continued with `resume:<run-id>` entries in the same way.

Step 4, per run of step 3, on the CPU (`<run-id>` is the run ID its log prints, `<config>-seed<N>-...`; `<cache>` is `cloudsen12-l1c-high` for Sieb and `cloudsen12-l1c-all` for Wandler):

```bash
FULL_METRICS=1 ROBUSTNESS=1 PERTURBATIONS="rescale=0.5 rescale=2" bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch frames /scratch/<project>/tiefer-lab/reports/evaluation/<run-id>_val.json --cache <cache>
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch int8 <run-id>
```

and once per family, over its three seeds:

```bash
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch seeds /scratch/<project>/tiefer-lab/runs/sieb-seed0-<rest> /scratch/<project>/tiefer-lab/runs/sieb-seed1-<rest> /scratch/<project>/tiefer-lab/runs/sieb-seed2-<rest>
bash hpc/roihu/submit.sh hpc/roihu/diagnose.sbatch seeds /scratch/<project>/tiefer-lab/runs/wandler_1m-seed0-<rest> /scratch/<project>/tiefer-lab/runs/wandler_1m-seed1-<rest> /scratch/<project>/tiefer-lab/runs/wandler_1m-seed2-<rest>
```

Step 5, only after issues 21 and 22 are approved, per run of step 3, on the CPU:

```bash
bash hpc/roihu/submit.sh hpc/roihu/calibrate_cpu.sbatch <run-id>
CLOUD_BIAS=auto FRACTION=soft FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
```

Step 6, only if rule 3 calls for it: three seeds of each variant, packed with the `wandler_1m` packing (the variants change no work per step), then one validation evaluation per run as in step 4:

```bash
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/wandler_1m_grad_clip.toml@0 configs/wandler_1m_grad_clip.toml@1 configs/wandler_1m_grad_clip.toml@2
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/wandler_1m_skip_nonfinite.toml@0 configs/wandler_1m_skip_nonfinite.toml@1 configs/wandler_1m_skip_nonfinite.toml@2
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/wandler_1m_warmup10.toml@0 configs/wandler_1m_warmup10.toml@1 configs/wandler_1m_warmup10.toml@2
```

Step 7, only the configs rule 4 calls for, each committed first (a Wandler variant on top of the stability change of rule 3); a crop or rescaling variant gets its 15-minute timing job first; `@0` only for a Sieb variant when rule 1 allows one seed; the export variants on the CPU:

```bash
bash hpc/roihu/submit.sh hpc/roihu/timing.sbatch configs/<crop-or-rescale-variant>.toml
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/<variant>.toml@0 configs/<variant>.toml@1 configs/<variant>.toml@2
EXPORT_CONFIG=configs/<family>_int8_<setting>.toml bash hpc/roihu/submit.sh hpc/roihu/export_cpu.sbatch <run-id>
```

Step 7b, only if rule 5 calls for it, after `configs/<family>_candidate.toml` is filled from the step 7 winners and committed:

```bash
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/sieb_candidate.toml@0 configs/sieb_candidate.toml@1 configs/sieb_candidate.toml@2
bash hpc/roihu/submit.sh --time=<limit> hpc/roihu/train_packed.sbatch configs/wandler_1m_candidate.toml@0 configs/wandler_1m_candidate.toml@1 configs/wandler_1m_candidate.toml@2
FULL_METRICS=1 ROBUSTNESS=1 PERTURBATIONS="rescale=0.5 rescale=2" bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
```

Step 8, per run of step 3, on the CPU:

```bash
bash hpc/roihu/submit.sh hpc/roihu/export_cpu.sbatch <run-id>
```

Step 9, per candidate of rule 6 and dataset, on the CPU:

```bash
DATA=s2_cloud_catalogue REASON="independent evaluation of <run-id>, candidate of hpc/roihu/plan.md section 3.2, rule 6" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
DATA=kappaset REASON="independent evaluation of <run-id>, candidate of hpc/roihu/plan.md section 3.2, rule 6" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
```

After every job, and the persistent files of each candidate to `/projappl` once it is selected (its run folder holds the checkpoints, the ONNX files and the metadata):

```bash
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
mkdir -p /projappl/<project>/tiefer-lab/keep && cp -r /scratch/<project>/tiefer-lab/runs/<run-id> /projappl/<project>/tiefer-lab/keep/
```

### 3.5 Final test requests (step 10)

Written by the assistant from the copied report files after step 9, for the maintainer, who alone runs them. One request per frozen candidate: the config, the run ID, the selection rule and the reason, for example:

```bash
FINAL=1 REASON="final test of <run-id>, frozen by hpc/roihu/plan.md section 3.2 on <date>" FULL_METRICS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
FINAL=1 REASON="final test of <run-id>, robustness for CMP-05" PERTURBATIONS="rescale=0.5 rescale=2" ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate_cpu.sbatch <run-id>
FINAL=1 REASON="final export check of <run-id>" EXPORT_CONFIG=configs/<selected-export>.toml bash hpc/roihu/submit.sh hpc/roihu/export_cpu.sbatch <run-id>
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
| `CMP-03` | steps 8 and 10; export variants in step 7; ONNX Runtime on the CPU, a proxy: the TensorRT value comes from the Jetson | as `sieb` |
| `CMP-04` | not applicable: not band-flexible | not measured: the four-band specialist `lupe_1m` is not in this plan |
| `CMP-05` | steps 4 and 10, robustness at `rescale=0.5` and `rescale=2` | as `sieb` |
| `CMP-06` | not measured: no other-sensor dataset is planned yet | as `sieb` |
| `CMP-07` | not applicable: four bands only | steps 4 and 10, band set B02 B03 B04 |
| `OBD-01`, `OBD-02`, `OBD-04`, `OBD-05`, `OBD-06` | not measured on Roihu: they need the Jetson benchmark ([jetson/README.md](../../jetson/README.md)) of the exported files of step 10 | as `sieb` |
| `OBD-03` | step 8, the size of the exported files | as `sieb` (a 1 M model) |
| `STD-01` | steps 4 and 10, worst stratum | steps 4 and 10 |
| `STD-02`, `STD-03`, `STD-04` | measured by the tests and documents, not by runs ([docs/REQUIREMENTS.md](../../docs/REQUIREMENTS.md)) | as `sieb` |

### 3.8 Budget tables

**GPU.** For every training step: runs x hours per run / runs per GPU = GPU-hours, times 200 GPU BU. Hours per run and runs per GPU come from the packing reports of step 2; until then they read "pending the timing report". Upper bounds are from the time limits; the bill follows the runtime.

| Step | Jobs or runs | Runs | Hours per run | Runs per GPU | GPU-hours | GPU BU |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | `setup_gpu.sbatch`, `smoke.sbatch` (`gputest`) | 2 jobs | at most 0.25 | 1 | at most 0.5 | at most 100 |
| 2 | `timing_packed.sbatch`: `sieb`, `wandler_1m` | 2 jobs | at most 1 | 1 to 4, measured | at most 2 | at most 400 |
| 3 | `sieb` seeds 0, 1, 2 | 3 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 3 | `wandler_1m` seeds 0, 1, 2 | 3 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 6 | three stability variants, three seeds each (conditional) | 9 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 7 | 15-minute timing jobs of the crop and rescaling variants (`gputest`) | up to 4 jobs | at most 0.25 | 1 | at most 1 | at most 200 |
| 7 | Sieb variants of rule 4 (`sieb_lovasz`, `sieb_rescale_2x`), one or three seeds | 2 to 6 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 7 | Wandler variants of rule 4 (`wandler_1m_lovasz`, `wandler_1m_crop384`, `wandler_1m_rescale_2x`, `wandler_1m_rescale_3x`), three seeds | up to 12 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 7b | `sieb_candidate`, three seeds (conditional) | 3 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| 7b | `wandler_1m_candidate`, three seeds (conditional) | 3 | pending the timing report | pending the timing report | pending the timing report | pending the timing report |
| total | every step above | up to 39 training runs | n/a | n/a | at most 3.5 fixed; the rest pending the timing report | at most 700 fixed; the rest pending the timing report |
| stop line | no new GPU job beyond it | n/a | n/a | n/a | 47.5 | 9,500 |

With every conditional step running, the 39 training runs share 8,800 GPU BU, 44 GPU-hours, after the fixed 700: on average at most 1.13 GPU-hours per run after packing (for example a run of 3.4 hours alone, three per GPU, if packing slows it by nothing). The gate of section 2 checks this with the real values before step 3.

**CPU.** Every job that does not train, at its cores and memory (2 GiB per core where the job allows, so both billing terms are equal), with the time limit as the upper bound of its hours. Acceptance and comparison read the copied report files and use no Roihu billing units.

| Job | Cores, memory | CPU BU per hour | Jobs | Hours, upper bound | CPU BU, upper bound |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `setup_cpu.sbatch` | 4, 8 GiB | 3 | 1 | 1 | 3 |
| `check_sources.sbatch` | 1, 2 GiB | 0.75 | 1 | 1 | 1 |
| `survey.sbatch` | 2, 8 GiB | 3 | 1 | 1 | 3 |
| `data.sbatch` (both caches, the 13-band shards and merge, the reference masks) | 16, 16 GiB | 12 | 10 | 24 | 2,880 |
| `independent.sbatch` | 8, 32 GiB | 12 | 2 | 24 | 576 |
| `evaluate_cpu.sbatch` (steps 4, 5, 6, 7, 7b, 9 and 10) | 32, 64 GiB | 24 | 53 | 4 | 5,088 |
| `calibrate_cpu.sbatch` (step 5) | 32, 64 GiB | 24 | 6 | 1 | 144 |
| `diagnose.sbatch` (`frames`, `seeds`, `int8`) | 32, 64 GiB | 24 | 14 | 6 | 2,016 |
| `export_cpu.sbatch` (steps 7, 8 and 10) | 32, 64 GiB | 24 | 20 | 2 | 960 |
| `timing_cpu.sbatch` (step 2, `medium`) | one node, 384 cores | 288 | 2 | 1 | 576 |
| total | n/a | n/a | 110 jobs | n/a | 12,247 of 60,000 |

**Storage.** From the recorded sizes. `/scratch` holds the caches and the runs during the campaign; the downloads of the independent datasets are deleted once their caches are built and checked (`independent.sbatch`); the persistent files of the candidates go to `/projappl` (section 3.4).

| What | Where | Size, upper bound | Source of the size |
| :--- | :---: | :---: | :---: |
| CloudSEN12+ caches, high quality 509 x 509 patches, 4 and 13 bands | `/scratch` | 248 GB, the whole dataset | [docs/DATA.md](../../docs/DATA.md), the Hugging Face page; 6.67 MiB per patch with 13 bands and 2.22 MiB with four |
| downloads of the Catalogue and KappaSet, until their caches are complete | `/scratch` | 71.4 GB (15,206,407,392 and 56,186,540,640 bytes) | `files` of `src/tiefer_lab/data/independent.py` |
| caches of the Catalogue and KappaSet | `/scratch` | 71.4 GB, their downloads | as above |
| runs, ONNX files and reports | `/scratch` | small: a 1 M model is about 4 MB per checkpoint | `OBD-03` |
| virtual environments, source and the candidates' run folders | `/projappl` | pending the setup step | step 0 |

At the upper bound, `/scratch` holds 391 GB, 0.36 TiB: 6 x 0.36 x 24 = 51 storage BU per day, 1,536 per 30 days. The 30,000 storage BU last about 585 days at that size, so storage does not limit the plan; `/projappl` is added once step 0 has measured the environments.

**Storage projection.** At that upper bound from 16 October 2026, with `/projappl` not yet measured, the 30,000 storage BU would run out after about 585 days, on 23 May 2028; the real date moves later, because the caches are built step by step and the downloads are deleted once their caches are complete, and earlier by the `/projappl` use, which the revision after step 0 adds. If the storage BUs ran out, no job could be submitted and access to `/scratch` and `/projappl` would end 30 days later ([usage policy](https://docs.csc.fi/computing/usage-policy/) (page of 15 October 2026, read 16 October 2026)). Scratch files not accessed for 180 days are deleted (projects with less than 5 TiB of scratch quota; `csc-workspaces` shows the cycle), so the candidates' run folders are copied to `/projappl` (section 3.4), and a cache older than that is rebuilt by its data job.

---

## Changelog

- 16 October 2026: the CSC usage policy: running out of BUs, the worst-case cost check of `submit.sh` and `sweep.sh` against the balance typed in, the storage projection with its date, scratch cleaning after 180 days, no packing that leaves the GPU underused, CPU training as a measured option (`timing_cpu.sbatch`), and the setup as batch jobs; drafted with an AI-assisted system.
- 16 October 2026: on the maintainer's review: the time-limit margin is 50 percent, and a stopped run resumes from `last.pt`; the 15-minute timing of crop and rescaling variants is recorded as a departure, with its reason; every reported evaluation runs on the CPU and one table never mixes devices; drafted with an AI-assisted system.
- 16 October 2026: the fixed allocation (10,000 GPU, 60,000 CPU, 30,000 storage BU) with the billing rules of CSC; the stop line at 9,500 GPU BU; the gate after the timing step with its cut order; every job that does not train on the CPU; packed training with time limits from the packing reports; the timing step with 1 to 4 runs per GPU; GPU, CPU and storage tables in section 3.8; downloads deleted once their caches are complete; drafted with an AI-assisted system.
- 16 October 2026: on the maintainer's review, before any run: step 6 (stability) is conditional; the tie margin is the measured reference spread, at least 0.002; the fallback ranks by false discard rate before cloud BOA; step 7b combines the step 7 winners into the `_candidate` configs; steps 0 to 4 are approved first and steps 5 to 10 are revised with the timing costs before submission; step 5 names issues 21 and 22; drafted with an AI-assisted system.
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
