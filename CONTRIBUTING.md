<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Contributing to Tiefer Lab

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For anyone who wants to change Tiefer Lab: what to do before you start, how to set up and check your work, how commits and pull requests are made, the rules for results and data, and the terms of contributions. This is the Lab version of the organisation's contributing guide; it follows the same process and adds what is specific to Lab.

---

## 1. Ways to contribute

| Contribution | Where |
| :--- | :---: |
| Report a bug | an issue with the bug report form |
| Question a number or a source in the documentation | an issue that names the document, the section and the value |
| Propose a feature or a change of method | an issue with the feature request form, before any code |
| Fix a typo or a broken link | a pull request directly |
| Fix a bug, add a test, improve documentation | a pull request that links an issue |
| Add a config, band set, model, metric, dataset or hardware target | an issue first, then the path of [EXTENDING.md](EXTENDING.md) |
| Report a security problem | never in public; see [SECURITY.md](SECURITY.md) |

Tiefer is an early-stage company with a small team. Contributions are welcome. Reading this guide first saves both sides time.

---

## 2. Before you start

- For anything larger than a typo, open an issue first. Describe the problem, the change you propose and why. Wait for the maintainer to agree before you build it.
- Search existing issues and pull requests first.
- Read [START-HERE.md](START-HERE.md) to find the document that owns your topic, and [docs/STYLE.md](docs/STYLE.md) before you write documentation.
- If you use an AI-assisted system for anything in an issue or a pull request, read [AI_ASSISTANCE.md](AI_ASSISTANCE.md) first: every such system is disclosed, and some content may never be given to one.
- Changes to results, metrics, splits, thresholds, data handling or the evaluation protocol need an issue and agreement first, because they change what the published numbers mean ([GOVERNANCE.md](GOVERNANCE.md), section 2).

---

## 3. Set-up and checks

Tiefer Lab needs Python 3.12 or newer and uv 0.8 or newer. The first run is in [GETTING-STARTED.md](GETTING-STARTED.md); other platforms in [INSTALL.md](INSTALL.md).

| `make` target | What it runs | When to run it |
| :--- | :---: | :---: |
| `make setup` | `uv sync --frozen` | once, and after `uv.lock` changes |
| `make lint` | `ruff check .` and `ruff format --check .` | before every commit |
| `make typecheck` | `mypy` in strict mode on `src/` | before every commit |
| `make test` | `pytest` | before every commit |
| `make check` | `lint`, `typecheck` and `test` | before every pull request; CI runs the same checks |
| `make coverage` | the tests under coverage, with the floor of `pyproject.toml` | when you add or remove code |
| `make smoke` | the whole pipeline on a tiny subset (`SMOKE_SOURCE=synthetic` for no network) | when you change the pipeline |
| `make shellcheck` | ShellCheck on every script under `hpc/` and `jetson/` | when you change a shell script |
| `make requirements` | regenerates `hpc/roihu/requirements.txt` from `uv.lock` | after every lock change |

The tests also check text: forbidden characters and spelling forms (`tests/test_text_rules.py`), the Markdown standard (`tests/test_markdown_style.py`), public hygiene such as e-mail addresses, absolute paths and tokens (`tests/test_public_hygiene.py`), the requirements matrix (`tests/test_requirements_doc.py`), the standards matrix (`tests/test_wording.py`) and the index of documents (`tests/test_docs_index.py`).

Do not commit environment files, credentials, tokens, datasets, caches, checkpoints, ONNX files or other large binary files. `.gitignore` lists what stays out.

---

## 4. Branches and commits

1. Fork the repository and create a branch from `main`. Name it `<type>/<short-description>`, for example `fix/test-guard-message` or `docs/data-card-bands`.
2. Keep each commit to one topic, small enough to review on its own.
3. Write the commit subject as `<type>(<scope>): <what changes>`, in lower case, without a full stop, at most 72 characters. The scope is optional.
4. Explain why in the body when the subject does not make it obvious. Wrap the body at 72 characters.
5. Do not repeat a commit message; two commits with the same subject are hard to tell apart in the history.

Types used in Tiefer repositories:

| Type | Use |
| :--- | :---: |
| `feat` | new behaviour |
| `fix` | a bug fix |
| `docs` | documentation only |
| `tests` | tests only |
| `configs` | configuration files |
| `ci` | workflows and CI tools |
| `hpc` | HPC job scripts and guides |
| `models` | model cards, checksums and release folders |
| `reports` | report files copied from a run |
| `deps` | dependencies and lock files |
| `refactor` | code changes without a change in behaviour |

Use the author name and e-mail address you want to be public. GitHub's no-reply address keeps your personal address out of the history.

---

## 5. Pull requests

1. Fill in the pull request template completely.
2. Link the issue it resolves (`Closes #123`).
3. Keep one pull request to one change. Split unrelated changes.
4. Run `make check` locally first. CI must pass before review.
5. Update every document your change affects, in the same pull request (section 8).
6. Do not force-push after review has started; add commits instead.

CI is organised in three workflows:

