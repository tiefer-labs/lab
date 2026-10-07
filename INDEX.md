<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Index of documents

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For anyone looking for a document by name or by state. This document owns the list of every Markdown file in the repository, the topic each one owns, and its lifecycle state; the route from a task to a document is in [START-HERE.md](START-HERE.md).

---

## 1. Every document

"Owns" is the topic whose facts live in that document only; other documents link to it. "Status" is the status line of the file, and "Last changed" the date of the newest line of its changelog. `tests/test_docs_index.py` checks that every tracked Markdown file is listed here and that every listed file exists.

| File | Purpose | Audience | Owns | Status | Last changed |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Front door and routes** | | | | | |
| [README.md](README.md) | what Lab is and is not, status at a glance, where to go next | everyone | front door | in development | 7 October 2026 |
| [START-HERE.md](START-HERE.md) | route from a task to the document that owns it | everyone | routes | in use | 7 October 2026 |
| [INDEX.md](INDEX.md) | every Markdown file with its purpose, audience, owner topic and status | everyone | document index and lifecycle | in use | 7 October 2026 |
| **How to run** | | | | | |
| [GETTING-STARTED.md](GETTING-STARTED.md) | first run and the offline proof | first-time users | first run, offline proof | in use | 7 October 2026 |
| [INSTALL.md](INSTALL.md) | every way to install, and the provenance checks | users | installation, provenance checks | in use | 7 October 2026 |
| [LEARNING-PATH.md](LEARNING-PATH.md) | the concepts needed to understand and change Lab, in order | new contributors, researchers | curriculum | in use | 7 October 2026 |
| **Results and evidence** | | | | | |
| [docs/RESULTS.md](docs/RESULTS.md) | every measured result with its source report file | researchers, evaluators | measured values | in development | 7 October 2026 |
| [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md) | which result answers which question, supersession, citation | evaluators | current results, citation form | in use | 7 October 2026 |
| [CLAIMS.md](CLAIMS.md) | status and evidence of every public capability statement | evaluators, partners, the founder | public claims | in use | 7 October 2026 |
| [POLICY.md](POLICY.md) | the gates for numbers, test-split access, model cards, comparisons, data and compute | maintainers, contributors | measurement and release gates | in use | 7 October 2026 |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | requirements and acceptance targets with their verification | evaluators | requirements, acceptance targets | in development | 7 October 2026 |
| [docs/LANDSCAPE.md](docs/LANDSCAPE.md) | published values of related systems and what decides each comparison | evaluators | related systems | in development | 7 October 2026 |
| **Data** | | | | | |
| [docs/DATA.md](docs/DATA.md) | data card for CloudSEN12+ | researchers | dataset facts, caches | in development | 7 October 2026 |
| [docs/DATASETS.md](docs/DATASETS.md) | catalogue of every dataset, roles per split, metric comparison | researchers | dataset catalogue | in development | 7 October 2026 |
| **Specification and standards** | | | | | |
| [docs/SPEC.md](docs/SPEC.md) | specification of milestones L1 and L2 | contributors | specification | in development | 7 October 2026 |
| [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) | assumptions with evidence, status and triggers | researchers, evaluators | assumptions | in development | 7 October 2026 |
| [docs/STANDARDS.md](docs/STANDARDS.md) | standards, handbooks and formats, clauses read and status | evaluators | standards matrix | in development | 7 October 2026 |
| [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | every dependency, its version and licence | users, evaluators | dependencies | in use | 7 October 2026 |
| [docs/STYLE.md](docs/STYLE.md) | the documentation standard | contributors | writing rules, document types | in use | 7 October 2026 |
| [EXTENDING.md](EXTENDING.md) | golden paths to extend Lab | contributors | extension paths | in use | 7 October 2026 |
| **Policies and community** | | | | | |
| [CONTRIBUTING.md](CONTRIBUTING.md) | the contributor contract | contributors | contribution process | in use | 7 October 2026 |
| [AI_ASSISTANCE.md](AI_ASSISTANCE.md) | disclosure of AI-assisted systems in issues and pull requests, data rules, labelling, EU legal references | contributors, maintainers | AI assistance policy, regulatory references | in use | 7 October 2026 |
| [CLA.md](CLA.md) | proposed contributor terms, not in force | the founder, contributors | contributor licence agreement | draft | 7 October 2026 |
| [GOVERNANCE.md](GOVERNANCE.md) | roles, decision classes, versions, continuity | contributors, evaluators | decisions and roles | in use | 7 October 2026 |
| [LICENSING.md](LICENSING.md) | the licence of every part of the repository | users, contributors | licences | in use | 7 October 2026 |
| [NOTICE.md](NOTICE.md) | attributions of third-party data, typeface and software | users | attributions | in use | 7 October 2026 |
| [TRADEMARK.md](TRADEMARK.md) | use of the Tiefer name and logo | everyone | marks | in use | 7 October 2026 |
| [SECURITY.md](SECURITY.md) | security policy and private reporting | security researchers, maintainers | security | in use | 7 October 2026 |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | expected behaviour and how reports are handled | everyone | conduct | in use | 7 October 2026 |
| [SUPPORT.md](SUPPORT.md) | where to ask for help | everyone | support | in use | 7 October 2026 |
| [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) | what Tiefer's products may not be used for | customers, users | acceptable use | in use | 7 October 2026 |
| **Issue forms and pull request templates** | | | | | |
| `.github/ISSUE_TEMPLATE/` | 19 issue forms, one per kind of issue, and the chooser configuration | everyone who opens an issue | issue forms | in use | 7 October 2026 |
| `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/` | the default pull request template and nine templates by kind of change | contributors | pull request templates | in use | 7 October 2026 |
| **Folder guides** | | | | | |
| [hpc/roihu/README.md](hpc/roihu/README.md) | guide for training on CSC Roihu | maintainers | CSC Roihu steps and facts | in development | 7 October 2026 |
| [hpc/roihu/plan.md](hpc/roihu/plan.md) | what ran on CSC Roihu against the plan, next steps | maintainers, evaluators | run plan, compute budget | in development | 7 October 2026 |
| [jetson/README.md](jetson/README.md) | how to run the benchmark on a Jetson Orin | hardware testers | Jetson steps | in development | 7 October 2026 |
| **Models** | | | | | |
| [models/cloud-filter/README.md](models/cloud-filter/README.md) | what a release folder contains | users | release folders | in development | 7 October 2026 |
| [models/cloud-filter/MODEL_CARD_TEMPLATE.md](models/cloud-filter/MODEL_CARD_TEMPLATE.md) | template for a model card | maintainers | model card fields | in use | 7 October 2026 |
| [models/cloud-filter/v0.1.0/MODEL_CARD.md](models/cloud-filter/v0.1.0/MODEL_CARD.md) | model card of l1_base s0 | evaluators | model v0.1.0 | draft | 7 October 2026 |
| **Reports** | | | | | |
| [reports/README.md](reports/README.md) | what each report file is and which script writes it | users | report files | in development | 7 October 2026 |
| [reports/jetson/README.md](reports/jetson/README.md) | where Jetson results land | hardware testers | Jetson reports | in development | 7 October 2026 |
| [reports/test_log.md](reports/test_log.md) | log of every use of the test split | maintainers, evaluators | test-split log | in use | n/a (append-only log) |

---

## 2. Lifecycle

The status words are defined in [docs/STYLE.md](docs/STYLE.md), section 4.

| Status | Meaning | Files |
| :--- | :---: | :---: |
| `draft` | written, not yet reviewed or not yet complete | [CLA.md](CLA.md), [models/cloud-filter/v0.1.0/MODEL_CARD.md](models/cloud-filter/v0.1.0/MODEL_CARD.md) |
| `in development` | in use and still changing with the work it describes | [README.md](README.md), [docs/RESULTS.md](docs/RESULTS.md), [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), [docs/LANDSCAPE.md](docs/LANDSCAPE.md), [docs/DATA.md](docs/DATA.md), [docs/DATASETS.md](docs/DATASETS.md), [docs/SPEC.md](docs/SPEC.md), [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), [docs/STANDARDS.md](docs/STANDARDS.md), [hpc/roihu/README.md](hpc/roihu/README.md), [hpc/roihu/plan.md](hpc/roihu/plan.md), [jetson/README.md](jetson/README.md), [models/cloud-filter/README.md](models/cloud-filter/README.md), [reports/README.md](reports/README.md), [reports/jetson/README.md](reports/jetson/README.md) |
| `in use` | complete for its purpose; changes are recorded in the changelog | [START-HERE.md](START-HERE.md), [INDEX.md](INDEX.md), [GETTING-STARTED.md](GETTING-STARTED.md), [INSTALL.md](INSTALL.md), [LEARNING-PATH.md](LEARNING-PATH.md), [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), [CLAIMS.md](CLAIMS.md), [POLICY.md](POLICY.md), [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), [docs/STYLE.md](docs/STYLE.md), [EXTENDING.md](EXTENDING.md), [CONTRIBUTING.md](CONTRIBUTING.md), [AI_ASSISTANCE.md](AI_ASSISTANCE.md), [GOVERNANCE.md](GOVERNANCE.md), [LICENSING.md](LICENSING.md), [NOTICE.md](NOTICE.md), [TRADEMARK.md](TRADEMARK.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SUPPORT.md](SUPPORT.md), [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md), [models/cloud-filter/MODEL_CARD_TEMPLATE.md](models/cloud-filter/MODEL_CARD_TEMPLATE.md), [reports/test_log.md](reports/test_log.md) |
| `superseded` | replaced; the document names its successor | none |

The plan of 2 October 2026 in [hpc/roihu/plan.md](hpc/roihu/plan.md), section 5, is superseded inside a file that is in development.

---

## Changelog

- 7 October 2026: one row each for the issue forms folder and the pull request templates folder.
- 7 October 2026: AI_ASSISTANCE.md added to the policies and to the files in use.
- 7 October 2026: first version: 39 Markdown files in nine groups, with purpose, audience, owned topic, status and last change, and the files in each lifecycle state.
