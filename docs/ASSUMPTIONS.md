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
| `A-1.8` | Landsat 8 OLI bands are named after the Sentinel-2 band of the closest centre wavelength and width: band 1 B01, 2 B02, 3 B03, 4 B04, 5 (865 nm, narrow) B8A, 6 B11, 7 B12, 9 (cirrus) B10 | the band-flexible model reads Sentinel-2 band names; the decision of the open fact of [DATASETS.md](DATASETS.md), section 3 | none, design choice; the numeric tolerance stays open; `LANDSAT8_TO_S2` in `src/tiefer_lab/data/independent.py` | the first Landsat 8 evaluation is read, or the Landsat 8 band specification is cited here | open | 14 October 2026 |
| `A-1.9` | A four-band model run on Landsat 8 reads band 5 in place of B08; such a result is a substitution, reported apart from the band-flexible model run with B8A | the four-band models were trained on B08 (842 nm, wide); Landsat 8 has no band at that position | none, design choice; `evaluate --substitute` records it in the report | the substitution and the B8A run are compared | open | 14 October 2026 |
| `A-1.10` | A learned Sentinel-2 reference algorithm of the paper's Table 6 may run on Landsat 8 through the band names of `A-1.8` and the B08 substitution of `A-1.9`, only when every input band it reads is then available, and such a result is reported apart as a substitution; Sentinel-2 processors and product bands (Sen2Cor, QA60) never run on Landsat 8 | the coverage of `reports/coverage.md` then names a route for every learned algorithm on Landsat 8 instead of ruling it out by sensor alone | none, design choice; `route` in `src/tiefer_lab/paper_models.py`; no input band list of these algorithms is verified yet, so every such route is `open` | the input bands of an algorithm are verified, or the maintainer rules cross-sensor reference runs out | open | 15 October 2026 |

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
| `A-2.8` | On an independent dataset a patch is a non-overlapping 509 x 509 tile cut from the top left after resampling to 10 m, and a tile with more than 0.1 unlabelled pixels is dropped; the native resolution is evaluated as a perturbation | 509 x 509 at 10 m is the CloudSEN12 patch, so per-patch medians stay comparable; the onboard filter resamples to 10 m (`tiefer_lab.onboard.predict_frame`) | none, design choice; a protocol decision proposed in a method-change issue; [INDEPENDENT.md](INDEPENDENT.md), section 4 | the maintainer agrees or changes it in that issue | open | 14 October 2026 |
| `A-2.9` | On 95-Cloud only the 57 scenes it adds to 38-Cloud are scored, and on 38-Cloud only its 20 test scenes and 18 training scenes with entire-scene masks | 95-Cloud holds every 38-Cloud scene (95-Cloud README; Cloud-Net+ paper), so scoring both whole would count 38 scenes twice | none, design choice; `DATASETS["landsat8_95cloud"].note` in `src/tiefer_lab/data/independent.py` | a later licence decision allows 38-Cloud or 95-Cloud ([DATASETS.md](DATASETS.md), section 1.1); until then neither is used | open | 15 October 2026 |
| `A-2.10` | Azersky (SPOT 7, Azercosmos) scenes, if data arrives, are resampled from their verified ground sampling to 10 m by the existing path of the independent datasets (`tiefer_lab.data.independent.resample`, as `A-2.8`), and their native resolution is evaluated only as the `rescale` perturbation | the models are trained at 10 m, and the same path keeps Azersky comparable with the other independent datasets; the multispectral ground sampling is stated as 6 m but not verified | none, design choice (maintainer decision of 17 October 2026); `src/tiefer_lab/data/azersky.py` | the ground sampling is verified from the DIMAP metadata of a delivered product | open | 17 October 2026 |
| `A-2.11` | Azersky labels are made by Tiefer from scratch, not by correcting the output of any model, in the class scheme of CloudSEN12: clear, thick cloud, thin cloud, cloud shadow | labels corrected from a model's output would carry that model's errors into the test, and the same classes keep it comparable with CloudSEN12+ | none, decision of the maintainer of 17 October 2026; `LABEL_CLASSES` of `src/tiefer_lab/data/azersky.py` | the data agreement with Azercosmos states what may be labelled | open | 17 October 2026 |

