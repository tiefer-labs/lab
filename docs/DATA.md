<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: CloudSEN12+ for the cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What data milestones L1 and L2 train and evaluate on, which facts about it the code depends on, how each fact was checked, and what the data does not represent.

---

## 1. Source

|  | Value |
| :--- | :---: |
| Dataset | CloudSEN12+, Level-1C variant, labels of quality high only, 509 x 509 patches only |
| Publisher | TACO Foundation on Hugging Face: [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Licence | CC0 1.0 |
| Dataset card version | 1.1.2 |
| Reader | `tacoreader` 0.5.6 (v1 API) and `rasterio`; the card example uses 0.5.3, and 0.5.6 works on CSC Roihu |
| Revision used | `f9490f7de11b4f387f72ef800e73ccbb754711de`, written by the builder to `index.json` and copied into every evaluation report ([RESULTS.md](RESULTS.md), section 4) |
| Included in this repository | no; patches are read at run time and cached outside git |

The dataset is not part of this repository. `python -m tiefer_lab.data.build_cache` reads only the bands it is asked for and the label of each selected patch: the four L1 bands by default, or all 13 Level-1C bands with `--bands all` (section 10). The full dataset (about 248 GB according to the specification) is never downloaded.

> [!NOTE]
> The facts below were checked against the dataset card, version 1.1.2, on 1 October 2026. Two facts are still marked `TODO(verify)`: the split field, which the card does not name, and the revision field of the Hugging Face API, which was not checked. The reader prints the metadata columns once per build and stops with a clear message when the split field or another field it needs is missing.

---

## 2. Facts the code depends on

All of these are defined once, in `src/tiefer_lab/data/source.py`.

| Fact | Value in the code | How it was checked |
| :--- | :---: | :---: |
| **Access** | | |
| Reader API | `tacoreader.load(name)` returns a metadata table; `table.read(i)` returns the sample; `sample.read(k)` returns a GDAL virtual file path for item `k` | verified by reading the source of `tacoreader` 0.5.6 ([PyPI](https://pypi.org/project/tacoreader/0.5.6/)); 2.x rejects `tacofoundation:` names and refers to 0.x for them |
| Level-1C variant name | `tacofoundation:cloudsen12-l1c` | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Variant with the reference masks | `tacofoundation:cloudsen12-extra` | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Dataset format | TACO v1 (`.taco` files), read by `tacoreader` 0.5 | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12): its example uses `tacoreader` 0.5.3; 0.5.6 works on CSC Roihu |
| Dataset revision | `sha` field of the Hugging Face dataset API, recorded at build time | TODO(verify) the [API response](https://huggingface.co/api/datasets/tacofoundation/cloudsen12) |
| **Image** | | |
| Band order of the image item | B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12 | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time: 13 bands, and band descriptions when present |
| Bands used | L1 and the four-band specialist: B02, B03, B04, B08 (rasterio indexes 2, 3, 4, 8); the band-flexible L2 model: any of the 13 | follows from the band order; tested in `tests/test_bands_and_labels.py` and `tests/test_cache.py` |
| Scale factor | reflectance = DN x 0.0001, no offset | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Data type | uint16 | checked at run time |
| Patch size | field `real_proj_shape`, 509 or 2000; only 509 is kept, as the export input is 512 x 512 | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); kept and dropped counts are written to `index.json` |
| **Labels and metadata** | | |
| Label codes | 0 clear, 1 thick cloud, 2 thin cloud, 3 cloud shadow | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time: any other code stops the build |
| Item positions in a sample | `read(0)` image, `read(1)` label | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Split field and values | `tortilla:data_split`: `train`, `validation`, `test` | TODO(verify): the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) does not name it; checked at run time, and the reader prints the metadata columns to find it |
| Quality field and value | `label_type` = `high` (values high, scribble, nolabel) | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time |
| Patch ID field | `roi_id` (also `old_roi_id`), used in every report | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Row key | `tortilla:id`, used only to sort rows and to resume a build | `tacoreader` source |
| Reference masks: how a row of the extra table links to a Level-1C row, the item name of each mask, and how each mask is encoded (four classes, or cloud against non-cloud) | `REFERENCE_LINK_FIELD`, `REFERENCE_MASK_ITEMS`, `REFERENCE_ENCODINGS` | TODO(verify) from the survey; until then `build_cache --references` stops with a clear message |
| Reference masks | `cloudmask_qa60`, `cloudmask_sen2cor`, `cloudmask_s2cloudless`, `cloudmask_cloudscore_cs_v1`, `cloudmask_cloudscore_cs_cdf_v1`, `cloudmask_unetmobv2_v1`, `cloudmask_unetmobv2_v2`, `cloudmask_sensei_v2`, in the extra variant | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); added to a complete split by `build_cache --references` once their encodings are verified |

