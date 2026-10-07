<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Licensing

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For users, contributors and evaluators who need to know which licence covers which part of Tiefer Lab. This document owns the licence of every part of the repository and the plain-language summary of MPL 2.0; the licence text is [LICENSE](LICENSE), and attributions of third-party work are in [NOTICE.md](NOTICE.md).

This document is not legal advice.

---

## 1. Licence of each part

| Part | Licence | Where the notice is | Notes |
| :--- | :---: | :---: | :---: |
| Source code (`src/`) | MPL 2.0 | the MPL notice at the top of every file | the empty marker file `src/tiefer_lab/py.typed` has no notice |
| Scripts and job files (`hpc/`, `jetson/`, `.github/`) | MPL 2.0 | the MPL notice at the top of every file | generated lists without a notice: `hpc/roihu/requirements.txt`, `.github/ci-tools/requirements.in` and `.github/ci-tools/requirements.txt`; the repository licence covers them |
| Configurations (`configs/`, `pyproject.toml`, `Makefile`) | MPL 2.0 | the MPL notice at the top of every file | n/a |
| Tests (`tests/`) | MPL 2.0 | the MPL notice at the top of every file | n/a |
| Documentation (every Markdown file) | MPL 2.0 | the status line of every file | n/a |
| Report files (`reports/`) | MPL 2.0 | the repository licence; Markdown reports carry it in their status line | numbers derived from CloudSEN12+ carry the data notice of section 3 |
| `CITATION.cff` | MPL 2.0 | the MPL notice as a comment; `license: MPL-2.0` | n/a |
| `docs/assets/` (header image and logos) | not licensed; all rights reserved by Tiefer | this table | excluded from MPL 2.0; forks remove them ([TRADEMARK.md](TRADEMARK.md)) |
| The Tiefer name and logo | not licensed | [TRADEMARK.md](TRADEMARK.md) | MPL 2.0 section 2.3 grants no trademark rights |
| CloudSEN12+ and its reference masks | CC0 1.0, third-party | [NOTICE.md](NOTICE.md) | not included in the repository; the Copernicus notice applies |
| Trained models (weights, checkpoints, ONNX files) | none; no licence is granted | this table | not in the repository and not distributed from it |
| Dependencies and CI tools | their own licences | [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | installed by the user, not distributed |

---

## 2. MPL 2.0 in plain words

The Mozilla Public License 2.0 [1] is a file-level copyleft licence [2]:

- **Use.** Anyone may use, copy, modify and distribute the covered files, for any purpose, including commercially.
- **What must stay open.** If you distribute a covered file, changed or not, its source code must be available under MPL 2.0, and you may not remove its licence notice (MPL 2.0, sections 3.1 and 3.2). The copyleft applies per file: your own files keep the licence you choose.
- **Larger Work.** You may combine covered files with other code, under other licences, in a Larger Work, provided the covered files stay under MPL 2.0 (MPL 2.0, section 3.3).
- **Secondary Licenses.** MPL 2.0 allows combination with the GNU GPL, LGPL and AGPL, unless a file carries the "Incompatible With Secondary Licenses" notice of Exhibit B. No file in this repository carries Exhibit B.
- **Patents.** Each contributor grants a patent licence for its contributions (MPL 2.0, section 2.1). The grant ends for anyone who sues claiming that a contributor version infringes a patent (MPL 2.0, section 5.2).
- **No warranty and no liability** (MPL 2.0, sections 6 and 7).

The licence text is in [LICENSE](LICENSE); Mozilla's answers to common questions are in its FAQ [2].

---

## 3. Data, models and marks

- The CloudSEN12+ terms, its citations and the Copernicus Sentinel data notice are in [NOTICE.md](NOTICE.md).
- No licence is granted for trained models; they are not distributed from this repository. No pretrained weights are used ([NOTICE.md](NOTICE.md)).
- The use of the Tiefer name and logo is set out in [TRADEMARK.md](TRADEMARK.md).

---

## 4. Contributions

Contributions are accepted under the licence of the repository, MPL 2.0, inbound equals outbound: [CONTRIBUTING.md](CONTRIBUTING.md), section 9. [CLA.md](CLA.md) is a draft and is not in force.

No commercial licence is offered in this repository. For a commercial agreement, write to [hello@tiefer.space](mailto:hello@tiefer.space).

---

## 5. Sources

1. Mozilla Public License, version 2.0, Mozilla, https://www.mozilla.org/en-US/MPL/2.0/, accessed 7 October 2026.
2. MPL 2.0 FAQ, Mozilla, https://www.mozilla.org/en-US/MPL/2.0/FAQ/, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: references to sections of the licence name MPL 2.0, so that they are not read as sections of this document.
- 7 October 2026: this table is the place that states the exclusion of `docs/assets/` and of trained models; NOTICE.md keeps the attributions only.
- 7 October 2026: first version: the licence of each part of the repository, MPL 2.0 in plain words, and the terms of contributions.
