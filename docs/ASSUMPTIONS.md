<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Assumptions

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The assumptions behind milestones L1 and L2 about the target sensor, the data, training and the hardware, the evidence for each, and when each one has to be revisited.

---

## 1. Sensor

Each row has an ID (`A-1.1`: section 1, row 1), the evidence (a source, or "none, design choice"), and a status in the words of [STYLE.md](STYLE.md), section 4: `open` (not yet tested), `confirmed` (tested, with evidence), `revisit due` (the trigger has happened) or `superseded`. "Last checked" is the date the row was last compared with its evidence. External sources are listed in section 8.

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-1.1` | Milestone L1 uses four bands: blue, green, red and near infrared (Sentinel-2 B02, B03, B04, B08) | very high resolution optical satellites, the target sensors, carry these four bands and a panchromatic band, not the shortwave infrared bands that classic cloud algorithms use | SPOT-6 and SPOT-7 NAOMI: one panchromatic band and four multispectral bands, blue, green, red and near infrared [1] | a customer's exact sensor and band set are known | open | 7 October 2026 |
| `A-1.2` | Milestone L2 also uses all 13 Level-1C bands: the band-flexible model reads any of them and is scored per band set (3, 4, 6 and 13 bands); the four-band specialist reads the four L1 bands | target sensors differ in their bands, and one model for all of them is simpler to qualify and update; whether it costs accuracy on four bands is measured against the specialist (section 7) | none, design choice | the product decision of section 7 is recorded | open | 7 October 2026 |
| `A-1.3` | B11 and B12 are the shortwave infrared bands of the 6-band set; B10 is not in it | the 6-band set stands for a sensor with blue, green, red, near infrared and two shortwave infrared bands | B11 1613.7 nm and B12 2202.4 nm on Sentinel-2A, both 20 m; B10 (1373.5 nm, 60 m) is the cirrus band [2] | n/a | confirmed | 7 October 2026 |
| `A-1.4` | Sentinel-2 spectral responses stand in for the target sensor's | no public cloud dataset with labels is known for the target sensors | the datasets checked are listed in [DATASETS.md](DATASETS.md) | spectral response functions of the target sensor are available | open | 7 October 2026 |
| `A-1.5` | 10 m ground sampling stands in for very high resolution | CloudSEN12+ is Sentinel-2 at 10 m to 60 m; cloud and shadow texture look different at finer sampling | [DATA.md](DATA.md), section 2.1 | labelled very high resolution frames are available | open | 7 October 2026 |
| `A-1.6` | The panchromatic band is not used | it is not in the training data | Sentinel-2 has no panchromatic band ([DATA.md](DATA.md), section 2.1) | the target sensor and its onboard processing chain are known | open | 7 October 2026 |
| `A-1.7` | Nothing is assumed about the bands of target satellites whose specifications are not public | an assumption without a source cannot be checked | none, design choice | a target sensor's specification is available | open | 7 October 2026 |

---

## 2. Data on board

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-2.1` | Top-of-atmosphere reflectance (Level-1C) is the closest public proxy for onboard data | there is no atmospheric correction on board | none, design choice | the onboard radiometric calibration chain is known | open | 7 October 2026 |
| `A-2.2` | Onboard frames can be scaled to reflectance before the filter runs | the model is trained on reflectance normalised with training split statistics | none, design choice | the onboard data format (raw counts, bit depth, calibration on board or not) is known | open | 7 October 2026 |
| `A-2.3` | The normalisation statistics of the Sentinel-2 training split transfer to the target sensor | the model sees inputs normalised with those statistics | none; the gain and offset perturbations of `src/tiefer_lab/data/sensor.py` are simulated on Sentinel-2 | labelled data of the target sensor is available | open | 8 October 2026 |
| `A-2.4` | Input shape: the L1 models and the four-band specialist take 1 x 4 x 512 x 512; the band-flexible model is exported as one file per band set, 1 x N x 512 x 512 with N the number of bands of the set | the export input is fixed; at 10 m a tile covers 5.12 km x 5.12 km | `[export]` of the configs: opset 17, input size 512; `REQ-EXP-02` ([REQUIREMENTS.md](REQUIREMENTS.md), section 5) | the sensor's frame size and the onboard tiling are known | open | 8 October 2026 |
| `A-2.5` | A larger frame is resampled to 10 m and processed in 512-pixel tiles overlapping by 64 pixels; the logits are averaged where tiles overlap | a tile edge has less context than its centre | `src/tiefer_lab/onboard.py` (`overlap = 64`); `REQ-OBD-04` | the sensor's frame size and the onboard tiling are known | open | 7 October 2026 |
| `A-2.6` | Operational design domain: top-of-atmosphere reflectance in [0, 2], ground sampling 0.5 to 20 m, at most 1 percent invalid pixels, at least 32 pixels per side; a frame outside it is sent and flagged | outside the domain the filter is not validated, and a doubtful frame costs downlink, never a lost frame | `tiefer_lab.onboard.Domain` and [SPEC.md](SPEC.md), section 9; validated on Sentinel-2 Level-1C at 10 m only | data of another sensor is evaluated | open | 7 October 2026 |
| `A-2.7` | Compression happens after the filter | the training data has no compression artefacts | none, design choice | the onboard compression and its position in the pipeline are known | open | 7 October 2026 |

