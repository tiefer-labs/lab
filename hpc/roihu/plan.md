<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Run plan on CSC Roihu

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What ran on CSC Roihu for milestone L2, how it compares with the plan of 2 October 2026, and the next steps. GPU BU are GPU billing units. Sections 1 to 4 and 6 are current; section 5, the plan of 2 October 2026, is superseded and kept as the record; section 6 is the re-evaluation after the padding fix, which comes before every new run.

---

## 1. What ran

The plan of 2 October 2026 (section 5) is superseded by this section and sections 2 and 3; it stays in this file, unchanged except for the tense of its budget and deadline, the sources of two values, the marks on its commands and its internal section numbers, as the record of what was planned.

The GPU maintenance of CSC Roihu began on 6 October 2026 at 08:00 Finnish time (05:00 UTC); no GPU job of this repository has run since. Elapsed times, GPU hours and GPU BU (200 per GPU hour) are those of [docs/RESULTS.md](../../docs/RESULTS.md), section 16.

| Step | Planned | Status | Jobs | Elapsed | GPU BU, planned upper bound | GPU BU, measured |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | timing runs of seven configs | pending (note 1) | pending | pending | 350 | pending |
| 2 | `l1_full`, seed 0 | done | 2001000 | 00:22:36 | 72 | 75.333 |
| 3 | `l2_flex_1m`, seed 0 | changed (note 2) | 2000912, 2000941 (failed), 2000949 | 00:00:55, 00:00:55, 01:28:11 | 581 | 300.056 |
| 4 | `l2_spec_1m`, seed 0 | changed (note 3) | 2001425 | 00:37:27 | 249 | 124.833 |
| 5 | `l2_flex_1m_zero`, seed 0 | not run | n/a | n/a | 581 | n/a |
| 6 | `l2_flex_0p5m`, seed 0 | not run | n/a | n/a | 360 | n/a |
| 7 | seeds 1 and 2 of the 1 M pair | not run | n/a | n/a | 1660 | n/a |
| 8 | `l2_flex_4m`, seed 0 | not run | n/a | n/a | up to 1971 | n/a |

Notes:

1. No timing job is in the compute reports read so far; whether the timing runs were submitted is pending until the job list of 2 and 3 October 2026 is read.
2. Batch 64 and learning rate 0.004, after two attempts at batch 128 ran out of GPU memory.
3. Batch 64; the learning rate is pending until its run `config.toml` is read.

Steps 5 to 8 were not submitted before the maintenance deadline of 6 October 2026. They are carried into the next steps (section 3), with their costs estimated again from the measured epoch times of section 2.

Also run, outside the steps above: `l1_base` seed 1 (training job pending; evaluations 2000417 and 2000418; export 2000438, 01:28:24, 294.667 GPU BU), the evaluations of every trained run, the exports of the three L1 runs, three export jobs whose run is not identified (2002028, 2002101, 2002148), and the robustness evaluations of `l1_base` seed 0. All GPU jobs with a known elapsed time add up to at least 1510.389 GPU BU (7.552 GPU hours); the total is a lower bound, because the elapsed times of three export jobs were read while they ran and several jobs have no elapsed time yet. The 13-band cache was built in CPU jobs on `small` (RESULTS.md, section 16); their CPU billing units are pending.

Remaining budget: pending until the CSC usage report is read in MyCSC.

---

## 2. Plan against actual

Seconds per epoch are the elapsed time of the training job divided by 150 epochs, so they include the start of the job and are an upper value. `l1_full` ran 150 epochs (patience 150); `l2_flex_1m` reached epoch 150 according to the session notes; the epochs of `l2_spec_1m` are pending, so its value assumes 150.

| Config | Batch | Planned seconds per epoch | Measured seconds per epoch | GPU BU, planned upper bound | GPU BU, measured | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `l1_full` | 128 | 8.6 | 9.040 (00:22:36) | 72 | 75.333 | job 2001000 (log) |
| `l2_flex_1m` | 128 planned, 64 run | 69.8 | 35.273 (01:28:11) | 581 | 300.056 | job 2000949 (log) |
| `l2_spec_1m` | 128 planned, 64 run | 29.8 | 14.980 (00:37:27) | 249 | 124.833 | job 2001425 (page) |

