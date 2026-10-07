<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Run plan on CSC Roihu

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The training runs of milestone L2 in the order they are submitted, with their expected cost, so that an early stop still leaves a result. The total stays under 5000 GPU billing units (BU). Section 1 records what ran before the maintenance of 6 October 2026; sections 2 to 5 are the plan as written on 2 October 2026.

---

## 1. What ran

The GPU maintenance of CSC Roihu began on 6 October 2026 at 08:00 Finnish time (05:00 UTC); no GPU job of this repository has run since. Elapsed times, GPU hours and GPU BU (200 per GPU hour) are those of [docs/RESULTS.md](../../docs/RESULTS.md), section 16.

| Step | Planned | Outcome | Jobs | Elapsed | GPU BU, planned upper bound | GPU BU, measured |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | timing runs of seven configs | pending: no timing job is in the compute reports read so far | pending | pending | 350 | pending |
| 2 | `l1_full`, seed 0 | done | 2001000 | 00:22:36 | 72 | 75.333 |
| 3 | `l2_flex_1m`, seed 0 | done, changed: batch 64 and learning rate 0.004 after two attempts at batch 128 ran out of GPU memory | 2000912, 2000941 (failed), 2000949 | 00:00:55, 00:00:55, 01:28:11 | 581 | 300.056 |
| 4 | `l2_spec_1m`, seed 0 | done, changed: batch 64; learning rate pending | 2001425 | 00:37:27 | 249 | 124.833 |
| 5 | `l2_flex_1m_zero`, seed 0 | not run | n/a | n/a | 581 | n/a |
| 6 | `l2_flex_0p5m`, seed 0 | not run | n/a | n/a | 360 | n/a |
| 7 | seeds 1 and 2 of the 1 M pair | not run | n/a | n/a | 1660 | n/a |
| 8 | `l2_flex_4m`, seed 0 | not run | n/a | n/a | up to 1971 | n/a |

Also run, outside the steps above: `l1_base` seed 1 (training job pending; evaluations 2000417 and 2000418; export 2000438, 01:28:24, 294.667 GPU BU), the evaluations of every trained run, the exports of the three L1 runs, three export jobs whose run is not identified (2002028, 2002101, 2002148), and the robustness evaluations of `l1_base` seed 0. All GPU jobs with a known elapsed time add up to at least 1510.389 GPU BU (7.552 GPU hours); the total is a lower bound, because the elapsed times of three export jobs were read while they ran and several jobs have no elapsed time yet. The 13-band cache was built in CPU jobs on `small` (RESULTS.md, section 16); their CPU billing units are pending.

Remaining budget: pending until the CSC usage report is read in MyCSC.

---

## 2. Budget and basis

- Budget: about 6000 GPU BU remain (2 October 2026); this plan uses at most 5000. One GPU hour costs 200 GPU BU ([billing](https://docs.csc.fi/computing/hpc-billing/)).
- Deadline: GPU nodes go into maintenance on 6 October 2026 at 08:00 Finnish time. Every run is a separate one-GPU job on `gpumedium`, so several run at the same time; jobs with 2 or 4 GPUs waited about 1.5 hours, and no run uses more than one GPU without a measured speed-up.
- Measured basis: `l1_base` (0.24 M parameters, 2.19 G multiply-accumulates per 512 x 512 tile, four bands) trains at 1304 patches per second on one GH200, 8.6 s per epoch including validation (2 October 2026). That is 8490 / 1304 = 6.51 s of training and 2.09 s of validation per epoch.
- Estimate of a config, until its own timing run replaces it: training time x r x (1.25 with self-distillation, else 1) plus validation time x r x number of band sets, per epoch, where r is the config's multiply-accumulates divided by those of `l1_base`. The factor 1.25 counts the extra forward pass with all bands on the three of four steps that draw a smaller band set. A small network does not use the GPU fully, so scaling by operations gives an upper bound, not a prediction.
- Every new configuration first gets a timing run (`hpc/roihu/timing.sbatch`, one epoch cut to 50 steps on `gputest`, at most 15 minutes). Its `full epoch ... s (estimated)` replaces the estimate below before the long run is submitted.

---

## 3. Upper-bound cost per configuration

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

---

## 4. Order of runs

The runs with the largest expected gain come first. Cumulative cost is the upper bound of section 3.

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

---

## 5. Commands

From `roihu-gpu.csc.fi`, in the repository folder, after the 13-band cache `cloudsen12-l1c-all` is complete:

```bash
bash hpc/roihu/sweep.sh --timing configs/l2_flex_0p5m.toml configs/l2_flex_1m.toml configs/l2_flex_4m.toml \
  configs/l2_flex_22m.toml configs/l2_flex_cnx_21m.toml configs/l2_spec_1m.toml configs/l2_spec_22m.toml
bash hpc/roihu/sweep.sh configs/l1_full.toml configs/l2_flex_1m.toml configs/l2_spec_1m.toml configs/l2_flex_1m_zero.toml configs/l2_flex_0p5m.toml
# step 7: use configs/l2_flex_1m_zero.toml instead if the zero design won on validation
bash hpc/roihu/sweep.sh --seeds 1,2 configs/l2_flex_1m.toml configs/l2_spec_1m.toml
```

`l1_full` reads the four-band cache `cloudsen12-l1c-high`, which is complete; it can start at once. After the runs, `python -m tiefer_lab.experiments` writes `reports/experiments.md` with the measured GPU hours of every run.

---

## 6. Open measurements

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

## Changelog

- 7 October 2026: links to docs/DATA.md follow its new section numbers.
- 7 October 2026: correction: 2002028, 2002101 and 2002148 are three export jobs whose run is not identified.
- 7 October 2026: correction: the GPU maintenance began on 6 October 2026, 05:00 UTC, and has not passed; no GPU job has run since.
- 7 October 2026: section 6, the open measurements that would decide the comparisons of docs/LANDSCAPE.md.
- 7 October 2026: section 1, what ran before the maintenance, with job IDs, elapsed times and GPU BU; the plan of 2 October 2026 stays below as the record of what was planned.
- 2 October 2026: the three sensor robustness runs added below the cut line.
- 2 October 2026: first version, with upper-bound costs from the measured speed of `l1_base`.
