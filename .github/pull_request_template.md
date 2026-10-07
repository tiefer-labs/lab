Pull request template for default. Only the questions marked required must be answered; answer the others when they apply. The required questions are 1, 35, 36, 38, 39, 40, 41, 42, 52, 59 and 60.

Do not paste secrets, tokens, passwords, keys or personal data other than your GitHub handle. Security problems never go into a pull request: report them privately as SECURITY.md describes.

## 1. Summary

### 1. What does this pull request change? (required)
One or two sentences on the change and its effect.


### 2. Linked issue
The issue this pull request resolves, as `Closes #123`. Anything larger than a typo needs an issue first (CONTRIBUTING.md, section 2).


### 3. Why is the change needed?
The problem it solves or the decision it carries out.


## 2. Kind and scope

### 4. Kind of change
The commit types of CONTRIBUTING.md, section 4. Choose all that apply.

- [ ] `feat`: new behaviour
- [ ] `fix`: a bug fix
- [ ] `docs`: documentation only
- [ ] `tests`: tests only
- [ ] `configs`: configuration files
- [ ] `ci`: workflows and CI tools
- [ ] `hpc`: HPC job scripts and guides
- [ ] `models`: model cards, checksums and release folders
- [ ] `reports`: report files copied from a run
- [ ] `deps`: dependencies and lock files
- [ ] `refactor`: no change in behaviour

### 5. Decision class
The classes of GOVERNANCE.md, section 2, that the change falls under. Choose all that apply.

- [ ] Editorial documentation change
- [ ] Code change without behavioural effect
- [ ] Code change with behavioural effect
- [ ] Metrics, splits, thresholds or the evaluation protocol
- [ ] Acceptance targets
- [ ] New dependency
- [ ] New dataset
- [ ] Test-split access
- [ ] Compute spend
- [ ] Model card release
- [ ] Public claim
- [ ] Security fix
- [ ] Policy change
- [ ] Licence or trademark change

### 6. Size of the change
One pull request carries one change (CONTRIBUTING.md, section 5). Choose one.

- [ ] A typo or a link
- [ ] One topic in a few files
- [ ] One topic in many files
- [ ] Several topics (split them into separate pull requests)

### 7. Files added, renamed or removed
List new, renamed and removed files. Changed files are visible in the diff.


### 8. Components touched
Choose all that apply.

- [ ] `src/tiefer_lab/data/`
- [ ] `src/tiefer_lab/models/` or `train.py`
- [ ] Evaluation, metrics or baselines
- [ ] `src/tiefer_lab/export/`
- [ ] `onboard.py`
- [ ] `configs/`
- [ ] `hpc/`
- [ ] `jetson/`
- [ ] `tests/`
- [ ] `.github/`
- [ ] `reports/`
- [ ] `models/`
- [ ] Markdown documents
- [ ] `pyproject.toml` or `uv.lock`
- [ ] `Makefile`

## 3. Behaviour

### 9. Behaviour change
A change of a default or of a report format needs a minor version bump (GOVERNANCE.md, section 3). Choose one.

- [ ] No change in behaviour
- [ ] New behaviour or option
- [ ] A default changes
- [ ] A bug fix
- [ ] A report format changes
- [ ] A command or option is removed
- [ ] Not sure

### 10. Behaviour before and after
For any change in behaviour: what happened before and what happens now.


## 4. Tests and checks

### 11. Tests added or changed
The test files and test names added or changed, and what each one checks.


### 12. Commands run and their results
The exact commands you ran and the summary line of each, for example the pytest line with the number of tests passed.


### 13. `make check`
`make check` runs lint, typecheck and the tests; CI runs the same checks (CONTRIBUTING.md, section 3). Choose one.

- [ ] Passed
- [ ] Failed (explain under commands run)
- [ ] Not run

### 14. `make smoke`
Run it when the pipeline changes (CONTRIBUTING.md, section 3). Choose one.

- [ ] Passed with `make smoke`
- [ ] Passed with `make smoke SMOKE_SOURCE=synthetic`
- [ ] Failed
- [ ] Not run, the pipeline is not affected
- [ ] Not run

### 15. CI status
The status of the workflows of CONTRIBUTING.md, section 5, on the head commit. Choose one.

- [ ] All jobs green
- [ ] Some jobs failing (name them under commands run)
- [ ] Not yet run
- [ ] Not sure

## 5. Documentation