---

## 3. Bands used and why

Milestone L1 uses only blue, green, red and near infrared (Sentinel-2 B02, B03, B04 and B08, all at 10 m). Very high resolution optical satellites, the sensors Tiefer targets, typically carry these four bands plus panchromatic, and not the shortwave infrared bands that classic cloud algorithms rely on. Milestone L2 also reads all 13 Level-1C bands: the band-flexible model is trained on band sets drawn from them and scored per band set (3, 4, 6 and 13 bands), and the four-band specialist keeps the four L1 bands. The data is Level-1C (top-of-atmosphere reflectance) because there is no atmospheric correction on board. See [ASSUMPTIONS.md](ASSUMPTIONS.md), sections 1 and 7.

---

## 4. Classes

| Class index | Name | Meaning |
| :--- | :---: | :---: |
| 0 | clear | no cloud and no cloud shadow |
| 1 | thick cloud | cloud that hides the surface |
| 2 | thin cloud | semi-transparent cloud through which the surface is still visible |
| 3 | cloud shadow | surface in the shadow of a cloud |

The codes and names are those of the [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); the meanings column is this repository's short description. The cloud fraction of a frame counts thick and thin cloud; cloud shadow is reported separately.

---

## 5. Split sizes

The dataset's own train, validation and test splits are used. Of the high quality patches of a split, only those with `real_proj_shape` 509 are kept; the 2000 x 2000 patches are dropped. The cache builder prints both counts and writes them to `index.json` (`splits.<split>.selection`: `high_quality`, `kept_509`, `dropped_other_shape`); the number of cached patches is `splits.<split>.count` and is copied into every evaluation report.

| Split | High quality patches | Kept (509 x 509) | Dropped (other size) |
| :--- | :---: | :---: | :---: |
| train | pending | 8490 | pending |
| validation | pending | 535 | pending |
| test | pending | 975 | pending |

The kept counts are those of the caches built on CSC Roihu on 2 October 2026 ([RESULTS.md](RESULTS.md), section 5); the high quality and dropped counts are in `index.json` of the cache and are pending until it is read.

---

## 5A. Extra training patches

Besides the high quality patches, the card lists the label types `scribble` and `nolabel`. They can add training data, never evaluation data, under three rules, each checked by the code:

- Only 509 x 509 patches of the training split are used.
- A patch is dropped when its location appears in any row of the validation or test split, of any label type. `python -m tiefer_lab.data.cache overlap <cache> <field>` proves it on a built cache: it reads the metadata in the index and exits with an error when a training patch shares a location with val or test, or lacks the field.
- Scribble labels are partial: unlabelled pixels get class index 255 and the loss ignores them. Nolabel patches have no label; every pixel is 255.

Two facts are still `TODO(verify)` and must be read from the survey (`hpc/roihu/survey.sbatch`) before these patches are built; until they are set in `src/tiefer_lab/data/source.py`, the build of the `train_extra` split stops with a clear message:

