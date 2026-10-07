<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Related systems

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The onboard cloud detection systems, onboard AI platforms and reference algorithms that Tiefer's cloud filter is compared with, what each has published, and what this repository has measured against it.

---

## 1. How to read this page

- Every fact comes from a public source listed in section 6, opened and accessed on 7 October 2026. A source that could not be opened is not used.
- A value from another system is labelled "published": it was measured by its authors, on their data, hardware and definitions. Published values are kept apart from the values this repository measured ([RESULTS.md](RESULTS.md)).
- "none published" means the source states no number for that system.
- This page makes no claim that Tiefer's filter is better or worse than another system. Such a claim needs both to be measured by this repository on the same data or the same hardware; section 5 lists the measurement that would decide each comparison.

---

## 2. Onboard cloud detection in orbit

| System | Output | Hardware | Input | Published values | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| CloudScout, ESA Phi-sat-1 (paper published 10 July 2020) | frame-level cloudy or not cloudy; a frame counts as cloudy from 70 percent cloudy pixels | Intel Movidius Myriad 2 on the Eyes of Things board | 3 bands (Sentinel-2 bands 1, 2 and 8, data processed to emulate the HyperScout-2 camera), 512 x 512 tiles at 60 m | published: 92 percent accuracy and 1 percent false positives on the authors' test set; 325 ms per inference; 1.8 W average power; 2.1 MB memory footprint | [1] |
| KP Labs cloud detection application, ESA Phi-sat-2 (launch reported on 19 August 2024, SpaceX Transporter-11) | processes images in orbit and downlinks only clear images; also classifies clouds | Ubotica CogniSAT SPACE:AI | multispectral camera, seven bands from visible to near infrared | none published | [2], [3] |
| NASA JPL Dynamic Targeting on CogniSAT-6 (first flight test in mid-July 2025) | looks about 500 km ahead, identifies clouds and cancels or replans imaging to capture cloud-free ground | Ubotica payload with a commercially available AI processor | camera seeing visible and near-infrared light, tilted forward 40 to 50 degrees for the look-ahead | none published for accuracy; 60 to 90 s from look-ahead to imaging | [4] |
| Spiral Blue Space Edge One (SE-1), hosted on a Satellogic NewSat (launched on Transporter-6, January 2023; commissioned April 2023) | in-orbit applications including cloud detection | Space Edge One computer | the satellite's imaging system | none published | [5], [6] |
| Craft Prospect Cloud Detector | images the Earth ahead of the satellite and identifies, classifies and maps cloud cover; up to 4 minutes of forecast to the payload computer | Cloud Detector unit | imagery ahead of the satellite | none published | [7] |
| SkyServe STORM on D-Orbit ION (announced 22 April 2024) | data processing in orbit including "smart discard", tasking and compression | D-Orbit ION Satellite Carrier onboard compute (ION SCV004 Elysian Eleonora, then a further ION in 2025) | D-Orbit's live Earth observation data feed | none published | [8] |

CloudScout's published values come from a test on the ground, on the Eyes of Things board, with a test set derived from Sentinel-2; they are not measurements in orbit. A false positive there is a not-cloudy image classified as cloudy, which would not be sent (the paper reduced false positives by making the network more prone to classify images as cloudless), and the paper states the 1 percent "with respect to the given dataset" [1].

---

## 3. Onboard AI platforms that could run a cloud filter

| Platform | Processor | What the source reports | Source |
| :--- | :---: | :---: | :---: |
| Planet Pelican-4 | NVIDIA Jetson Orin module | on 25 March 2026 it ran an AI model on board that detected airplanes in an image of the airport of Alice Springs, Australia (article of 7 April 2026) | [9] |
| EDGX Sterna | data processing unit built on NVIDIA Jetson Orin | first in-orbit demonstration planned on a SpaceX Falcon 9 in February 2026 (article of 11 August 2025); whether it flew is not checked here | [10] |
| KP Labs Intuition-1 | Leopard data processing unit | hyperspectral sensor with 192 bands; launched in November 2023; first images processed on board (press release of 11 April 2024) | [11] |
| Ubotica CogniSAT | CogniSAT SPACE:AI | runs the onboard applications of Phi-sat-2, including the cloud detection application; also the payload of CogniSAT-6 | [2], [4] |
| NVIDIA space computing | Space-1 Vera Rubin Module, IGX Thor, Jetson Orin | announced on 16 March 2026; IGX Thor and Jetson Orin available at that date, Space-1 Vera Rubin Module later; Planet is named among the users | [12] |

The NVIDIA Jetson Orin targeted by the benchmark in [jetson/](../jetson/README.md) is the same module family as on Pelican-4 and Sterna; the sources do not name the exact Orin module, so a latency or power value measured on one Orin module does not carry over to another without measuring it.

---

## 4. Reference algorithms on CloudSEN12

Published cloud and cloud shadow BOA from the CloudSEN12 paper [13], Table 6: the median over the 975 image patches of that paper's test set of the per-patch balanced overall accuracy. They were measured on the labels of the 2022 release, not on this repository's revision of CloudSEN12+, whose labels were curated and refined in version 1.1.0 [15]. Shadow is `n/a` where the algorithm has no cloud shadow class; the paper scores shadow only for algorithms that detect it.