### 16. Documents updated
CONTRIBUTING.md, section 8, lists what each kind of change must also update. Choose all that apply.

- [ ] INDEX.md (a Markdown file was added, renamed or removed)
- [ ] CLAIMS.md
- [ ] docs/RESULTS.md and BENCHMARK-AUTHORITY.md
- [ ] docs/DEPENDENCIES.md
- [ ] docs/REQUIREMENTS.md
- [ ] A changelog line in every changed Markdown file
- [ ] No document is affected

### 17. docs/STYLE.md
Every Markdown file follows docs/STYLE.md; the tests check part of it. Choose one.

- [ ] Every changed Markdown file follows docs/STYLE.md
- [ ] Not checked
- [ ] No Markdown file changed

## 6. Results, gates and data

### 18. Results affected
A changed result needs its report file and commit (POLICY.md, gate 1). Choose one.

- [ ] No result changes
- [ ] Results change (name them below)
- [ ] Not sure

### 19. Results affected and their sources
Each changed value with its docs/RESULTS.md section and its source key or report file.


### 20. POLICY.md gates
The gates of POLICY.md that the change must pass. Choose all that apply.

- [ ] Gate 1: a number on a results page
- [ ] Gate 2: a number quoted outside the repository
- [ ] Gate 3: access to the test split
- [ ] Gate 4: a model card
- [ ] Gate 5: a comparison with another system
- [ ] Gate 6: a new dataset
- [ ] Gate 7: compute spend on CSC Roihu
- [ ] No gate

### 21. Test-split use
The test split is read only through `--final` with a reason, which writes `reports/test_log.md` (POLICY.md, gate 3). Choose one.

- [ ] The test split was not used
- [ ] Used through `--final` with a reason, logged in `reports/test_log.md`
- [ ] Used in another way (explain in the summary)
- [ ] Not sure

### 22. Data added
Data is added only under a licence that allows it, and never with personal data (POLICY.md, gate 6). Choose one.

- [ ] No data added
- [ ] Data added under a licence that allows it (name it below)
- [ ] Not sure

### 23. Data and licences
Each dataset or data file added, with its licence and its row in docs/DATASETS.md.


## 7. Dependencies, security and compute

### 24. Dependencies
A new dependency is a maintainer decision (GOVERNANCE.md, section 2). Choose one.

- [ ] No dependency change
- [ ] A dependency is added
- [ ] A dependency is updated
- [ ] A dependency is removed

### 25. Dependencies and licences
Each dependency added or updated, with its version and SPDX licence; the licence must be compatible with MPL 2.0.


### 26. Security and secrets
SECURITY.md, section 7, and `tests/test_public_hygiene.py` set these rules. Choose all that apply.

- [ ] No secret, token, key or `.env` content in the diff or in any commit
- [ ] No absolute personal path, CSC project number or e-mail address other than hello@tiefer.space
- [ ] No security problem is described in public (SECURITY.md)

### 27. Compute
Compute on CSC Roihu is planned in hpc/roihu/plan.md before it is spent (POLICY.md, gate 7). Choose one.

- [ ] No compute was used
- [ ] Compute on CSC Roihu, planned in hpc/roihu/plan.md
- [ ] Compute elsewhere
- [ ] Not sure

### 28. Compute spent
The billing units spent, from `reports/compute/<job-id>.json` written by `usage.sh`. Example: `124.833 GPU BU`.


## 8. Provenance

### 29. Head commit
The short hash of the last commit you tested, printed by `git rev-parse --short HEAD`. Example: `74a1c68`.


### 30. Clean working tree
Whether `git status --porcelain` printed nothing when you ran the checks. Choose one.

- [ ] Yes
- [ ] No
- [ ] Not sure

### 31. Base commit
The commit of `main` the branch starts from, printed by `git merge-base HEAD origin/main`. Example: `ef40d3b`.


## 9. Review and rollback

### 32. Where should the reviewer look first?
The files or lines that carry the risk, and any question you want answered.


### 33. Rollback plan
How to undo the change if it causes a problem after the merge.


### 34. Can it be reverted with `git revert` alone?
Some changes also need a lock, a cache or a document restored. Choose one.

- [ ] Yes
- [ ] No, more steps are needed (describe them in the rollback plan)
- [ ] Not sure

## 10. Licence of the contribution

### 35. Terms of contributions (required)
By submitting you confirm the four points of CONTRIBUTING.md, section 9. Tick each one. Choose all that apply.

