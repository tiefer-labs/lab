<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: CloudSEN12+ for the cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What data milestone L1 trains and evaluates on, which facts about it the code depends on, how each fact was checked, and what the data does not represent.

---

## 1. Source

|  | Value |
| :--- | :---: |
| Dataset | CloudSEN12+, Level-1C variant, labels of quality high only, 509 x 509 patches only |
| Publisher | TACO Foundation on Hugging Face: [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Licence | CC0 1.0 |
| Dataset card version | 1.1.2 |
| Reader | `tacoreader` 0.5.6 (v1 API) and `rasterio`; the card example uses 0.5.3, and 0.5.6 works on CSC Roihu |
| Revision used | not yet recorded: the builder writes it to `index.json` |
| Included in this repository | no; patches are read at run time and cached outside git |

The dataset is not part of this repository. `python -m tiefer_lab.data.build_cache` reads only the four used bands and the label of each selected patch; the full dataset (about 248 GB according to the specification) is never downloaded.

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
| Bands used | B02, B03, B04, B08 (rasterio indexes 2, 3, 4, 8) | follows from the band order; tested in `tests/test_bands_and_labels.py` |
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
| Reference masks | `cloudmask_qa60`, `cloudmask_sen2cor`, `cloudmask_s2cloudless`, `cloudmask_cloudscore_cs_v1`, `cloudmask_cloudscore_cs_cdf_v1`, `cloudmask_unetmobv2_v1`, `cloudmask_unetmobv2_v2`, `cloudmask_sensei_v2`, in the extra variant | [card 1.1.2](https://huggingface.co/datasets/tacofoundation/cloudsen12); not read by the cache builder yet |

---

## 3. Bands used and why

Only blue, green, red and near infrared (Sentinel-2 B02, B03, B04 and B08, all at 10 m) are used. Very high resolution optical satellites, the sensors Tiefer targets, typically carry these four bands plus panchromatic, and not the shortwave infrared bands that classic cloud algorithms rely on. The data is Level-1C (top-of-atmosphere reflectance) because there is no atmospheric correction on board. See [ASSUMPTIONS.md](ASSUMPTIONS.md).

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
| train | not yet measured | not yet measured | not yet measured |
| validation | not yet measured | not yet measured | not yet measured |
| test | not yet measured | not yet measured | not yet measured |

---

## 6. Normalisation

Per-band mean and standard deviation of top-of-atmosphere reflectance are computed on the training split only, over all pixels of the cached patches, and stored in `index.json` (`normalisation`). Validation and test use the same statistics.

---

## 7. Known biases

The geographic, seasonal and land cover distribution of the high quality patches has not yet been analysed in this repository. Every patch keeps its scalar metadata in the cache index, and evaluation reports break results down by every metadata field with a small number of distinct values, with sample counts, so imbalances become visible in the results. Any statement about bias in this card will cite such a report.

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

Add `--limit <n>` for a small subset. The build is resumable: run the same command again after an interruption. On CSC Roihu use `hpc/roihu/data.sbatch` (see [hpc/roihu/README.md](../hpc/roihu/README.md)).

---

## Changelog

- 1 October 2026: dataset facts checked against the card, version 1.1.2; only 509 x 509 patches are kept, with kept and dropped counts per split; `roi_id` is the patch identifier; the split field is still `TODO(verify)`.
- 1 October 2026: first version; dataset facts marked `TODO(verify)` because the dataset card was not reachable from the build environment.
