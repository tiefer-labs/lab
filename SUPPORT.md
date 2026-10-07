<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Getting help

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Where to ask for help with a Tiefer repository, what to include, and what response to expect.

---

## 1. Where to ask

| You have | Go to |
| :--- | :---: |
| A question about how to use or run a repository | an issue in that repository |
| A bug | an issue with the bug report form |
| A question about a number, a source or a method in the documentation | an issue with the documentation and results form |
| An idea or a feature request | an issue with the feature request form |
| A security problem | not an issue; follow [SECURITY.md](SECURITY.md) |
| A conduct problem | [hello@tiefer.space](mailto:hello@tiefer.space), subject "Code of conduct"; see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| Interest in a pilot, a partnership or a commercial licence | [hello@tiefer.space](mailto:hello@tiefer.space) or the contact form on [tiefer.space](https://tiefer.space) |
| A press or event enquiry | [hello@tiefer.space](mailto:hello@tiefer.space) |

---

## 2. Before you ask

1. Read the repository's `README.md`, including its troubleshooting table if it has one.
2. For Tiefer Lab, check the folder guide of the part you use (for example `hpc/roihu/README.md` or `jetson/README.md`) and the documents in `docs/`.
3. Search the open and closed issues.

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

- Trained models are not distributed in the public repositories, and no support is given for obtaining them outside an agreement.
- Running jobs on your behalf, or on computing resources Tiefer does not control.
- Uses that break the [acceptable use policy](ACCEPTABLE_USE.md).

---

## Changelog

- 7 October 2026: header image and table alignment follow docs/STYLE.md of this repository.
- 7 October 2026: rewritten to the Tiefer Markdown standard; table of channels, what to include, response times, languages and what is not supported added.
- 27 September 2026: first version.