---

## 3. Decision

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-3.1` | A frame is sent when its predicted cloud fraction (thick plus thin cloud) is below the operator's threshold, otherwise kept on board | an operator can set and check the rule with one number | none, design choice | operators state their own decision rules | open | 7 October 2026 |
| `A-3.2` | Cloud shadow does not count towards the cloud fraction; it is reported separately | shadowed ground can still be useful for some products | none, design choice | operators state whether shadow makes a frame useless | open | 7 October 2026 |
| `A-3.3` | Thresholds of 30, 50 and 70 percent are evaluated; the configurable default is 50 percent | they span strict to lenient use; none is preferred before operators say so | none, design choice; `decision_threshold = 0.5` in `src/tiefer_lab/config.py` | an operator chooses a threshold | open | 7 October 2026 |
| `A-3.4` | A false discard (a useful frame kept on board) is the most costly error | a kept frame is lost to the customer; a sent cloudy frame only costs downlink | none, design choice | operators state the cost of each error | open | 7 October 2026 |
| `A-3.5` | A cloud logit bias chosen on validation (the value closest to 0 with a false discard rate of at most 0.01 and 1 minus the false send rate of at least 0.90) may be folded into the model; the decision threshold stays at 50 percent | it moves the model's errors towards the cheaper one without a new operator; it is chosen for a frame target, so its cost in cloud BOA and mean IoU is reported | none, design choice; a protocol option, off by default (`python -m tiefer_lab.calibrate`, `evaluate --cloud-bias`), chosen on the CPU | the maintainer decides in [issue 21](https://github.com/tiefer-labs/lab/issues/21) | open | 16 October 2026 |
| `A-3.6` | The predicted cloud fraction may be the mean cloud probability at a temperature fitted on validation instead of the share of argmax cloud pixels | a soft fraction does not jump at the class boundary of thin cloud; the temperature does not change the argmax | none, design choice; a protocol option, off by default (`evaluate --fraction soft`); not yet in the onboard code, which needs an export with cloud probabilities | the maintainer decides in [issue 22](https://github.com/tiefer-labs/lab/issues/22) | open | 16 October 2026 |

---

## 4. Hardware

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-4.1` | An NVIDIA Jetson Orin is a flight-like reference, not flight hardware | the same module family flies on Planet Pelican-4 and EDGX Sterna | [LANDSCAPE.md](LANDSCAPE.md), section 3; the sources do not name the exact Orin module | the flight computer is chosen | open | 7 October 2026 |
| `A-4.2` | Only operators that TensorRT handles well in INT8 are used | INT8 is the likely onboard precision | none yet; checked in Project Schatten | the flight computer's runtime is known, or INT8 loses more than one point of mean IoU | open | 8 October 2026 |
| `A-4.3` | Radiation, vacuum and thermal effects are out of scope | they need hardware testing outside this repository | none, design choice | hardware qualification starts | open | 7 October 2026 |

---

