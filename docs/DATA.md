<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: CloudSEN12+ for the cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What data milestone L1 trains and evaluates on, which facts about it the code depends on, how each fact was checked, and what the data does not represent.

---

## 1. Source

|  | Value |
| :--- | :---: |
| Dataset | CloudSEN12+, Level-1C variant, labels of quality high only |
| Publisher | TACO Foundation on Hugging Face: [tacofoundation/cloudsen12](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Licence | CC0 1.0 |
| Reader | `tacoreader` 0.5.6 (v1 API) and `rasterio` |
| Revision used | not yet recorded: the builder writes it to `index.json` |
| Included in this repository | no; patches are read at run time and cached outside git |

The dataset is not part of this repository. `python -m tiefer_lab.data.build_cache` reads only the four used bands and the label of each selected patch; the full dataset (about 248 GB according to the specification) is never downloaded.

> [!NOTE]
> The build environment of Part A could not reach `huggingface.co` (blocked by its network policy). Every fact below that comes from the dataset card is therefore marked `TODO(verify)` and must be checked against the card before the first real cache build. The reader also checks each of them against the data at run time and stops with a clear message when one does not hold.

---

## 2. Facts the code depends on

All of these are defined once, in `src/tiefer_lab/data/source.py`.

| Fact | Value in the code | How it was checked |
| :--- | :---: | :---: |
| **Access** | | |
| Reader API | `tacoreader.load(name)` returns a metadata table; `table.read(i)` returns the sample; `sample.read(k)` returns a GDAL virtual file path for item `k` | verified by reading the source of `tacoreader` 0.5.6 ([PyPI](https://pypi.org/project/tacoreader/0.5.6/)); 2.x rejects `tacofoundation:` names and refers to 0.x for them |
| Level-1C variant name | `tacofoundation:cloudsen12-l1c` | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Dataset format | TACO v1 (`.taco` files), read by `tacoreader` 0.5 | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) that the dataset is still published in this format |
| Dataset revision | `sha` field of the Hugging Face dataset API, recorded at build time | TODO(verify) the [API response](https://huggingface.co/api/datasets/tacofoundation/cloudsen12) |
| **Image** | | |
| Band order of the image item | B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12 | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time: 13 bands, and band descriptions when present |
| Bands used | B02, B03, B04, B08 (rasterio indexes 2, 3, 4, 8) | follows from the band order; tested in `tests/test_bands_and_labels.py` |
| Scale factor | reflectance = DN x 0.0001 + 0.0 | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12), including whether an offset applies |
| Data type | uint16 | checked at run time |
| Patch size | read from the data; all patches of a split must share it | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12); export assumes at most 512 x 512 |
| **Labels and metadata** | | |
| Label codes | 0 clear, 1 thick cloud, 2 thin cloud, 3 cloud shadow | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time: any other code stops the build |
| Item positions in a sample | image item 0, label item 1 | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| Split field and values | `tortilla:data_split`: `train`, `validation`, `test` | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time |
| Quality field and value | `label_type` = `high` | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12); checked at run time |
| Patch ID field | `tortilla:id` | the reader sorts by this column (`tacoreader` source); TODO(verify) its meaning on the card |
| Reference masks | none configured | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) which algorithm masks ship with the dataset |

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

The meanings are the usual CloudSEN12 definitions; TODO(verify) the exact wording on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12). The cloud fraction of a frame counts thick and thin cloud; cloud shadow is reported separately.

---

## 5. Split sizes

The dataset's own train, validation and test splits are used. Counts are written by the cache builder to `index.json` (`splits.<split>.count`) and copied into every evaluation report.

| Split | High quality patches |
| :--- | :---: |
| train | not yet measured |
| validation | not yet measured |
| test | not yet measured |

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

CloudSEN12+ is CC0 1.0, so no citation is required, but the work behind it is cited here:

- CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2. Scientific Data, 2022. DOI `10.1038/s41597-022-01878-2`. TODO(verify) at [doi.org](https://doi.org/10.1038/s41597-022-01878-2).
- CloudSEN12+: the largest dataset of expert-labeled pixels for cloud and cloud shadow detection in Sentinel-2. Data in Brief, 2024. DOI `10.1016/j.dib.2024.110852`. TODO(verify) at [doi.org](https://doi.org/10.1016/j.dib.2024.110852).

Authors are listed at the DOI links; this repository names no individuals.

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

- 1 October 2026: first version; dataset facts marked `TODO(verify)` because the dataset card was not reachable from the build environment.
