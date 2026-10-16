<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Related systems

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The onboard cloud detection systems, onboard AI platforms and reference algorithms that Tiefer's cloud filter is compared with, what each has published, and what this repository has measured against it.

---

## 1. How to read this page

- Every fact comes from a public source listed in section 6, opened and accessed on 7 October 2026. A source that could not be opened is not used.
- A value from another system is labelled "published": it was measured by its authors, on their data, hardware and definitions. Published values are kept apart from the values this repository measured ([RESULTS.md](RESULTS.md)).
- "none published" means the sources listed here state no number for that system.
- Values of this repository are rounded to 3 decimals, half up, as in RESULTS.md; published values are written as their source wrote them.
- This page makes no claim that Tiefer's filter is better or worse than another system. Such a claim needs both to be measured by this repository on the same data or the same hardware ([POLICY.md](../POLICY.md), gate 5); section 5 lists the measurement that would decide each comparison. Which value of this repository to quote is in [BENCHMARK-AUTHORITY.md](../BENCHMARK-AUTHORITY.md).

---

## 2. Onboard cloud detection in orbit

| System | Output | Hardware | Input | Published values | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| CloudScout, ESA Phi-sat-1 (paper published 10 July 2020) | frame-level cloudy or not cloudy; a frame counts as cloudy from 70 percent cloudy pixels | Intel Movidius Myriad 2 on the Eyes of Things board | 3 bands (Sentinel-2 bands 1, 2 and 8, data processed to emulate the HyperScout-2 camera), 512 x 512 tiles at 60 m | published: 92 percent accuracy and 1 percent false positives on the authors' test set; 325 ms per inference; 1.8 W average power during inference; 2.1 MB memory footprint | [1] |
| KP Labs cloud detection application, ESA Phi-sat-2 (launch reported on 19 August 2024, SpaceX Transporter-11) | processes images in orbit and downlinks only clear images; also classifies clouds | Ubotica CogniSAT SPACE:AI | multispectral camera, seven bands from visible to near infrared | none published | [2], [3] |
| NASA JPL Dynamic Targeting on CogniSAT-6 (first flight test in mid-July 2025) | looks about 500 km ahead, identifies clouds and cancels or replans imaging to capture cloud-free ground | Ubotica payload with a commercially available AI processor | camera seeing visible and near-infrared light, tilted forward 40 to 50 degrees for the look-ahead | none published for accuracy; 60 to 90 s from look-ahead to imaging | [4] |
| Spiral Blue Space Edge One (SE-1), hosted on a Satellogic NewSat (launched on Transporter-6, January 2023; commissioned April 2023) | in-orbit applications including cloud detection | Space Edge One computer | the satellite's imaging system | none published | [5], [6] |
| Craft Prospect Cloud Detector | images the Earth ahead of the satellite and identifies, classifies and maps cloud cover; up to 4 minutes of forecast to the payload computer | Cloud Detector unit | imagery ahead of the satellite | none published | [7] |
| SkyServe STORM on D-Orbit ION (announced 22 April 2024) | data processing in orbit including "smart discard", tasking and compression | D-Orbit ION Satellite Carrier onboard compute (ION SCV004 Elysian Eleonora, then a further ION in 2025) | D-Orbit's live Earth observation data feed | none published | [8] |

CloudScout's architecture (a 5 x 5 size reduction layer, groups of 3 x 3, 1 x 1 and 3 x 3 convolutions, global max pooling, fully connected decision layers) and its loss, which doubles the penalty of a false positive, are described in [1], section 3.4 and Figure 7; the paper gives no filter numbers. This repository has a re-implementation trained by Tiefer Lab from random initialisation, not the flown model (`src/tiefer_lab/models/cloudscout.py`, `configs/cloudscout*.toml`), so the frame comparison can be measured on the same frames.

CloudScout's published values come from a test on the ground, on the Eyes of Things board, with a test set derived from Sentinel-2; they are not measurements in orbit. A false positive there is a not-cloudy image classified as cloudy, which would not be sent (the paper reduced false positives by making the network more prone to classify images as cloudless), and the paper states the 1 percent "with respect to the given dataset" [1].

---

