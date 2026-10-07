<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: CloudSEN12+ for the cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What data milestones L1 and L2 train and evaluate on, answered in the order of the usual datasheet questions, followed by the facts the code depends on and the caches built on CSC Roihu.

---

## 1. Motivation

| Question | Answer | Source |
| :--- | :---: | :---: |
| Why does this repository use the data? | to train and evaluate a cloud and cloud shadow filter that decides on board whether a frame is worth sending | [SPEC.md](SPEC.md) |
| Who created the dataset? | the CloudSEN12 and CloudSEN12+ authors; published by the TACO Foundation on Hugging Face | [1], [3] |
| What does the dataset card say it is? | "The largest dataset of expert-labeled pixels for cloud and cloud shadow detection in Sentinel-2" (version 1.1.2) | [1] |
| Why this dataset? | it has dense labels of the four classes this repository predicts, on Sentinel-2 Level-1C, under CC0 1.0 | [1] |

---

## 2. Composition

One instance is one Sentinel-2 Level-1C patch with 13 bands and one label item. This repository keeps only patches with high quality labels and an original size of 509 x 509 pixels (section 5).

### 2.1 Bands

The 13 bands of the Level-1C image item, in the order of the card [1]. The resolutions are those of the card and of ESA [5], which agree. The card gives a centre wavelength per band; ESA gives the equivalent wavelength of each band of Sentinel-2A [5]. The scale factor is 0.0001 for every band except B10, for which the card gives "N/A".

| Band | Name on the card | Resolution | Centre wavelength, card | Equivalent wavelength, Sentinel-2A | Used by |
| :--- | :---: | :---: | :---: | :---: | :---: |
| B01 | Coastal aerosol | 60 m | 443.5 nm | 442.7 nm | L2 set of 13 |
| B02 | Blue | 10 m | 496.5 nm | 492.7 nm | L1; L2 sets of 3, 4, 6 and 13 |
| B03 | Green | 10 m | 560.0 nm | 559.9 nm | L1; L2 sets of 3, 4, 6 and 13 |
| B04 | Red | 10 m | 664.5 nm | 664.6 nm | L1; L2 sets of 3, 4, 6 and 13 |
| B05 | Red edge 1 | 20 m | 704.5 nm | 704.1 nm | L2 set of 13 |
| B06 | Red edge 2 | 20 m | 740.5 nm | 740.5 nm | L2 set of 13 |
| B07 | Red edge 3 | 20 m | 783.0 nm | 782.8 nm | L2 set of 13 |
| B08 | NIR | 10 m | 840.0 nm | 832.8 nm | L1; L2 sets of 4, 6 and 13 |
| B8A | Red edge 4 | 20 m | 864.5 nm | 864.7 nm | L2 set of 13 |
| B09 | Water vapor | 60 m | 945.0 nm | 945.1 nm | L2 set of 13 |
| B10 | Cirrus | 60 m | 1375.5 nm | 1373.5 nm | L2 set of 13 |
| B11 | SWIR 1 | 20 m | 1613.5 nm | 1613.7 nm | L2 sets of 6 and 13 |
| B12 | SWIR 2 | 20 m | 2199.5 nm | 2202.4 nm | L2 sets of 6 and 13 |

The four band sets of the band-flexible L2 model (`train.band_sets` in the `l2_flex_*` configs): 3 bands B02, B03, B04; 4 bands B02, B03, B04, B08; 6 bands B02, B03, B04, B08, B11, B12; and all 13 bands.

Milestone L1 and the four-band L2 specialist use B02, B03, B04 and B08 (rasterio indexes 2, 3, 4 and 8). Very high resolution optical satellites, the sensors Tiefer targets, carry these four bands and often a panchromatic band, and not the shortwave infrared bands that classic cloud algorithms rely on ([ASSUMPTIONS.md](ASSUMPTIONS.md), section 1). The band-flexible L2 model is trained on these band sets and scored per band set. The data is Level-1C, top-of-atmosphere reflectance, because there is no atmospheric correction on board.

### 2.2 Classes

