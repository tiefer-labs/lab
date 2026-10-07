<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Measurement and release policy

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For everyone who writes, quotes or releases a number, a model or a statement from Tiefer Lab. This document owns the gates each of them must pass; who decides is in [GOVERNANCE.md](GOVERNANCE.md), and which result is current is in [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md).

---

## 1. How the gates work

Every gate has a rule, the evidence that shows it is met, who checks it, and what happens when it is broken. The maintainer ([GOVERNANCE.md](GOVERNANCE.md), section 1) checks every gate before a merge to `main` or a statement in public. A broken gate is corrected, never hidden: the affected document gets a changelog line that starts with "correction:", and [CLAIMS.md](CLAIMS.md) records the change when the statement was public.

| Gate | Applies to |
| :--- | :---: |
| 1 | a number on a results page |
| 2 | a number quoted outside the repository |
| 3 | access to the test split |
| 4 | a model card |
| 5 | a comparison with another system |
| 6 | a new dataset |
| 7 | compute spend on CSC Roihu |

---

## 2. Gate 1: a number on a results page

| Part | Content |
| :--- | :---: |
| Rule | the number names its source report file and the git commit recorded in it; it is rounded to 3 decimals, half up ([docs/STYLE.md](docs/STYLE.md), section 7); a number measured but whose report file is not in the repository is written `pending`, or named as a session-notes value (`notes`) with its exit condition |
| Evidence | the source cell of its table ([docs/RESULTS.md](docs/RESULTS.md), section 2), and the report file in [docs/RESULTS.md](docs/RESULTS.md), Appendix A |
| Who checks | the maintainer, in review |
| When broken | the value is replaced by `pending` or removed, with a correction line in the changelog of [docs/RESULTS.md](docs/RESULTS.md) |

---

## 3. Gate 2: a number quoted outside the repository

Outside means the website, the organisation profile, posts, slides, applications and messages to partners.

| Part | Content |
| :--- | :---: |
| Rule | the claim has status MEASURED in [CLAIMS.md](CLAIMS.md); its report file is committed; the quote states the value with its interval, the split and the run, and the caveats of [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), section 3; it is cited in the form of [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), section 4. A session-notes value or a `pending` value is never quoted outside |
| Evidence | the row in [CLAIMS.md](CLAIMS.md) and the citation |
| Who checks | the maintainer, before publication |
| When broken | the public text is corrected at its source, and [CLAIMS.md](CLAIMS.md), section 4, lists the statement until it is fixed |

On 7 October 2026 no report file of the CSC Roihu runs is committed yet, so no number passes this gate yet ([docs/RESULTS.md](docs/RESULTS.md), Appendix A).

---

## 4. Gate 3: access to the test split

| Part | Content |
| :--- | :---: |
| Rule | the test split is read only through `python -m tiefer_lab.evaluate --split test --final --reason "<why>"` or `python -m tiefer_lab.export --final --reason "<why>"`, which append an entry to `reports/test_log.md` before the data is read; on CSC Roihu with `FINAL=1` and `REASON`. It is never used to choose a model, a threshold or a setting. Only the maintainer runs it ([GOVERNANCE.md](GOVERNANCE.md), section 2) |
| Evidence | the entry in `reports/test_log.md`; the guard's tests (`tests/test_test_guard.py`) |
| Who checks | the code refuses the test split without `--final`; the maintainer checks the log against the report files |
| When broken | a result chosen with the test split is marked in [docs/RESULTS.md](docs/RESULTS.md) as not independent, with a correction line; the choice is made again on validation |

The entries of the test evaluations of 3 October 2026 are on CSC Roihu and pending a copy ([docs/RESULTS.md](docs/RESULTS.md), section 20).

---

## 5. Gate 4: a model card

| Part | Content |
| :--- | :---: |
| Rule | a model card is published only with: the export report of its files; `SHA256SUMS` of every file it names, or an explicit exclusion; the quantisation table; the hardware table (`not measured` is allowed); the limitations; and whether it is the selected model. It follows `models/cloud-filter/MODEL_CARD_TEMPLATE.md` |
| Evidence | the card and its release folder |
| Who checks | the maintainer, in review ([GOVERNANCE.md](GOVERNANCE.md), section 2) |
| When broken | the card's status goes back to `draft`, with a correction line |

`models/cloud-filter/v0.1.0/MODEL_CARD.md` is a draft: its export report is not yet in the repository.

---

## 6. Gate 5: a comparison with another system

| Part | Content |
| :--- | :---: |
| Rule | a statement that Tiefer Lab is better, worse or equal to another system needs both systems measured by this repository on the same data or the same hardware. Otherwise only the published values are listed, labelled "published", in [docs/LANDSCAPE.md](docs/LANDSCAPE.md) |
| Evidence | the head-to-head status of [docs/LANDSCAPE.md](docs/LANDSCAPE.md), section 5 |
| Who checks | the maintainer |
| When broken | the statement is withdrawn and recorded in [CLAIMS.md](CLAIMS.md) |

On 7 October 2026 no comparison passes this gate ([docs/LANDSCAPE.md](docs/LANDSCAPE.md), section 5).

---

## 7. Gate 6: a new dataset

| Part | Content |
| :--- | :---: |
| Rule | the licence is recorded from a primary source and allows the use; the data holds no personal data; the reader stops on any fact that is not verified; the data card or the catalogue is updated |
| Evidence | the row in [docs/DATASETS.md](docs/DATASETS.md), section 1; the facts in [docs/DATA.md](docs/DATA.md), section 9 |
| Who checks | the maintainer, before any run reads the data |
| When broken | the data is removed from every cache and the results that used it are marked in [docs/RESULTS.md](docs/RESULTS.md) |

---

## 8. Gate 7: compute spend

| Part | Content |
| :--- | :---: |
| Rule | a run is added to [hpc/roihu/plan.md](hpc/roihu/plan.md) with its estimated cost in GPU billing units before it is submitted, and its config is committed |
| Evidence | the row in [hpc/roihu/plan.md](hpc/roihu/plan.md); the measured cost in [docs/RESULTS.md](docs/RESULTS.md), section 16 |
| Who checks | the maintainer |
| When broken | the run is added to the plan afterwards with a correction line, and its results carry the provenance note of [docs/RESULTS.md](docs/RESULTS.md), section 4 |

The L2 runs of 3 October 2026 used a batch size and learning rate that are not in their committed configs ([docs/RESULTS.md](docs/RESULTS.md), section 4); this gate exists so that it does not happen again.

---

## Changelog

- 7 October 2026: first version: seven gates for results, public quotes, the test split, model cards, comparisons, datasets and compute spend.
