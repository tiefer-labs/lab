<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Assumptions

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The assumptions behind milestones L1 and L2 about the target sensor, the data, training and the hardware, and when each one has to be revisited.

---

## 1. Sensor

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Milestone L1 uses four bands only: blue, green, red, near infrared (Sentinel-2 B02, B03, B04, B08) | Very high resolution optical satellites typically carry these four bands plus panchromatic, not the shortwave infrared bands that classic cloud algorithms use | a customer's exact sensor and band set are known |
| Milestone L2 also uses all 13 Level-1C bands: the band-flexible model reads any of them and is scored per band set (3, 4, 6 and 13 bands); the four-band specialist reads the four L1 bands; which cache its seed 0 run read is pending ([DATA.md](DATA.md), section 10) | Target sensors differ in their bands, and one model for all of them is simpler to qualify and update; whether it costs accuracy on four bands is measured against the specialist (section 7). The 13-band cache serves every band set (docs/DATA.md, section 10) | the product decision of section 7 is confirmed on validation |
| Sentinel-2 spectral responses stand in for the target sensor's | No public cloud dataset with labels exists for the target sensors | spectral response functions of the target sensor are available |
| 10 m ground sampling stands in for very high resolution | CloudSEN12+ is Sentinel-2 at 10 m; cloud and shadow texture look different at finer sampling | labelled very high resolution frames are available |
| The panchromatic band is not used | It is not in the training data | the target sensor and its onboard processing chain are known |

---

## 2. Data on board

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Top-of-atmosphere reflectance (Level-1C) is the closest public proxy for onboard data | There is no atmospheric correction on board | the onboard radiometric calibration chain is known |
| Onboard frames can be scaled to reflectance before the filter runs | The model is trained on reflectance normalised with training split statistics | the onboard data format (raw counts, bit depth, calibration on board or not) is known |
| A frame is processed as 512 x 512 pixel tiles | The exported model has a fixed 1 x 4 x 512 x 512 input; at 10 m a tile covers 5.12 km x 5.12 km | the sensor's frame size and the onboard tiling are known |
| Compression happens after the filter | The training data has no compression artefacts | the onboard compression and its position in the pipeline are known |

---

## 3. Decision

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| A frame is sent when its predicted cloud fraction (thick plus thin cloud) is below the operator's threshold, otherwise kept on board | A simple, explainable rule that an operator can set | operators state their own decision rules |
| Cloud shadow does not count towards the cloud fraction; it is reported separately | Shadowed ground can still be useful for some products | operators state whether shadow makes a frame useless |
| Thresholds of 30, 50 and 70 percent are evaluated; the configurable default is 50 percent | They span strict to lenient use; none is preferred before operators say so | an operator chooses a threshold |
| A false discard (a useful frame kept on board) is the most costly error | A kept frame is lost to the customer; a sent cloudy frame only costs downlink | operators state the cost of each error |

---

## 4. Hardware

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| An NVIDIA Jetson Orin is a flight-like reference, not flight hardware | It runs the same TensorRT software stack as candidate flight computers | the flight computer is chosen |
| Only operators that TensorRT handles well in INT8 are used | INT8 is the likely onboard precision | the flight computer's runtime is known |
| Radiation, vacuum and thermal effects are out of scope | They need hardware testing outside this repository | hardware qualification starts |

---