## 3. Onboard AI platforms that could run a cloud filter

| Platform | Processor | What the source reports | Source |
| :--- | :---: | :---: | :---: |
| Planet Pelican-4 | NVIDIA Jetson Orin module | on 25 March 2026 it ran an AI model on board that detected airplanes in an image of the airport of Alice Springs, Australia (article of 7 April 2026) | [9] |
| EDGX Sterna | data processing unit built on NVIDIA Jetson Orin [10]; NVIDIA-based, power scaled between 10 W and 45 W [16] | first in-orbit demonstration launched on SpaceX Transporter-16, with two hosted payloads in orbit (press release of 9 April 2026); planned for February 2026 in the article of 11 August 2025 | [10], [16] |
| KP Labs Intuition-1 | Leopard data processing unit | hyperspectral sensor with 192 bands; launched in November 2023; first images processed on board (press release of 11 April 2024) | [11] |
| Ubotica CogniSAT | CogniSAT SPACE:AI | runs the onboard applications of Phi-sat-2, including the cloud detection application; also the payload of CogniSAT-6 | [2], [4] |
| NVIDIA space computing | Space-1 Vera Rubin Module, IGX Thor, Jetson Orin | announced on 16 March 2026; IGX Thor and Jetson Orin available at that date, Space-1 Vera Rubin Module later; Planet is named among the users | [12] |

The NVIDIA Jetson Orin targeted by the benchmark in [jetson/](../jetson/README.md) is the same module family as on Pelican-4 and Sterna; the sources do not name the exact Orin module, so a latency or power value measured on one Orin module does not carry over to another without measuring it.

---

## 4. Reference algorithms on CloudSEN12

Published cloud and cloud shadow BOA from the CloudSEN12 paper [13], Table 6: the median over the 975 image patches of that paper's test set of the per-patch balanced overall accuracy. They were measured on the labels of the 2022 release, not on this repository's revision of CloudSEN12+, whose labels were curated and refined in version 1.1.0 [15]. Shadow is `n/a` where the algorithm has no cloud shadow class; the paper scores shadow only for algorithms that detect it.

| Algorithm | Input | Cloud BOA, published | Shadow BOA, published | How this repository measures it on the same pixels | Note | Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Human level | n/a | 0.99 | 0.99 | n/a | agreement of the labels before and after quality control, not an algorithm | [13] |
| UNetMobV2 | 13 Level-1C bands | 0.92 | 0.89 | extra-table masks `cloudmask_unetmobv2_v1` and `cloudmask_unetmobv2_v2` | trained on CloudSEN12 | [13], [15] |
| Fmask | not stated in [13] | 0.84 | 0.72 | run Fmask 4.0 on the test patches | run by the paper's authors; not in the extra table | [13] |
| KappaMask L1C | all Level-1C bands | 0.82 | 0.74 | run the model | not in the extra table | [13] |
| KappaMask L2A | Level-2A bands except red edge 3 | 0.77 | 0.64 | run the model on Level-2A | not in the extra table | [13] |
| s2cloudless | not stated in [13] | 0.79 | n/a | extra-table mask `cloudmask_s2cloudless` | scored on the cloud probability, without threshold or dilation | [13], [15] |
| CD-FCNN-RGBI | B2, B3, B4, B8 | 0.72 | n/a | run the model | not in the extra table | [13] |
| CD-FCNN-RGBISWIR | B2, B3, B4, B8, B11, B12 | 0.72 | n/a | run the model | not in the extra table | [13] |
| Sen2Cor | Level-2A scene classification | 0.71 | 0.51 | extra-table mask `cloudmask_sen2cor` | n/a | [13], [15] |
| QA60 | Level-1C quality band | 0.58 | n/a | extra-table mask `cloudmask_qa60` | n/a | [13], [15] |
| CloudScore+ (cs) | not stated in [15] | none published | none published | extra-table mask `cloudmask_cloudscore_cs_v1` | n/a | [15] |
| CloudScore+ (cs_cdf) | not stated in [15] | none published | none published | extra-table mask `cloudmask_cloudscore_cs_cdf_v1` | n/a | [15] |
| SEnSeI v2 | not stated in [15] | none published | none published | extra-table mask `cloudmask_sensei_v2` | n/a | [15] |
| dtacs4bands | NIR, red, green and blue of Level-1C | none published | none published | run the model | licence CC BY-NC 4.0 | [14] |