| Algorithm | Input | Cloud BOA, published | Shadow BOA, published | How this repository measures it on the same pixels | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Human level | manual labels | 0.99 | 0.99 | n/a (agreement of labellers, not an algorithm) | [13] |
| UNetMobV2 | 13 Level-1C bands | 0.92 | 0.89 | extra-table masks `cloudmask_unetmobv2_v1` and `cloudmask_unetmobv2_v2` | [13], [15] |
| Fmask | Fmask 4.0 for Landsat and Sentinel-2, run by the paper's authors | 0.84 | 0.72 | run Fmask 4.0 on the test patches; not in the extra table | [13] |
| KappaMask L1C | all Level-1C bands | 0.82 | 0.74 | run the model; not in the extra table | [13] |
| KappaMask L2A | Level-2A bands except red edge 3 | 0.77 | 0.64 | run the model on Level-2A; not in the extra table | [13] |
| s2cloudless | cloud probability of the Sentinel Hub detector, without threshold or dilation | 0.79 | n/a | extra-table mask `cloudmask_s2cloudless` | [13], [15] |
| CD-FCNN-RGBI | B2, B3, B4, B8 | 0.72 | n/a | run the model; not in the extra table | [13] |
| CD-FCNN-RGBISWIR | B2, B3, B4, B8, B11, B12 | 0.72 | n/a | run the model; not in the extra table | [13] |
| Sen2Cor | Level-2A scene classification | 0.71 | 0.51 | extra-table mask `cloudmask_sen2cor` | [13], [15] |
| QA60 | Level-1C quality band | 0.58 | n/a | extra-table mask `cloudmask_qa60` | [13], [15] |
| CloudScore+ (cs) | not stated in [15] | none published here | none published here | extra-table mask `cloudmask_cloudscore_cs_v1` | [15] |
| CloudScore+ (cs_cdf) | not stated in [15] | none published here | none published here | extra-table mask `cloudmask_cloudscore_cs_cdf_v1` | [15] |
| SEnSeI v2 | not stated in [15] | none published here | none published here | extra-table mask `cloudmask_sensei_v2` | [15] |
| dtacs4bands | NIR, red, green and blue of Level-1C | none published here | none published here | run the model; licence CC BY-NC 4.0 | [14] |

The extra-table masks are those of the dataset variant `tacofoundation:cloudsen12-extra`, which the dataset card says are not normalised to the CloudSEN12 class schema [15]. `build_cache --references` adds them to a split once their link and encodings are verified ([DATA.md](DATA.md), section 2); until then it stops with a clear message. CD-FCNN-RGBI and dtacs4bands use the same four bands as the L1 models and `l2_spec_1m`.

---

## 5. Head-to-head status

"Ours" values are from [RESULTS.md](RESULTS.md); "theirs" values are published unless the cell says measured here. No row is decided yet: each status names the measurement that would decide it. The open measurements are listed as work items in [hpc/roihu/plan.md](../hpc/roihu/plan.md), section 6.

| Comparison | Metric | Our value | Their value | Status |
| :--- | :---: | :---: | :---: | :---: |
| Reference algorithms on the same CloudSEN12+ test pixels | cloud and shadow BOA, median over patches | l2_spec_1m s0, test: 0.918 [0.911, 0.926] and 0.894 [0.884, 0.901] (RESULTS.md, section 11) | not measured here; published on the 2022 test set in section 4 | open: score the extra-table masks and the runnable algorithms with this repository's code on the same 975 test patches |
| dtacs4bands on the same pixels and the same four bands | cloud and shadow BOA; mean IoU | l2_spec_1m s0, test: BOA as above; mean IoU 0.720 [0.707, 0.732] (RESULTS.md, section 6) | not measured here; none published here | open: run dtacs4bands on the test split with B02, B03, B04, B08, after checking that its CC BY-NC 4.0 licence allows the use |
| CloudScout false positives against our false discard rate | useful frames discarded | l2_spec_1m s0, test: false discard rate 0.042 [0.026, 0.059] at 50 percent and 0.042 [0.029, 0.056] at 70 percent, the threshold CloudScout uses (RESULTS.md, section 7) | published: 1 percent false positives with respect to the authors' dataset, at 70 percent | open: different data and definitions; the deciding measurement is a threshold sweep that reports the false send rate at a false discard rate of 0.01 |
| CloudScout accuracy against our decision accuracy | frames decided correctly at 70 percent | l2_spec_1m s0, test: 0.944 [0.928, 0.958] (RESULTS.md, section 7) | published: 92 percent on the authors' test set | open: different data, bands and resolution; deciding: both models on the same frames |
| Latency, power and energy per 512 x 512 tile | ms, W and J per tile | not measured (RESULTS.md, section 15) | published: 325 ms and 1.8 W per inference on Myriad 2, for 512 x 512 x 3; 0.585 J, computed here from those two values | open: `jetson/bench.py` on a Jetson Orin, FP16 and INT8, with the input rail power |
| Model size | bytes | l1_base s0: FP32 993,280; INT8 455,680 with a mean IoU loss of 0.070 (RESULTS.md, section 14); l2_spec_1m s0: no export report yet; export jobs 2002028, 2002101 and 2002148 are not matched to a run | published: 2.1 MB memory footprint | open: different models and measures (file size against memory footprint on the device); deciding: file size and memory during inference of the selected model on a Jetson Orin |

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

---

## Changelog

- 7 October 2026: correction: l2_spec_1m s0 has no export report yet, and three export jobs are not matched to a run.
- 7 October 2026: first version: onboard cloud detection systems, onboard AI platforms, reference algorithms on CloudSEN12 with their published values, and the measurements that would decide each comparison.