## 5. Software and data access

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-5.1` | CloudSEN12+ is published in the TACO v1 format that `tacoreader` 0.5 reads | the card's example uses `tacoreader` 0.5.3; the lock holds 0.5.6 | dataset card 1.1.2 [3]; the read with the locked 0.5.6 is checked in Project Schatten | the card moves to a newer TACO format | open | 8 October 2026 |
| `A-5.2` | The CSC PyTorch module on Roihu provides Python 3.12 or newer | the package requires Python 3.12 or newer | observed on Roihu on 1 October 2026, before Project Schatten: `python-pytorch/2.10` gave Python 3.12.12 on a GPU node [4]; the scripts keep this module, and step 0 (setup) of [hpc/roihu/plan.md](../hpc/roihu/plan.md) confirms it for Project Schatten | step 0 has run, or the module is updated or `python-pytorch/2.10` is removed | open | 15 October 2026 |
| `A-5.3` | Results do not depend on the PyTorch version: the lock holds torch 2.14.1 for local checks and CI, while the jobs on Roihu use the CSC module, torch 2.10.0+cu130 | the CSC module is built for the GH200 nodes; `hpc/roihu/env.sh` loads it for every job | none yet; checked in Project Schatten | a result is reproduced with another PyTorch version | open | 8 October 2026 |
| `A-5.4` | The legacy TorchScript ONNX exporter (`dynamo=False`) is available in the PyTorch versions used | it needs no extra dependency | `tests/test_export.py` passes with torch 2.14.1 (with a deprecation warning); with 2.10.0+cu130 on Roihu none yet; checked in Project Schatten | PyTorch removes it; then `onnxscript` would be needed, which requires the team's agreement | open | 8 October 2026 |
| `A-5.5` | The dataset padded each 509 x 509 patch to 512 x 512 on the left and bottom sides, so the left 3 columns and the bottom 3 rows of a cached patch are padding (`PADDING_SIDES` in `src/tiefer_lab/data/padding.py`) | the labels are masked at load time on these sides; the width comes from `real_proj_shape` and the stored size of each patch | dataset card 1.1.2 [3]; not yet checked on a cache | `python -m tiefer_lab.data.cache padding` runs on `cloudsen12-l1c-high` and `cloudsen12-l1c-all`, validation and test ([DATA.md](DATA.md), section 13) | open | 7 October 2026 |
| `A-5.6` | Third-party sources are used only as the maintainer's licence decisions of 15 October 2026 allow: S2-Hollstein, L8-38Cloud, L8-95Cloud, S2-CESBIO and the Copernicus imagery for S2-Hollstein and S2-CESBIO are not used; dtacs4bands and the CloudSEN12 release of 2022 are declined, pending legal review; WHUS2-CD+, L8 Biome and L8 SPARCS are candidates without a decision; all are treated as not used. The Sentinel-2 Cloud Mask Catalogue and KappaSet are used. A source without a recorded decision is not read | a non-commercial or unstated licence, or a download that needs credentials, is not used without a decision | the decision table of [DATASETS.md](DATASETS.md), section 1.1, recorded in the licence decision [issue 7](https://github.com/tiefer-labs/lab/issues/7); `LicenceDecision` in `src/tiefer_lab/data/source.py` | the maintainer records a later decision for one of these sources | confirmed | 15 October 2026 |
| `A-5.7` | The project's `/scratch` quota on Roihu is 500 GiB and 1,000,000 files; the plan keeps its peak use under 450 GiB | the quota bounds the caches, downloads and runs held at once; storage is billed on the space used, not the quota | maintainer input from MyCSC, 17 October 2026, after an approved increase; [hpc/roihu/plan.md](../hpc/roihu/plan.md), section 3.8 | the quota changes in MyCSC | open | 17 October 2026 |
| `A-5.8` | The project's `/projappl` quota on Roihu is 50 GiB and 200,000 files; the Python environments stay plain venvs while together under 35 GiB and 150,000 files, and move to Tykky containers above | the environments, the source and the candidates' run folders live there | maintainer input from MyCSC, 17 October 2026; the measured environments of [hpc/roihu/plan.md](../hpc/roihu/plan.md), section 3.8, and the sizes the setup jobs print | the setup jobs of step 0 print the real sizes, or the quota changes | open | 17 October 2026 |

---

## 6. Training

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-6.1` | The dense high quality labels of CloudSEN12+ are the ground truth | no other labels exist for these patches | the labels are not perfect: producer's accuracy 0.780 for thin cloud between the labels before and after quality control ([DATA.md](DATA.md), section 3) | labels of another source are available for the same patches | open | 7 October 2026 |
| `A-6.2` | The training, validation and test splits are independent by location | a shared location would inflate validation and test results | not checked: the location field is an open fact ([DATA.md](DATA.md), section 6.4) | the overlap check runs on the built caches | open | 7 October 2026 |
| `A-6.3` | 509 x 509 patches stand in for 2000 x 2000 patches and for larger frames | the export input is fixed at 512 x 512 | none, design choice ([DATA.md](DATA.md), section 5) | the 2000 x 2000 patches are evaluated | open | 7 October 2026 |
| `A-6.4` | Final runs train to the end of the cosine schedule (`patience` equal to `epochs`), and `best.pt` keeps the epoch with the best validation mean IoU | an early stop can end a run while its training loss is still falling, long before the cosine schedule has decayed the learning rate | none yet; checked in Project Schatten | a full run shows validation mean IoU falling for many epochs before the end | open | 8 October 2026 |
| `A-6.5` | A linear warm-up of the learning rate (5 epochs) and an exponential moving average of the weights (decay 0.999) make validation steadier | validation mean IoU can swing between nearby epochs | none, design choice; the values are not measured optima; checked in Project Schatten | the per-epoch validation values of the Project Schatten runs show whether the swing is smaller | open | 15 October 2026 |
| `A-6.6` | `sieb` changes three settings of `sieb_base` at once (warm-up, moving average, patience) | one run that changes the three settings costs less GPU time than three ablation runs | none, design choice | the budget allows ablation runs | open | 8 October 2026 |
| `A-6.7` | Every L2 config trains with batch 64 and learning rate 0.004; the L1 configs keep batch 128 and learning rate 0.008 | 13 bands at batch 128 may not fit in the memory of one GH200; batch size and learning rate are halved together, following the linear scaling of the L1 configs (0.008 x 64 / 128), and the whole L2 family uses the same values so that its results stay comparable | none yet; checked by a Project Schatten timing run | an L2 run with batch 128 fits in memory, or the L1 and L2 results are compared at the same settings | open | 8 October 2026 |
| `A-6.8` | One seed is enough for a provisional decision | the GPU budget limits the number of seeds per config | none yet; checked in Project Schatten | three seeds of the final pair are run | open | 8 October 2026 |
| `A-6.9` | The placeholder design for missing bands is chosen over the zero design on validation | the choice is measured, not assumed | none, design choice; `configs/wandler_1m_zero_design.toml` has not run | `wandler_1m_zero_design` is evaluated on validation | open | 7 October 2026 |
| `A-6.10` | L1 weights the loss by median class frequency; L2 does not | the L2 configs keep one change per variant, and `wandler_1m_class_weights` measures the weighting | none, design choice; `wandler_1m_class_weights` has not run | `wandler_1m_class_weights` is evaluated on validation | open | 7 October 2026 |
| `A-6.11` | The one-change variants run one seed each; the candidate references run three | the GPU budget allows one seed per variant; ACC-09 needs three seeds of the reference | none, design choice | a variant's gain is smaller than the seed spread of its reference | open | 14 October 2026 |
| `A-6.12` | Export-only variants (`*_int8_percentile`, `*_int8_entropy`, `*_int8_calib1024`, `*_int8_calib_stratified`, `*_int8_float_ends`, `*_int8_input_clip`) reuse the trained run of their reference with `export --settings-from` | their change is in `[export]` only, so training them again would cost GPU time for the same weights | none, design choice | n/a | open | 14 October 2026 |
| `A-6.13` | The CloudScout re-implementation (re-implementation trained by Tiefer Lab, not the flown model) uses widths 16, 32, 64, 128, 128 (about 0.63 M parameters), whole 512 x 512 patches at 10 m, Level-1C reflectance and this repository's schedule | the CloudScout paper gives no filter numbers, used 512 x 512 tiles at 60 m of radiance, and an exponential learning rate decay | the paper, Remote Sensing 12(14), 2205, 2020, sections 3.3 and 3.4, read on 14 October 2026 [5] | the authors publish the filter numbers | open | 14 October 2026 |