The paper summarises PA and UA as shares of its 975 test patches, in percent: low below 0.1, middle from 0.1 to 0.9, high above 0.9, with PA and UA of cloudless patches set to NaN [13], Table 6 and Technical Validation. They are written as the paper wrote them, published values on the 2022 labels; this repository computes the same summary with `evaluate --full-metrics` ([DATASETS.md](DATASETS.md), section 4), whose share denominator is still `TODO(verify)`.

| Algorithm | PA low, published | PA middle, published | PA high, published | UA low, published | UA middle, published | UA high, published |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cloud against no cloud** | | | | | | |
| Human level | 1.03 | 14.03 | 84.94 | 0.13 | 4.39 | 95.48 |
| UNetMobV2 | 0.77 | 30.63 | 68.6 | 0.26 | 25.03 | 74.71 |
| KappaMask L2A | 2.83 | 31.92 | 65.25 | 1.56 | 63.04 | 35.41 |
| KappaMask L1C | 4.89 | 45.3 | 49.81 | 0.65 | 38.38 | 60.97 |
| Fmask | 5.92 | 40.54 | 53.54 | 0.26 | 52.65 | 47.09 |
| s2cloudless | 7.08 | 52.38 | 40.54 | 0.65 | 31.5 | 67.84 |
| Sen2Cor | 13.13 | 64.86 | 22.01 | 1.58 | 20.05 | 78.36 |
| QA60 | 24.84 | 49.94 | 25.23 | 1.39 | 37.62 | 60.99 |
| CD-FCNN-RGBI | 17.50 | 74.00 | 8.49 | 1.62 | 12.58 | 85.79 |
| CD-FCNN-RGBISWIR | 18.40 | 71.43 | 10.17 | 0.82 | 9.43 | 89.75 |
| **Cloud shadow** | | | | | | |
| Human level | 3.11 | 22.04 | 74.85 | 0.60 | 9.97 | 89.43 |
| UNetMobV2 | 8.88 | 67.16 | 23.96 | 7.99 | 46.65 | 45.36 |
| KappaMask L2A | 37.28 | 59.76 | 2.96 | 12.24 | 36.9 | 50.85 |
| KappaMask L1C | 30.03 | 60.95 | 9.02 | 20.67 | 59.36 | 19.97 |
| Fmask | 22.34 | 76.04 | 1.63 | 14.53 | 77.06 | 8.41 |
| Sen2Cor | 64.5 | 35.21 | 0.30 | 6.90 | 18.10 | 75.00 |
| **Valid against invalid** | | | | | | |
| Human level | 1.03 | 14.8 | 84.17 | 0.13 | 2.33 | 97.55 |
| UNetMobV2 | 0.77 | 28.57 | 70.66 | 0.00 | 17.14 | 82.86 |
| KappaMask L2A | 2.96 | 39.38 | 57.66 | 1.29 | 44.32 | 54.39 |
| KappaMask L1C | 3.99 | 47.62 | 48.39 | 0.65 | 32.64 | 66.71 |
| Fmask | 4.89 | 45.43 | 49.68 | 0.26 | 44.34 | 55.39 |
| Sen2Cor | 13.77 | 69.63 | 16.6 | 1.05 | 18.58 | 80.37 |

The extra-table masks are those of the dataset variant `tacofoundation:cloudsen12-extra`, which the dataset card says are not normalised to the CloudSEN12 class schema [15]. `build_cache --references` adds them to a split once their link and encodings are verified ([DATA.md](DATA.md), section 9); until then it stops with a clear message. CD-FCNN-RGBI and dtacs4bands use the same four bands as the L1 models and `lupe_1m`.

---

## 5. Head-to-head status

The column "This repository" holds values measured here, from [RESULTS.md](RESULTS.md); the column "Other system" holds published values unless the cell says otherwise. No row is decided yet: each status names the measurement that would decide it. The deciding measurements are added as steps of the plan of Project Schatten ([hpc/roihu/plan.md](../hpc/roihu/plan.md)).

