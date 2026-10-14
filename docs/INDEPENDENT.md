<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: independent test datasets

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The four datasets that test the cloud filter on data it never saw: what each one is, the facts the code depends on with their sources, how they are made comparable with CloudSEN12+, and the facts still open. They are never used for training, selection, calibration or thresholds. The catalogue row of each is in [DATASETS.md](DATASETS.md), section 1; the code is `src/tiefer_lab/data/independent.py`.

---

## 1. Motivation

| Question | Answer | Source |
| :--- | :---: | :---: |
| Why are independent datasets used? | a result on the CloudSEN12+ test split shares its labelling protocol, sensor and processing level with the training data; acceptance targets `IND-01` to `IND-04` and `CMP-06` need data labelled by others, on Sentinel-2 and on another sensor | [REQUIREMENTS.md](REQUIREMENTS.md), section 8 |
| Why these four? | they are four of the nine datasets the CloudSEN12 paper lists next to CloudSEN12 (Table 1): worldwide or broad coverage, full or partial scenes with cloud shadow, and two sensors | [1], Table 1 |
| Why not the others? | see section 8 | [1], Table 1 |
| Are they independent of the models? | yes for training: no model of this repository reads them before its selection is frozen; Sentinel-2 products that CloudSEN12+ also uses are dropped first (section 5) | `build_cache --source` |

---

## 2. Composition

| Dataset | Sensor and processing level | Size | Classes | Strata | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| L8 Biome (`landsat8_biome`) | Landsat 8 OLI and TIRS, pre-collection Level-1T | 96 scenes | not stated on the page; `TODO(verify)` | biome of each scene | [2] |
| L8 SPARCS (`landsat8_sparcs`) | Landsat 8, pre-collection Level-1 | 80 subsets of 1000 x 1000 pixels | 0 shadow, 1 shadow over water, 2 water, 3 snow, 4 land, 5 cloud, 6 flooded | none | [3] |
| Sentinel-2 Cloud Mask Catalogue (`s2_cloud_catalogue`) | Sentinel-2 Level-1C, 2018 archive | 513 subscenes of 1022 x 1022 pixels at 20 m | CLEAR, CLOUD, CLOUD_SHADOW (one-hot) | 11 surface type tags, difficulty, shadows marked or not | [4], [5] |
| KappaSet (`kappaset`) | Sentinel-2 Level-1C | 9,251 sub-tiles of 512 x 512 pixels at 10 m from 1,038 products | 0 undefined, 1 clear, 2 cloud shadow, 3 semi-transparent cloud, 4 cloud, 5 missing | season | [6], [7] |

- The Catalogue marks shadow in 424 subscenes; in 89, shadow could not be annotated, so the shadow problem is scored only on tiles with `shadows_marked` = 1 [5].
- The KappaSet README says the data mostly covers land (about 91 percent) with some water (about 9 percent), about 7 percent contains snow, and the sub-tiles have no georeferencing [7].
- The paper's Table 1 lists the KappaZeta dataset with 155 scenes in Northern Europe [1]; the KappaSet record of 2022 has 1,038 products distributed over the globe [6]. This card uses the record of 2022.

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

---

## 6. Open facts

| Fact | What resolves it | Where it is used |
| :--- | :---: | :---: |
| L8 Biome label codes | the data release files, or the paper that describes them (doi:10.1016/j.rse.2017.03.026, not yet opened) | `DATASETS["landsat8_biome"].label_codes` |
| L8 Biome scene layout and the biome of each scene | the downloaded files | `read_biome` |
| L8 SPARCS file names and the band order of its band-interleaved file | the downloaded files | `read_sparcs` |
| Pre-collection quality band (BQA) bit layout | the USGS product guide of pre-collection Landsat 8 Level-1 | `COMPARISON_CODES["reference_landsat_qa"]` |
| Sentinel-2 product naming (processing baseline, tile, sensing date) | the ESA naming convention of Sentinel-2 products | `s2_baseline`, `tile_and_date` |
| CloudSEN12+ field with the Sentinel-2 product ID | the survey report (`reports/data/survey.json`) | `CLOUDSEN12_PRODUCT_FIELD` |
| KappaSet band scale, product ID of a sub-tile, NetCDF read with the locked GDAL | one KappaSet file read on CSC Roihu | `read_kappaset` |
| Sen2Cor SCL codes | the Sen2Cor product documentation, with Table 5 of [1] | `COMPARISON_CODES["reference_sen2cor"]` |
| Licence of L8 Biome and L8 SPARCS | their pages state none; the USGS policy page says USGS-authored or produced data are in the U.S. Public Domain [9]; the maintainer confirms that it covers these releases | `DATASETS[...].licence` |
| Download sizes and storage billing units of the Landsat datasets | the maintainer's download on CSC Roihu | [hpc/roihu/plan.md](../hpc/roihu/plan.md) |

---

## 7. Distribution

| Dataset | Licence | Download | Size as the source states it | Source |
| :--- | :---: | :---: | :---: | :---: |
| L8 Biome | U.S. Public Domain under the USGS policy, to be confirmed (section 6) | the USGS page | not stated on the page | [2], [9] |
| L8 SPARCS | as L8 Biome | the USGS page | 1.4 GB | [3], [9] |
| Catalogue | CC BY 4.0 | Zenodo record 4172871 | `subscenes.zip` 15,197,196,473 bytes, `masks.zip` 7,241,097 bytes | [4] |
| KappaSet | CC BY 4.0 | Zenodo record 7100327 | `kappaset.zip` 56,186,308,652 bytes | [6] |

None of the data is in this repository. CC BY 4.0 asks for attribution: a result on the Catalogue or KappaSet cites its record, and [NOTICE.md](../NOTICE.md) gains the attribution when the first such result is published. `hpc/roihu/independent.sbatch` downloads the Zenodo files at a capped rate and resumes a stopped download.

---

## 8. Datasets left out

| Dataset (paper name) | Why it is left out | Source |
| :--- | :---: | :---: |
| S2-Hollstein | labels are polygons over 59 scenes, very few pixels | [1], Table 1 |
| L8-38Cloud, L8-95Cloud | United States only, cloud class only; kept as candidates | [1], Table 1; [DATASETS.md](DATASETS.md) |
| WHUS2-CD | China only, cloud class only | [1], Table 1 |
| S2-CESBIO | small (38 scenes, Europe); kept as the replacement if the overlap check removes too much of KappaSet | [1], Table 1 |

**Third sensor (candidate, for the `IND-01` target).** The target asks for datasets from at least 3 sensors; the four above cover two. A candidate outside the paper: the L7 Irish cloud validation masks, 206 pre-collection Landsat 7 ETM+ Level-1G scenes stratified by latitude zone, with manual cloud masks, doi:10.5066/F7XD0ZWC [10]. Its classes, licence and size are not stated on the page; it stays a candidate until the maintainer decides.

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

---

## Changelog

- 14 October 2026: first version: four independent test datasets from the CloudSEN12 paper, their facts with sources, preprocessing, independence, comparison masks, open facts, distribution, the datasets left out and a third-sensor candidate; drafted with an AI-assisted system.
