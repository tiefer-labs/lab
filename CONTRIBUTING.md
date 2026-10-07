<picture>
  <source media="(prefers-color-scheme: dark)" srcset="profile/tiefer-logo-white.svg">
  <img alt="Tiefer" src="profile/tiefer-logo.svg" width="200">
</picture>

# Contributing to Tiefer

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

How to contribute to any repository of the `tiefer-labs` organisation: what to do before you start, how to set up, how commits and pull requests are made, the writing and evidence rules, and the licence of contributions. A repository's own `CONTRIBUTING.md`, if it has one, takes precedence.

---

## 1. Ways to contribute

| Contribution | Where |
| :--- | :--- |
| Report a bug | an issue with the bug report form |
| Question a number or a source in the documentation | an issue with the documentation and results form |
| Propose a feature or a change of method | an issue with the feature request form, before any code |
| Fix a typo or a broken link | a pull request directly |
| Fix a bug, add a test, improve documentation | a pull request that links an issue |
| Report a security problem | never in public; see [SECURITY.md](SECURITY.md) |

Tiefer is an early-stage company with a small team, and its public repositories are small. Contributions are welcome. Reading this guide first saves both sides time.

---

## 2. Before you start

- For anything larger than a typo, open an issue first. Describe the problem, the change you propose and why. Wait for a maintainer to agree before you build it; this avoids work that cannot be merged.
- Search existing issues and pull requests first.
- Read the repository's `README.md` and, for Tiefer Lab, [docs/STYLE.md](https://github.com/tiefer-labs/lab/blob/main/docs/STYLE.md) and [docs/SPEC.md](https://github.com/tiefer-labs/lab/blob/main/docs/SPEC.md).
- Changes to results, metrics, data handling or the evaluation protocol need an issue and agreement first, because they change what the published numbers mean.

---

## 3. Setting up

Each repository's `README.md` has the exact steps. In short:

