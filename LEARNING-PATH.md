<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Learning path

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For a new contributor or researcher who wants to understand and change Tiefer Lab. This document owns the curriculum: the concepts Lab depends on, in the order in which they build on each other, each with where it appears in the repository and one primary reference.

---

## 1. How to use this path

The path has 11 tracks and 33 concepts. Work through the tracks in order; within a track, a concept lists its prerequisites by ID. "What it is" is a short orientation, not a definition to quote; the reference is where to read it properly. Every reference was opened on 7 October 2026 and is listed in section 13.

---

## 2. Earth observation basics

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `EO-1` | Orbit and swath | An Earth observation satellite images a strip of ground, its swath, as it moves along its orbit. Sentinel-2 flies a sun-synchronous orbit at a mean altitude of 786 km with a 290 km field of view. | The swath and the sensor decide how large a frame is, and so how it is cut into tiles on board. | none | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), `A-2.4` and `A-2.5` | [1] |
| `EO-2` | Ground sampling distance | The size on the ground of one pixel. Sentinel-2 has bands at 10 m, 20 m and 60 m. | Lab trains at 10 m and resamples other frames to 10 m before inference. | `EO-1` | [docs/DATA.md](docs/DATA.md), section 2.1; [docs/SPEC.md](docs/SPEC.md), section 9 | [1] |
| `EO-3` | Downlink budget and onboard filtering | A satellite can send only a limited amount of data to the ground. Filtering frames on board keeps the downlink for useful data. | The cloud filter exists to decide which frames are worth sending. | `EO-1` | [docs/SPEC.md](docs/SPEC.md), section 1 | [6] |

---

## 3. Sentinel-2 and processing levels

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `S2-1` | Multispectral bands | The Multi-Spectral Instrument of Sentinel-2 samples 13 bands from visible to shortwave infrared. Each band has its own wavelength and resolution. | L1 uses four bands; the band-flexible L2 model reads any of the 13. | `EO-2` | [docs/DATA.md](docs/DATA.md), section 2.1 | [1] |
| `S2-2` | Processing levels | Level-1C is top-of-atmosphere reflectance, orthorectified; Level-2A adds atmospheric correction to surface reflectance. | Lab uses Level-1C because there is no atmospheric correction on board. | `S2-1` | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), `A-2.1`; [docs/DATA.md](docs/DATA.md), section 4 | [2] |
| `S2-3` | Digital numbers and reflectance | Products store digital numbers; a scale factor turns them into reflectance. | The reader converts with reflectance = DN x 0.0001 and checks the data type. | `S2-2` | [docs/DATA.md](docs/DATA.md), section 5 | [3] |

---

## 4. Clouds and cloud shadow

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `CL-1` | Thick cloud, thin cloud and cloud shadow | Thick cloud hides the surface; thin cloud lets it show through; cloud shadow darkens the ground next to a cloud. | These are three of the four classes every model predicts. | `S2-1` | [docs/DATA.md](docs/DATA.md), section 2.2 | [3] |
| `CL-2` | Why labelling is hard | People disagree most on thin cloud and shadow. The CloudSEN12 paper measures agreement between labels before and after quality control. | The agreement bounds what any model can score on those classes. | `CL-1` | [docs/DATA.md](docs/DATA.md), section 3 | [4] |

---

## 5. The CloudSEN12+ dataset

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `DS-1` | Splits and label quality | The dataset has its own train, validation and test splits and three label types: high quality, scribble and no label. | Lab uses high quality 509 x 509 patches of the dataset's splits. | `CL-1` | [docs/DATA.md](docs/DATA.md), section 2.3 | [3] |
| `DS-2` | Padding | The card says patches are padded from 509 x 509 to 512 x 512 with zeros. | The cached patches hold the padding, and every metric counts it. | `DS-1` | [docs/DATA.md](docs/DATA.md), section 5 | [3] |
| `DS-3` | Reference masks | The extra variant of the dataset ships the masks of other cloud algorithms, not normalised to the class schema. | They are the planned comparison on the same pixels. | `DS-1` | [docs/LANDSCAPE.md](docs/LANDSCAPE.md), section 4 | [3] |