Every setting in which the L1 and L2 configs differ, as the configs and the defaults of `src/tiefer_lab/config.py` resolve them:

| Setting | `sieb_base` | `sieb` | L2 band-flexible (`wandler_*`) | L2 specialists (`lupe_*`) |
| :--- | :---: | :---: | :---: | :---: |
| Input bands | 4, fixed | 4, fixed | 13, one band set drawn per batch | 4, fixed |
| Cache (`data.cache_name`) | `cloudsen12-l1c-high` | `cloudsen12-l1c-high` | `cloudsen12-l1c-all` | `cloudsen12-l1c-all` |
| Widths of the network | 16 to 256 | 16 to 256 | 24 to 384 (0.5 M), 32 to 512 (1 M), 64 to 1024 (4 M), larger for 21 M and 22 M | 32 to 512 (1 M), 160 to 2560 (22 M) |
| Batch size | 128 | 128 | 64 | 64 |
| Learning rate | 0.008 | 0.008 | 0.004 | 0.004 |
| Warm-up epochs | 0 | 5 | 5 | 5 |
| Moving average of the weights (`ema_decay`) | none (0.0) | 0.999 | 0.999 | 0.999 |
| Patience | 15 | 150 | 150 | 150 |
| Class weighting | `median_frequency`, the default of `config.py`; not set in the file | `median_frequency`, the default; not set in the file | `none`, except `wandler_1m_class_weights`: `median_frequency` | `none` |
| Self-distillation (`distill_weight`) | 0.0 | 0.0 | 1.0, except `wandler_1m_no_self_distill`: 0.0 | 0.0 |
| `load_mode` | `auto` | `auto` | `memory` for `wandler_1m` and its single-change variants; `auto` for the other sizes | `auto` |

