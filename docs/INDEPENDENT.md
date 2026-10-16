<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: independent test datasets

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The nine datasets of the CloudSEN12 paper's Table 1 as candidates to test the cloud filter on data it never saw, and which of them the licence decisions allow: what each one is, the facts the code depends on with their sources, how they are made comparable with CloudSEN12+, the coverage of every model on every dataset, and the facts still open. They are never used for training, selection, calibration or thresholds. The catalogue row of each is in [DATASETS.md](DATASETS.md), section 1; the code is `src/tiefer_lab/data/independent.py`.

---

## 1. Motivation

| Question | Answer | Source |
| :--- | :---: | :---: |
| Why are independent datasets used? | a result on the CloudSEN12+ test split shares its labelling protocol, sensor and processing level with the training data; acceptance targets `IND-01` to `IND-04` and `CMP-06` need data labelled by others, on Sentinel-2 and on another sensor | [REQUIREMENTS.md](REQUIREMENTS.md), section 8 |
| Why these nine? | they are all the datasets the CloudSEN12 paper lists next to CloudSEN12 (Table 1); every model of this repository and every algorithm of the paper's Table 6 is scored on each of them that the licence decisions allow, where it can be (sections 2.1 and 8) | [1], Table 1 |
| Are they independent of the models? | yes for training: no model of this repository reads them before its selection is frozen; Sentinel-2 products that CloudSEN12+ also uses are dropped first (section 5) | `build_cache --source` |

---

## 2. Composition

| Dataset | Sensor and processing level | Size | Classes | Strata | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| L8 Biome (`landsat8_biome`) | Landsat 8 OLI and TIRS, pre-collection Level-1T | 96 scenes | 0 fill, 64 cloud shadow, 128 clear, 192 thin cloud, 255 cloud | biome of each scene (8 biomes of 12 scenes) | [2], [21] |
| L8 SPARCS (`landsat8_sparcs`) | Landsat 8, pre-collection Level-1 | 80 subsets of 1000 x 1000 pixels | 0 shadow, 1 shadow over water, 2 water, 3 snow, 4 land, 5 cloud, 6 flooded | none | [3] |
| Sentinel-2 Cloud Mask Catalogue (`s2_cloud_catalogue`) | Sentinel-2 Level-1C, 2018 archive | 513 subscenes of 1022 x 1022 pixels at 20 m | CLEAR, CLOUD, CLOUD_SHADOW (one-hot) | 11 surface type tags, difficulty, shadows marked or not | [4], [5] |
| KappaSet (`kappaset`) | Sentinel-2 Level-1C | 9,251 sub-tiles of 512 x 512 pixels at 10 m from 1,038 products | 0 undefined, 1 clear, 2 cloud shadow, 3 semi-transparent cloud, 4 cloud, 5 missing | season | [6], [7] |
| WHUS2-CD+ (`whus2_cd`) | Sentinel-2A Level-1C, full SAFE products | 36 scenes (the 32 of WHUS2-CD and 4 snow and ice scenes), masks of 10980 x 10980 pixels at 10 m | 0 no data, 128 clear, 255 cloud | none | [11], [12] |
| 38-Cloud (`landsat8_38cloud`) | Landsat 8 Collection 1 Level-1 | 18 training and 20 test scenes; patches of 384 x 384 pixels, red, green, blue and near infrared only | entire-scene masks 0 clear, 1 cloud; patch masks 0 and 255 | none | [13], [14] |
| 95-Cloud (`landsat8_95cloud`) | Landsat 8 Collection 1 Level-1 | 38-Cloud and 57 more training scenes; only the 57 are used | as 38-Cloud | none | [15], [16] |
| S2-Hollstein (`s2_hollstein`) | Sentinel-2 Level-1C spectra at 20 m | 3,028,733 labelled pixels of 48 products (file of 10 July 2017); no images | 10 clear, 20 water, 30 shadow, 40 cirrus, 50 cloud, 60 snow | continent | [17], [18] |
| S2-CESBIO (`s2_cesbio`) | Sentinel-2 Level-1C, masks only | 31 scenes of `Reference_dataset`, 1830 x 1830 pixels at 60 m; no images | 0 no data, 1 not used, 2 low clouds, 3 high clouds, 4 cloud shadows, 5 land, 6 water, 7 snow | none | [19], [20] |

