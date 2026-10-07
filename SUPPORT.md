<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Getting help

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Where to ask for help with Tiefer Lab, what to include, and what response to expect. This is the Lab copy of the organisation's support page; the channels and times are the same.

---

## 1. Where to ask

| You have | Go to |
| :--- | :---: |
| A question about how to use or run Tiefer Lab | an issue with [`19_question.yml`](https://github.com/tiefer-labs/lab/issues/new?template=19_question.yml) |
| A bug | an issue with [`01_bug_report.yml`](https://github.com/tiefer-labs/lab/issues/new?template=01_bug_report.yml) |
| A question about a number, a source or a method in the documentation | an issue with [`02_results_question.yml`](https://github.com/tiefer-labs/lab/issues/new?template=02_results_question.yml), or [`11_method_change.yml`](https://github.com/tiefer-labs/lab/issues/new?template=11_method_change.yml) for a method |
| An idea or a feature request | an issue with [`10_feature_request.yml`](https://github.com/tiefer-labs/lab/issues/new?template=10_feature_request.yml) |
| A security problem | not an issue; follow [SECURITY.md](SECURITY.md) |
| Any other kind of issue | the form for it, listed in [CONTRIBUTING.md](CONTRIBUTING.md), section 1 |
| A conduct problem | [hello@tiefer.space](mailto:hello@tiefer.space), subject "Code of conduct"; see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| Interest in a pilot, a partnership or a commercial licence | [hello@tiefer.space](mailto:hello@tiefer.space) or the contact form on [tiefer.space](https://tiefer.space) |
| A press or event enquiry | [hello@tiefer.space](mailto:hello@tiefer.space) |

---

## 2. Before you ask

1. Find the document that owns your question in [START-HERE.md](START-HERE.md).
2. For a first run, read [GETTING-STARTED.md](GETTING-STARTED.md); for installation, [INSTALL.md](INSTALL.md). Both have a troubleshooting table.
3. Check the folder guide of the part you use: [hpc/roihu/README.md](hpc/roihu/README.md), [jetson/README.md](jetson/README.md), [reports/README.md](reports/README.md) or [models/cloud-filter/README.md](models/cloud-filter/README.md).
4. Search the open and closed issues.

---

## 3. What to include

| Information | Why |
| :--- | :---: |
| Repository and commit (`git rev-parse --short HEAD`) | the code changes often |
| The exact command you ran | so it can be repeated |
| The full error message or log, as text in a code block | screenshots of text cannot be searched |
| Operating system, CPU architecture and versions (Python, uv, Go, CUDA, as relevant) | many problems depend on the platform |
| What you expected and what happened instead | to tell a bug from a misunderstanding |

Remove tokens, passwords, personal paths and other private data from logs before you post them.

---

## 4. Response times

Tiefer is a small team. A maintainer aims to answer an issue within 5 working days and an e-mail within 3 working days (Monday to Friday, Baku time, UTC+4). This is a target, not a guarantee.

Public issues are written in English so that everyone can follow them. By e-mail you may also write in Azerbaijani or Turkish.

---

## 5. What is not supported

- Trained models are not distributed in this repository ([LICENSING.md](LICENSING.md)), and no support is given for obtaining them outside an agreement.
- Running jobs on your behalf, or on computing resources Tiefer does not control.
- Uses that break the [acceptable use policy](ACCEPTABLE_USE.md).

---

## Changelog

- 7 October 2026: section 1 links the issue form for each kind of question by its file name, and CONTRIBUTING.md for the full list of forms.
- 7 October 2026: this copy is the Lab version of the organisation file: it points to START-HERE.md, GETTING-STARTED.md, INSTALL.md and the folder guides of this repository; a question about a number is an ordinary issue, since no documentation and results form exists. The channels and times are unchanged.
- 7 October 2026: header image and table alignment follow docs/STYLE.md of this repository.
- 7 October 2026: rewritten to the Tiefer Markdown standard; table of channels, what to include, response times, languages and what is not supported added.
- 27 September 2026: first version.