---

## 6. Semantic segmentation

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `SG-1` | Encoder-decoder networks | An encoder reduces the image to features at lower resolution; a decoder restores the resolution, with skip connections from the encoder. U-Net is the common form. | Every Lab model is a U-Net style network. | none | `src/tiefer_lab/models/cloud_filter.py`; [docs/SPEC.md](docs/SPEC.md), section 8 | [7] |
| `SG-2` | Depthwise separable convolutions | A convolution split into a per-channel and a 1 x 1 step, with far fewer operations. | It keeps the L1 models under 1.0 million parameters. | `SG-1` | `src/tiefer_lab/models/cloud_filter.py` | [8] |
| `SG-3` | Cross-entropy and Dice loss | Cross-entropy scores each pixel; the Dice loss scores the overlap of whole regions. | Lab trains on the sum of both. | `SG-1` | `src/tiefer_lab/models/losses.py` | [9] |
| `SG-4` | Class imbalance | Some classes have far fewer pixels than others. Class weights or a focal term give them more weight in the loss. | L1 uses median-frequency weights; L2 compares weights and a focal term in separate runs. | `SG-3` | `src/tiefer_lab/models/losses.py`; [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), `A-6.10` | [10] |
| `SG-5` | Distillation | A model learns from the soft predictions of another model, or of itself with more input. | The band-flexible model learns from its own prediction with all 13 bands. | `SG-3` | `src/tiefer_lab/models/losses.py`; [docs/SPEC.md](docs/SPEC.md), section 8 | [11] |
| `SG-6` | Band-flexible input | One model accepts different sets of bands, with a flag that marks each missing band. | Target sensors carry different bands; L2 measures whether one model can serve them. | `S2-1`, `SG-1` | `src/tiefer_lab/models/flexible.py`; [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 7 | [5] |

---

## 7. Evaluation

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `EV-1` | Intersection over union | The overlap of predicted and labelled pixels of a class divided by their union; mean IoU averages it over classes. | It is the headline pixel metric of every run. | `SG-1` | `src/tiefer_lab/metrics.py`; [docs/RESULTS.md](docs/RESULTS.md), section 2 | [12] |
| `EV-2` | Balanced overall accuracy, producer's and user's accuracy | Per-patch accuracies of a binary problem, such as cloud against the rest. | They make Lab comparable with the CloudSEN12 benchmark. | `EV-1`, `CL-2` | `src/tiefer_lab/binary_metrics.py`; [docs/DATASETS.md](docs/DATASETS.md), section 4 | [4] |
| `EV-3` | Frame decisions | A frame is sent when its predicted cloud fraction is below a threshold. The false discard rate counts useful frames kept on board, the false send rate cloudy frames sent, and decision accuracy all correct decisions. | The false discard rate is the error that costs an operator most. | `EO-3`, `EV-1` | `src/tiefer_lab/metrics.py`, `src/tiefer_lab/decisions.py`; [docs/RESULTS.md](docs/RESULTS.md), section 2 | [6] |
| `EV-4` | Bootstrap intervals | Resampling the patches with replacement gives the spread of a metric. | Every interval in RESULTS.md is a 95 percent bootstrap interval over patches. | `EV-1` | `src/tiefer_lab/bootstrap.py` | [13] |
| `EV-5` | Seeds and reproducibility | A run depends on its random seed; results differ between seeds even with the same code. | l1_base has two seeds that differ by 0.042 in validation mean IoU; every other run is a single seed. | `EV-4` | [docs/RESULTS.md](docs/RESULTS.md), section 18 | [14] |
| `EV-6` | Validation and test discipline | The validation split chooses models and settings; the test split is read once, for the final result. | Lab logs every use of the test split and never chooses with it. | `DS-1` | [POLICY.md](POLICY.md), gate 3; `reports/test_log.md` | [4] |

---

## 8. Compute

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `CP-1` | Slurm batch jobs | A job script asks the scheduler for resources and runs when they are free. | Every training and evaluation run on CSC Roihu is a Slurm job. | none | `hpc/roihu/`; [hpc/roihu/README.md](hpc/roihu/README.md) | [15] |
| `CP-2` | CSC Roihu GPU nodes | Each GPU node has four NVIDIA GH200 superchips, each a Hopper GPU with a 72-core ARM Grace CPU. | GPU jobs run on aarch64, so the software is set up per architecture. | `CP-1` | [hpc/roihu/README.md](hpc/roihu/README.md), section 6 | [16] |
| `CP-3` | Billing units | CSC measures resource use in billing units. | The run plan and the cost of each run are counted in GPU billing units. | `CP-1` | [hpc/roihu/plan.md](hpc/roihu/plan.md); [docs/RESULTS.md](docs/RESULTS.md), section 16 | [17] |
| `CP-4` | Mixed precision | Some operations run in a lower precision floating point type, such as bfloat16, to save time and memory. | Training uses bf16 autocast on the GH200. | `SG-1` | `src/tiefer_lab/utils/devices.py`; [docs/SPEC.md](docs/SPEC.md), section 8 | [18] |

---

## 9. Deployment

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `DP-1` | ONNX and operator sets | A file format for trained models; the opset version fixes which operators a file may use. | Every export is pinned to opset 17. | `SG-1` | `src/tiefer_lab/export/`; [docs/STANDARDS.md](docs/STANDARDS.md), section 2 | [19] |
| `DP-2` | Post-training quantisation | A model is converted to 8-bit integers after training, with scales computed on calibration data; the QDQ format marks where values are quantised. | INT8 is the likely onboard precision. | `DP-1` | `src/tiefer_lab/export/quantise.py` | [20] |
| `DP-3` | Quantisation error | Integer arithmetic approximates the floating point model, and accuracy can drop. | INT8 loses 0.060 to 0.154 validation mean IoU in Lab, more than its limit. | `DP-2`, `EV-1` | [docs/RESULTS.md](docs/RESULTS.md), section 14 | [21] |
| `DP-4` | TensorRT engines | TensorRT builds an engine for a specific NVIDIA device from an ONNX file; `trtexec` builds and times it. | The Jetson scripts build FP16 and INT8 engines with `trtexec`. | `DP-1` | `jetson/build_engines.sh` | [22] |

---

## 10. Hardware measurement

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `HW-1` | Power modes and power rails | A Jetson module runs in a power mode set by `nvpmodel`, and `tegrastats` reports the power of its rails. | Every Jetson measurement records the mode and reads the input rail. | `DP-4` | `jetson/power.py`, `jetson/device_info.sh` | [23] |
| `HW-2` | Latency and throughput | Latency is the time of one inference, reported as percentiles; throughput is inferences per second. | The acceptance targets `OBD-01` and `OBD-02` are set on them. | `DP-4` | `jetson/bench.py`; [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), section 8 | [24] |
| `HW-3` | Energy per tile | Mean power times mean latency gives the energy of one inference. | It is the hardware number that onboard power budgets need; it is not measured yet. | `HW-1`, `HW-2` | `jetson/bench.py`; [docs/RESULTS.md](docs/RESULTS.md), section 15 | [23] |

---

## 11. Onboard constraints

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `OB-1` | Size, power and model updates | Onboard computers have limited power and memory, and a new model must fit through the uplink. | Lab bounds the model file size (`OBD-03`) and keeps models small. | `EO-3`, `DP-2` | [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), section 8; [docs/SPEC.md](docs/SPEC.md), section 4 | [6] |
| `OB-2` | Radiation and commercial hardware | Commercial processors in orbit must tolerate radiation, which needs testing outside software. | Lab treats the Jetson Orin as flight-like reference hardware, not flight hardware, and leaves radiation out of scope. | `OB-1` | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), `A-4.1` and `A-4.3` | [6] |