- [ ] The contribution is licensed under MPL 2.0
- [ ] I wrote it, or I have the right to submit it under that licence
- [ ] If my employer or another party has rights in it, I have their permission
- [ ] Any third-party code or data in it keeps its licence notice, and that licence is compatible with MPL 2.0

## 11. AI assistance disclosure

If any AI-assisted system was used to write, change, review, translate or analyse anything in this issue or pull request, every such system must be disclosed below. This is this repository's policy ([AI_ASSISTANCE.md](https://github.com/tiefer-labs/lab/blob/main/AI_ASSISTANCE.md)).

### 36. Was any AI-assisted system used? (required)
Any system that writes, changes, reviews, translates, summarises or analyses content with a machine-learning model counts (AI_ASSISTANCE.md, section 1). If you answer No, write n/a in the required fields below. Choose one.

- [ ] No
- [ ] Yes

### 37. What was it used for?
Choose all that apply. The purpose tells the reviewer which parts to check most closely.

- [ ] Code generation
- [ ] Code completion
- [ ] Refactoring
- [ ] Test generation
- [ ] Debugging
- [ ] Code review
- [ ] Documentation or prose writing
- [ ] Translation
- [ ] Summarising
- [ ] Commit or pull request text
- [ ] Issue text
- [ ] Data analysis
- [ ] Figures or images
- [ ] Configuration
- [ ] Shell commands
- [ ] Research or literature search
- [ ] Other (describe under further AI-assisted systems)

### 38. Provider (required)
The company or organisation that operates the service you used. Write n/a if no system was used. Example: `n/a`.


### 39. Developer of the model (required)
The organisation that trained the model, if different from the provider; otherwise repeat the provider. Write n/a if no system was used. Example: `n/a`.


### 40. Product or tool name and version (required)
The name and version of the product or tool, as its About page or `--version` output shows it. Write n/a if no system was used. Example: `n/a`.


### 41. Model name (required)
The name of the model as the product shows it. Write n/a if no system was used. Example: `n/a`.


### 42. Exact model version or identifier, and date used (required)
The exact version or identifier of the model, and the date or dates you used it. Write not known for a value the product does not show, and n/a if no system was used. Example: `<model identifier>, 7 October 2026`.


### 43. How it was accessed
The way you used the system. It tells the reviewer where your content went. Choose one.

- [ ] Web chat
- [ ] IDE extension
- [ ] Command-line agent
- [ ] API
- [ ] Self-hosted model
- [ ] Model inside another product
- [ ] Other (describe under further AI-assisted systems)

### 44. Where the model ran
Where the model processed your content, as the provider's terms or settings state it. It matters for data rules (AI_ASSISTANCE.md, section 4). Choose one.

- [ ] Provider's cloud
- [ ] Provider's cloud in the EU or EEA
- [ ] Provider's cloud outside the EU or EEA
- [ ] Self-hosted on own hardware
- [ ] Not known

### 45. Further AI-assisted systems
If you used more than one system, write one line per further system in the form shown. Also describe any Other answer of this section here. Example: `provider; developer; product and version; model; model version; purpose`.


### 46. What content was given to the system?
Choose all that apply. Credentials, personal data and confidential partner material must never be given to such a system (AI_ASSISTANCE.md, section 4).

- [ ] None
- [ ] Public code of this repository
- [ ] Unpublished code
- [ ] Report files
- [ ] Configuration
- [ ] Logs
- [ ] Data samples
- [ ] Personal data
- [ ] Credentials or tokens
- [ ] Confidential partner material
- [ ] Other (describe under further AI-assisted systems)

### 47. How much of the contribution did the system produce?
An estimate of the share of the submitted text, code or data that came from the system before your edits. Choose one.

- [ ] None of it
- [ ] Less than a quarter
- [ ] A quarter to a half
- [ ] A half to three quarters
- [ ] More than three quarters
- [ ] Not known

### 48. Human review of every AI-produced line
The person submitting is responsible for every line, whoever or whatever wrote it (AI_ASSISTANCE.md, section 3). Choose one.

- [ ] Every line reviewed and understood by me
- [ ] Partly reviewed
- [ ] Not reviewed

### 49. How the AI-produced parts were verified
What you did to check the output: tests run, sources opened, numbers recomputed from report files. Example: `tests run, sources checked, numbers recomputed`.