| Comparison | Metric | This repository | Other system | Status | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Reference algorithms on the same CloudSEN12+ test pixels | cloud and shadow BOA, median over patches | not measured (Project Schatten pending) | not measured here; published values on the 2022 test set in section 4 | open (note 1) | RESULTS.md, section 11; [13] |
| dtacs4bands on the same pixels and the same four bands | cloud and shadow BOA; mean IoU | not measured (Project Schatten pending) | not measured here; none published | open (note 2) | RESULTS.md, sections 6 and 11; [14] |
| CloudScout false positives against the false discard rate | useful frames discarded | not measured (Project Schatten pending) | published: 1 percent false positives on the authors' dataset, at 70 percent | open (note 3) | RESULTS.md, section 7; [1] |
| CloudScout accuracy against decision accuracy | frames decided correctly at 70 percent | not measured (Project Schatten pending) | published: 92 percent on the authors' test set | open (note 4) | RESULTS.md, section 7; [1] |
| CloudScout re-implementation trained by Tiefer Lab, not the flown model, on the same frames | false discard rate and false send rate at 50 and 70 percent; size, parameters, multiply-accumulates | not measured | not measured here | open (note 7) | `reports/comparison.md` |
| Latency, power and energy per 512 x 512 tile | ms, W and J per tile | not measured (Project Schatten pending) | published: 325 ms per inference and 1.8 W average power during inference on Myriad 2, for 512 x 512 x 3; 0.585 J per inference, derived here from those two values, not published | open (note 5) | RESULTS.md, section 15; [1] |
| Model size | bytes | not measured (Project Schatten pending) | published: 2.1 MB memory footprint | open (note 6) | RESULTS.md, section 14; [1] |

Notes:

1. Deciding measurement: score the extra-table masks and the runnable algorithms with this repository's code on the same test patches.
2. Deciding measurement: run dtacs4bands on the test split with B02, B03, B04 and B08, after checking that its CC BY-NC 4.0 licence allows the use.
3. Different data and definitions. A threshold sweep that reports the false send rate at a false discard rate of 0.01 gives a comparable operating point for this repository's model, but it does not decide the comparison without both models on the same frames.
4. Different data, bands and resolution. Deciding measurement: both models on the same frames.
5. Deciding measurement: `jetson/bench.py` on a Jetson Orin, FP16 and INT8, with the input rail power.
6. Different models and measures: file size here, memory footprint on the device for CloudScout. Deciding measurement: file size and memory during inference of the selected model on a Jetson Orin.
7. Deciding measurement: `configs/cloudscout_reimpl_step1_th30.toml`, then `configs/cloudscout_reimpl_th70.toml` and `configs/cloudscout_reimpl_th50.toml`, trained and evaluated on the CloudSEN12+ splits with the same code as Tiefer's models. It decides the comparison with the re-implementation, not with the flown model on its own data.

---

## 6. Sources

All accessed 7 October 2026.