| Fact | Where it is set | Status |
| :--- | :---: | :---: |
| The field that identifies a patch's location (candidates in the metadata: `roi_id`, `stac:centroid`) | `LOCATION_FIELD` | TODO(verify) from the survey |
| The code of unlabelled pixels in scribble labels | `SCRIBBLE_UNLABELLED_CODE` | TODO(verify) from the survey |
| How many scribble and nolabel patches there are, and whether they carry a split | survey report | TODO(verify) from the survey |
| Whether `tacofoundation:cloudsen12-extra` has reference masks for them | survey report | TODO(verify) from the survey |

The high quality 2000 x 2000 patches stay out. Whether they show new locations and whether tiling them to 509 x 509 is sound cannot be decided from the facts verified so far; the survey reports their counts and locations.

---

## 6. Normalisation

Per-band mean and standard deviation of top-of-atmosphere reflectance are computed on the training split only, over all pixels of the cached patches, and stored in `index.json` (`normalisation`). Validation and test use the same statistics.

---

## 7. Known biases

Every patch keeps its scalar metadata in the cache index, and evaluation reports break results down by every metadata field with a small number of distinct values, with sample counts, so imbalances become visible in the results. Any statement about bias in this card cites such a report.

First measurement: the validation split by the field `equi_zone` has EU 105, SA 40, AS 100, NA 160, AF 80 and OC 50 patches (535 in all), and the mean IoU of `l1_base` seed 0 ranges from 0.685 (EU) to 0.561 (OC) over these groups ([RESULTS.md](RESULTS.md), section 9). The meaning of the codes is not verified from the card (section 12), and the causes of the difference are not analysed. The seasonal and land cover distribution has not yet been analysed.

---

## 8. What the data does not represent

- Very high resolution sensors: CloudSEN12+ is Sentinel-2 at 10 m; Tiefer's target sensors have much finer ground sampling, different spectral responses and different noise.
- Onboard radiometry: the patches are processed Level-1C products (radiometric and geometric corrections, orthorectification), not raw onboard data.
- Compression artefacts: the patches do not show the compression an onboard pipeline may apply before or after the filter.
- Space environment effects: radiation, thermal and vacuum effects on the sensor or the computer are not in the data.

---

## 9. Citation

CloudSEN12+ is CC0 1.0, so no citation is required, but the work behind it is cited here. These are the citations of the [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12):

