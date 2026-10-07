<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Standards matrix

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How the repository relates to the standards, handbooks and formats a space agency or satellite operator may ask about: one row per document, with its revision, the clause read, the evidence in the repository and the status. A row is only marked `met` or `partly` after its document was read and the clause cited.

---

## 1. Status of this matrix

Status words, as in [STYLE.md](STYLE.md), section 4: `met`, `partly` and `not met` are self-assessed against clauses that were read; `not applicable` means the clause does not apply to this repository; `not read` means the document has not been read yet; `no document` means no standard was chosen or found for the area.

On 7 October 2026 the catalogue pages of every document below were opened, and their identifier, revision, title and issue date are taken from those pages. The PDF of ECSS-E-HB-40-02A downloads without an account. The texts of the ECSS, NASA and CMIX documents and the OpenSSF and SLSA specifications were not read, so their rows stay `not read` and nothing is claimed about any of their clauses. On 2 October 2026, ecss.nl, swehb.nasa.gov, nodis3.gsfc.nasa.gov, standards.nasa.gov and calvalportal.ceos.org could not be reached from the environment where the first version was written. The formats that the repository writes (CycloneDX, SPDX identifiers, Citation File Format, ONNX operator set) were checked against the clause named in their row.

There is no single agency standard for a cloud filter. The repository never states that the software meets an agency's or operator's standard; once a document is read, the correct statement is "self-assessed alignment with <document>, see docs/STANDARDS.md". Qualification for a mission is done with the operator and the satellite prime for that mission's software criticality category. The next review of a row is three months after it was last checked.

---

## 2. Matrix

