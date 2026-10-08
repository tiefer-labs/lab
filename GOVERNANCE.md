<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Governance

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For contributors and evaluators who need to know who may change what in Tiefer Lab. This document owns the roles, the decision classes, the version and release rules, and continuity; the measurement gates are in [POLICY.md](POLICY.md), and the contribution process in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 1. Roles

| Role | Who | What they may do |
| :--- | :---: | :---: |
| Maintainer | Tiefer, currently the founder | merge pull requests, push to `main`, run jobs on CSC Roihu, read the test split through `--final`, publish model cards, accept public claims into [CLAIMS.md](CLAIMS.md) |
| Reviewer | a person the maintainer asks to review a pull request | review and approve; the merge stays with the maintainer |
| Contributor | anyone who opens an issue or a pull request | propose changes under [CONTRIBUTING.md](CONTRIBUTING.md) |

A person becomes a maintainer when the current maintainer adds them in writing, in a pull request that changes the table above and adds a changelog line. A maintainer who leaves is removed the same way.

---

## 2. Decision classes

| Change class | Examples | Who decides | How it is proposed | Where it is recorded |
| :--- | :---: | :---: | :---: | :---: |
| Editorial documentation change | wording, links, layout | maintainer | pull request | changelog line of the document |
| Code change without behavioural effect | refactor, typing, tests | maintainer | pull request | commit message |
| Code change with behavioural effect | new option, changed default, bug fix | maintainer | issue, then pull request | commit message; changelog of the affected document |
| Metrics, splits, thresholds or the evaluation protocol | a new metric definition, another decision threshold, a new split | maintainer | issue first, with the reason and the affected results | changelog line of [docs/SPEC.md](docs/SPEC.md); affected results are evaluated again and [docs/RESULTS.md](docs/RESULTS.md) records it |
| Acceptance targets | a minimum or target of `src/tiefer_lab/acceptance.py` | maintainer | issue first | [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), section 8, and its changelog |
| New dependency | a runtime or development package | maintainer | issue or pull request with the reason and the licence | `uv.lock`; [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) |
| New dataset | a reader, a cache, a candidate | maintainer | issue first; [POLICY.md](POLICY.md), gate 6 | [docs/DATA.md](docs/DATA.md) or [docs/DATASETS.md](docs/DATASETS.md) |
| Test-split access | a final evaluation or export | maintainer | a reason for `--final` ([POLICY.md](POLICY.md), gate 3) | `reports/test_log.md` |
| Compute spend | a job on CSC Roihu | maintainer | the run is added to [hpc/roihu/plan.md](hpc/roihu/plan.md) with its estimated cost ([POLICY.md](POLICY.md), gate 7) | [hpc/roihu/plan.md](hpc/roihu/plan.md); [docs/RESULTS.md](docs/RESULTS.md), section 16 |
| Model card release | a new folder under `models/cloud-filter/` | maintainer | pull request ([POLICY.md](POLICY.md), gate 4) | the model card and its changelog |
| Public claim | a statement on the website, the profile or in a document for others | maintainer | a row in [CLAIMS.md](CLAIMS.md) ([POLICY.md](POLICY.md), gate 2) | [CLAIMS.md](CLAIMS.md) |
| Security fix | a vulnerability, an exposed credential | maintainer | privately, as [SECURITY.md](SECURITY.md) describes | a GitHub security advisory when the fix is out |
| Policy change | a rule of [AI_ASSISTANCE.md](AI_ASSISTANCE.md) | maintainer | issue first, with the reason | the changelog of the policy |
| Licence or trademark change | a new licence for a part, a change of [TRADEMARK.md](TRADEMARK.md) | maintainer, after legal advice where needed | issue | [LICENSING.md](LICENSING.md) or [TRADEMARK.md](TRADEMARK.md), and [NOTICE.md](NOTICE.md) |

---

## 3. Versions and releases

| Item | Rule | Now |
| :--- | :---: | :---: |
| Package version (`pyproject.toml`, `src/tiefer_lab/__init__.py`) | semantic versioning; 0.x while the milestones run. A minor bump for a change of behaviour, of a report format or of the evaluation protocol; a patch bump for a fix without such a change | 0.1.0 |
| Model card version (`models/cloud-filter/<version>/`) | a new version for every set of model files with new checksums; an existing folder changes only in its card text, with a changelog line | none yet; the first comes from the v2 campaign |
| Git tags | a tag `v<version>` on the commit that sets a package version, once the maintainer decides to tag | none |

A version bump or a tag is a maintainer decision and is not part of a documentation change. Results are cited by commit, not by version ([BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), section 4).

---

## 4. Continuity

If Tiefer stops maintaining Tiefer Lab, the repository stays public under MPL 2.0 and is archived on GitHub with a final note in [README.md](README.md) that says so and from which date. The Tiefer name and logo are not transferred with the code ([TRADEMARK.md](TRADEMARK.md)).

---

## 5. Changes to this document

A change to this document needs the maintainer's approval and a changelog line.

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: section 2 adds the decision class "policy change" for the rules of AI_ASSISTANCE.md.
- 7 October 2026: first version: roles, decision classes, versions and releases, continuity.