| Class index | Name | Meaning | Source |
| :--- | :---: | :---: | :---: |
| 0 | clear | no cloud and no cloud shadow | [1] |
| 1 | thick cloud | cloud that hides the surface | [1] |
| 2 | thin cloud | semi-transparent cloud through which the surface is still visible | [1] |
| 3 | cloud shadow | surface in the shadow of a cloud | [1] |
| 255 | no label | pixel without a label; the loss ignores it (`IGNORE_INDEX`) | `src/tiefer_lab/data/source.py` |

The codes 0 to 3 and their names are those of the card; the meanings are this repository's short description of the card's definitions. Class 255 is this repository's own and appears only in the extra training patches (section 11), never in high quality labels. The cloud fraction of a frame counts thick and thin cloud; cloud shadow is reported separately.

### 2.3 Split sizes

The dataset's own train, validation and test splits are used. The cache builder writes the number of high quality patches, the number kept and the number dropped per split to `index.json` (`splits.<split>.selection`: `high_quality`, `kept_509`, `dropped_other_shape`).

| Split | High quality patches | Kept (509 x 509) | Dropped (other size) | Class shares | Source |
| :--- | :---: | :---: | :---: | :---: | :---: |
| train | pending | 8,490 | pending | pending | kept: builds of 2 October 2026 |
| validation | pending | 535 | pending | [RESULTS.md](RESULTS.md), section 5 | kept and shares: `b0-val` (report) |
| test | pending | 975 | pending | pending | kept: `b0-test` (h-c3e861a) |
| total | pending | 10,000 | pending | pending | sum of the rows |

The source keys are those of [RESULTS.md](RESULTS.md), section 2. The high quality and dropped counts and the training class shares are pending until `index.json` of the cache is read; the test class shares are pending until `b0-test` is copied into the repository.

### 2.4 Metadata fields

Every patch keeps its scalar metadata in the cache index. The fields this repository relies on, with the card's description [1]:

| Field | Meaning | Used for |
| :--- | :---: | :---: |
| `roi_id` | unique identifier of the region of interest (also `old_roi_id`, the previous identifier) | patch ID in every report |
| `label_type` | `high`, `scribble` or `nolabel` | selection of high quality patches |
| `real_proj_shape` | original size of the patch before padding: 509 or 2000 | selection of 509 x 509 patches |
| `equi_id` | identifier in the Equi7Grid system | breakdown in reports |
| `equi_zone` | zone of the Equi7Grid system | breakdown in reports |
| `thick_percentage`, `thin_percentage`, `cloud_shadow_percentage`, `clear_percentage` | share of each class estimated by the annotator for high quality labels; derived from UNetMobV2-V1 predictions for scribble and nolabel patches | breakdown in reports |

The Equi7Grid has seven continental zones, each with its own projection: AF Africa, AN Antarctica, AS Asia, EU Europe, NA North America, OC Oceania and SA South America [4]. The validation split has patches in six of them (section 6.3).

---

## 3. Collection and labelling

| Question | Answer | Source |
| :--- | :---: | :---: |
| How were the patches selected and labelled? | image patches were selected by the authors' cloud detection expert group and labelled by hand with the IRIS active learning tool, after a calibration phase for the labellers and followed by quality control | [3], Methods |
| How well do labels agree? | the paper compares the manual labels before and after its quality control: median balanced overall accuracy (BOA) 0.99 for cloud and 0.99 for cloud shadow on its 975 test patches | [3], Table 6 |
| Agreement per class | producer's accuracy 0.991 clear, 0.966 thick cloud, 0.780 thin cloud and 0.918 cloud shadow | [3], Methods, quality control phase |
| Are the labels complete? | high quality labels are dense; scribble labels are partial; nolabel patches have none | [1] |
| Is there personal or sensitive data? | none known; Sentinel-2 images at 10 m do not show individuals | this card |

The agreement values are for the labels of the 2022 release and its test set, not for the revision this repository reads: the card says that all labels of the previous version were curated and refined in version 1.1.0 [1].

---

## 4. Preprocessing by the dataset authors

