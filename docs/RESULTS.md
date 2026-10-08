<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Results

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Measured results of milestones L1 (four-band cloud filter) and L2 (model size, band-flexible model and four-band specialist), written by hand from the report files named in each table.

---

## 1. Summary

No results yet. The v2 campaign runs from commit <to be filled> on CSC Roihu; see [hpc/roihu/plan.md](../hpc/roihu/plan.md).

---

## 2. How to read this page

- Numbers are rounded to 3 decimals, half up (0.0075 becomes 0.008); counts, bytes and times are exact.
- Intervals in brackets are 95 percent bootstrap intervals over patches, with 1,000 resamples and seed 0 (`[evaluation]` of every config). A value without brackets has no interval in its source.
- `pending`, `not measured` and `n/a` have the meanings of [docs/STYLE.md](STYLE.md), section 4: measured but not yet in the repository; never measured; does not apply. "v2 pending" marks a row that waits for the v2 campaign; the rows per run are added when the v2 campaign plan is written.
- Times are in UTC. Durations are written `hh:mm:ss`; CPU time as Slurm prints it. GPU BU means GPU billing units of CSC.
- Which value answers which question, what supersedes what and how to cite a value are in [BENCHMARK-AUTHORITY.md](../BENCHMARK-AUTHORITY.md); the gates a value must pass before it appears here or is quoted outside the repository are in [POLICY.md](../POLICY.md), gates 1 and 2.
- Every table has a source column, written `key (kind)`: the key of a report file, defined in Appendix A, and the kind of source the value was copied from: `report` (a report file in `reports/`), `log` (Slurm or terminal output, with the job ID) or `config` (a configuration file at the commit named).

TP, TN, FP and FN are the true positive, true negative, false positive and false negative pixels of a patch, for cloud (thick plus thin) or for cloud shadow against the rest.

| Metric | Meaning | Better when |
| :--- | :---: | :---: |
| Mean IoU | mean over the four classes of the intersection over union of predicted and labelled pixels | higher |
| False discard rate | share of useful frames (labelled cloud fraction below the threshold) that the model would keep on board | lower |
| False send rate | share of cloudy frames (labelled cloud fraction at or above the threshold) that the model would send to the ground | lower |
| Decision accuracy | share of frames whose send or keep decision from the predicted mask equals the one from the label | higher |
| Cloud fraction mean absolute error | mean over frames of the absolute difference between predicted and labelled cloud fraction (thick plus thin cloud) | lower |
| BOA | balanced overall accuracy per patch, (PA + TN / (TN + FP)) / 2, median over patches | higher |
| PA | producer's accuracy per patch, TP / (TP + FN), median over patches | higher |
| UA | user's accuracy per patch, TP / (TP + FP), median over patches | higher |

A frame whose cloud fraction is at or above the threshold is kept on board; below it, the frame is sent. 50 percent is the configured default ([ASSUMPTIONS.md](ASSUMPTIONS.md), section 3). BOA, PA and UA are defined in `src/tiefer_lab/binary_metrics.py`. Every metric counts only the real image area of each patch: the dataset's padding is masked when the labels are loaded ([DATA.md](DATA.md), section 5).

---

## 3. Runs

| Run | Full run ID | Source |
| :--- | :---: | :---: |
| v2 pending | pending | pending |

| Run | Config | Bands | Parameters | Multiply-accumulates per 512 x 512 tile | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

| Run | Batch size | Learning rate | Epochs and stop | Best epoch | Training job | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending |

---

## 4. Environment and provenance

| Item | Value | Source |
| :--- | :---: | :---: |
| v2 pending | pending | pending |

The commit of each report and whether it was made from a clean working tree are listed in Appendix A. Every v2 run starts from one tagged, clean commit.

---

## 5. Data

CloudSEN12+, Level-1C, high quality labels, 509 x 509 pixel patches; see [DATA.md](DATA.md).

| Split | Patches | Use | Source |
| :--- | :---: | :---: | :---: |
| v2 pending | pending | pending | pending |

Labelled pixels per class of each split are recorded by the v2 build and its evaluation reports.