### 50. Do the tool's terms let you contribute its output under MPL 2.0?
Contributions are licensed under MPL 2.0 (CONTRIBUTING.md, section 9). Read the terms of the tool before you submit its output. Choose one.

- [ ] Yes, checked
- [ ] Not checked
- [ ] No
- [ ] Not sure

### 51. Could the output reproduce third-party code or text?
Search for distinctive lines of the output. A match keeps its original notice and licence, or is removed (AI_ASSISTANCE.md, section 5). Choose one.

- [ ] Checked, no match found
- [ ] Checked, match found and attributed
- [ ] Not checked

## 12. Data protection and AI regulation acknowledgement

Issues and pull requests on GitHub are public: anyone can read them, and search engines can index them. GitHub's privacy statement applies to the platform (https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). This repository's rules on personal data and AI-assisted systems are in [AI_ASSISTANCE.md](https://github.com/tiefer-labs/lab/blob/main/AI_ASSISTANCE.md), which lists the articles named below. This text is not legal advice.

### 52. Does this contain personal data of any person, including yourself beyond your GitHub handle? (required)
Personal data has the meaning of GDPR Article 4(1): any information relating to an identified or identifiable person. Remove someone else's personal data before you submit. Choose one.

- [ ] No
- [ ] Yes, only my own, and I want it public
- [ ] Yes, someone else's

### 53. Are special categories of personal data present?
GDPR Article 9 lists the special categories, such as health data, political opinions or biometric data that identify a person. They must never be posted here. Choose one.

- [ ] No
- [ ] Yes

### 54. Was personal data given to an AI-assisted system while preparing this?
GDPR Article 5(1)(c) (data minimisation) and Article 5(1)(f) (integrity and confidentiality) apply, and Chapter V (Articles 44 to 49) when the system runs outside the EU or EEA. Choose one.

- [ ] No
- [ ] Yes, my own only
- [ ] Yes, someone else's
- [ ] Not sure

### 55. Does this touch training data, labels, evaluation, model behaviour or a model card of an AI system Tiefer may place on the market or put into service?
"AI system", "provider" and "placing on the market" are defined in EU AI Act Article 3. Such changes need the documentation that POLICY.md asks for. Choose one.

- [ ] No
- [ ] Training data
- [ ] Labels
- [ ] Evaluation or metrics
- [ ] Model behaviour
- [ ] Model card or documentation
- [ ] Several of these
- [ ] Not sure

### 56. Will any AI-generated text, image, audio or video from this be published?
EU AI Act Article 50 sets transparency obligations for providers and deployers of certain AI systems, including the marking of generated content. This repository labels AI-generated content in all cases (AI_ASSISTANCE.md, section 6). Choose one.

- [ ] No
- [ ] Yes, and it is labelled as AI-generated
- [ ] Yes, not labelled
- [ ] Not sure

### 57. Does this involve any AI practice listed in EU AI Act Article 5?
Article 5 lists prohibited AI practices. ACCEPTABLE_USE.md also applies. Choose one.

- [ ] No
- [ ] Yes
- [ ] Not sure

### 58. For a new dataset, or text and data used to train a model: has the rightholder reserved text and data mining?
Directive (EU) 2019/790, Article 4, allows text and data mining unless the rightholder has expressly reserved it, for example by machine-readable means online. Choose one.

- [ ] No reservation found
- [ ] Reservation found
- [ ] Not checked
- [ ] Does not apply (no new dataset, text or data)

### 59. Acknowledgement (required)
Confirm each statement. They follow this repository's policy in AI_ASSISTANCE.md. Choose all that apply.

- [ ] I have read AI_ASSISTANCE.md and disclosed every AI-assisted system I used
- [ ] I have not posted personal data of anyone else, nor any special category of personal data (GDPR Articles 4(1) and 9)
- [ ] I have not given credentials, personal data or confidential partner material to an AI-assisted system
- [ ] I have read the transparency rule for AI-generated content in AI_ASSISTANCE.md, which follows the purpose of EU AI Act Article 50
- [ ] I understand that I am responsible for every line I submit

## 13. Closing checklist

### 60. Before you ask for review (required)
Confirm each point (CONTRIBUTING.md, section 5). Choose all that apply.

- [ ] I ran `make check` on the head commit
- [ ] This pull request carries one change
- [ ] I updated every document the change affects
- [ ] I will add commits instead of force-pushing after review starts
- [ ] I follow the code of conduct (CODE_OF_CONDUCT.md)
