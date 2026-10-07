<picture>
  <source media="(prefers-color-scheme: dark)" srcset="profile/tiefer-logo-white.svg">
  <img alt="Tiefer" src="profile/tiefer-logo.svg" width="200">
</picture>

# Security policy

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

How to report a security vulnerability in any repository of the `tiefer-labs` organisation or in the Tiefer website, what happens after a report, and what is in scope.

---

## 1. Supported versions

Tiefer's public repositories do not publish versioned releases yet. Security fixes are made on the default branch only.

| Asset | Supported |
| :--- | :--- |
| Default branch (`main`) of every public `tiefer-labs` repository | yes |
| Older commits, forks and archived repositories | no |
| The website at [tiefer.space](https://tiefer.space), as deployed | yes |

---

## 2. Reporting a vulnerability

Do not open a public issue, pull request or discussion about a security problem.

Report it privately, by one of these routes:

1. **GitHub private vulnerability reporting (preferred).** Open the repository where you found the problem, go to the **Security** tab and choose **Report a vulnerability**. Only you and the maintainers can see the report.
2. **E-mail.** Write to [hello@tiefer.space](mailto:hello@tiefer.space) with the subject line "Security". Tiefer does not publish an encryption key yet; if you need one, ask in a first message without details.

Include, as far as you can:

| Information | Example |
| :--- | :--- |
| What and where | repository, file and line, commit, URL or endpoint |
| Type of problem | for example exposed credential, injection, unsafe deserialisation, supply chain |
| Steps to reproduce | commands or requests, with the exact inputs |
| Impact | what an attacker could do with it |
| Severity estimate | a CVSS vector if you have one |
| Proof of concept | minimal, without accessing other people's data |
| Suggested fix | optional |
| How to credit you | name or handle, or anonymous |

---

## 3. What happens next

| Step | Target time |
| :--- | :--- |
| Confirm that the report was received | within 3 working days |
| Say whether the problem is reproduced, its severity and the plan to fix it | within 10 working days |
| Fix a critical or high severity problem | within 30 days of confirmation |
| Fix a medium or low severity problem | within 90 days of confirmation |
| Publish an advisory, with credit if you want it | when the fix is available |

Working days are Monday to Friday in Baku, Azerbaijan (UTC+4), excluding public holidays. Severity is judged with CVSS. If a fix needs more time, we tell you why and agree a new date with you. You are kept informed until the problem is closed.

Tiefer is a small, early-stage team and does not run a paid bug bounty programme.

---

## 4. Coordinated disclosure

Please give us 90 days from your report, or until a fix is available if that is sooner, before you disclose the problem publicly. If the problem is being actively exploited, we may agree a shorter time with you. We publish fixed vulnerabilities as GitHub security advisories and credit the reporter unless they prefer not to be named.

---

## 5. Scope

In scope:

- every public repository of the `tiefer-labs` organisation, including its CI workflows, scripts, configuration and git history;
- credentials, tokens or personal data exposed in any of these repositories or their history;
- the website at [tiefer.space](https://tiefer.space);
- integrity problems in published material, for example a model card whose checksums do not match the files Tiefer distributes to a partner.

Out of scope:

- denial-of-service and load tests;
- social engineering, phishing and physical attacks;
- reports from automated scanners without a demonstrated impact;
- missing security headers or best-practice settings without a demonstrated impact;
- vulnerabilities in third-party services and dependencies themselves, such as GitHub, CSC or a Python package; report those to their owners, and tell us if they affect a Tiefer repository;
- forks and archived repositories.

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

## 7. What Tiefer does

These measures are in place in Tiefer Lab and are the baseline for every repository:

- secret scanning of the full git history (gitleaks) on every push;
- dependency audit (pip-audit) on every push and weekly;
- code scanning (CodeQL);
- GitHub Actions pinned by full commit SHA, minimal workflow permissions and no stored credentials in checkouts;
- downloaded tools checked against a recorded SHA-256 sum;
- a locked environment and a CycloneDX software bill of materials;
- trained models are not published in the repositories; model cards list the SHA-256 sums of the model files.

If a credential is found anywhere in a repository or its history, it is revoked first and then removed.

---

## Changelog

- 7 October 2026: rewritten to the Tiefer Markdown standard; supported versions, e-mail route, report contents, fix times by severity, coordinated disclosure, scope details and the measures in place added.
- 27 September 2026: first version.