| Repository | Language and tools | Set up | Checks before a pull request |
| :--- | :--- | :--- | :--- |
| [lab](https://github.com/tiefer-labs/lab) | Python 3.12, [uv](https://docs.astral.sh/uv/), make | `make setup` | `make check` (ruff, mypy in strict mode, pytest); `make smoke` when you change the pipeline |
| [web](https://github.com/tiefer-labs/web) | Go | see its README | `gofmt`, `go vet`, `go test ./...` |
| [.github](https://github.com/tiefer-labs/.github) | Markdown and YAML | none | read the rendered file on GitHub |

Do not commit environment files, credentials, tokens, datasets, trained models or other large binary files. The `.gitignore` of each repository lists what stays out.

---

## 4. Branches and commits

1. Fork the repository and create a branch from `main`. Name it `<type>/<short-description>`, for example `fix/test-guard-message` or `docs/data-card-bands`.
2. Keep each commit to one topic, small enough to review on its own.
3. Write the commit subject as `<type>(<scope>): <what changes>`, in lower case, without a full stop, at most 72 characters. The scope is optional.
4. Explain why in the body when the subject does not make it obvious. Wrap the body at 72 characters.
5. Do not repeat a commit message; two commits with the same subject are hard to tell apart in the history.

Types used in Tiefer repositories:

| Type | Use |
| :--- | :--- |
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

Use the author name and e-mail address you want to be public. GitHub's no-reply address (`<id>+<username>@users.noreply.github.com`) keeps your personal address out of the history.

---

## 5. Pull requests

1. Fill in the pull request template completely.
2. Link the issue it resolves (`Closes #123`).
3. Keep one pull request to one change. Split unrelated changes.
4. Run the repository's checks locally first (section 3). CI must pass before review.
5. Update the documentation and the changelog line of every Markdown file you change, in the same pull request.
6. Do not force-push after review has started; add commits instead, and they are squashed or rebased on merge.

What CI runs in Tiefer Lab, as an example of what to expect:

| Check | What it does |
| :--- | :--- |
| Lint and type check | ruff and mypy in strict mode on `src/` |
| Tests | pytest on x86 and ARM, with a coverage floor |
| Text rules | forbidden characters, spelling forms and document structure in every tracked text file |
| Shell scripts | ShellCheck |
| Smoke run | the whole pipeline on synthetic data |
| Secrets | gitleaks over the full history |
| Dependencies | pip-audit on every push and weekly |
| Code scanning | CodeQL |
| SBOM | a CycloneDX bill of materials |

Review: a maintainer gives a first response within 5 working days (Monday to Friday, Baku time, UTC+4). A pull request may be closed if it has had no activity for 30 days after a review comment; it can be reopened.

---

## 6. Writing and documentation

Every Markdown file follows the Tiefer Markdown standard, [docs/STYLE.md](https://github.com/tiefer-labs/lab/blob/main/docs/STYLE.md) in Tiefer Lab. The rules you will meet most often:

- Plain, precise English with British spelling (licence, quantise, analyse). Short sentences.
- No emoji and no decorative symbols.
- No em dash (U+2014) and no U+2015. The en dash (U+2013) only in a range, without spaces (`2026–2028`). Use a comma, colon or full stop instead of a dash in a sentence.
- Facts over adjectives. No marketing words such as revolutionary, cutting-edge, seamless or AI-powered.
- "On board" is the adverb, "onboard" the adjective. Dates are written `7 October 2026`.
- Every file starts with the header, the title and a status line, and ends with a changelog, newest line first.
- Tables are plain Markdown tables; a missing value is `not measured`, `pending` or `n/a`, never an empty cell.

CI rejects text that breaks the character rules.

---

## 7. Results, data and claims

Tiefer publishes results with their method: measured, not claimed.

- Every number you add to a results page names its source: a report file in the repository, with the git commit that produced it. A value that was measured but whose report is not in the repository yet is written `pending`.
- Never add an estimated, rounded-up or copied number as if it were measured. Never round to flatter a result.
- Published values of other systems belong only in Tiefer Lab's [docs/LANDSCAPE.md](https://github.com/tiefer-labs/lab/blob/main/docs/LANDSCAPE.md), with their source and access date, and never next to our measurements on a results page.
- The test split of a dataset is used only for final evaluation, through the logged `--final` path. Do not use it to choose models, thresholds or settings.
- Do not add data without a licence that allows it, and state the licence in the data card. Never add personal data.
- Do not commit datasets, caches, checkpoints or trained models. Model files are identified by their SHA-256 sums in the model card.

---

## 8. Dependencies

- Add a dependency only when it is needed, and say why in the pull request.
- Its licence must be compatible with the Mozilla Public License 2.0. Copyleft licences that would change the licence of the repository are not accepted.
- In Tiefer Lab, add it with uv so that `uv.lock` changes in the same commit, and add a row to [docs/DEPENDENCIES.md](https://github.com/tiefer-labs/lab/blob/main/docs/DEPENDENCIES.md) with its purpose and licence.
- Pin GitHub Actions by full commit SHA, with the version in a comment.

---

## 9. Licence of contributions

Unless a repository says otherwise, Tiefer's repositories are licensed under the [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/). By submitting a contribution you confirm that:

1. the contribution is licensed under the same licence as the repository you contribute to;
2. you wrote it, or you have the right to submit it under that licence;
3. if your employer or another party has rights in your work, you have their permission to contribute it;
4. any third-party code or data in it keeps its original licence notice, and that licence is compatible with the repository's licence.

New source files start with the MPL 2.0 notice used in the repository (Exhibit A of the licence).

---

## 10. Trademarks

The Tiefer name and logo are trademarks of Tiefer. They are not licensed by the code licence. Forks and derivative projects must not use them in a way that suggests they are Tiefer's or endorsed by Tiefer.

---

## 11. Code of conduct

Everyone who takes part follows the [code of conduct](CODE_OF_CONDUCT.md).

---

## Changelog

- 7 October 2026: rewritten to the Tiefer Markdown standard; set-up per repository, commit and branch rules, CI checks, writing rules aligned with the en dash rule of docs/STYLE.md, rules for results and data, dependencies and the terms of contribution added.
- 27 September 2026: first version.