- [1] CloudScout: A Deep Neural Network for On-Board Cloud Detection on Hyperspectral Images, Remote Sensing 12(14), 2205, 2020: [mdpi.com](https://www.mdpi.com/2072-4292/12/14/2205)
- [2] ESA's Phi-sat-2 mission, powered by Ubotica's CogniSAT, 19 August 2024: [ubotica.com](https://www.ubotica.com/news/esas--cf-86sat-2-powered-by-uboticas-cognisat)
- [3] Boosting in-orbit cloud detection with AI, KP Labs: [kplabs.space](https://kplabs.space/blog/boosting-in-orbit-cloud-detection-with-ai)
- [4] How NASA is testing AI to make Earth-observing satellites smarter, NASA JPL, 24 July 2025: [jpl.nasa.gov](https://www.jpl.nasa.gov/news/how-nasa-is-testing-ai-to-make-earth-observing-satellites-smarter/)
- [5] Spiral Blue's SE-1 computer reaches orbit, SatNews, 8 January 2023: [satnews.com](https://satnews.com/2023/01/08/spiral-blues-se-1-computer-reaches-orbit/)
- [6] Spiral Blue brings space-based AI to Australians, SatNews, 5 June 2023: [satnews.com](https://satnews.com/2023/06/05/spiral-blue-brings-space-based-ai-to-australians/)
- [7] Cloud Detector, Craft Prospect, satsearch: [satsearch.co](https://satsearch.co/products/craft-prospect-cloud-detector)
- [8] D-Orbit announces on-orbit edge computing collaboration with SkyServe STORM, SatNews, 22 April 2024: [satnews.com](https://satnews.com/2024/04/22/d-orbit-announces-on-orbit-edge-computing-collaboration-with-skyserve-storm/)
- [9] Planet details AI-driven object detection onboard Pelican-4 satellite, Via Satellite, 7 April 2026: [satellitetoday.com](https://www.satellitetoday.com/imagery-and-sensing/2026/04/07/planet-details-ai-driven-object-detection-onboard-pelican-4-satellite)
- [10] Belgian spacetech EDGX raises 2.3M to bring edge computing to space, tech.eu, 11 August 2025: [tech.eu](https://tech.eu/2025/08/11/belgian-spacetech-edgx-raises-2-3m-to-bring-edge-computing-to-space/)
- [11] First hyperspectral images processed by AI on board Intuition-1 satellite, KP Labs, 11 April 2024: [kplabs.space](https://kplabs.space/blog/press-release-first-hyperspectral-images-processed-by-ai-on-board-intuition-1-satellite/)
- [12] NVIDIA launches space computing, rocketing AI into orbit, NVIDIA, 16 March 2026: [investor.nvidia.com](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Launches-Space-Computing-Rocketing-AI-Into-Orbit/default.aspx)
- [13] CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2, Scientific Data 9, 782, 2022: [pmc.ncbi.nlm.nih.gov](https://pmc.ncbi.nlm.nih.gov/articles/PMC9789947/)
- [14] CloudSEN12 trained models, model card: [huggingface.co](https://huggingface.co/isp-uv-es/cloudsen12_models)
- [15] CloudSEN12+ dataset card, version 1.1.2: [huggingface.co](https://huggingface.co/datasets/tacofoundation/cloudsen12)
- [16] EDGX launches first in-orbit demonstration of its AI computing system on SpaceX Transporter-16, EDGX via PR Newswire, 9 April 2026: [prnewswire.co.uk](https://www.prnewswire.co.uk/news-releases/edgx-launches-first-in-orbit-demonstration-of-its-ai-computing-system-on-spacex-transporter-16-302738209.html)

---

## Changelog

- 16 October 2026: the CloudScout re-implementation is labelled "re-implementation trained by Tiefer Lab, not the flown model" wherever it is described; drafted with an AI-assisted system.
- 15 October 2026: config names follow the scheme of docs/SPEC.md, section 8 (Sieb, Wandler, Lupe, the CloudScout re-implementation); drafted with an AI-assisted system.
- 15 October 2026: campaign names of withdrawn campaigns replaced by Project Schatten or by what the thing is; drafted with an AI-assisted system.
- 14 October 2026: section 4 gains the published PA and UA shares of the CloudSEN12 paper's Table 6 for all three experiments, read in the Europe PMC full text; section 2 describes CloudScout's architecture and its re-implementation in this repository; section 5 adds the comparison with that re-implementation; drafted with an AI-assisted system.
- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: section 1 links POLICY.md, gate 5, and BENCHMARK-AUTHORITY.md.
- 7 October 2026: status `in development`, like the other pages that change with the work.
- 7 October 2026: correction: the EDGX Sterna demonstration launched on SpaceX Transporter-16 (press release of 9 April 2026); the page no longer says that whether it flew is not checked.
- 7 October 2026: CloudScout's 1.8 W is its average power during inference, as the paper states; 0.585 J is derived here, not published.
- 7 October 2026: section 4 has a note column, so the input column holds inputs only; one term, "none published".
- 7 October 2026: links to docs/DATA.md follow its new section numbers.
- 7 October 2026: first version: onboard cloud detection systems, onboard AI platforms, reference algorithms on CloudSEN12 with their published values, and the measurements that would decide each comparison.