Settings not listed are the same in every config (crop 256, weight decay 0.0001, Dice weight 1.0, minimum improvement 0.001, 150 epochs, brightness and contrast augmentation 0.1). A difference between an L1 and an L2 result can come from any row of this table, not from the model alone.

The candidate references and stages, which change more than one setting of their reference; each is its own reference config. The candidate references are drafts: before step 7b of [hpc/roihu/plan.md](../hpc/roihu/plan.md) each is filled from the step 7 winners of its family, nothing else, and it is selected only under section 3.2, rule 5.

| Config | Reference | Settings changed | Why |
| :--- | :---: | :---: | :---: |
| `sieb_candidate` | `sieb` | rescaling 0.5 to 2, gradient norm clip 1.0, skip of non-finite steps | `CMP-05`, stability; then the winners |
| `wandler_1m_candidate` | `wandler_1m` | rescaling 0.5 to 2, gradient norm clip 1.0, skip of non-finite steps | `CMP-05`, `ACC-09`; then the winners |
| `wandler_1m_candidate_finetune` | `wandler_1m_candidate` | starts from `wandler_1m_candidate-seed0`; crop 512, batch 16, 20 epochs, warm-up 1, learning rate 0.0004, frame term 0.5 | a fine-tune on whole patches, so the crop's cloud fraction is the frame's (`FRM-01`, `ACC-07`) |
| `sieb_qat` | `sieb` | starts from `sieb-seed0`; quantisation-aware fine-tuning (`qat`), 10 epochs, learning rate 0.0008, patience 10, no warm-up | `CMP-03` of Sieb, item 20 of the optional queue of [hpc/roihu/plan.md](../hpc/roihu/plan.md), section 3.9; a fine-tune of trained weights, so a tenth of the learning rate and no warm-up |
| `cloudscout_reimpl_step1_th30` | none (a reference algorithm) | frame classifier of `A-6.13`, labels at 30 percent | step 1 of the CloudScout paper |
| `cloudscout_reimpl_th70` | `cloudscout_reimpl_step1_th30` | labels at 70 percent, only the decision layers trained, starts from `cloudscout_reimpl_step1_th30-seed0`, 20 epochs | step 2 of the CloudScout paper |
| `cloudscout_reimpl_th50` | `cloudscout_reimpl_th70` | labels at 50 percent | this repository's decision threshold |

---

## 7. Product decision