- `l1_full` cost 75.333 GPU BU against an upper bound of 72, so the bound did not hold for it. The plan's 8.6 s per epoch was measured for `l1_base`; the measured 9.040 s includes the start of the job. The next estimates are rounded up and include the start of the job.
- The L2 runs cost about half of their bounds. They ran at batch 64, not the planned 128, and the bound is an upper bound by construction (section 5.1), so the measured values replace the estimates for the next steps.
- The elapsed times are those of [docs/RESULTS.md](../../docs/RESULTS.md), section 16; GPU BU = elapsed seconds / 18 (200 per GPU hour).

---

## 3. Next steps

| Step | What | Why | Status |
| :--- | :---: | :---: | :---: |
| 1 | Copy the report files of 2 and 3 October 2026 into the repository with `bash hpc/roihu/collect.sh <run-id>`, with the test log entries | every `pending` value of RESULTS.md waits on them | not run |
| 2 | Read the run `config.toml` of `l2_spec_1m` seed 0 | its learning rate and cache are pending | not run |
| 3 | Export `l2_spec_1m` seed 0 with `export.sbatch` | it has no export report; `CMP-01` to `CMP-03` and `OBD-03` | not run |
| 4 | Three seeds for `l2_spec_1m` and `l1_full`, from a clean commit with the batch and learning rate in the config files | single-seed results decide nothing (docs/ASSUMPTIONS.md, `A-6.8`) | not run |
| 5 | Steps 5 to 8 of section 5.3, with costs from section 2 at batch 64 | the input design, the size ladder and the seeds of the 1 M pair | not run |
| 6 | Reference masks: run the survey, set the link and encodings, then `build_cache --references` and score them | `ACC-04` and the comparisons of docs/LANDSCAPE.md, section 5 | not run |
| 7 | dtacs4bands and the threshold sweep (section 4) | the comparisons of docs/LANDSCAPE.md, section 5 | not run |

Steps 3 and 4 run only after the re-evaluation of section 6, items 3 and 4, from the same clean commit, so that every new result is computed with the padding masked.

Remaining budget: pending until the CSC usage report is read in MyCSC.

---

## 4. Open measurements

The measurements that would decide the comparisons of [docs/LANDSCAPE.md](../../docs/LANDSCAPE.md), section 5. None has started. GPU BU are estimated before submission like every run of this plan.

| Item | Decides | Where | Acceptance target | Status |
| :--- | :---: | :---: | :---: | :---: |
| Score the extra-table reference masks (QA60, Sen2Cor, s2cloudless, CloudScore+ cs and cs_cdf, UNetMobV2 v1 and v2, SEnSeI v2) on the 975 test patches with this repository's code | references on the same CloudSEN12+ test pixels | CSC Roihu, CPU job; needs the verified link and encodings of `build_cache --references` (docs/DATA.md, section 9) | `ACC-04` | not started |
| Run Fmask 4.0, KappaMask L1C and L2A, CD-FCNN-RGBI and CD-FCNN-RGBISWIR on the same test patches | references not in the extra table | CSC Roihu | `ACC-04` | not started |
| Run dtacs4bands on the test split with B02, B03, B04, B08 | dtacs4bands on the same pixels and bands | CSC Roihu, GPU job; first check that its CC BY-NC 4.0 licence allows this use | none | not started |
| Threshold sweep of `l2_spec_1m` s0 on test: false send rate at a false discard rate of 0.01, with usefulness fixed at 70 percent cloud | CloudScout false positives against our false discard rate | CSC Roihu, GPU job; needs a decision threshold separate from the usefulness threshold, because `evaluate` uses one threshold for both today | `FRM-01`, `FRM-02` | not started |
| Latency, power and energy per 512 x 512 tile, FP16 and INT8, with `jetson/bench.py` | latency, power and energy against CloudScout | Jetson Orin ([jetson/README.md](../../jetson/README.md)) | `OBD-01`, `OBD-02`, `OBD-05` | not started |
| File size and memory during inference of the selected model | model size against CloudScout's memory footprint | export on CSC Roihu, memory on the Jetson Orin | `OBD-03`, `OBD-04` | not started |

