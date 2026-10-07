<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Datasets and their roles

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Which datasets the cloud filter uses or may use, the role each one plays, how labels from different datasets are made comparable, and which metrics are reported for comparison with published results. The facts the code depends on for CloudSEN12+ are in [DATA.md](DATA.md).

---

## 1. Roles

A dataset has exactly one role per experiment. The validation split chooses models and settings; the test split is only read with `--final`, and every such read is logged where it runs. At least eight test evaluations ran on 3 October 2026 (`b0-test`, `b1-test`, `f0-test`, `s-test`, `x-test-3`, `x-test-4`, `x-test-6`, `x-test-13` in docs/RESULTS.md, Appendix A); their log entries are on CSC Roihu and pending a copy into `reports/test_log.md`, which has no entries yet.

| Dataset | Role | Status |
| :--- | :---: | :---: |
| CloudSEN12+ Level-1C, training split, high quality labels | training | facts checked against card 1.1.2 (DATA.md, section 2) |
| CloudSEN12+ Level-1C, validation split | model and setting selection | facts checked against card 1.1.2 |
| CloudSEN12+ Level-1C, test split | independent test: never used for selection | facts checked against card 1.1.2 |
| CloudSEN12+ scribble and nolabel patches, training split, away from val and test locations | extra training data only | TODO(verify) from the survey (DATA.md, section 5A) |
| CloudSEN12+ extra variant, reference masks | comparison algorithms on the same patches, not ground truth | TODO(verify) from the survey (DATA.md, section 2) |
| Any other dataset | none until its row in section 2 is checked | not checked |

The test split is independent of the training patches, not of the dataset: it shares the labelling protocol, the sensor and the processing level. A result on it says nothing about other sensors (section 2 and [RESULTS.md](RESULTS.md), section 18).

---

## 2. Candidates, not checked from primary sources

Other public cloud mask datasets could serve as a second independent test or as cross-sensor tests. None of them was checked from a primary source for this repository: the dataset pages could not be reached when this file was written. Until a row is checked, the dataset is not used, and no fact about it is stated here.

| Candidate | Sensor, bands, resolution | Classes | Licence | Possible role once checked | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Sentinel-2 Cloud Mask Catalogue | TODO(verify) | TODO(verify) | TODO(verify) | second independent test on Sentinel-2 | not checked |
| KappaSet | TODO(verify) | TODO(verify) | TODO(verify) | second independent test on Sentinel-2 | not checked |
| Landsat 8 Biome cloud validation data | TODO(verify) | TODO(verify) | TODO(verify) | cross-sensor test | not checked |
| 38-Cloud and 95-Cloud | TODO(verify) | TODO(verify) | TODO(verify) | cross-sensor test | not checked |
| Data from the target sensor | to be provided by the operator (STANDARDS.md, section 3) | not applicable | not applicable | the decisive test for a mission | not available |

To check a candidate: read its primary source (paper or data page), fill every column with a link, add its reader behind a `TODO(verify)` stop like the CloudSEN12+ reader, and record it in this table's changelog.

---

## 3. Harmonisation

Rules for making another dataset's labels and images comparable to the four classes of this repository. They apply once a candidate is checked.

- **Classes:** each source class maps to clear (0), thick cloud (1), thin cloud (2), cloud shadow (3) or unlabelled (255). A source that does not separate thick and thin cloud is scored on the cloud problem only (binary metrics, section 4); a source without shadow is not scored on shadow. The reference masks of the extra variant follow the same rule (`MaskEncoding` in `src/tiefer_lab/data/source.py`).
- **Unlabelled pixels:** fill values, no-data and unlabelled pixels map to 255 and are left out of every metric.
- **Bands:** a band is used only when its centre wavelength and width are checked against the sensor's documentation and match a Sentinel-2 band closely enough to be named the same; all other bands are unavailable, and the band-flexible model runs with the band set that remains. Matching rules per sensor are TODO(verify).
- **Values:** top-of-atmosphere reflectance with the scale and offset from the sensor's documentation; a source given only in digital numbers or surface reflectance is not used until its conversion is checked.
- **Resolution:** frames are resampled to 10 m before inference and the mask back to the frame's size (`tiefer_lab.onboard.predict_frame`).

---

## 4. Metrics for comparison with published results

Published cloud mask comparisons, such as the CloudSEN12+ paper and the CEOS Cloud Mask Intercomparison eXercise, report per-patch accuracies for binary problems. The repository reports the same kind of numbers next to its own four-class metrics:

| Metric | Definition in this repository | Matches the published definition |
| :--- | :---: | :---: |
| Balanced overall accuracy (BOA) | (TP / (TP + FN) + TN / (TN + FP)) / 2 per patch, median over patches | TODO(verify) |
| Producer's accuracy (PA) | TP / (TP + FN) per patch, median over patches | TODO(verify) |
| User's accuracy (UA) | TP / (TP + FP) per patch, median over patches | TODO(verify) |
| Overall accuracy (OA) | (TP + TN) / all valid pixels per patch, median over patches | TODO(verify) |

The cloud problem is thick plus thin cloud against the rest; the shadow problem is cloud shadow against the rest (`src/tiefer_lab/binary_metrics.py`). Published values are never placed next to these measurements until the definitions are verified (`PAPER_DEFINITION_VERIFIED` and `PUBLISHED` in the code); [STANDARDS.md](STANDARDS.md) lists the comparison exercise as not read.

---

## 5. Richness

How varied each built split is (class shares, cloud cover bins, shadow, verified metadata fields) is reported by `python -m tiefer_lab.data.richness`; see [DATA.md](DATA.md), section 12.

---

## Changelog

- 7 October 2026: correction: the test log entries of 3 October 2026 are on CSC Roihu and pending a copy into `reports/test_log.md`.
- 7 October 2026: the link to the limitations follows the new section numbers of RESULTS.md.
- 2 October 2026: first version; only CloudSEN12+ is checked, other candidates are listed as not checked.