- The Catalogue marks shadow in 424 subscenes; in 89, shadow could not be annotated, so the shadow problem is scored only on tiles with `shadows_marked` = 1 [5].
- The KappaSet README says the data mostly covers land (about 91 percent) with some water (about 9 percent), about 7 percent contains snow, and the sub-tiles have no georeferencing [7].
- The paper's Table 1 gives 59 scenes for S2-Hollstein and 38 for S2-CESBIO. The Hollstein file of 10 July 2017 holds 48 products; the CESBIO record holds 31 plus 7 scenes, one of them in both folders, and its paper speaks of 32 reference scenes [17], [19], [20]. This card uses the files.
- WHUS2-CD labels thin cloud whose surface cannot be seen as cloud and other thin cloud as clear; 38-Cloud and 95-Cloud label thin cloud and haze as cloud [12], [13]. These datasets are scored on the cloud problem only.
- The paper's Table 1 lists the KappaZeta dataset with 155 scenes in Northern Europe [1]; the KappaSet record of 2022 has 1,038 products distributed over the globe [6]. This card uses the record of 2022.

### 2.1 Status

Which datasets the maintainer's licence decisions allow; only a dataset recorded as used is read. The licence, the decision, its date and its reason are recorded once, in [DATASETS.md](DATASETS.md), section 1.1; a refused dataset is never downloaded, cached, evaluated or reported, and its reader stops with the decision.

| Dataset | Status |
| :--- | :---: |
| L8 Biome | used, licence decision of 16 October 2026; download not planned yet |
| L8 SPARCS | used, licence decision of 16 October 2026; download not planned yet, planned before L8 Biome |
| Sentinel-2 Cloud Mask Catalogue | used |
| KappaSet | used |
| WHUS2-CD+ | not used, decision of 16 October 2026 (scope, not licence) |
| 38-Cloud | not used, licence decision of 15 October 2026 |
| 95-Cloud | not used while it needs credentials, licence decision of 15 October 2026 |
| S2-Hollstein | not used, licence decision of 15 October 2026 |
| S2-CESBIO | not used, licence decision of 15 October 2026 (its imagery is not downloaded) |

---

## 3. Collection and labelling

| Dataset | How it was labelled | Agreement stated by the authors | Source |
| :--- | :---: | :---: | :---: |
| L8 Biome | manual cloud masks for the validation of cloud cover assessment algorithms | not stated on the page | [2] |
| L8 SPARCS | manual masks of subsets of scenes | not stated on the page | [3] |
| Catalogue | semi-automatically with the IRIS toolkit (a Random Forest that the annotators correct), by two annotators | 60 subscenes labelled by both; pixel agreement and F1 per class in the README | [5] |
| KappaSet | semi-automatically with CVAT and Segments.ai | not stated | [7] |

The Catalogue README advises that, when in doubt at large thin cloud boundaries, pixels were marked as cloud [5]. Its agreement values are the authors', on their labels, and are not compared with any value of this repository.

---

## 4. Preprocessing in this repository