## 5. Software and data access

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| CloudSEN12+ is published in the TACO v1 format that `tacoreader` 0.5 reads | The [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) example uses `tacoreader` 0.5.3; 0.5.6 works on CSC Roihu | the card moves to a newer TACO format |
| The CSC PyTorch module on Roihu provides Python 3.12 or newer | The package requires Python 3.12 or newer; observed on Roihu on 1 October 2026: `python-pytorch/2.10` gives Python 3.12.12 on a GPU node ([GPU and ML guide](https://docs.csc.fi/support/tutorials/gpu-ml/)) | the module is updated or `python-pytorch/2.10` is removed |
| The legacy TorchScript ONNX exporter (`dynamo=False`) is available in the PyTorch version used | It needs no extra dependency; it works in PyTorch 2.14 with a deprecation warning | PyTorch removes it; then `onnxscript` would be needed, which requires the team's agreement |

---

## 6. Training

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Final runs train to the end of the cosine schedule (`patience` equal to `epochs`), and `best.pt` keeps the epoch with the best validation mean IoU | On Roihu on 2 October 2026, `l1_base` stopped early while the training loss was still falling: seed 0 at epoch 72 (best validation mean IoU 0.678 at epoch 57), seed 1 at epoch 36 (best 0.626 at epoch 21); source: training log of 2 October 2026, training-loop values, reports pending. On 3 October 2026, `l1_base` seed 0 stopped early again with its best epoch at 32 (its evaluation report, [RESULTS.md](RESULTS.md), section 17). Its cosine schedule is defined over 150 epochs, so patience 15 ended it long before the learning rate had decayed | a full run shows validation mean IoU falling for many epochs before the end |
| A linear warm-up of the learning rate (5 epochs) and an exponential moving average of the weights (decay 0.999) make validation steadier | Validation mean IoU moved by up to 0.10 between nearby epochs in the same runs; the learning rate 0.008 is scaled for a batch of 128. Both values are design choices, not measured optima | the `l1_full` runs show whether the swing is smaller; one change per run separates the effect of each |
| `l1_full` changes three settings of `l1_base` at once (warm-up, moving average, patience) | The GPU budget before the maintenance on 6 October 2026 favours one run that fixes the known problems; separating the three effects needs extra runs | the budget allows ablation runs |
| Every L2 config trains with batch 64 and learning rate 0.004; the L1 configs keep batch 128 and learning rate 0.008 | With 13 bands, `l2_flex_1m` ran out of GPU memory at batch 128 on one GH200 on 3 October 2026 (jobs 2000912 and 2000941; expandable segments in the allocator did not help). Batch and learning rate were halved together, following the linear scaling of the L1 configs (0.008 x 64 / 128), and that run finished (job 2000949). The whole L2 family uses the same values so that its results stay comparable; a difference between an L1 and an L2 result is therefore not caused by the model alone. `l2_spec_1m` seed 0 ran with batch 64 (session notes); its learning rate is pending until its run `config.toml` is read, so the configs hold 0.004 to be confirmed | an L2 run with batch 128 fits in memory, or the L1 and L2 results are compared at the same settings |

---

## 7. Product decision

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Product rule: the band-flexible model is the product if its validation mean IoU on the band set B02 B03 B04 B08 lies within the 95 percent bootstrap interval of the validation mean IoU of the four-band specialist of the same size (1 M), with as many seeds as are available for both; otherwise specialists are shipped per sensor | One model for every sensor is simpler to qualify and update, but not at a measurable cost in accuracy on the sensors that matter most | the first comparison of `l2_flex_1m` and `l2_spec_1m` on validation |
| Target sensors are optical satellites whose bands differ; high resolution satellites usually carry blue, green, red and near infrared only, for example SPOT-7 NAOMI ([eoPortal](https://directory.eoportal.org/web/eoportal/satellite-missions/s/spot-6-7), TODO(verify) the page) | Specifications of newer target satellites are not public, so nothing about them is assumed | a target sensor's specification is available |

Status on 7 October 2026: no decision is recorded yet. The rule is applied on validation, and the four-band validation mean IoU of `l2_flex_1m` seed 0 (`x-val-4`) is pending ([RESULTS.md](RESULTS.md), section 12). The test split never selects a model or a setting ([SPEC.md](SPEC.md), section 2, rule 5), so the test values (0.609 for `l2_flex_1m` seed 0, a session-notes value, against 0.720 [0.707, 0.732] for `l2_spec_1m` seed 0) are informational only. Both runs are a single seed.

---

## Changelog

- 7 October 2026: section 6 names the source of the early stops of 2 October 2026 (training log) and adds the stop of `l1_base` seed 0 on 3 October 2026.
- 7 October 2026: correction: section 7 states the product rule completely (mean IoU, validation, B02 B03 B04 B08, 1 M, seeds as available, the specialist's interval); no decision is recorded until `x-val-4` is read, and the test values are informational only.
- 7 October 2026: section 1 points to the cache table of DATA.md for the cache of `l2_spec_1m` seed 0, which is pending.
- 7 October 2026: correction: the learning rate of the `l2_spec_1m` run is pending; only `l2_flex_1m` is known to have used 0.004.
- 7 October 2026: section 1 says that L1 uses four bands and L2 also all 13; section 6 adds batch 64 and learning rate 0.004 for the L2 family, with the out-of-memory error that caused it; section 7 records the provisional outcome of the product decision.
- 2 October 2026: section 7, product decision between the band-flexible model and four-band specialists.
- 2 October 2026: section 6, training: run to the end of the schedule, warm-up and moving average, with the measured reason.
- 1 October 2026: the PyTorch module assumption is checked on Roihu.
- 1 October 2026: the TACO format assumption is checked against the dataset card, version 1.1.2.
- 1 October 2026: first version for milestone L1.