---

## 3. Decision

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-3.1` | A frame is sent when its predicted cloud fraction (thick plus thin cloud) is below the operator's threshold, otherwise kept on board | an operator can set and check the rule with one number | none, design choice | operators state their own decision rules | open | 7 October 2026 |
| `A-3.2` | Cloud shadow does not count towards the cloud fraction; it is reported separately | shadowed ground can still be useful for some products | none, design choice | operators state whether shadow makes a frame useless | open | 7 October 2026 |
| `A-3.3` | Thresholds of 30, 50 and 70 percent are evaluated; the configurable default is 50 percent | they span strict to lenient use; none is preferred before operators say so | none, design choice; `decision_threshold = 0.5` in `src/tiefer_lab/config.py` | an operator chooses a threshold | open | 7 October 2026 |
| `A-3.4` | A false discard (a useful frame kept on board) is the most costly error | a kept frame is lost to the customer; a sent cloudy frame only costs downlink | none, design choice | operators state the cost of each error | open | 7 October 2026 |

---

## 4. Hardware

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-4.1` | An NVIDIA Jetson Orin is a flight-like reference, not flight hardware | the same module family flies on Planet Pelican-4 and EDGX Sterna | [LANDSCAPE.md](LANDSCAPE.md), section 3; the sources do not name the exact Orin module | the flight computer is chosen | open | 7 October 2026 |
| `A-4.2` | Only operators that TensorRT handles well in INT8 are used | INT8 is the likely onboard precision | none yet; checked in v2 | the flight computer's runtime is known, or INT8 loses more than one point of mean IoU | open | 8 October 2026 |
| `A-4.3` | Radiation, vacuum and thermal effects are out of scope | they need hardware testing outside this repository | none, design choice | hardware qualification starts | open | 7 October 2026 |

---