| Step | Rule | Where |
| :--- | :---: | :---: |
| Reflectance, Landsat 8 | (REFLECTANCE_MULT_BAND_x x DN + REFLECTANCE_ADD_BAND_x) / sin(SUN_ELEVATION), from each scene's MTL file; DN 0 is fill | `landsat_toa_reflectance` [8] |
| Reflectance, Catalogue | stored as top-of-atmosphere reflectance, the Level-1C integers divided by 10,000 [5]; a product of processing baseline 04.00 or later stops, because its radiometric offset would be missing | `read_catalogue`, `s2_needs_offset` |
| Reflectance, KappaSet | whether the NetCDF bands are digital numbers or reflectance is open (section 6) | `read_kappaset` |
| Bands | Landsat 8 band 1 B01, 2 B02, 3 B03, 4 B04, 5 B8A, 6 B11, 7 B12, 9 B10; a four-band model reads band 5 in place of B08 only with `--substitute`, reported apart | [ASSUMPTIONS.md](ASSUMPTIONS.md), `A-1.8` and `A-1.9` |
| Labels | mapped to clear 0, thick cloud 1, thin cloud 2, cloud shadow 3, unlabelled 255; snow, water and flooded are clear; a dataset without thin cloud is scored on the cloud problem only; any code outside the verified map stops the build | `harmonise` |
| Resolution | resampled to 10 m as `tiefer_lab.onboard.predict_frame` does (area averaging when finer, bilinear when coarser; labels nearest); `--resolution native` keeps the native resolution as a perturbation | `resample` |
| Patch | non-overlapping 509 x 509 tiles from the top left; the remainder strips are left out; a tile with more than 0.1 unlabelled pixels is dropped and counted | `tiles`; [ASSUMPTIONS.md](ASSUMPTIONS.md), `A-2.8` |
| Normalisation | always the training statistics of the evaluated run's own cache, never statistics of the independent data | `evaluate --data` |

The patch definition is a protocol decision proposed in a method-change issue; its default may change only there.

---

## 5. Independence and comparison masks

- **Sentinel-2.** CloudSEN12+ uses Sentinel-2 scenes of 2018 to 2020. Before a Catalogue or KappaSet product is tiled, its product ID, and its MGRS tile with its sensing date, are compared with every CloudSEN12+ patch of every split; a match drops the product, and the counts are written to the cache index. The CloudSEN12+ field that holds the product ID is open (section 6). Footprints are not compared yet; the Catalogue ships shapefiles that would allow it.
- **Landsat 8.** A different sensor; scenes are not dropped. Geographic overlap with CloudSEN12+ is to be reported once footprints are compared.
- **`IND-02` (Sen2Cor on the same pixels).** The `test` folder of KappaSet holds the Sen2Cor scene classification (SCL), Fmask, s2cloudless, IdePix and MAJA maps of the same sub-tiles [7], so Sen2Cor needs no download with credentials. Its codes come from the Sen2Cor documentation; the semantic mapping of the CloudSEN12 paper's Table 5 is used, and codes Table 5 does not list (for example no data, saturated and unclassified) are decisions recorded before use. For the Catalogue no Sen2Cor source is verified, so `IND-02` stays `not measured` there.
- **`IND-03` (the operational mask).** The quality band of each Landsat 8 product, decoded to the cloud problem by the bit layout of the USGS product guide of its collection (pre-collection; section 6).

### 5.1 What limits measurement

Checked on 16 October 2026 from the primary pages (section 9); what can be downloaded is in [DATASETS.md](DATASETS.md), section 1.2.

- **KappaSet is not georeferenced** [7]. The independence check against CloudSEN12+ uses the product ID and the sensing date only; footprints cannot be compared.
- **L8 Biome is pre-collection** [21]. Its quality band (BQA) is decoded by the bit layout of the pre-collection Landsat 8 product guide, not by that of Collection 1 or 2 (section 6). The access page marks for each scene whether shadows are in its mask [21]; how scenes without marked shadow count on the shadow problem is decided before use.
- **KappaMask and Fmask need whole products.** Both run on a whole Level-1C (KappaMask also Level-2A) product, not on 509 x 509 patches ([references/README.md](../references/README.md)); on the datasets above, which ship sub-tiles or subscenes, they are not measured.
- **s2cloudless is CC BY-SA 4.0.** It runs from its installed package under `references/` and is never copied into this repository.
- **CD-FCNN was trained on L8 Biome.** Its weights are named after L8 Biome ([references/README.md](../references/README.md)); a result of CD-FCNN on L8 Biome is not independent of its training data.
- **`IND-02` on the Catalogue stays `not measured`.** Sen2Cor masks for its subscenes would need the Level-2A products, and their download needs credentials.

---

## 6. Open facts