| Class | Pixels | Share | Source |
| :--- | :---: | :---: | :---: |
| v2 pending | pending | pending | pending |

| Cache | Bands | Size on disk | Built | Used by | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

---

## 6. All runs at a glance

| Run | Val mean IoU | Test mean IoU | Val false discard rate at 50 percent | Test false discard rate at 50 percent | Test decision accuracy at 50 percent | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending |

---

## 7. Selected model in detail

| Metric | Validation | Test | Source |
| :--- | :---: | :---: | :---: |
| v2 pending | pending | pending | pending |

No model is selected yet. The model is selected on the validation split only.

---

## 8. Accuracy by class

IoU per class:

| Run | Clear | Thick cloud | Thin cloud | Cloud shadow | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

Overall accuracy and cloud fraction mean absolute error:

| Run | Overall accuracy, val | Overall accuracy, test | Mean absolute error, val | Mean absolute error, test | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

Confusion matrix on the validation split, in pixels; rows are the labelled class, columns the predicted class:

| Labelled class | Predicted clear | Predicted thick cloud | Predicted thin cloud | Predicted cloud shadow | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

Frame metrics at each threshold. Useful frames are those whose labelled cloud fraction is below the threshold; they depend only on the labels (`src/tiefer_lab/metrics.py`).

| Run, split and threshold | Decision accuracy | False discard rate | False send rate | Useful frames | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

---

## 9. Accuracy by region

Broken down by the dataset field `equi_zone`, the continental zone of the Equi7Grid ([DATA.md](DATA.md), section 2.4).

| `equi_zone` | Patches | Mean IoU | False discard rate at 50 percent | Source |
| :--- | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending |

---

## 10. Baselines

| Baseline | Split | Mean IoU | False discard rate at 50 percent | Decision accuracy at 50 percent | Overall accuracy | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending |

IoU per class of the threshold rule on the validation split:

| Baseline | IoU clear | IoU thick cloud | IoU thin cloud | IoU cloud shadow | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

The threshold rule is tuned on the validation split; its validation values are scored on the data it was tuned on, and the test values are the comparison that counts.

The reference algorithms are not measured by this repository. Published values of other systems are not quoted on this page, because they were measured on other data or with other settings; they are in [LANDSCAPE.md](LANDSCAPE.md), section 4, which also says how each one would be measured on the same pixels.

| Reference algorithm | Mean IoU | Cloud BOA | Shadow BOA | Source |
| :--- | :---: | :---: | :---: | :---: |
| UNetMobV2 | not measured | not measured | not measured | n/a |
| Fmask | not measured | not measured | not measured | n/a |
| KappaMask L1C | not measured | not measured | not measured | n/a |
| KappaMask L2A | not measured | not measured | not measured | n/a |
| s2cloudless | not measured | not measured | not measured | n/a |
| CD-FCNN-RGBI | not measured | not measured | not measured | n/a |
| CD-FCNN-RGBISWIR | not measured | not measured | not measured | n/a |
| Sen2Cor | not measured | not measured | not measured | n/a |
| QA60 | not measured | not measured | not measured | n/a |
| CloudScore+ (cs) | not measured | not measured | not measured | n/a |
| CloudScore+ (cs_cdf) | not measured | not measured | not measured | n/a |
| SEnSeI v2 | not measured | not measured | not measured | n/a |
| dtacs4bands | not measured | not measured | not measured | n/a |

---

## 11. Cloud and shadow accuracy

Median over patches of the per-patch BOA, PA and UA, for cloud (thick and thin) against the rest and for cloud shadow against the rest (section 2).

Cloud against the rest:

| Run | Cloud BOA | Cloud PA | Cloud UA | Source |
| :--- | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending |

Cloud shadow against the rest:

| Run | Shadow BOA | Shadow PA | Shadow UA | Source |
| :--- | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending |

---

## 12. Band-flexible model by band set

| Model and band set | Bands | Val mean IoU | Test mean IoU | Test false discard rate at 50 percent | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

