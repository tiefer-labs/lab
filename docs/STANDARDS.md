<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Standards matrix

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How the repository relates to the standards and handbooks a space agency or satellite operator may ask about: one row per requirement area, with the source document and clause, what the repository does, the evidence, and the status. A row is only marked "met" or "partly" after its document was read and the clause cited.

---

## 1. Status of this matrix

None of the documents below could be read when this matrix was written (2 October 2026): ecss.nl, swehb.nasa.gov, nodis3.gsfc.nasa.gov, standards.nasa.gov and calvalportal.ceos.org were not reachable from the environment where it was written. Every row is therefore "not read", nothing is claimed about any clause, and the "What the repository does" column only describes the repository. The rows are to be completed by reading each document, citing its version and clause.

There is no single agency standard for a cloud filter. The repository never states that the software meets an agency's or operator's standard; once a document is read, the correct statement is "self-assessed alignment with <document>, see docs/STANDARDS.md". Qualification for a mission is done with the operator and the satellite prime for that mission's software criticality category.

---

## 2. Matrix

| Requirement area | Source document and clause | What the repository does | Evidence | Status |
| :--- | :---: | :---: | :---: | :---: |
| Machine learning life cycle: data management, training, verification of learned models | ECSS-E-HB-40-02A, 15 November 2024 ([ecss.nl](https://ecss.nl/)), clauses not read | Data card with provenance and leakage checks, fixed splits, validation-only model selection, a guarded test split, run provenance | `docs/DATA.md`, `reports/test_log.md`, `reports/experiments.md` | not read |
| Software requirements and their verification | ECSS-E-ST-40C ([ecss.nl](https://ecss.nl/)), clauses not read | Every requirement has an ID and a linked test or report; a test fails when one is missing | `docs/REQUIREMENTS.md`, `tests/test_requirements_doc.py` | not read |
| Software product assurance | ECSS-Q-ST-80C ([ecss.nl](https://ecss.nl/)), clauses not read | Lint, type checks and tests on every commit; pinned dependencies with hashes in `uv.lock`; CodeQL | `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `uv.lock` | not read |
| Software engineering requirements | NASA NPR 7150.2D ([nodis3.gsfc.nasa.gov](https://nodis3.gsfc.nasa.gov/)) with the NASA Software Engineering Handbook ([swehb.nasa.gov](https://swehb.nasa.gov/)), clauses not read | Version control, traceable requirements, reproducible runs with recorded commit, config and data version | `docs/REQUIREMENTS.md`, `src/tiefer_lab/utils/metadata.py` | not read |
| Software assurance and software safety | NASA-STD-8739.8 ([standards.nasa.gov](https://standards.nasa.gov/)), clauses not read | Fail-safe decision: invalid input or any error sends the frame and flags it; the model file hash is checked before inference | `src/tiefer_lab/onboard.py`, `tests/test_onboard.py` | not read |
| Validation protocol and metric definitions for cloud masks | CEOS Cloud Mask Intercomparison eXercise (CMIX) ([calvalportal.ceos.org](https://calvalportal.ceos.org/)), sections not read | Overall, balanced overall, producer's and user's accuracy per patch, median over patches, with bootstrap intervals; the dataset paper's definition is also TODO(verify) | `src/tiefer_lab/binary_metrics.py` | not read |
| Operational design domain and fail-safe behaviour | no document chosen yet | Design domain in the specification; frames outside it are sent and flagged | `docs/SPEC.md`, `src/tiefer_lab/onboard.py` | not applicable |
| Operator requirements | Azercosmos: no public technical standard was found | The questions in section 3 are asked instead of assuming answers | this page, section 3 | not applicable |

---

## 3. Questions for the satellite operator

No public technical standard of Azercosmos was found, so nothing about its requirements is assumed. These are the questions to ask:

1. Which spectral bands does each target sensor deliver on board, with their wavelengths, bit depth, ground sampling distance and radiometric calibration?
2. Which on-board computer runs the filter: processor, accelerator, memory, operating system and the inference runtime it supports?
3. Through which interfaces does the filter receive frames and return decisions, and what must happen when it fails?
4. Which software criticality category applies to the filter, and under which standard is it assessed?
5. What is the acceptance procedure: which tests, data and documents does the operator require before the software flies?
6. How are model updates signed, uplinked and verified on board?

---

## Changelog

- 2 October 2026: first version; every document not read, questions for the operator listed.