## 5. Software and data access

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-5.1` | CloudSEN12+ is published in the TACO v1 format that `tacoreader` 0.5 reads | the card's example uses `tacoreader` 0.5.3; the lock holds 0.5.6 | dataset card 1.1.2 [3]; the read with the locked 0.5.6 is checked in v2 | the card moves to a newer TACO format | open | 8 October 2026 |
| `A-5.2` | The CSC PyTorch module on Roihu provides Python 3.12 or newer | the package requires Python 3.12 or newer | observed on Roihu on 1 October 2026: `python-pytorch/2.10` gives Python 3.12.12 on a GPU node [4] | the module is updated or `python-pytorch/2.10` is removed | confirmed | 1 October 2026 |
| `A-5.3` | Results do not depend on the PyTorch version: the lock holds torch 2.14.1 for local checks and CI, while the jobs on Roihu use the CSC module, torch 2.10.0+cu130 | the CSC module is built for the GH200 nodes; `hpc/roihu/env.sh` loads it for every job | none yet; checked in v2 | a result is reproduced with another PyTorch version | open | 8 October 2026 |
| `A-5.4` | The legacy TorchScript ONNX exporter (`dynamo=False`) is available in the PyTorch versions used | it needs no extra dependency | `tests/test_export.py` passes with torch 2.14.1 (with a deprecation warning); with 2.10.0+cu130 on Roihu none yet; checked in v2 | PyTorch removes it; then `onnxscript` would be needed, which requires the team's agreement | open | 8 October 2026 |
| `A-5.5` | The dataset padded each 509 x 509 patch to 512 x 512 on the left and bottom sides, so the left 3 columns and the bottom 3 rows of a cached patch are padding (`PADDING_SIDES` in `src/tiefer_lab/data/padding.py`) | the labels are masked at load time on these sides; the width comes from `real_proj_shape` and the stored size of each patch | dataset card 1.1.2 [3]; not yet checked on a cache | `python -m tiefer_lab.data.cache padding` runs on `cloudsen12-l1c-high` and `cloudsen12-l1c-all`, validation and test ([DATA.md](DATA.md), section 13) | open | 7 October 2026 |

---

## 6. Training

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-6.1` | The dense high quality labels of CloudSEN12+ are the ground truth | no other labels exist for these patches | the labels are not perfect: producer's accuracy 0.780 for thin cloud between the labels before and after quality control ([DATA.md](DATA.md), section 3) | labels of another source are available for the same patches | open | 7 October 2026 |
| `A-6.2` | The training, validation and test splits are independent by location | a shared location would inflate validation and test results | not checked: the location field is an open fact ([DATA.md](DATA.md), section 6.4) | the overlap check runs on the built caches | open | 7 October 2026 |
| `A-6.3` | 509 x 509 patches stand in for 2000 x 2000 patches and for larger frames | the export input is fixed at 512 x 512 | none, design choice ([DATA.md](DATA.md), section 5) | the 2000 x 2000 patches are evaluated | open | 7 October 2026 |
| `A-6.4` | Final runs train to the end of the cosine schedule (`patience` equal to `epochs`), and `best.pt` keeps the epoch with the best validation mean IoU | an early stop can end a run while its training loss is still falling, long before the cosine schedule has decayed the learning rate | none yet; checked in v2 | a full run shows validation mean IoU falling for many epochs before the end | open | 8 October 2026 |
| `A-6.5` | A linear warm-up of the learning rate (5 epochs) and an exponential moving average of the weights (decay 0.999) make validation steadier | validation mean IoU can swing between nearby epochs | none, design choice; the values are not measured optima; checked in v2 | the per-epoch validation values of the v2 runs show whether the swing is smaller | open | 8 October 2026 |
| `A-6.6` | `l1_full` changes three settings of `l1_base` at once (warm-up, moving average, patience) | one run that changes the three settings costs less GPU time than three ablation runs | none, design choice | the budget allows ablation runs | open | 8 October 2026 |
| `A-6.7` | Every L2 config trains with batch 64 and learning rate 0.004; the L1 configs keep batch 128 and learning rate 0.008 | 13 bands at batch 128 may not fit in the memory of one GH200; batch size and learning rate are halved together, following the linear scaling of the L1 configs (0.008 x 64 / 128), and the whole L2 family uses the same values so that its results stay comparable | none yet; checked by the v2 timing run | an L2 run with batch 128 fits in memory, or the L1 and L2 results are compared at the same settings | open | 8 October 2026 |
| `A-6.8` | One seed is enough for a provisional decision | the GPU budget limits the number of seeds per config | none yet; checked in v2 | three seeds of the final pair are run | open | 8 October 2026 |
| `A-6.9` | The placeholder design for missing bands is chosen over the zero design on validation | the choice is measured, not assumed | none, design choice; `configs/l2_flex_1m_zero.toml` has not run | `l2_flex_1m_zero` is evaluated on validation | open | 7 October 2026 |
| `A-6.10` | L1 weights the loss by median class frequency; L2 does not | the L2 configs keep one change per variant, and `l2_flex_1m_classweights` measures the weighting | none, design choice; `l2_flex_1m_classweights` has not run | `l2_flex_1m_classweights` is evaluated on validation | open | 7 October 2026 |

Every setting in which the L1 and L2 configs differ, as the configs and the defaults of `src/tiefer_lab/config.py` resolve them:

| Setting | `l1_base` | `l1_full` | L2 band-flexible (`l2_flex_*`) | L2 specialists (`l2_spec_*`) |
| :--- | :---: | :---: | :---: | :---: |
| Input bands | 4, fixed | 4, fixed | 13, one band set drawn per batch | 4, fixed |
| Cache (`data.cache_name`) | `cloudsen12-l1c-high` | `cloudsen12-l1c-high` | `cloudsen12-l1c-all` | `cloudsen12-l1c-all` |
| Widths of the network | 16 to 256 | 16 to 256 | 24 to 384 (0.5 M), 32 to 512 (1 M), 64 to 1024 (4 M), larger for 21 M and 22 M | 32 to 512 (1 M), 160 to 2560 (22 M) |
| Batch size | 128 | 128 | 64 | 64 |
| Learning rate | 0.008 | 0.008 | 0.004 | 0.004 |
| Warm-up epochs | 0 | 5 | 5 | 5 |
| Moving average of the weights (`ema_decay`) | none (0.0) | 0.999 | 0.999 | 0.999 |
| Patience | 15 | 150 | 150 | 150 |
| Class weighting | `median_frequency`, the default of `config.py`; not set in the file | `median_frequency`, the default; not set in the file | `none`, except `l2_flex_1m_classweights`: `median_frequency` | `none` |
| Self-distillation (`distill_weight`) | 0.0 | 0.0 | 1.0, except `l2_flex_1m_nodistill`: 0.0 | 0.0 |
| `load_mode` | `auto` | `auto` | `memory` for `l2_flex_1m` and its single-change variants; `auto` for the other sizes | `auto` |

Settings not listed are the same in every config (crop 256, weight decay 0.0001, Dice weight 1.0, minimum improvement 0.001, 150 epochs, brightness and contrast augmentation 0.1). A difference between an L1 and an L2 result can come from any row of this table, not from the model alone.

---

## 7. Product decision

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-7.1` | Product rule: the band-flexible model is the product if its validation mean IoU on the band set B02 B03 B04 B08 lies within the 95 percent bootstrap interval of the validation mean IoU of the four-band specialist of the same size (1 M), with as many seeds as are available for both; otherwise specialists are shipped per sensor | one model for every sensor is simpler to qualify and update, but not at a measurable cost in accuracy on the sensors that matter most | none, design choice | the first comparison of `l2_flex_1m` and `l2_spec_1m` on validation | open | 7 October 2026 |

Status: no decision is recorded. The rule is applied on validation only; the test split never selects a model or a setting ([SPEC.md](SPEC.md), section 2, rule 5).

---

## 8. Sources

1. SPOT-6 and SPOT-7, eoPortal, https://www.eoportal.org/satellite-missions/spot-6-7, accessed 7 October 2026.
2. S2 Mission, spectral and spatial resolution, ESA SentiWiki, https://sentiwiki.copernicus.eu/web/s2-mission, accessed 7 October 2026.
3. CloudSEN12+ dataset card, version 1.1.2, TACO Foundation, Hugging Face, https://huggingface.co/datasets/tacofoundation/cloudsen12, accessed 7 October 2026.
4. GPU and ML guide, CSC, https://docs.csc.fi/support/tutorials/gpu-ml/, accessed 1 October 2026.

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: `A-5.5`, the sides of the dataset's padding, an assumption until the padding check runs on CSC Roihu.
- 7 October 2026: every row has an ID, evidence, a status and the date it was last checked; rows without a source say "none, design choice".
- 7 October 2026: one band statement in `A-1.1`, checked against the SPOT-6 and SPOT-7 page of eoPortal (a `TODO(verify)` resolved); the row on target sensors moved from section 7 to section 1 (`A-1.7`).
- 7 October 2026: new rows: B11 and B12 (`A-1.3`), normalisation transfer (`A-2.3`), input shapes (`A-2.4`), tile overlap (`A-2.5`), operational design domain (`A-2.6`), PyTorch versions (`A-5.3`), labels as ground truth (`A-6.1`), split independence (`A-6.2`), patch size (`A-6.3`), one seed (`A-6.8`), input design (`A-6.9`) and class weighting (`A-6.10`).
- 7 October 2026: the decision rule's reason no longer uses adjectives; links are relative.
- 7 October 2026: section 6 lists every setting in which the L1 and L2 configs differ, as resolved by the configs and the defaults of `config.py`.
- 2 October 2026: section 7, product decision between the band-flexible model and four-band specialists.
- 2 October 2026: section 6, training: run to the end of the schedule, warm-up and moving average, with the measured reason.
- 1 October 2026: the PyTorch module assumption is checked on Roihu.
- 1 October 2026: the TACO format assumption is checked against the dataset card, version 1.1.2.
- 1 October 2026: first version for milestone L1.