| Fact | What resolves it | Where it is used |
| :--- | :---: | :---: |
| L8 Biome scene layout and the biome of each scene | the downloaded files | `read_biome` |
| L8 SPARCS file names and the band order of its band-interleaved file | the downloaded files | `read_sparcs` |
| Pre-collection quality band (BQA) bit layout | the USGS product guide of pre-collection Landsat 8 Level-1 | `COMPARISON_CODES["reference_landsat_qa"]` |
| Sentinel-2 product naming (processing baseline, tile, sensing date) | the ESA naming convention of Sentinel-2 products | `s2_baseline`, `tile_and_date` |
| CloudSEN12+ field with the Sentinel-2 product ID | the survey report (`reports/data/survey.json`) | `CLOUDSEN12_PRODUCT_FIELD` |
| KappaSet band scale, product ID of a sub-tile, NetCDF read with the locked GDAL | one KappaSet file read on CSC Roihu | `read_kappaset` |
| Sen2Cor SCL codes | the Sen2Cor product documentation, with Table 5 of [1] | `COMPARISON_CODES["reference_sen2cor"]` |
| Input bands of each algorithm of the paper's Table 6 | its primary source | `ALGORITHMS` in `src/tiefer_lab/paper_models.py` |
| Storage billing units of every download | pending maintainer input | [hpc/roihu/plan.md](../hpc/roihu/plan.md) |
| DOI of L8 SPARCS: the page cites 10.5066/F7FB5146, which DataCite titles "L8 SPARCS Cloud Validation Masks" but which resolves to the L8 Biome page; the release metadata cites 10.5066/F7FQ9TQN, which resolves to a retired host (HTTP 503); checked through doi.org and the DataCite API on 16 October 2026 [24] | a DOI that resolves to the SPARCS release | `DATASETS["landsat8_sparcs"].version` |

---

## 7. Distribution

| Dataset | Licence | Download | Size as the source states it | Source |
| :--- | :---: | :---: | :---: | :---: |
| L8 Biome | U.S. Government data; the release metadata states use constraints "none" and points to the Landsat Data Distribution Policy [22]; used since 16 October 2026 | one `.tar.gz` per scene on the access page, no login | not stated on the page; the 96 archives answer 94,130,145,717 bytes in all (HEAD, 16 October 2026); no checksums published | [21], [9] |
| L8 SPARCS | as L8 Biome [23] | `l8cloudmasks.zip` on the USGS page, no login | 1.4 GB on the page; 1,555,733,976 bytes (HEAD, 16 October 2026); no checksum published | [3], [9] |
| Catalogue | CC BY 4.0 | Zenodo record 4172871, no login | `subscenes.zip` 15,197,196,473 bytes, `masks.zip` 7,241,097 bytes, with `classification_tags.csv` and `README.pdf`; MD5 of each on the record | [4] |
| KappaSet | CC BY 4.0 | Zenodo record 7100327, no login | `kappaset.zip` 56,186,308,652 bytes and `README.pdf`; MD5 of each on the record | [6] |
| WHUS2-CD+ | CC BY 4.0 on Zenodo; the GitHub repository states none | Zenodo record 5511793 | 36 product zips of 0.6 to 0.92 GB, `ReferenceMask.zip` 20,946,052 bytes | [11] |
| 38-Cloud | Unknown on Kaggle; the repository's Apache 2.0 file covers its code | Kaggle | 17,051,954,786 bytes | [14] |
| 95-Cloud | CC0 on Kaggle, for the 57 added scenes | Kaggle | 18,563,733,339 bytes | [16] |
| S2-Hollstein | CC BY-NC 4.0 (LICENCE file) or CC BY-NC-SA 4.0 (inside the file) | GFZ GitLab | one HDF5 file | [17] |
| S2-CESBIO | CC BY 4.0 | Zenodo record 1460961 | 234,569,318 bytes | [19] |

The file names, sizes and checksums the code compares are `files` of each dataset in `src/tiefer_lab/data/independent.py`. None of the data is in this repository. CC BY 4.0 asks for attribution: a result on the Catalogue or KappaSet cites its record, and the attribution of both is in [NOTICE.md](../NOTICE.md). `hpc/roihu/independent.sbatch` downloads the Zenodo files at a capped rate and resumes a stopped download.

---

## 8. Coverage of every model on every dataset