| Workflow | Jobs | When |
| :--- | :---: | :---: |
| `.github/workflows/ci.yml` | `lint`, `typecheck`, `test (ubuntu-24.04)` with coverage and its floor, `test (ubuntu-24.04-arm)`, `shellcheck`, `smoke`, `sbom`, `secrets` (gitleaks over the full history) | every push and pull request |
| `.github/workflows/audit.yml` | `pip-audit` over every package of `uv.lock` | every push and pull request, weekly and on demand |
| `.github/workflows/codeql.yml` | CodeQL for Python and GitHub Actions | every push and pull request, and weekly |

Review: a maintainer gives a first response within 5 working days (Monday to Friday, Baku time, UTC+4). A pull request may be closed if it has had no activity for 30 days after a review comment; it can be reopened.

---

## 6. Writing and documentation

Every Markdown file follows [docs/STYLE.md](docs/STYLE.md). The rules you will meet most often:

- Plain, precise English with British spelling (licence, quantise, analyse). Short sentences.
- No emoji and no decorative symbols.
- No em dash (U+2014) and no U+2015. The en dash (U+2013) only in a range, without spaces (`2026–2028`).
- Facts over adjectives. No marketing words; the list is in [docs/STYLE.md](docs/STYLE.md), section 3.
- "On board" is the adverb, "onboard" the adjective. Dates are written `7 October 2026`.
- Every file starts with the header, the title and a status line, and ends with a changelog, newest line first.
- Each fact lives in one document; other documents link to it ([INDEX.md](INDEX.md) shows which document owns which topic).

---

## 7. Results, data and the test split

Tiefer Lab publishes results with their method: measured, not claimed. The gates a number must pass are in [POLICY.md](POLICY.md); in short:

- Every number on a results page names its report file and the git commit that produced it. A value measured but not yet in the repository is `pending`.
- To add a report file, copy it unchanged from the run (`hpc/roihu/collect.sh` packs them on CSC Roihu) into `reports/`, in a commit of type `reports` that names the run, the job and the commit recorded in the file. Never edit a report file.
- Never add an estimated, rounded-up or copied number as if it were measured.
- The test split is used only through `python -m tiefer_lab.evaluate --split test --final --reason "<why>"` or `python -m tiefer_lab.export --final --reason "<why>"`, which write an entry to `reports/test_log.md` before the data is read. Never use it to choose a model, a threshold or a setting. Only the maintainer runs it ([GOVERNANCE.md](GOVERNANCE.md), section 2).
- Before a run on CSC Roihu, its config is committed and the run is added to [hpc/roihu/plan.md](hpc/roihu/plan.md) with its estimated cost.
- Published values of other systems belong only in [docs/LANDSCAPE.md](docs/LANDSCAPE.md).
- Do not add data without a licence that allows it; never add personal data ([POLICY.md](POLICY.md), gate 6).

---

## 8. Documents to update with a change

| If your change | Also update |
| :--- | :---: |
| adds, renames or removes a Markdown file | [INDEX.md](INDEX.md) (a test checks it) |
| adds or changes something Tiefer may state in public | [CLAIMS.md](CLAIMS.md) |
| changes a result or how it is read | [docs/RESULTS.md](docs/RESULTS.md) and [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md) |
| adds a dependency | `uv.lock`, `hpc/roihu/requirements.txt` (`make requirements`) and [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) |
| adds a requirement or changes how it is verified | [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) |
| changes any Markdown file | its changelog line, newest first |

---

## 9. Terms of contributions

Contributions are accepted inbound equals outbound: your contribution is licensed under the licence of the repository, the Mozilla Public License 2.0 ([LICENSING.md](LICENSING.md)). By submitting a contribution you confirm that:

1. the contribution is licensed under MPL 2.0;
2. you wrote it, or you have the right to submit it under that licence;
3. if your employer or another party has rights in your work, you have their permission to contribute it;
4. any third-party code or data in it keeps its original licence notice, and that licence is compatible with MPL 2.0.

New source files start with the MPL 2.0 notice used in the repository (Exhibit A of the licence). [CLA.md](CLA.md) is a draft and is not in force; it changes nothing about these terms until the founder approves it.

Add a dependency only when it is needed, and say why. Its licence must be compatible with MPL 2.0; a copyleft licence that would change the licence of the repository is not accepted. Pin GitHub Actions by full commit SHA, with the version in a comment.

---

## 10. Trademarks

The Tiefer name and logo are not licensed by the code licence. Forks must not use them in a way that suggests they are Tiefer's or endorsed by Tiefer; see [TRADEMARK.md](TRADEMARK.md).

---

## 11. Code of conduct

Everyone who takes part follows the [code of conduct](CODE_OF_CONDUCT.md).

---

## Changelog

- 7 October 2026: section 2 links AI_ASSISTANCE.md for the disclosure of AI-assisted systems.
- 7 October 2026: rewritten as the Lab version of the organisation file: the `make` targets, the text tests, how to add a report file, the test split, configs and the run plan before a CSC Roihu run, the documents to update with a change, the three CI workflows, and the terms of contributions with CLA.md as a draft. The process, addresses and times are those of the organisation version.
- 7 October 2026: header image and table alignment follow docs/STYLE.md of this repository.
- 7 October 2026: rewritten to the Tiefer Markdown standard; set-up per repository, commit and branch rules, CI checks, writing rules aligned with the en dash rule of docs/STYLE.md, rules for results and data, dependencies and the terms of contribution added.
- 27 September 2026: first version.