---

## 12. Standards

| ID | Concept | What it is | Why it matters in Lab | Prerequisites | Where in the repository | Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `ST-1` | ECSS machine learning handbook | ECSS-E-HB-40-02A, the European space handbook on machine learning, issued on 15 November 2024. | It is the first document to read for an alignment of Lab's life cycle; it is not read yet. | `EV-6` | [docs/STANDARDS.md](docs/STANDARDS.md), section 2 | [25] |
| `ST-2` | ECSS software standards | ECSS-E-ST-40C Rev.1 (software) and ECSS-Q-ST-80C Rev.2 (software product assurance), both of 30 April 2025. | An operator may ask for them; Lab states no more than a self-assessed alignment, and has not read them yet. | `ST-1` | [docs/STANDARDS.md](docs/STANDARDS.md), section 2 | [26] |

---

## 13. References

All accessed 7 October 2026.

1. S2 Mission, ESA SentiWiki, https://sentiwiki.copernicus.eu/web/s2-mission
2. S2 Processing, ESA SentiWiki, https://sentiwiki.copernicus.eu/web/s2-processing
3. CloudSEN12+ dataset card, version 1.1.2, TACO Foundation, Hugging Face, https://huggingface.co/datasets/tacofoundation/cloudsen12
4. CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2, Scientific Data, 2022, https://doi.org/10.1038/s41597-022-01878-2
5. SPOT-6 and SPOT-7, eoPortal, https://www.eoportal.org/satellite-missions/spot-6-7
6. CloudScout: A Deep Neural Network for On-Board Cloud Detection on Hyperspectral Images, Remote Sensing, 2020, https://www.mdpi.com/2072-4292/12/14/2205
7. U-Net: Convolutional Networks for Biomedical Image Segmentation, arXiv:1505.04597, https://arxiv.org/abs/1505.04597
8. MobileNetV2: Inverted Residuals and Linear Bottlenecks, arXiv:1801.04381, https://arxiv.org/abs/1801.04381
9. V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation, arXiv:1606.04797, https://arxiv.org/abs/1606.04797
10. Focal Loss for Dense Object Detection, arXiv:1708.02002, https://arxiv.org/abs/1708.02002
11. Distilling the Knowledge in a Neural Network, arXiv:1503.02531, https://arxiv.org/abs/1503.02531
12. Generalized Intersection over Union: A Metric and A Loss for Bounding Box Regression, arXiv:1902.09630, https://arxiv.org/abs/1902.09630
13. Bootstrap Methods: Another Look at the Jackknife, The Annals of Statistics 7(1), 1979, https://doi.org/10.1214/aos/1176344552 (read as its Crossref metadata record)
14. Reproducibility, PyTorch 2.14 documentation, https://docs.pytorch.org/docs/2.14/notes/randomness.html
15. sbatch, Slurm Workload Manager, https://slurm.schedmd.com/sbatch.html
16. Roihu, Docs CSC, https://docs.csc.fi/computing/systems-roihu/
17. Billing, Docs CSC, https://docs.csc.fi/computing/hpc-billing/
18. Automatic Mixed Precision package, PyTorch 2.14 documentation, https://docs.pytorch.org/docs/2.14/amp.html
19. ONNX Concepts, ONNX documentation, https://onnx.ai/onnx/intro/concepts.html
20. Quantize ONNX models, ONNX Runtime documentation, https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
21. Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference, arXiv:1712.05877, https://arxiv.org/abs/1712.05877
22. Quick Start Guide, NVIDIA TensorRT documentation, https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/quick-start-guide.html
23. Jetson Orin Nano Series, Jetson Orin NX Series and Jetson AGX Orin Series, NVIDIA Jetson Linux Developer Guide, https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html
24. Best Practices, NVIDIA TensorRT documentation, https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/best-practices.html
25. ECSS-E-HB-40-02A, Machine learning handbook, 15 November 2024, ECSS, https://ecss.nl/wp-content/uploads/2024/12/ECSS-E-HB-40-02A%2815November2024%29.pdf
26. ECSS-E-ST-40C Rev.1, Software, 30 April 2025, ECSS, https://ecss.nl/standard/ecss-e-st-40c-rev-1-software-30-april-2025/

---

## Changelog

- 7 October 2026: first version: 11 tracks and 33 concepts, each with its place in the repository and one primary reference.