`python -m tiefer_lab.paper_models` writes `reports/coverage.md`: one row for each model of this repository and each algorithm of the paper's Table 6, one column for CloudSEN12+ and for each dataset of the paper's Table 1 that the licence decisions allow (section 2.1); a refused or undecided dataset has no column, and a note at the top of the page names each one left out. A cell is `measured` when an evaluation report holds it; otherwise it names the route and its reason:

| Route | Meaning |
| :--- | :---: |
| `shipped` | the dataset ships the algorithm's mask on the same pixels (CloudSEN12+: Sen2Cor, QA60, s2cloudless, UNetMobV2; KappaSet: Sen2Cor, Fmask, s2cloudless) |
| `not used: licence decision` | the source is refused by a licence decision, for example the masks of the CloudSEN12 release of 2022 on the CloudSEN12+ pixels ([DATASETS.md](DATASETS.md), section 1.1) |
| `run` | the published model is run with `references/run_reference.py` on the dataset's cache |
| `needs product` | the full Level-1C product is needed (Sen2Cor, QA60, Fmask on most Sentinel-2 datasets) |
| `open` | a fact is not verified yet, such as the input bands of a learned algorithm |
| `n/a` | it cannot be measured there, for example Sen2Cor or QA60 on Landsat 8, or a model that needs a band the dataset lacks |

`hpc/roihu/evaluate_all.sh` evaluates one run on every allowed dataset whose cache is built, with the baselines and the reference masks each cache holds, and lists the datasets not built yet.

**Third sensor (candidate, for the `IND-01` target).** The target asks for datasets from at least 3 sensors; the allowed datasets of the paper cover two. A candidate outside the paper: the L7 Irish cloud validation masks, 206 pre-collection Landsat 7 ETM+ Level-1G scenes stratified by latitude zone, with manual cloud masks, doi:10.5066/F7XD0ZWC [10]. Its classes, licence and size are not stated on the page; it stays a candidate until the maintainer decides.

---

## 9. Sources

1. CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2, Scientific Data 9, 782, 2022, https://doi.org/10.1038/s41597-022-01878-2, Table 1 and Table 5, full text at Europe PMC (PMC9789947), accessed 14 October 2026.
2. Landsat 8 Cloud Cover Assessment Validation Data, USGS, https://www.usgs.gov/landsat-missions/landsat-8-cloud-cover-assessment-validation-data, accessed 14 October 2026.
3. Spatial Procedures for Automated Removal of Cloud and Shadow (SPARCS) Validation Data, USGS, https://www.usgs.gov/landsat-missions/spatial-procedures-automated-removal-cloud-and-shadow-sparcs-validation-data, accessed 14 October 2026.
4. Sentinel-2 Cloud Mask Catalogue, Zenodo record 4172871, https://zenodo.org/records/4172871, accessed 14 October 2026.
5. Sentinel-2 Cloud Mask Catalogue, README.pdf of record 4172871, accessed 14 October 2026.
6. KappaSet: Sentinel-2 KappaZeta Cloud and Cloud Shadow Masks, Zenodo record 7100327, version 1, https://zenodo.org/records/7100327, accessed 14 October 2026.
7. KappaSet, README.pdf of record 7100327, accessed 14 October 2026.
8. Using the USGS Landsat Level-1 Data Product, USGS, https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product, accessed 14 October 2026.
9. Copyrights and Credits, USGS, https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits, accessed 14 October 2026.
10. Landsat 7 Cloud Cover Assessment Validation Data, USGS, https://www.usgs.gov/landsat-missions/landsat-7-cloud-cover-assessment-validation-data, accessed 14 October 2026.
11. WHUS2-CD+ dataset for Sentinel-2 cloud detection validation, Zenodo record 5511793, https://zenodo.org/records/5511793, accessed 14 October 2026.
12. Li, J. et al., A lightweight deep learning-based cloud detection method for Sentinel-2A imagery fusing multiscale spectral and spatial features, IEEE TGRS, 2021, doi:10.1109/TGRS.2021.3069641, arXiv 2105.00967, accessed 14 October 2026.
13. 38-Cloud README, https://github.com/SorourMo/38-Cloud-A-Cloud-Segmentation-Dataset, accessed 14 October 2026.
14. 38-Cloud on Kaggle, https://www.kaggle.com/datasets/sorour/38cloud-cloud-segmentation-in-satellite-images, version 4, accessed 14 October 2026.
15. 95-Cloud README, https://github.com/SorourMo/95-Cloud-An-Extension-to-38-Cloud-Dataset, accessed 14 October 2026.
16. 95-Cloud on Kaggle, https://www.kaggle.com/datasets/sorour/95cloud-cloud-segmentation-on-satellite-images, version 3, accessed 14 October 2026.
17. Sentinel-2 manual classification database, GFZ GitLab, https://git.gfz-potsdam.de/EnMAP/sentinel2_manual_classification_clouds, accessed 14 October 2026.
18. Hollstein, A. et al., Ready-to-use methods for the detection of clouds, cirrus, snow, shadow, water and clear sky pixels in Sentinel-2 MSI images, Remote Sensing 8, 666, 2016, https://doi.org/10.3390/rs8080666, accessed 14 October 2026.
19. Sentinel-2 reference cloud masks generated by an active learning method, Zenodo record 1460961, https://zenodo.org/records/1460961, accessed 14 October 2026.
20. Baetens, L., Desjardins, C. and Hagolle, O., Validation of Copernicus Sentinel-2 cloud masks obtained from MAJA, Sen2Cor and FMask processors using reference cloud masks generated with a supervised active learning procedure, Remote Sensing 11, 433, 2019, https://doi.org/10.3390/rs11040433, accessed 14 October 2026.
21. Landsat 8 Cloud Cover Assessment Validation Data, access page of the pre-collection release, USGS, https://landsat.usgs.gov/landsat-8-cloud-cover-assessment-validation-data, accessed 16 October 2026.
22. L8 Biome Cloud Validation Masks, metadata file, USGS, https://landsat.usgs.gov/cloud-validation/cca_l8/L8_Biome_Cloud_Validation_Masks.xml, accessed 16 October 2026.
23. L8 SPARCS Cloud Validation Masks, metadata file, USGS, https://landsat.usgs.gov/cloud-validation/sparcs/L8_SPARCS_Cloud_Validation_Masks.xml, accessed 16 October 2026.
24. DataCite REST API, https://api.datacite.org/dois/10.5066/F7251GDH, .../F79Z930Q, .../F7FB5146 and .../F7FQ9TQN, and their resolution through https://doi.org, accessed 16 October 2026. 10.5066/F7251GDH resolves to the L8 Biome page; the older 10.5066/F79Z930Q of the Biome metadata resolves to a retired page (HTTP 404).

---

## Changelog

- 16 October 2026: L8 Biome and L8 SPARCS used and WHUS2-CD+ not used, decisions of 16 October 2026; the DOIs of both Landsat releases checked through the DOI resolver and DataCite: Biome's resolves, SPARCS stays an open fact; drafted with an AI-assisted system.
- 16 October 2026: L8 Biome classes read from its access page; section 5.1, what limits measurement; distribution facts and sizes of the four datasets checked by `check_sources`; drafted with an AI-assisted system.
- 15 October 2026: section 2.1, the Catalogue and KappaSet are used, L8 Biome and L8 SPARCS are candidates without a decision; section 7 points to the attribution in NOTICE.md; drafted with an AI-assisted system.
- 15 October 2026: WHUS2-CD+ is a candidate without a licence decision, treated as not used; the coverage page names the datasets it leaves out; drafted with an AI-assisted system.
- 15 October 2026: section 2.1, the status of each dataset under the maintainer's licence decisions; the refused datasets leave the open facts, the coverage and the evaluation steps; drafted with an AI-assisted system.
- 14 October 2026: all nine datasets of the paper's Table 1: WHUS2-CD+, 38-Cloud, 95-Cloud, S2-Hollstein and S2-CESBIO added with their facts and sources; section 8 is the coverage of every model on every dataset; drafted with an AI-assisted system.
- 14 October 2026: first version: four independent test datasets from the CloudSEN12 paper, their facts with sources, preprocessing, independence, comparison masks, open facts, distribution, the datasets left out and a third-sensor candidate; drafted with an AI-assisted system.