- The `cloudsen12-l1c` variant holds Sentinel-2 Level-1C patches, stored as digital numbers with a scale factor of 0.0001 [1]; the builder checks at run time that they are uint16.
- The card says that the images are padded from 509 x 509 to 512 x 512 and from 2000 x 2000 to 2048 x 2048, with zeros on the left and bottom sides, so that the patch size is divisible by 32; `real_proj_shape` keeps the original size [1].
- The card gives 99 as the no-data value, and says that scribble and nolabel patches contain it [1].
- The card says that the cloud masks of the `cloudsen12-extra` variant, which come from several sources, have not been normalised to the CloudSEN12 class schema [1].
- The Level-2A variant of the dataset was processed by Google Earth Engine [1]; this repository does not use it.

---

## 5. Preprocessing in this repository

| Step | What the code does | Where |
| :--- | :---: | :---: |
| Selection | keeps `label_type` = `high` and `real_proj_shape` = 509; the 2000 x 2000 patches are left out (below) | `src/tiefer_lab/data/source.py` |
| Bands | stores the four L1 bands, or all 13 with `--bands all`; a model selects its bands from the cache when it loads it | `src/tiefer_lab/data/build_cache.py`, `src/tiefer_lab/data/cache.py` |
| Labels | maps the label codes 0 to 3 to the class indexes 0 to 3; any other code stops the build | `src/tiefer_lab/data/source.py` |
| Reflectance | reflectance = DN x 0.0001 | `src/tiefer_lab/data/source.py` |
| Normalisation | per-band mean and standard deviation of reflectance, computed on the training split only over all pixels of the cached patches, stored in `index.json` (`normalisation`) and used for every split | `src/tiefer_lab/data/build_cache.py` |
| Class weights | the pixels per class of the training split (`class_pixels` in `index.json`) give median-frequency weights for the loss; L1 configs use them (the default), every L2 config except `l2_flex_1m_classweights` sets `class_weighting = "none"` | `src/tiefer_lab/train.py`; [ASSUMPTIONS.md](ASSUMPTIONS.md), section 6 |
| Training crops | random crops with flips and rescaling | `src/tiefer_lab/data/dataset.py` |
| Evaluation padding | each full patch is reflect-padded at the bottom and right to a multiple of 32, and the prediction is cropped back to the label's size | `src/tiefer_lab/data/dataset.py`, `src/tiefer_lab/data/transforms.py` |

The builder reads each raster as it is stored and does not remove the card's padding (section 4). The confusion matrix of `l1_base s0` on the validation split counts 140,247,040 labelled pixels ([RESULTS.md](RESULTS.md), section 5), which is 535 x 512 x 512; a 509 x 509 patch has 259,081 pixels. So the cached validation patches are 512 x 512, and the 3 padded rows and 3 padded columns, 3,063 pixels per patch, are part of every cached patch, of the normalisation statistics and of every metric. What label code the padded label pixels hold is an open fact (section 13); if it is 0, they count as clear. The stored height and width of each split are in `index.json` (`splits.<split>.height` and `width`).

The 2000 x 2000 patches are left out: the export input is fixed at 512 x 512, and a 2000 x 2000 patch holds 15.4 times the pixels of a 509 x 509 patch.

The normalisation values of each cache are pending until `index.json` is read (section 10).

---

## 6. Uses and limits

### 6.1 Intended use

Training and evaluation of the cloud filter of milestones L1 and L2, and scoring of other cloud masks on the same test pixels ([LANDSCAPE.md](LANDSCAPE.md), section 5).

### 6.2 What the data does not represent

- Very high resolution sensors: CloudSEN12+ is Sentinel-2 at 10 m to 60 m; Tiefer's target sensors have much finer ground sampling, different spectral responses and different noise.
- Onboard radiometry: the patches are processed Level-1C products (section 4), not raw onboard data.
- Compression artefacts: the patches do not show the compression an onboard pipeline may apply before or after the filter.
- Space environment effects: radiation, thermal and vacuum effects on the sensor or the computer are not in the data.

### 6.3 Known biases

Evaluation reports break results down by every scalar metadata field with between 2 and 30 distinct values (`MAX_GROUPS` = 30 in `src/tiefer_lab/evaluate.py`), with the patch count of each group, so imbalances become visible in the results. Any statement about bias in this card cites such a report.