- Scientific Data, 2022: [10.1038/s41597-022-01878-2](https://doi.org/10.1038/s41597-022-01878-2)
- Data in Brief, 2024: [10.1016/j.dib.2024.110852](https://doi.org/10.1016/j.dib.2024.110852)
- IGARSS 2023: [10.1109/IGARSS52108.2023.10282381](https://doi.org/10.1109/IGARSS52108.2023.10282381)

Titles and authors are listed at the DOI links; this repository names no individuals.

---

## 10. Building the cache

```bash
python -m tiefer_lab.data.build_cache --split train
python -m tiefer_lab.data.build_cache --split val
python -m tiefer_lab.data.build_cache --split test
```

`--bands all` stores all 13 Level-1C bands instead of the four L1 bands; models select their bands from the cache when they load it, so one cache serves every band set. A 509 x 509 patch takes 13 x 509 x 509 x 2 + 509 x 509 bytes, about 6.7 MiB, with all bands, and about 2.2 MiB with four; the builder prints the estimate for each split before it starts. `--shard I/N` builds part I of N of a split in its own folder and `--merge N` joins the shards; `--max-rate P` caps the reads per minute of the whole split.

The caches built on CSC Roihu:

| Cache | Bands | Dataset revision | Build jobs and dates | Size on disk | Configs that use it | Normalisation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `cloudsen12-l1c-high` | 4: B02, B03, B04, B08 | `f9490f7de11b4f387f72ef800e73ccbb754711de` | validation split built 2 October 2026, 05:42 UTC; jobs pending | about 22 GiB (notes) | `l1_base`, `l1_full`; `l2_spec_1m` seed 0: pending (notes say this cache; its config names `cloudsen12-l1c-all`) | pending (`index.json`) |
| `cloudsen12-l1c-all` | all 13 | pending (`index.json`) | training split in 4 shards, then merged (jobs in [RESULTS.md](RESULTS.md), section 16); validation and test jobs pending | about 66 GiB (notes); the builder's estimate is 65.1 GiB | every L2 config; `l2_spec_1m` seed 0: pending | pending (`index.json`) |

The cache that `l2_spec_1m` seed 0 read is pending: the session notes say the four-band cache, while `configs/l2_spec_1m.toml` names `cloudsen12-l1c-all`. Its run `config.toml` decides it; the config file is not changed until then. The training split of `cloudsen12-l1c-all` was built in 4 shards and merged; shard 0 failed with HTTP 404 from the dataset host and was submitted again, and the build resumed where it had stopped.

Add `--limit <n>` for a small subset. The build is resumable: run the same command again after an interruption, and a split that is already complete is left as it is. A build with another selection (for example `--limit`) into a folder that holds a complete or partly built split stops with an error instead of replacing it; use another `--name` or `$TIEFER_DATA_DIR`, or pass `--restart` to replace it on purpose. On CSC Roihu use `hpc/roihu/data.sbatch` (see [hpc/roihu/README.md](../hpc/roihu/README.md)).

---

## 11. Data sheet

Short answers to the usual data sheet questions, pointing to the section that holds the detail.

| Question | Answer |
| :--- | :---: |
| **Motivation** | |
| Why is the data used? | to train and evaluate a cloud and shadow filter that decides on board whether a frame is worth sending |
| Who created the dataset? | the CloudSEN12+ authors, published by the TACO Foundation (section 1, section 9) |
| **Composition** | |
| What is one instance? | one Sentinel-2 Level-1C patch of 509 x 509 pixels with 13 bands and a four-class label (section 2) |
| How many instances? | 8490 training, 535 validation and 975 test patches kept (section 5) |
| Is it a sample of a larger set? | yes: high quality labels and 509 x 509 patches only (sections 1 and 5) |
| Are labels complete? | high quality labels are dense; scribble labels are partial and nolabel patches have none (section 5A) |
| Is there personal or sensitive data? | none known; satellite images at 10 m do not show individuals |
| **Collection and labelling** | |
| How were images selected and labelled? | image patches were selected by the authors' cloud detection expert group and labelled by hand with the IRIS active learning tool, after a calibration phase for the labellers and followed by quality control (Scientific Data paper, Methods, opened on 7 October 2026: [PMC9789947](https://pmc.ncbi.nlm.nih.gov/articles/PMC9789947/)) |
| Human agreement on thin cloud and shadow | the paper compares the manual labels before and after its quality control: median BOA 0.99 for cloud and 0.99 for cloud shadow on its 975 test patches (Table 6); producer's accuracy 0.991 clear, 0.966 thick cloud, 0.780 thin cloud and 0.918 cloud shadow (Methods, quality control phase). These values are for the labels of the 2022 release and its test set, not for this repository's revision, whose labels were refined in version 1.1.0 (card 1.1.2) |
| **Preprocessing in this repository** | |
| What is done to the data? | selection, band selection at load time, reflectance scale, normalisation from the training split (sections 3, 6 and 10) |
| **Uses** | |
| What should it not be used for? | conclusions about other sensors, raw onboard data, compression or space environment effects (section 8) |
| **Distribution and maintenance** | |
| Licence | CC0 1.0 (section 1) |
| Revision used | recorded in `index.json` at build time (section 2) |

---

## 12. Richness report

`python -m tiefer_lab.data.richness <cache-name>` writes `$TIEFER_REPORTS_DIR/data/richness_<cache-name>.json` for every complete split of a built cache:

- patch count and the pixel share of each class;
- patches per cloud cover bin (thick plus thin cloud as a share of labelled pixels: below 0.1, 0.1 to 0.3, 0.3 to 0.7, 0.7 to 0.9, 0.9 and above) and patches that contain shadow;
- distinct values of the verified fields `roi_id`, `label_type` and `real_proj_shape`.

Other metadata fields are listed by name only. Their meaning is not verified from the card, so the report draws no conclusion about geography, season or land cover from them; section 7 stays open until such a field is verified.

---

## Changelog

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
