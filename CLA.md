<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Contributor licence agreement

Status: draft. Owner: Tiefer. Licence: MPL 2.0.

For the founder, who decides how contributions are accepted, and for contributors who want to know what may change. This document owns the proposed contributor terms; the terms in force are in [CONTRIBUTING.md](CONTRIBUTING.md), section 9.

---

## 1. This agreement is not in force

This document is a draft. It has not been reviewed by a lawyer, and it does not apply to any contribution. Until the founder approves a version after legal review and changes the status line of this file to `in use`, contributions are accepted under the inbound-equals-outbound terms of [CONTRIBUTING.md](CONTRIBUTING.md): a contribution is licensed under MPL 2.0, the licence of the repository ([LICENSING.md](LICENSING.md)).

---

## 2. The decision

The founder chooses one of two options, or keeps the current terms.

| | Contributor licence agreement (section 3) | Developer Certificate of Origin (section 4) |
| :--- | :---: | :---: |
| What a contributor gives | a copyright licence and a patent licence to Tiefer, broader than MPL 2.0 | a statement, per commit, that they have the right to submit the contribution under the repository's licence |
| Effect on Tiefer | Tiefer may relicense contributions, for example under a commercial licence | Tiefer receives contributions under MPL 2.0 only, like every other user |
| Effect on contributors | one agreement to sign before the first contribution; their contribution may later be used under other terms | a `Signed-off-by:` line in every commit; no separate agreement |
| Effort | a signing process and a record of who signed | a check in CI that every commit carries a sign-off |
| Legal review | needed before it is used | the text is fixed by its authors; the choice to use it still needs the founder's approval |

Neither option replaces the disclosure of AI-assisted systems, which [AI_ASSISTANCE.md](AI_ASSISTANCE.md) requires in every issue and pull request now.

---

## 3. Option A: contributor licence agreement (draft for legal review)

There are two versions with the same clauses: one for an individual who contributes on their own behalf, and one for an entity, signed by a person who may bind it, that lists the people who contribute for it.

1. **Definitions.** "You" means the individual or the entity that signs this agreement. "Contribution" means any work of authorship, including code, documentation, data descriptions and configuration, that you submit to a Tiefer repository on GitHub. "Tiefer" means the owner of the repository.
2. **Copyright licence.** You grant Tiefer and the recipients of software distributed by Tiefer a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright licence to reproduce, prepare derivative works of, publicly display, publicly perform, sublicense and distribute your contributions and such derivative works.
3. **Patent licence.** You grant Tiefer and those recipients a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable patent licence to make, have made, use, offer to sell, sell, import and otherwise transfer your contribution, where such a licence applies only to the patent claims licensable by you that are necessarily infringed by your contribution alone or by its combination with the work to which you submitted it. If any entity starts patent litigation alleging that your contribution, or the work to which you contributed, infringes a patent, the patent licences granted to that entity under this agreement end on the date the litigation is filed.
4. **Right to relicense.** Tiefer may license your contributions under licences other than MPL 2.0, including commercial licences. Tiefer will always also keep each contribution available under MPL 2.0 in the public repository to which it was submitted, for as long as that repository is public.
5. **Your representations.** You represent that each contribution is your original creation, or that you have the right to submit it under this agreement, and that you are legally entitled to grant the licences above. If your employer has rights to what you create, you represent that you have its permission, or that it has signed the entity version of this agreement.
6. **Third-party work.** If a contribution contains work that is not yours, you identify it, with its licence and its source, when you submit it.
7. **No obligation.** Tiefer is not obliged to use any contribution.
8. **No warranty.** Unless required by law or agreed in writing, you provide your contributions "as is", without warranties or conditions of any kind.
9. **Moral rights.** Where the applicable law gives you moral rights that cannot be waived, you agree not to assert them against the uses permitted by this agreement, to the extent the law allows.
10. **Notice of changes.** You agree to tell Tiefer if any representation in clause 5 or 6 becomes untrue.
11. **Applicable law.** To be decided in legal review.

---

## 4. Option B: Developer Certificate of Origin

The Developer Certificate of Origin, version 1.1 [1], is a short statement in which a contributor certifies, for each contribution, that they wrote it or otherwise have the right to submit it under the licence of the file, and that the contribution and its record, including the sign-off, are public. A contributor makes the statement by adding a line to each commit message, for example with `git commit -s`:

```text
Signed-off-by: <your name> <<your e-mail address>>
```

The certificate does not grant Tiefer any right beyond the licence of the repository, MPL 2.0.

---

## 5. How signing would work

| Step | Option A | Option B |
| :--- | :---: | :---: |
| How a contributor agrees | a comment on their first pull request that quotes the agreement version and says "I have read the CLA and I agree to it", or a signed form sent to [hello@tiefer.space](mailto:hello@tiefer.space) | a `Signed-off-by:` line in every commit |
| Where it is recorded | a list of signatories, with the agreement version and the date, kept by the maintainer outside the public repository | the git history |
| How it is checked | the maintainer checks the list before merging | a CI check that rejects commits without a sign-off |
| How a contributor stops | they write to [hello@tiefer.space](mailto:hello@tiefer.space); the agreement then ends for contributions submitted after that date, and contributions already submitted keep the licences already granted | they stop contributing; past sign-offs stay in the history |

---

## 6. Sources

1. Developer Certificate of Origin, version 1.1, The Linux Foundation and its contributors, https://developercertificate.org/, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: section 2 says that neither option replaces the disclosure of AI-assisted systems in AI_ASSISTANCE.md.
- 7 October 2026: first version, a draft that is not in force: the decision between a contributor licence agreement and the Developer Certificate of Origin, the draft clauses for legal review, and how signing would work.