---

## 5. Plan of 2 October 2026 (superseded)

### 5.1 Budget and basis

- Budget: about 6000 GPU BU remained on 2 October 2026; this plan was to use at most 5000. One GPU hour costs 200 GPU BU ([billing](https://docs.csc.fi/computing/hpc-billing/)).
- Deadline: the GPU nodes went into maintenance on 6 October 2026 at 08:00 Finnish time (05:00 UTC). Every run is a separate one-GPU job on `gpumedium`, so several run at the same time; jobs with 2 or 4 GPUs waited about 1.5 hours (log of 2 October 2026, job pending), and no run uses more than one GPU without a measured speed-up.
- Measured basis: `l1_base` (0.24 M parameters, 2.19 G multiply-accumulates per 512 x 512 tile, four bands) trains at 1304 patches per second on one GH200, 8.6 s per epoch including validation (log of 2 October 2026, job pending). That is 8490 / 1304 = 6.51 s of training and 2.09 s of validation per epoch.
- Estimate of a config, until its own timing run replaces it: training time x r x (1.25 with self-distillation, else 1) plus validation time x r x number of band sets, per epoch, where r is the config's multiply-accumulates divided by those of `l1_base`. The factor 1.25 counts the extra forward pass with all bands on the three of four steps that draw a smaller band set. A small network does not use the GPU fully, so scaling by operations gives an upper bound, not a prediction.
- Every new configuration first gets a timing run (`hpc/roihu/timing.sbatch`, one epoch cut to 50 steps on `gputest`, at most 15 minutes). Its `full epoch ... s (estimated)` replaces the estimate below before the long run is submitted.


### 5.2 Upper-bound cost per configuration

150 epochs each, from the formula above.

| Config | Parameters | r | Seconds per epoch | GPU hours | GPU BU |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `l1_full` | 0.24 M | 1.00 | 8.6 | 0.36 | 72 |
| `l2_flex_0p5m` | 0.53 M | 2.62 | 43.2 | 1.80 | 360 |
| `l2_flex_1m` | 0.92 M | 4.23 | 69.8 | 2.91 | 581 |
| `l2_flex_1m_zero` | 0.92 M | 4.23 | 69.8 | 2.91 | 581 |
| `l2_flex_1m_classweights` | 0.92 M | 4.23 | 69.8 | 2.91 | 581 |
| `l2_flex_1m_focal` | 0.92 M | 4.23 | 69.8 | 2.91 | 581 |
| `l2_flex_1m_nodistill` | 0.92 M | 4.23 | 62.9 | 2.62 | 524 |
| `l2_flex_1m_rescale`, `l2_flex_1m_gainoffset`, `l2_flex_1m_noiseblur` | 0.92 M | 4.23 | 69.8 | 2.91 | 581 each |
| `l2_spec_1m` | 0.92 M | 3.47 | 29.8 | 1.24 | 249 |
| `l2_flex_4m` | 3.59 M | 14.34 | 236.6 | 9.86 | 1971 |
| `l2_flex_cnx_21m` | 20.56 M | 42.36 | 698.7 | 29.11 | 5823 |
| `l2_spec_22m` | 22.04 M | 76.19 | 655.2 | 27.30 | 5460 |
| `l2_flex_22m` | 22.07 M | 79.98 | 1319.3 | 54.97 | 10994 |

If the timing runs confirm these bounds, the 22 M models do not fit the budget at 150 epochs. Then the whole size ladder moves to the same smaller number of epochs (settings stay identical across sizes), chosen so that the largest model fits, and the change is recorded here before submission.


### 5.3 Order of runs

The runs with the largest expected gain come first. Cumulative cost is the upper bound of section 5.2.

| Step | Runs | Why | GPU BU | Cumulative |
| :--- | :---: | :---: | :---: | :---: |
| 1 | timing runs of `l2_flex_0p5m`, `l2_flex_1m`, `l2_flex_4m`, `l2_flex_22m`, `l2_flex_cnx_21m`, `l2_spec_1m`, `l2_spec_22m` | replace the upper bounds by measured costs | 350 | 350 |
| 2 | `l1_full`, seed 0 | the L1 result run to the end of its schedule | 72 | 422 |
| 3 | `l2_flex_1m`, seed 0 | the band-flexible product candidate | 581 | 1003 |
| 4 | `l2_spec_1m`, seed 0 | its four-band control (decision rule in docs/ASSUMPTIONS.md) | 249 | 1252 |
| 5 | `l2_flex_1m_zero`, seed 0 | the second input design; the better one on validation is kept | 581 | 1833 |
| 6 | `l2_flex_0p5m`, seed 0 | the smallest size | 360 | 2193 |
| 7 | the kept 1 M design, seeds 1 and 2; `l2_spec_1m`, seeds 1 and 2 | three seeds for the final pair | 1660 | 3853 |
| 8 | `l2_flex_4m`, seed 0, if its measured cost fits | the next size | up to 1971 | up to 5824 |

The cut line is 5000 GPU BU: a step that would cross it with its measured cost is not submitted. The largest models, the loss variants (`classweights`, `focal`, `nodistill`) and the robustness runs (`rescale`, `gainoffset`, `noiseblur`) follow only if measured costs leave room; each is then added to this table with its measured cost before it is submitted.


### 5.4 Commands

From `roihu-gpu.csc.fi`, in the repository folder, after the 13-band cache `cloudsen12-l1c-all` is complete:

```bash
# not executed as written: no timing job is in the compute reports read so far
bash hpc/roihu/sweep.sh --timing configs/l2_flex_0p5m.toml configs/l2_flex_1m.toml configs/l2_flex_4m.toml \
  configs/l2_flex_22m.toml configs/l2_flex_cnx_21m.toml configs/l2_spec_1m.toml configs/l2_spec_22m.toml
# executed for l1_full, l2_flex_1m and l2_spec_1m only (section 1); not executed for
# l2_flex_1m_zero and l2_flex_0p5m
bash hpc/roihu/sweep.sh configs/l1_full.toml configs/l2_flex_1m.toml configs/l2_spec_1m.toml configs/l2_flex_1m_zero.toml configs/l2_flex_0p5m.toml
# not executed (step 7)
# step 7: use configs/l2_flex_1m_zero.toml instead if the zero design won on validation
bash hpc/roihu/sweep.sh --seeds 1,2 configs/l2_flex_1m.toml configs/l2_spec_1m.toml
```

`l1_full` reads the four-band cache `cloudsen12-l1c-high`, which is complete; it can start at once. After the runs, `python -m tiefer_lab.experiments` writes `reports/experiments.md` with the measured GPU hours of every run.

---

## 6. Re-evaluation after the padding fix

Every value measured so far counts the dataset's padded pixels ([docs/RESULTS.md](../../docs/RESULTS.md), section 21). Since commit `e01804d` the padding is masked when the labels are loaded. This section evaluates every trained run again with the same checkpoints, before any new run, so that every result is computed the same way.

Rules for every job of this section:

- Run from commit `e01804d`, or from the commit that changes `PADDING_SIDES` if item 1 calls for it, on a clean tree: `git status --porcelain` prints nothing. Every evaluation report records the commit and the dirty flag.
- GPU jobs are submitted from `roihu-gpu.csc.fi` with `hpc/roihu/submit.sh`, the login check runs on `roihu-cpu.csc.fi` ([README.md](README.md), step 3).
- GPU BU are estimated before submission from the measured elapsed times of [docs/RESULTS.md](../../docs/RESULTS.md), section 16, at 200 GPU BU per GPU hour (GPU BU = elapsed seconds / 18). An evaluation of one run on one split and one band set or perturbation is counted at 00:02:00, the longest evaluation job measured (2000113, 00:01:56, rounded up; the others took 00:00:24 to 00:01:15). Jobs bill their elapsed time, not their time limit.

### 6.1 Order and commands

1. On the login node first, the padding check of both caches, validation and test, 50 patches each. It reads a few patches and writes nothing. If any command ends with `differs from PADDING_SIDES`, or shows label values other than the card leads to expect, stop and report before any job; `PADDING_SIDES` is then changed in a commit of its own, and the jobs below run from that commit.

   ```bash
   ssh <user>@roihu-cpu.csc.fi
   cd /projappl/<project>/tiefer-lab/src
   git fetch origin && git checkout e01804d && git status --porcelain
   source hpc/roihu/env.sh
   python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-high --split val --patches 50
   python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-high --split test --patches 50
   python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-all --split val --patches 50
   python3 -m tiefer_lab.data.cache padding cloudsen12-l1c-all --split test --patches 50
   ```

2. A smoke job on `gputest`, because Slurm was upgraded from 25.05 to 26.05 during the service break (stated by the founder on 7 October 2026). Its outputs are labelled smoke and are never results.

   ```bash
   ssh <user>@roihu-gpu.csc.fi
   cd /projappl/<project>/tiefer-lab/src
   git fetch origin && git checkout e01804d && git status --porcelain
   bash hpc/roihu/submit.sh hpc/roihu/smoke.sbatch
   ```

3. Validation evaluations, with the baselines. `evaluate.sbatch` evaluates every band set of a run with `--band-set all`, so the four band sets of `l2_flex_1m` s0 are one job; `ROBUSTNESS=1` adds the seven perturbations of `l1_base` s0 to its job (rescale 0.5 and 2, gain 0.9 and 1.1, offset 0.01, noise 0.01, blur 1).

   ```bash
   ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_base-seed0-20261003T093922Z-81ab34b
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_base-seed1-20261003T124209Z-5ba4585
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_full-seed0-20261003T141417Z-5ba4585
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l2_spec_1m-seed0-20261003T145219Z-0f0984d
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l2_flex_1m-seed0-20261003T140653Z-5ba4585
   ```

4. Test evaluations of the same runs and band sets, without the perturbations. This reads the test split again for a measurement correction only: the checkpoints are the ones already evaluated, and no model, threshold or setting is chosen from the result ([POLICY.md](../../POLICY.md), gate 3). It is the decision class "test-split access" of [GOVERNANCE.md](../../GOVERNANCE.md), section 2, decided by the maintainer, and every evaluation appends an entry with this reason to `reports/test_log.md` before the data is read.

   ```bash
   FINAL=1 REASON="re-evaluation with padded pixels masked, same checkpoints, no selection" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_base-seed0-20261003T093922Z-81ab34b
   FINAL=1 REASON="re-evaluation with padded pixels masked, same checkpoints, no selection" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_base-seed1-20261003T124209Z-5ba4585
   FINAL=1 REASON="re-evaluation with padded pixels masked, same checkpoints, no selection" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l1_full-seed0-20261003T141417Z-5ba4585
   FINAL=1 REASON="re-evaluation with padded pixels masked, same checkpoints, no selection" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l2_spec_1m-seed0-20261003T145219Z-0f0984d
   FINAL=1 REASON="re-evaluation with padded pixels masked, same checkpoints, no selection" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch l2_flex_1m-seed0-20261003T140653Z-5ba4585
   ```

5. The export reports, lower priority than items 3 and 4. `python -m tiefer_lab.export` has no option to score existing ONNX files again: every run exports, checks and quantises anew (`src/tiefer_lab/export/__main__.py`; its options are `--run`, `--checkpoint`, `--skip-int8`, `--final`, `--reason` and `--band-set`). The FP32, FP16 and INT8 values of the three exported runs are therefore redone with `export.sbatch`:

   ```bash
   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch l1_base-seed0-20261003T093922Z-81ab34b
   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch l1_base-seed1-20261003T124209Z-5ba4585
   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch l1_full-seed0-20261003T141417Z-5ba4585
   ```

6. Only after items 3 and 4, from the same clean commit: the new seeds 1 and 2 of `l2_spec_1m` and `l1_full` (section 3, step 4), their validation and test evaluations, and the export of `l2_spec_1m` s0 (section 3, step 3).

   ```bash
   bash hpc/roihu/sweep.sh --seeds 1,2 configs/l2_spec_1m.toml configs/l1_full.toml
   # for each of the four new run IDs printed in the training logs:
   bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
   FINAL=1 REASON="final evaluation of a new seed, computed with padded pixels masked" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
   bash hpc/roihu/submit.sh hpc/roihu/export.sbatch l2_spec_1m-seed0-20261003T145219Z-0f0984d
   ```

After each job: `bash hpc/roihu/usage.sh <job-id>` and `bash hpc/roihu/collect.sh <run-id>`, then the report files go into `reports/` unchanged and the new values into [docs/RESULTS.md](../../docs/RESULTS.md), section 21.

### 6.2 Estimated cost

| Item | Jobs | Basis | GPU BU, estimate |
| :--- | :---: | :---: | :---: |
| 1. Padding check | none; login node | four commands that read 50 patches each | 0 |
| 2. Smoke job | 1 on `gputest` | its time limit of 00:15:00, an upper bound; its elapsed time was never recorded (job 1975865) | 50.000 |
| 3. Validation evaluations | 5 | 15 evaluations: `l1_base` s0 plain and 7 perturbations, `l1_base` s1, `l1_full` s0, `l2_spec_1m` s0, `l2_flex_1m` s0 with 4 band sets; 15 x 00:02:00 | 100.000 |
| 4. Test evaluations | 5 | 8 evaluations: the same runs and band sets without perturbations; 8 x 00:02:00 | 53.333 |
| 5. Exports again | 3 | `l1_base` s1: 01:28:24 (job 2000438); `l1_full` s0: 01:20:54 (job 2001281); `l1_base` s0: 01:28:24, the longest export measured, because its own export job is not identified (1982440, 00:30:55, is the candidate) | 859.000 |
| 6. Training of 4 new runs | 4 | `l2_spec_1m`: 00:37:27 each (job 2001425); `l1_full`: 00:22:36 each (job 2001000) | 400.333 |
| 6. Evaluations of the new runs | 8 | 4 runs, validation and test; 8 x 00:02:00 | 53.333 |
| 6. Export of `l2_spec_1m` s0 | 1 | 01:28:24, the longest export measured | 294.667 |
| Total | 27 | items 1 to 6 | 1,810.667 |

Items 1 to 4, which re-evaluate every existing result, cost an estimated 203.333 GPU BU; the exports of item 5 add 859.000, and the new runs of item 6 add 748.333. The remaining budget is pending until the CSC usage report is read in MyCSC (section 1).

---

## Changelog

- 7 October 2026: section 6, the re-evaluation of every trained run after the padding fix, with the commands in order and an estimated 1,810.667 GPU BU; the new seeds and the export of `l2_spec_1m` s0 come after it.
- 7 October 2026: the plan of 2 October 2026 is marked superseded and kept as section 5, the record; its budget and deadline are in the past tense, and its sweep commands are marked as executed or not executed.
- 7 October 2026: section 2 compares plan and actual: `l1_full` cost 75.333 GPU BU against a bound of 72 (9.040 s per epoch against 8.6); `l2_flex_1m` 35.273 s per epoch at batch 64 against 69.8 s; `l2_spec_1m` 14.980 s against 29.8 s.
- 7 October 2026: section 1 says that steps 5 to 8 were not submitted before the maintenance deadline; section 3 lists the next steps.
- 7 October 2026: the speed of 1304 patches per second and the queue wait of about 1.5 hours name their source (log of 2 October 2026, job pending).
- 7 October 2026: links to docs/DATA.md follow its new section numbers.
- 7 October 2026: correction: 2002028, 2002101 and 2002148 are three export jobs whose run is not identified.
- 7 October 2026: correction: the GPU maintenance began on 6 October 2026, 05:00 UTC, and has not passed; no GPU job has run since.
- 7 October 2026: section 6, the open measurements that would decide the comparisons of docs/LANDSCAPE.md.
- 7 October 2026: section 1, what ran before the maintenance, with job IDs, elapsed times and GPU BU; the plan of 2 October 2026 stays below as the record of what was planned.
- 2 October 2026: the three sensor robustness runs added below the cut line.
- 2 October 2026: first version, with upper-bound costs from the measured speed of `l1_base`.