Product decision. Under the rule of [ASSUMPTIONS.md](ASSUMPTIONS.md), section 7, the band-flexible model is the product if its validation mean IoU on the band set B02 B03 B04 B08 lies within the 95 percent bootstrap interval of the validation mean IoU of the four-band specialist of the same size (1 M), with as many seeds as are available for both; otherwise specialists are shipped per sensor. The rule is applied on validation only; no decision is recorded yet.

---

## 13. Sensor robustness

A fixed perturbation is applied to the input before the model sees it. The perturbations are applied to Sentinel-2 data and simulate properties of another sensor; they are not measurements of a real sensor. They are defined in `src/tiefer_lab/data/sensor.py`; the result is clamped to the valid reflectance range.

| Perturbation | What it simulates | Mean IoU | False discard rate at 50 percent | Decision accuracy at 50 percent | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

| Perturbation | IoU clear | IoU thick cloud | IoU thin cloud | IoU cloud shadow | Overall accuracy | Mean absolute error | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending | pending |

| Perturbation | Cloud BOA | Shadow BOA | Source |
| :--- | :---: | :---: | :---: |
| v2 pending | pending | pending | pending |

---

## 14. Quantisation

Scored with ONNX Runtime on the validation split; INT8 calibrated on training patches (`export.calibration_patches` of the config).

| Format | File size in bytes | Mean IoU | False discard rate at 50 percent | Source |
| :--- | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending |

INT8 change against FP32 for every exported run, on the validation split:

| Run | FP32 mean IoU | INT8 mean IoU | Change | FP32 false discard rate | INT8 false discard rate | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending |

[SPEC.md](SPEC.md), section 10, says that a drop of more than one point in mean IoU is reported and that quantisation-aware training is proposed. An export passes when the ONNX FP32 logits differ from PyTorch by at most 0.01 and the predicted class agrees on at least 0.999 of the pixels (`[export]` of the config).

---

## 15. Hardware

| Engine | Latency p50 | Latency p99 | Tiles per second | Energy per tile | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Jetson Orin, FP16 | not measured | not measured | not measured | not measured | n/a |
| Jetson Orin, INT8 | not measured | not measured | not measured | not measured | n/a |

---

## 16. Compute used

