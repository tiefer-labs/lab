<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Security policy

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For security researchers, users and maintainers of Tiefer Lab: how to report a vulnerability, what happens after a report, what is in scope, and how secrets, the supply chain and model files are protected. This is the Lab version of the organisation's security policy; the reporting routes, times and disclosure rules are the same.

---

## 1. Supported versions

Tiefer Lab does not publish versioned releases yet ([GOVERNANCE.md](GOVERNANCE.md), section 3). Security fixes are made on the default branch only.

| Asset | Supported |
| :--- | :---: |
| Default branch (`main`) of this repository | yes |
| Older commits, forks and archived copies | no |

---

## 2. Reporting a vulnerability

Do not open a public issue, pull request or discussion about a security problem.

Report it privately, by one of these routes:

1. **GitHub private vulnerability reporting.** Open this repository, go to the **Security** tab and choose **Report a vulnerability**. Only you and the maintainers can see the report. See the note for maintainers below.
2. **E-mail.** Write to [hello@tiefer.space](mailto:hello@tiefer.space) with the subject line "Security". Tiefer does not publish an encryption key yet; if you need one, ask in a first message without details.

Include, as far as you can:

| Information | Example |
| :--- | :---: |
| What and where | file and line, commit, workflow, job script |
| Type of problem | for example exposed credential, injection, unsafe deserialisation, supply chain |
| Steps to reproduce | commands, with the exact inputs |
| Impact | what an attacker could do with it |
| Severity estimate | a CVSS vector if you have one |
| Proof of concept | minimal, without accessing other people's data |
| Suggested fix | optional |
| How to credit you | name or handle, or anonymous |

> [!NOTE]
> For maintainers: on 7 October 2026, private vulnerability reporting was not enabled for this repository (the GitHub API returned `"enabled": false`). Until it is enabled in the repository settings (Settings, Advanced Security, Private vulnerability reporting [1]), the e-mail route is the only private route, and the button of route 1 does not appear.

---

## 3. What happens next

| Step | Target time |
| :--- | :---: |
| Confirm that the report was received | within 3 working days |
| Say whether the problem is reproduced, its severity and the plan to fix it | within 10 working days |
| Fix a critical or high severity problem | within 30 days of confirmation |
| Fix a medium or low severity problem | within 90 days of confirmation |
| Publish an advisory, with credit if you want it | when the fix is available |

Working days are Monday to Friday in Baku, Azerbaijan (UTC+4), excluding public holidays. Severity is judged with CVSS. If a fix needs more time, we tell you why and agree a new date with you.

Tiefer is a small, early-stage team and does not run a paid bug bounty programme.

---

## 4. Coordinated disclosure

Please give us 90 days from your report, or until a fix is available if that is sooner, before you disclose the problem publicly. If the problem is being actively exploited, we may agree a shorter time with you. We publish fixed vulnerabilities as GitHub security advisories and credit the reporter unless they prefer not to be named.

---

## 5. Scope

In scope, for this repository:

- the code in `src/`, the tests and the configs;
- the CI workflows in `.github/workflows/` and the tools they download or install (gitleaks, pip-audit, ShellCheck, CodeQL, the pinned actions);
- the git history, including credentials, tokens or personal data in any commit;
- the job scripts for CSC Roihu in `hpc/roihu/` and the Jetson scripts in `jetson/`;
- the model cards and `SHA256SUMS` under `models/cloud-filter/`, and the report files under `reports/`, where a mismatch would let a wrong file or number pass as Tiefer's.

Out of scope:

- denial-of-service and load tests;
- social engineering, phishing and physical attacks;
- reports from automated scanners without a demonstrated impact;
- vulnerabilities in third-party services and dependencies themselves, such as GitHub, CSC, Hugging Face or a Python package; report those to their owners, and tell us if they affect this repository;
- forks and archived copies.

The website and the other repositories of the organisation are covered by their own security policies.

---

## 6. Safe harbour

If you act in good faith, Tiefer will not pursue legal action against you for your research, provided you:

- stay within the scope above;
- avoid privacy violations, data destruction and service disruption;
- access only the data you need to show the problem, and delete it afterwards;
- do not use an exposed credential beyond confirming that it is valid;
- give us reasonable time to fix the problem before you disclose it (section 4).

If in doubt about whether an action is allowed, ask first through the routes in section 2.

---

## 7. Secrets

- No secret belongs in the repository. `.env.example` lists only the `TIEFER_*` locations and a commented `TIEFER_CSC_PROJECT`; `.env` is ignored by git.
- `HF_TOKEN`, the optional Hugging Face token, is read from the environment and passed to GDAL as a bearer token; it is never printed (`src/tiefer_lab/data/http.py`, `tests/test_http.py`).
- A git remote never holds a token: `git remote -v` shows a plain `https://github.com/...` URL.
- `tests/test_public_hygiene.py` rejects tokens of several formats, private keys, e-mail addresses other than the project address, CSC project numbers and absolute personal paths in every tracked file; gitleaks scans the full history on every push.
- If a credential appears in the repository or its history: revoke it first, at its issuer, then remove it from the files and, where needed, from the history, and record the event in a security advisory.

---

## 8. Supply chain

| Measure | Where | Details |
| :--- | :---: | :---: |
| Locked environment with hashes | `uv.lock` | [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) |
| Actions pinned by full commit SHA; workflow permissions `{}` with job-level permissions; `persist-credentials: false` | `.github/workflows/` | [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), section 2.3 |
| CI tools installed with `--require-hashes`; gitleaks checked against its SHA-256 | `.github/ci-tools/requirements.txt`, `.github/workflows/ci.yml` | [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), section 2.2 |
| Vulnerability audit | `.github/workflows/audit.yml` | [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md), section 4 |
| Code scanning | `.github/workflows/codeql.yml` | CodeQL for Python and GitHub Actions |
| Software bill of materials | CI artifact `sbom-cdx` | CycloneDX 1.5 ([INSTALL.md](INSTALL.md), section 3) |

---

## 9. Model integrity

Trained models are not published in this repository. Each release folder lists the SHA-256 sum of every model file in `SHA256SUMS`, and the onboard code checks the hash of a model file before inference and stops with a clear status on a mismatch (`src/tiefer_lab/onboard.py`, `tests/test_onboard.py`). To verify a set of files, run `sha256sum -c SHA256SUMS` in the folder that holds them ([INSTALL.md](INSTALL.md), section 3). Report a mismatch between a file Tiefer gave you and its listed sum through section 2.

---

## 10. Sources

1. Configuring private vulnerability reporting for a repository, GitHub Docs, https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: rewritten as the Lab version of the organisation file, with the same reporting routes, times and disclosure rules: the assets in scope for this repository, secrets, the supply chain, model integrity, and a note that private vulnerability reporting is not yet enabled for this repository.
- 7 October 2026: header image and table alignment follow docs/STYLE.md of this repository.
- 7 October 2026: rewritten to the Tiefer Markdown standard; supported versions, e-mail route, report contents, fix times by severity, coordinated disclosure, scope details and the measures in place added.
- 27 September 2026: first version.