| ID | Assumption | Reason | Evidence | Revisit when | Status | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A-7.1` | Product rule: the band-flexible model is the product if its validation mean IoU on the band set B02 B03 B04 B08 lies within the 95 percent bootstrap interval of the validation mean IoU of the four-band specialist of the same size (1 M), with as many seeds as are available for both; otherwise specialists are shipped per sensor | one model for every sensor is simpler to qualify and update, but not at a measurable cost in accuracy on the sensors that matter most | none, design choice | the first comparison of `wandler_1m` and `lupe_1m` on validation | open | 7 October 2026 |

Status: no decision is recorded. The rule is applied on validation only; the test split never selects a model or a setting ([SPEC.md](SPEC.md), section 2, rule 5).

---

## 8. Sources

1. SPOT-6 and SPOT-7, eoPortal, https://www.eoportal.org/satellite-missions/spot-6-7, accessed 7 October 2026.
2. S2 Mission, spectral and spatial resolution, ESA SentiWiki, https://sentiwiki.copernicus.eu/web/s2-mission, accessed 7 October 2026.
3. CloudSEN12+ dataset card, version 1.1.2, TACO Foundation, Hugging Face, https://huggingface.co/datasets/tacofoundation/cloudsen12, accessed 7 October 2026.
4. GPU and ML guide, CSC, https://docs.csc.fi/support/tutorials/gpu-ml/, accessed 1 October 2026.
5. CloudScout: A Deep Neural Network for On-Board Cloud Detection on Hyperspectral Images, Remote Sensing 12(14), 2205, 2020, https://doi.org/10.3390/rs12142205, accessed 14 October 2026.

---

## Changelog

- 17 October 2026: `A-5.7` and `A-5.8`, the `/scratch` and `/projappl` quotas (maintainer input) and the Tykky threshold; drafted with an AI-assisted system.
- 17 October 2026: `A-2.10` and `A-2.11`, the resolution and the labels of Azersky; `sieb_qat`, the quantisation-aware fine-tune of Sieb, among the stages; drafted with an AI-assisted system.
- 16 October 2026: the CloudScout re-implementation is labelled "re-implementation trained by Tiefer Lab, not the flown model" wherever it is described; drafted with an AI-assisted system.
- 16 October 2026: `A-3.5` and `A-3.6` link their method-change issues 21 and 22; the bias is chosen on the CPU, and the soft fraction onboard needs an export with cloud probabilities; drafted with an AI-assisted system.
- 16 October 2026: the candidate references are filled from the step 7 winners before step 7b of the plan; drafted with an AI-assisted system.
- 16 October 2026: the candidate references are not in the plan of 16 October 2026, whose frozen selection rule picks each family candidate; drafted with an AI-assisted system.
- 15 October 2026: config names follow the scheme of docs/SPEC.md, section 8 (Sieb, Wandler, Lupe, the CloudScout re-implementation); drafted with an AI-assisted system.
- 15 October 2026: `A-5.2` is open again: its module observation predates Project Schatten and is confirmed by step 0 (setup) of the plan; drafted with an AI-assisted system.
- 15 October 2026: campaign names of withdrawn campaigns replaced by Project Schatten or by what the thing is; drafted with an AI-assisted system.
- 15 October 2026: `A-5.6` records the Catalogue and KappaSet as used, L8 Biome and L8 SPARCS as candidates, and fail-closed reading; drafted with an AI-assisted system.
- 15 October 2026: `A-1.10`, the band substitution of `paper_models.route` for learned reference algorithms on Landsat 8; drafted with an AI-assisted system.
- 15 October 2026: `A-5.6` links the licence decision issue 7; drafted with an AI-assisted system.
- 15 October 2026: `A-5.6` names WHUS2-CD+ as a candidate without a decision, treated as not used; drafted with an AI-assisted system.
- 15 October 2026: `A-5.6`, the maintainer's licence decisions; `A-2.9` waits for a later decision on 38-Cloud and 95-Cloud; drafted with an AI-assisted system.
- 14 October 2026: `A-2.9`, the scenes of 38-Cloud and 95-Cloud that are scored, so that no scene counts twice; drafted with an AI-assisted system.
- 14 October 2026: v3 rows: Landsat 8 band names (`A-1.8`) and the B08 substitution (`A-1.9`), the patch of an independent dataset (`A-2.8`), the cloud logit bias (`A-3.5`) and the soft cloud fraction (`A-3.6`) as protocol options, one seed per variant (`A-6.11`), export-only variants (`A-6.12`), the CloudScout re-implementation (`A-6.13`), and the table of the v3 references and stages; drafted with an AI-assisted system.
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