CSC bills GPU and CPU jobs in different units, so they are listed in two tables. GPU billing is 200 GPU BU per GPU hour ([CSC billing](https://docs.csc.fi/computing/hpc-billing/)); GPU hours are the elapsed time in seconds divided by 3,600, rounded half up.

| Job | Name | Run and task | State | Elapsed (hh:mm:ss) | GPU hours | GPU BU | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending | pending | pending |

| Job | Task | State | Elapsed (hh:mm:ss) | Source |
| :--- | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending |

---

## 17. Training notes

None yet; v2 pending.

---

## 18. Limitations

- Training and validation data is Sentinel-2 Level-1C at 10 m ground sampling only; no data from Tiefer's target sensors is used. Tiefer's target sensors are very high resolution, where clouds and shadows look different.
- Sensor robustness is simulated on Sentinel-2 (rescaling, gain, offset, noise and blur); a robustness result is evidence about those perturbations, not about a real sensor.
- Every result holds for the band set and model size stated next to it. The L1 models use four bands (blue, green, red, near infrared); the band-flexible L2 model is scored per band set.
- Thin cloud and cloud shadow are hard to label even for people, which bounds what any model can score on them; the CloudSEN12 paper reports a human-level median BOA of 0.99 for cloud and 0.99 for cloud shadow, and a producer's accuracy of 0.780 for thin cloud between the labels before and after its quality control, on its 975 test patches and the labels of the 2022 release, not on this repository's revision (docs/DATA.md, section 3).
- The test split is independent of the training patches, not of the dataset: it shares the labelling protocol, sensor and processing level (docs/DATASETS.md).
- Only 509 x 509 patches are used; the 2000 x 2000 patches are left out (docs/DATA.md, section 5).
- The cached patches are 512 x 512 and hold the dataset's padding; it is masked when the labels are loaded, so no metric counts it. The sides of the padding are an assumption until the padding check has run on the caches (docs/DATA.md, sections 5 and 13).
- The data is public Level-1C top-of-atmosphere reflectance, not raw onboard data with its own calibration, noise and compression.
- No space environment effects are covered: radiation, vacuum and thermal behaviour of the onboard computer are not tested.
- Hardware measurements, when present, come from an NVIDIA Jetson Orin, which is flight-like reference hardware, not flight hardware.
- No agency or operator standard is claimed to be met; docs/STANDARDS.md lists the documents and their status.

---

## 19. How to reproduce

| Run | Config | Seed | Commit | Cache | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v2 pending | pending | pending | pending | pending | pending |

Check out the commit of the run first, then run the steps. Locally, one command per step:

```bash
git checkout <commit>
uv run python -m tiefer_lab.data.build_cache --split all
uv run python -m tiefer_lab.data.build_cache --split all --name cloudsen12-l1c-all --bands all
uv run python -m tiefer_lab.train --config configs/<config>.toml --seed <seed>
uv run python -m tiefer_lab.evaluate --run <run-id> --split val --band-set all --baselines
uv run python -m tiefer_lab.evaluate --run <run-id> --split val --band-set all --perturb blur=1
uv run python -m tiefer_lab.evaluate --run <run-id> --split test --band-set all --baselines --final --reason "<why>"
uv run python -m tiefer_lab.export --run <run-id> --band-set all
```

On CSC Roihu, the same steps run as Slurm jobs from `roihu-gpu.csc.fi` ([hpc/roihu/README.md](../hpc/roihu/README.md)); the 13-band cache is built from `roihu-cpu.csc.fi` as described there:

```bash
git checkout <commit>
SEED=<seed> bash hpc/roihu/submit.sh hpc/roihu/train.sbatch configs/<config>.toml
bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
ROBUSTNESS=1 bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
FINAL=1 REASON="<why>" bash hpc/roihu/submit.sh hpc/roihu/evaluate.sbatch <run-id>
bash hpc/roihu/submit.sh hpc/roihu/export.sbatch <run-id>
bash hpc/roihu/usage.sh <job-id>
bash hpc/roihu/collect.sh <run-id>
```

Then copy the report files into `reports/` unchanged and their values into this page by hand.

---

## 20. Values pending

Every value on this page waits for the v2 campaign ([hpc/roihu/plan.md](../hpc/roihu/plan.md)).

---

## Appendix A. Report files

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: every table of measured values says that it counts padded pixels and that re-evaluation is pending; section 21 lists every run, split and band set to evaluate again with the padding masked, with the old value and the new value pending. No value is changed.
- 7 October 2026: section 2 links BENCHMARK-AUTHORITY.md and POLICY.md for how values may be used and cited; no value changes.
- 7 October 2026: section 18 says that every metric counts the padded pixels of the 512 x 512 cached patches.
- 7 October 2026: restructured to the results page of docs/STYLE.md: source cells as `key (kind)` with a source column in every table, the source-key grammar, half-up rounding, UTC times, thousands separators and GiB stated once.
- 7 October 2026: wide tables split by topic: metrics by split, reference algorithms, cloud and shadow accuracy, sensor robustness and calibration.
- 7 October 2026: section 10 lists every reference algorithm of the dataset with its status, all not measured.
- 7 October 2026: section 19 gives the commit of every run; section 20 lists every pending value with what resolves it.
- 7 October 2026: links to docs/DATA.md follow its new section numbers.
- 7 October 2026: section 2 names the former results generator without its module name (commit def30a4).
- 7 October 2026: sections 3 and 18 link the table of every L1 and L2 setting difference in docs/ASSUMPTIONS.md, section 6.
- 7 October 2026: section 18 gives the human agreement of the CloudSEN12 paper (Table 6) instead of "not yet verified".
- 7 October 2026: Appendix A says why the report files are not yet committed: the GPU maintenance of CSC Roihu that began on 6 October 2026.
- 7 October 2026: section 10 links docs/LANDSCAPE.md for the published values of other systems.