| Identifier and revision | Title | Issue date | URL | Clause | Evidence | Date read | Owner | Next review | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| ECSS-E-HB-40-02A | Machine learning handbook | 15 November 2024 | [ecss.nl](https://ecss.nl/wp-content/uploads/2024/12/ECSS-E-HB-40-02A%2815November2024%29.pdf) | not read | `docs/DATA.md`, `reports/test_log.md`, `src/tiefer_lab/experiments.py`, `tests/test_experiments.py` | n/a | Tiefer | 7 January 2027 | not read |
| ECSS-E-ST-40C Rev.1 | Software | 30 April 2025 | [ecss.nl](https://ecss.nl/standard/ecss-e-st-40c-rev-1-software-30-april-2025/) | not read | `docs/REQUIREMENTS.md`, `tests/test_requirements_doc.py` | n/a | Tiefer | 7 January 2027 | not read |
| ECSS-Q-ST-80C Rev.2 | Software product assurance | 30 April 2025 | [ecss.nl](https://ecss.nl/standard/ecss-q-st-80c-rev-2-software-product-assurance-30-april-2025/) | not read | `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `uv.lock` | n/a | Tiefer | 7 January 2027 | not read |
| NPR 7150.2D | NASA Software Engineering Requirements | effective 8 March 2022, expires 8 March 2027 | [nodis3.gsfc.nasa.gov](https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7150&s=2D) | not read | `docs/REQUIREMENTS.md`, `src/tiefer_lab/utils/metadata.py` | n/a | Tiefer | 7 January 2027 | not read |
| NASA-STD-8739.8 Version B | Software Assurance and Software Safety Standard | 8 September 2022 (09/08/2022 on the page) | [standards.nasa.gov](https://standards.nasa.gov/standard/NASA/NASA-STD-87398) | not read | `src/tiefer_lab/onboard.py`, `tests/test_onboard.py` | n/a | Tiefer | 7 January 2027 | not read |
| CMIX, Remote Sensing of Environment, doi 10.1016/j.rse.2022.112990 | Cloud Mask Intercomparison eXercise (CMIX): An evaluation of cloud masking algorithms for Landsat 8 and Sentinel-2 | issue of 1 June 2022 | [ntrs.nasa.gov](https://ntrs.nasa.gov/citations/20220006382) | not read | `src/tiefer_lab/binary_metrics.py` | n/a | Tiefer | 7 January 2027 | not read |
| CycloneDX 1.5 | CycloneDX v1.5 JSON Reference | not stated on the page | [cyclonedx.org](https://cyclonedx.org/docs/1.5/json/) | `bomFormat` must be "CycloneDX"; `specVersion` is required | `src/tiefer_lab/sbom.py` (`bomFormat`, `specVersion` 1.5), `tests/test_sbom.py` | 7 October 2026 | Tiefer | 7 January 2027 | partly |
| SPDX License List, `MPL-2.0` | Mozilla Public License 2.0 | n/a | [spdx.org](https://spdx.org/licenses/MPL-2.0.html) | licence identifier `MPL-2.0` | `pyproject.toml` (`license`), `CITATION.cff` (`license`) | 7 October 2026 | Tiefer | 7 January 2027 | met |
| Citation File Format 1.2.0 | Citation File Format (CFF) | n/a | [citation-file-format.github.io](https://citation-file-format.github.io/) | the minimal example on the home page (`cff-version: 1.2.0`, `message`, `title`, `authors`) | `CITATION.cff` | 7 October 2026 | Tiefer | 7 January 2027 | partly |
| ONNX operator set 17 | ONNX versioning, release table | n/a | [github.com/onnx/onnx](https://github.com/onnx/onnx/blob/main/docs/Versioning.md) | operator set 17 is the one of ONNX 1.12.0 | `src/tiefer_lab/config.py` (`opset = 17`), `b0-exp` ([RESULTS.md](RESULTS.md), section 14) | 7 October 2026 | Tiefer | 7 January 2027 | met |
| OpenSSF Scorecard | OpenSSF Scorecard | n/a | [scorecard.dev](https://scorecard.dev/) | not read | `.github/workflows/` | n/a | Tiefer | 7 January 2027 | not read |
| SLSA v1.0 | SLSA specification | n/a | [slsa.dev](https://slsa.dev/spec/v1.0/) | not read | `.github/workflows/ci.yml` | n/a | Tiefer | 7 January 2027 | not read |
| Operational design domain | no document chosen or found | n/a | n/a | n/a | `docs/SPEC.md`, section 9, `src/tiefer_lab/onboard.py` | n/a | Tiefer | 7 January 2027 | no document |
| Operator requirements (Azercosmos) | no public technical standard found | n/a | n/a | n/a | section 5 | n/a | Tiefer | 7 January 2027 | no document |

---

## 3. What the repository does per area

| Identifier | Requirement area | What the repository does |
| :--- | :---: | :---: |
| ECSS-E-HB-40-02A | machine learning life cycle: data management, training, verification of learned models | data card with provenance, fixed splits, validation-only model selection, a guarded test split, run provenance |
| ECSS-E-ST-40C Rev.1 | software requirements and their verification | every requirement has an ID and a linked test or report; a test fails when one is missing |
| ECSS-Q-ST-80C Rev.2 | software product assurance | lint, type checks and tests on every commit; dependencies locked with hashes in `uv.lock`; CodeQL |
| NPR 7150.2D | software engineering requirements | version control, traceable requirements, runs that record commit, config and data revision |
| NASA-STD-8739.8 Version B | software assurance and software safety | fail-safe decision: invalid input or any error sends the frame and flags it; the model file hash is checked before inference |
| CMIX | validation protocol and metric definitions for cloud masks | balanced overall, producer's, user's and overall accuracy per patch, median over patches, with bootstrap intervals; the definitions are compared with the CloudSEN12 paper in [DATASETS.md](DATASETS.md), section 4 |
| CycloneDX 1.5 | software bill of materials | `python -m tiefer_lab.sbom` writes a CycloneDX 1.5 JSON file in CI |
| SPDX License List | licence identifiers | the repository licence is declared as `MPL-2.0` |
| Citation File Format 1.2.0 | software citation | `CITATION.cff` |
| ONNX operator set 17 | model exchange format | every export is pinned to operator set 17 |
| OpenSSF Scorecard | open source security practices | actions pinned by commit, workflow permissions, secret scan, vulnerability audit |
| SLSA v1.0 | supply chain levels | builds run only in GitHub Actions; no release artifacts are published |
| Operational design domain | inputs the filter is designed for | design domain in the specification; frames outside it are sent and flagged |
| Operator requirements (Azercosmos) | what the operator requires | the questions of section 5 are asked instead of assuming answers |

---

## 4. Open facts

| Fact | What resolves it | Where it is used |
| :--- | :---: | :---: |
| The clauses of ECSS-E-HB-40-02A, ECSS-E-ST-40C Rev.1, ECSS-Q-ST-80C Rev.2, NPR 7150.2D and NASA-STD-8739.8 Version B that apply to an onboard cloud filter | reading each document and citing its clauses | section 2 |
| Whether the CMIX paper's metric definitions match those of [DATASETS.md](DATASETS.md), section 4 | reading the CMIX paper | section 2; `src/tiefer_lab/binary_metrics.py` |
| Whether the software bill of materials validates against the CycloneDX 1.5 JSON schema | validating the CI artifact against the schema | section 2 |
| Whether `CITATION.cff` validates against the Citation File Format 1.2.0 schema | validating it with the format's schema | section 2 |
| Issue date of CycloneDX 1.5 | the CycloneDX release notes | section 2 |

---

## 5. Questions for the satellite operator

No public technical standard of Azercosmos was found, so nothing about its requirements is assumed. These are the questions to ask:

1. Which spectral bands does each target sensor deliver on board, with their wavelengths, bit depth, ground sampling distance and radiometric calibration?
2. Which onboard computer runs the filter: processor, accelerator, memory, operating system and the inference runtime it supports?
3. Through which interfaces does the filter receive frames and return decisions, and what must happen when it fails?
4. Which software criticality category applies to the filter, and under which standard is it assessed?
5. What is the acceptance procedure: which tests, data and documents does the operator require before the software flies?
6. How are model updates signed, uplinked and verified on board?

---

## Changelog

- 7 October 2026: the matrix has the columns of docs/STYLE.md, section 12.9, with the status last, and one row per document; what the repository does per area moves to section 3.
- 7 October 2026: revisions and dates from the catalogue pages opened on 7 October 2026: ECSS-E-HB-40-02A of 15 November 2024 (a handbook), ECSS-E-ST-40C Rev.1 and ECSS-Q-ST-80C Rev.2 of 30 April 2025, NPR 7150.2D effective 8 March 2022, NASA-STD-8739.8 Version B of 8 September 2022, and CMIX as its paper in Remote Sensing of Environment.
- 7 October 2026: new rows for CycloneDX 1.5 (`partly`), the SPDX identifier `MPL-2.0` (`met`), Citation File Format 1.2.0 (`partly`) and ONNX operator set 17 (`met`), each with the clause read; OpenSSF Scorecard and SLSA v1.0 as `not read`.
- 7 October 2026: rows without a chosen document have the status `no document` instead of `not applicable`.
- 7 October 2026: the evidence of ECSS-E-HB-40-02A cites `src/tiefer_lab/experiments.py` and its test, since `reports/experiments.md` is not committed; open facts move out of table cells into section 4.
- 2 October 2026: first version; every document not read, questions for the operator listed.