First measurement: the breakdown of `l1_base s0` on the validation split by `equi_zone`, in six zones, is in [RESULTS.md](RESULTS.md), section 9. The causes of the difference are not analysed. The seasonal and land cover distribution is not analysed.

### 6.4 Leakage between splits

The splits are the dataset's own. Whether a training patch shares its location with a validation or test patch has not been checked on the built high quality caches: the check `python -m tiefer_lab.data.cache overlap <cache> <field>` needs the location field, which is an open fact (section 13). The extra training patches are built only once that check can run (section 11).

---

## 7. Distribution

| Question | Answer | Source |
| :--- | :---: | :---: |
| Publisher | TACO Foundation on Hugging Face: [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) | [1] |
| Licence | CC0 1.0 | [1] |
| Total size | 248 GB, as the Hugging Face page states it | [1] |
| Format | TACO v1 (`.taco` files), read by `tacoreader` 0.5.6 and `rasterio`; the card's example uses `tacoreader` 0.5.3 | [1], `uv.lock` |
| Included in this repository | no; patches are read at run time and cached outside git | `src/tiefer_lab/data/build_cache.py` |

`python -m tiefer_lab.data.build_cache` reads only the bands it is asked for and the label of each selected patch; the full dataset is never downloaded.

CloudSEN12+ is CC0 1.0, so no citation is required, but the work behind it is cited here. These are the citations of the card [1]:

- Scientific Data, 2022: [10.1038/s41597-022-01878-2](https://doi.org/10.1038/s41597-022-01878-2)
- Data in Brief, 2024: [10.1016/j.dib.2024.110852](https://doi.org/10.1016/j.dib.2024.110852)
- IGARSS 2023: [10.1109/IGARSS52108.2023.10282381](https://doi.org/10.1109/IGARSS52108.2023.10282381)

Titles and authors are listed at the DOI links; this repository names no individuals.

---

## 8. Maintenance

| Question | Answer | Source |
| :--- | :---: | :---: |
| Dataset card version | 1.1.2 | [1] |
| Revision read | `f9490f7de11b4f387f72ef800e73ccbb754711de`, the `sha` field of the Hugging Face dataset API, last modified 5 January 2025, 14:47:21 UTC | [2] |
| How the revision is recorded | the builder writes the `sha` field to `index.json` at build time, and every evaluation report copies it ([RESULTS.md](RESULTS.md), section 4) | `src/tiefer_lab/data/source.py` |
| Is the revision pinned? | no; it is recorded, not pinned: the reader reads the current revision, so a rebuild, a resumed build or a merge of shards can read a newer revision than the one recorded first | `src/tiefer_lab/data/source.py` |
| Revision of the 13-band cache | pending until its `index.json` is read | section 10 |
| What changes when the dataset changes | a new revision means a new cache; the facts of section 9 are checked again against the card | this card |

---

## 9. Facts the code depends on

Each fact is defined once, in `src/tiefer_lab/data/source.py`, and checked at run time where the last column says so.

| Fact | Value in the code | Source | Checked at run time |
| :--- | :---: | :---: | :---: |
| **Access** | | | |
| Reader API | `tacoreader.load(name)` returns a metadata table; `table.read(i)` returns the sample; `sample.read(k)` returns a GDAL virtual file path for item `k` | source of `tacoreader` 0.5.6 (`uv.lock`); 2.x rejects `tacofoundation:` names | no |
| Level-1C variant name | `tacofoundation:cloudsen12-l1c` | [1] | no |
| Variant with the reference masks | `tacofoundation:cloudsen12-extra` | [1] | no |
| Dataset revision | `sha` field of the Hugging Face dataset API | [2] | recorded at build time |
| **Image** | | | |
| Band order of the image item | B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12 | [1] | yes: 13 bands, and band descriptions when present |
| Scale factor | reflectance = DN x 0.0001, no offset | [1] | no |
| Data type | uint16 | run-time check | yes |
| Patch size field | `real_proj_shape`, 509 or 2000; only 509 is kept | [1] | yes: kept and dropped counts in `index.json` |
| **Labels and metadata** | | | |
| Label codes | 0 clear, 1 thick cloud, 2 thin cloud, 3 cloud shadow | [1] | yes: any other code stops the build |
| Item positions in a sample | `read(0)` image, `read(1)` label | [1] | yes: label shape equals image shape |
| Split field and values | `tortilla:data_split`: `train`, `validation`, `test` | builds of 2 October 2026 ([RESULTS.md](RESULTS.md), section 5) | yes: the reader stops when the field is missing |
| Quality field and value | `label_type` = `high` | [1] | yes |
| Patch ID field | `roi_id` | [1] | no |
| Row key | `tortilla:id`, used only to sort rows and to resume a build | source of `tacoreader` 0.5.6 | no |
| Reference mask names | `cloudmask_qa60`, `cloudmask_sen2cor`, `cloudmask_s2cloudless`, `cloudmask_cloudscore_cs_v1`, `cloudmask_cloudscore_cs_cdf_v1`, `cloudmask_unetmobv2_v1`, `cloudmask_unetmobv2_v2`, `cloudmask_sensei_v2` | [1] | no |
| Reference mask link, item names and encodings | `REFERENCE_LINK_FIELD`, `REFERENCE_MASK_ITEMS`, `REFERENCE_ENCODINGS`: not set | open fact (section 13) | `build_cache --references` stops with a clear message |

The card does not name the split field. The caches of 2 October 2026 were built with `tortilla:data_split` and the values `train`, `validation` and `test`, and gave 8,490, 535 and 975 kept patches; the reader stops when the field is missing, so the builds confirm the field and its values for revision `f9490f7de11b`.

---

## 10. Caches built

The four-band cache (the default name):

```bash
python -m tiefer_lab.data.build_cache --split train
python -m tiefer_lab.data.build_cache --split val
python -m tiefer_lab.data.build_cache --split test
```

The 13-band cache:

```bash
python -m tiefer_lab.data.build_cache --split all --bands all --name cloudsen12-l1c-all
```

| Option | Effect |
| :--- | :---: |
| `--split train`, `val`, `test`, `train_extra` or `all` | the split to build; `all` builds train, validation and test; `train_extra` holds the extra training patches (section 11) |
| `--bands used` (default) or `--bands all` | stores the four L1 bands or all 13 Level-1C bands |
| `--limit <n>` | builds only `n` patches per split |
| `--name <name>` | cache folder name in `$TIEFER_DATA_DIR` |
| `--shard I/N` | builds part I of N of a split in its own folder |
| `--merge N` | merges the N complete shards of a split into the cache |
| `--max-rate P` | caps the reads at P patches per minute for the whole split, shared between shards |
| `--workers <n>` | parallel readers; default `SLURM_CPUS_PER_TASK`, else 4 |
| `--taco <name>` | dataset file, URL or catalogue name; default `tacofoundation:cloudsen12-l1c`; repeatable |
| `--revision <sha>` | records this dataset revision; it does not select the revision that is read |
| `--references` | adds the reference masks of the extra variant to a complete split |
| `--restart` | replaces a split built or being built with another selection |
| `--synthetic`, `--patch-size <n>`, `--seed <n>` | writes synthetic scenes instead of reading the dataset; needs `--limit` |

A 509 x 509 patch takes 13 x 509 x 509 x 2 + 509 x 509 bytes, 6.67 MiB, with all bands, and 4 x 509 x 509 x 2 + 509 x 509 bytes, 2.22 MiB, with four; the builder prints the estimate for each split before it starts. The build is resumable: run the same command again after an interruption, and a split that is already complete is left as it is. A build with another selection into a folder that holds a complete or partly built split stops with an error instead of replacing it; use another `--name` or `$TIEFER_DATA_DIR`, or pass `--restart`. On CSC Roihu use `hpc/roihu/data.sbatch` ([hpc/roihu/README.md](../hpc/roihu/README.md)).

The caches built on CSC Roihu:

| Cache | Bands | Dataset revision | Build jobs and dates | Size on disk | Configs that use it | Normalisation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `cloudsen12-l1c-high` | 4: B02, B03, B04, B08 | `f9490f7de11b4f387f72ef800e73ccbb754711de` | validation split built 2 October 2026, 05:42 UTC; jobs pending | about 22 GiB (notes) | `l1_base`, `l1_full`; `l2_spec_1m s0`: pending | pending (`index.json`) |
| `cloudsen12-l1c-all` | all 13 | pending (`index.json`) | training split: shards 1 to 3 in jobs 1999650, 1999651 and 1999652, shard 0 in job 2000731, merge in job 2000814 ([RESULTS.md](RESULTS.md), section 16); validation and test jobs pending | about 66 GiB (notes); the builder's estimate is 65.1 GiB | every L2 config; `l2_spec_1m s0`: pending | pending (`index.json`) |

The cache that `l2_spec_1m s0` read is pending: the session notes say the four-band cache, while `configs/l2_spec_1m.toml` names `cloudsen12-l1c-all`. The run's `config.toml` decides it; the config file is not changed until then. The training split of `cloudsen12-l1c-all` was built in 4 shards of 2,122 or 2,123 patches. Shard 0 failed in job 1999649 with HTTP 404 from the dataset host, and job 2000731 ran it again with `--max-rate 120` and resumed where it had stopped.

---

## 11. Extra training patches

Besides the high quality patches, the card lists the label types `scribble` and `nolabel` [1]. They can add training data, never evaluation data, under three rules, each checked by the code:

- Only 509 x 509 patches of the training split are used.
- A patch is dropped when its location appears in any row of the validation or test split, of any label type. `python -m tiefer_lab.data.cache overlap <cache> <field>` proves it on a built cache: it reads the metadata in the index and exits with an error when a training patch shares a location with validation or test, or lacks the field.
- Scribble labels are partial: unlabelled pixels get class index 255 and the loss ignores them. Nolabel patches have no label; every pixel is 255.

Until `LOCATION_FIELD` and `SCRIBBLE_UNLABELLED_CODE` are set in `src/tiefer_lab/data/source.py`, the build of the `train_extra` split stops with a clear message. The facts that set them come from the survey (`hpc/roihu/survey.sbatch`) and are listed in section 13. The high quality 2000 x 2000 patches stay out: whether they show new locations, and whether tiling them to 509 x 509 is sound, is not decided by the facts verified so far; the survey reports their counts and locations.

---

## 12. Richness report

`python -m tiefer_lab.data.richness <cache-name>` writes `$TIEFER_REPORTS_DIR/data/richness_<cache-name>.json` for every complete split of a built cache:

- patch count and the pixel share of each class;
- patches per cloud cover bin (thick plus thin cloud as a share of labelled pixels: below 0.1, 0.1 to 0.3, 0.3 to 0.7, 0.7 to 0.9, 0.9 and above) and patches that contain shadow;
- distinct values of the fields `roi_id`, `label_type` and `real_proj_shape`.

Other metadata fields are listed by name only, and the report draws no conclusion about geography, season or land cover from them.

---

## 13. Open facts

| Fact | What resolves it | Where it is used |
| :--- | :---: | :---: |
| Label code of the padded pixels of a cached patch | label histogram of the padded rows and columns, or the survey | section 5; every metric |
| Stored height and width of the training and test patches | `index.json` of each cache (`splits.<split>.height`, `width`) | section 5 |
| Dataset revision of the 13-band cache | `index.json` of `cloudsen12-l1c-all` | sections 8 and 10 |
| High quality and dropped counts per split | `index.json` (`splits.<split>.selection`) | section 2.3 |
| Normalisation values of each cache | `index.json` (`normalisation`) | sections 5 and 10 |
| Field that identifies a patch's location (candidates: `roi_id`, `stac:centroid`) | survey report (`overlap_with_val_test`) | sections 6.4 and 11; `LOCATION_FIELD` |
| Code of unlabelled pixels in scribble labels: the card gives 99 as the no-data value [1]; the code is set after the survey's label histograms confirm it | survey report | section 11; `SCRIBBLE_UNLABELLED_CODE` |
| Number of scribble and nolabel patches, and whether they carry a split | survey report | section 11 |
| Whether `tacofoundation:cloudsen12-extra` has reference masks for the scribble and nolabel patches | survey report | section 11 |
| Link field between a Level-1C row and its row in the extra variant, item name and encoding of each reference mask | survey report (`extra.link_to_l1c`, `extra.samples[*].items[*].name`, value histograms) | section 9; `build_cache --references` |

---

## 14. Sources

1. CloudSEN12+ dataset card, version 1.1.2, TACO Foundation, Hugging Face, https://huggingface.co/datasets/tacofoundation/cloudsen12, accessed 7 October 2026.
2. Hugging Face dataset API, `tacofoundation/cloudsen12`, https://huggingface.co/api/datasets/tacofoundation/cloudsen12, accessed 7 October 2026.
3. CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2, Scientific Data, 2022, https://doi.org/10.1038/s41597-022-01878-2, full text at https://pmc.ncbi.nlm.nih.gov/articles/PMC9789947/, accessed 7 October 2026.
4. Equi7Grid, README, TUW-GEO, GitHub, https://github.com/TUW-GEO/Equi7Grid, accessed 7 October 2026.
5. S2 Mission, spectral and spatial resolution, ESA SentiWiki, https://sentiwiki.copernicus.eu/web/s2-mission, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: restructured to the data card of docs/STYLE.md: the sections follow the datasheet questions, then the facts the code depends on, the caches, the extra training patches, the richness report, open facts and sources. Section 5A is now section 11, and links from other files are updated.
- 7 October 2026: the split field `tortilla:data_split` is confirmed by the cache builds of 2 October 2026; one `TODO(verify)` resolved.
- 7 October 2026: the dataset revision is checked against the Hugging Face API (`sha` field, accessed 7 October 2026); one `TODO(verify)` resolved.
- 7 October 2026: a table of the 13 bands with the card's names, resolutions and centre wavelengths, the Sentinel-2A equivalent wavelengths from ESA, and the four L2 band sets.
- 7 October 2026: the cached validation patches are 512 x 512 and hold the card's padding (140,247,040 labelled pixels in `b0-val`, 535 x 512 x 512); the label code of the padded pixels is an open fact.
- 7 October 2026: the dataset revision is recorded, not pinned; the extra-variant masks are not normalised to the class schema (card); class weights from the training class pixels; every build option.
- 7 October 2026: class 255 (no label) in the class table, and the split total of 10,000 kept patches.
- 7 October 2026: the meaning of `equi_zone` (continental zone of the Equi7Grid) from the Equi7Grid README.
- 7 October 2026: the card's zero padding to 512 x 512 and no-data value 99, and the open fact of whether the cached patches hold the padding.
- 7 October 2026: the breakdown rule of the evaluation reports (fields with 2 to 30 distinct values) and the leakage check between splits, which has not run.
- 7 October 2026: the total size of 248 GB is sourced to the Hugging Face page instead of the specification; the reader version is stated once.
- 7 October 2026: the remaining `TODO(verify)` facts are listed in one open facts table (section 13).
- 7 October 2026: section 11, how the images were selected and labelled and the human agreement, from the CloudSEN12 paper (Table 6 and Technical Validation); two `TODO(verify)` resolved.
- 7 October 2026: one table of the caches built on CSC Roihu, with the cache of `l2_spec_1m` seed 0 recorded as pending.
- 7 October 2026: L2 also reads all 13 bands (sections 1, 2, 3 and 10); the 13-band cache, its size and its build in shards; the dataset revision and the kept counts per split; a first measurement of geographic bias by `equi_zone` (section 7).
- 2 October 2026: data sheet (section 11) and richness report (section 12).
- 2 October 2026: reference masks from the extra table, added to a split once their link and encodings are verified.
- 2 October 2026: extra training patches (scribble and nolabel) away from val and test, with the facts still to verify; 2000 x 2000 patches stay out.
- 2 October 2026: all 13 bands (`--bands all`), shards, a rate cap and a disk estimate.
- 2 October 2026: a build with another selection never replaces an existing split without `--restart`.
- 1 October 2026: dataset facts checked against the card, version 1.1.2; only 509 x 509 patches are kept, with kept and dropped counts per split; `roi_id` is the patch identifier; the split field is still `TODO(verify)`.
- 1 October 2026: first version; dataset facts marked `TODO(verify)` because the dataset card was not reachable from the build environment.
