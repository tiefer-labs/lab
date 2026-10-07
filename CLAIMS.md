<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Claims ledger

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For evaluators, partners and the founder: the first page to check before trusting any capability Tiefer states in public. This document owns the status of every capability statement Tiefer makes, with its evidence; the values behind a measured claim are in [docs/RESULTS.md](docs/RESULTS.md), and which value to quote is in [BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md).

---

## 1. How to read this page

| Status | Meaning |
| :--- | :---: |
| `MEASURED` | a number in [docs/RESULTS.md](docs/RESULTS.md) backed by a named report file |
| `IMPLEMENTED` | code and tests exist in this repository; not measured |
| `SIMULATED` | works only on synthetic or perturbed data, or in dry-run mode |
| `PLANNED` | in a plan or a specification; no code |
| `NOT STARTED` | stated somewhere public; nothing exists in any public Tiefer repository |
| `WITHDRAWN` | a statement Tiefer no longer makes |

Sources scanned on 7 October 2026: this repository (README.md, every file in `docs/`, the folder guides, the model cards and the community files); `tiefer-labs/.github` at commit `ddc88b8` (`profile/README.md` and the policies); and `tiefer-labs/web` at commit `a3b64eb` (the website text in `internal/content/en.go`). A location is written `<repository>:<file>:<line>`; `lab` is this repository. Business processes such as customer screening and contract terms are outside this ledger: they are not software capabilities, and no public repository can show them.

---

## 2. Rule

A capability may be stated in public, on the website, the organisation profile, in posts, slides, applications or documents for others, only if it has a row in section 3, and only with its status word next to it or in its wording: a `NOT STARTED` or `PLANNED` capability is stated as an aim, never in the present tense. A number may be quoted only as gate 2 of [POLICY.md](POLICY.md) allows. A new statement gets its row before it is published ([GOVERNANCE.md](GOVERNANCE.md), section 2).

---

## 3. Ledger

| ID | Claim as stated | Where it is stated | Status | Evidence | Caveats | Last checked |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `C-01` | a cloud filter that labels every pixel as clear, thick cloud, thin cloud or cloud shadow, with its accuracy and false discard rate | lab:README.md:35, 48 | `MEASURED` | [docs/RESULTS.md](docs/RESULTS.md), sections 6 and 7 | measured on Sentinel-2 Level-1C test patches on GPUs on CSC Roihu, not on board; single seed; report files pending a copy; padded pixels counted ([BENCHMARK-AUTHORITY.md](BENCHMARK-AUTHORITY.md), section 3) | 7 October 2026 |
| `C-02` | the filter runs in orbit and checks every frame for cloud and quality as it is captured | web:internal/content/en.go:14, 44, 65; .github:profile/README.md:14, 20; lab:docs/SPEC.md:15 | `NOT STARTED` | none for orbit; the ground measurement is `C-01` | no Tiefer model has flown | 7 October 2026 |
| `C-03` | frames that are not useful are compressed and kept on board, not deleted | web:internal/content/en.go:65, 78, 129; .github:profile/README.md:20, 29; .github:ACCEPTABLE_USE.md:25; lab:ACCEPTABLE_USE.md:51; lab:docs/SPEC.md:15; lab:README.md:15 | `NOT STARTED` | none: no compression or onboard storage code exists | the send or keep decision itself is `C-04` | 7 October 2026 |
| `C-04` | a send or keep decision per frame at a threshold the operator sets | lab:README.md:15; lab:docs/SPEC.md, section 8 | `IMPLEMENTED` | `src/tiefer_lab/decisions.py`; `decision_threshold` in `src/tiefer_lab/config.py`; `tests/test_decisions.py` | the frame metrics at 30, 50 and 70 percent are measured in `C-01` | 7 October 2026 |
| `C-05` | a four-band model and a band-flexible model that reads any of the 13 Sentinel-2 bands | lab:README.md:35, 40 | `MEASURED` | [docs/RESULTS.md](docs/RESULTS.md), sections 6 and 12 | single seed each; the band-flexible values per band set are session notes; the product decision is pending | 7 October 2026 |
| `C-06` | INT8 quantisation of the cloud filter | lab:README.md:36, 48 | `MEASURED` | [docs/RESULTS.md](docs/RESULTS.md), section 14 | loses 0.060 to 0.154 validation mean IoU, above the one-point limit; L1 runs only | 7 October 2026 |
| `C-07` | FP16 export | lab:README.md:36 | `MEASURED` | [docs/RESULTS.md](docs/RESULTS.md), section 14 | l1_base s0 only; its values are session notes until the export report is copied in | 7 October 2026 |
| `C-08` | latency, power and energy measured on flight-like hardware | web:internal/content/en.go:87, 133, 143; .github:profile/README.md:25, 32 | `NOT STARTED` | [docs/RESULTS.md](docs/RESULTS.md), section 15: not measured | the benchmark scripts are `C-09` | 7 October 2026 |
| `C-09` | Jetson Orin benchmark scripts for latency, throughput, power and energy | lab:README.md:45 | `IMPLEMENTED` | `jetson/`; `tests/test_jetson_dry_run.py` | never run on a board | 7 October 2026 |
| `C-10` | the Jetson scripts in dry-run mode | lab:README.md:45 | `SIMULATED` | `make smoke` runs them with `--dry-run` ([GETTING-STARTED.md](GETTING-STARTED.md)) | validates inputs and prints the plan; measures nothing | 7 October 2026 |
| `C-11` | tiled inference of large frames and a fail-safe that sends and flags any doubtful frame | lab:docs/SPEC.md, section 9 | `IMPLEMENTED` | `src/tiefer_lab/onboard.py`; `tests/test_onboard.py`; `REQ-OBD-01`, `REQ-OBD-03`, `REQ-OBD-04` | tested on synthetic frames | 7 October 2026 |
| `C-12` | the hash of a model file is checked before inference | lab:docs/SPEC.md, section 9 | `IMPLEMENTED` | `verify_model_file` in `src/tiefer_lab/onboard.py`; `REQ-OBD-02` | a SHA-256 check, not a signature (`C-15`) | 7 October 2026 |
| `C-13` | robustness to other sensors' properties | lab:docs/RESULTS.md, section 13 | `SIMULATED` | [docs/RESULTS.md](docs/RESULTS.md), section 13 | fixed perturbations of Sentinel-2 data, l1_base s0 only; not a real sensor | 7 October 2026 |
| `C-14` | event detection on board: fires, oil spills, vessels, floods | web:internal/content/en.go:44, 66, 80, 117–120; .github:profile/README.md:14, 21; lab:docs/SPEC.md:16; lab:README.md:15 | `NOT STARTED` | none | no detection model exists in any public repository | 7 October 2026 |
| `C-15` | model updates are signed, versioned and can be rolled back | web:internal/content/en.go:68, 132, 364; .github:profile/README.md:23, 31; .github:ACCEPTABLE_USE.md:28; lab:ACCEPTABLE_USE.md:54; lab:docs/SPEC.md:18; lab:README.md:15 | `NOT STARTED` | none | `C-12` checks a hash, not a signature | 7 October 2026 |
| `C-16` | kilobyte-sized alert packets with location, event type, confidence and an image chip | web:internal/content/en.go:14, 40, 44, 67, 95–107; .github:profile/README.md:14, 22; lab:docs/SPEC.md:17; lab:README.md:15 | `NOT STARTED` | none | the website's packet card is labelled "Illustrative example. Not real data." | 7 October 2026 |
| `C-17` | every alert labels observed and inferred apart, with a confidence value; generated imagery is never sent as evidence | web:internal/content/en.go:95, 130, 131, 362, 363; .github:profile/README.md:30; .github:ACCEPTABLE_USE.md:26, 27; lab:ACCEPTABLE_USE.md:52, 53 | `NOT STARTED` | none | no alert exists to apply the rule to | 7 October 2026 |
| `C-18` | Tiefer Lab trains and tests models in a virtual orbit simulator | web:internal/content/en.go:87, 143; .github:profile/README.md:25 | `NOT STARTED` | none: no simulator exists in this repository | Lab trains and tests on CloudSEN12+ patches | 7 October 2026 |
| `C-19` | Tiefer Ground runs the same models at the ground station today | web:internal/content/en.go:88; .github:profile/README.md:25 | `NOT STARTED` | none in any public repository | n/a | 7 October 2026 |
| `C-20` | Tiefer runs on the onboard compute operators already fly: GPU, VPU or FPGA | web:internal/content/en.go:70 | `NOT STARTED` | none for flight compute; the models are exported to ONNX and ran on GPUs on CSC Roihu | no VPU or FPGA target exists | 7 October 2026 |
| `C-21` | model versions, updates and alerts are logged for each deployment | .github:ACCEPTABLE_USE.md:20; lab:ACCEPTABLE_USE.md:42 | `NOT STARTED` | none | no deployment exists | 7 October 2026 |
| `C-22` | performance figures are measured and published with their method | .github:profile/README.md:32; web:internal/content/en.go:133 | `MEASURED` | [docs/RESULTS.md](docs/RESULTS.md) | accuracy only; latency and power are `C-08` | 7 October 2026 |
| `C-23` | a public benchmark repository with the first measured results | .github:profile/README.md:42 | `MEASURED` | this repository, [docs/RESULTS.md](docs/RESULTS.md) | the profile says it "will follow" and does not list it (section 4) | 7 October 2026 |
| `C-24` | every use of the test split is logged | lab:README.md:110 | `IMPLEMENTED` | `tests/test_test_guard.py`; [POLICY.md](POLICY.md), gate 3 | the entries of 3 October 2026 are pending a copy into `reports/test_log.md` | 7 October 2026 |
| `C-25` | secret scanning, dependency audit, code scanning, pinned actions and a software bill of materials | lab:SECURITY.md, section 8 | `IMPLEMENTED` | `.github/workflows/ci.yml`, `audit.yml`, `codeql.yml` | n/a | 7 October 2026 |
| `C-26` | security problems can be reported through GitHub private vulnerability reporting | lab:SECURITY.md:28; .github:SECURITY.md:9–13 | `NOT STARTED` | the GitHub API returned `"enabled": false` for this repository on 7 October 2026 | the e-mail route of [SECURITY.md](SECURITY.md) works; the setting is the maintainer's to enable | 7 October 2026 |
| `C-27` | the later stages of the roadmap: a ground pilot, a first flight, national satellites, more operators and radar data on board | web:internal/content/en.go:144–147 | `PLANNED` | none | stated as a roadmap, not as done | 7 October 2026 |

---

## 4. Statements that need correction

Public statements whose status is `NOT STARTED`, or that contradict [docs/RESULTS.md](docs/RESULTS.md). This repository does not edit `tiefer-labs/.github` or `tiefer-labs/web`; the founder fixes each statement at its source, and the row is removed here when the fix is published.

| Location | Statement | Problem | Claims |
| :--- | :---: | :---: | :---: |
| web:internal/content/en.go:14, 44 | Tiefer "filters out useless pixels in orbit, detects events on board, and sends kilobyte-sized alerts" | present tense for capabilities that do not exist; nothing has flown | `C-02`, `C-14`, `C-16` |
| web:internal/content/en.go:65–68 | the four stages described as what Tiefer does | filter on board, detection, alerts and signed updates are `NOT STARTED` | `C-02`, `C-03`, `C-14` to `C-16` |
| web:internal/content/en.go:70 | "It runs on the onboard compute operators already fly: GPU, VPU or FPGA." | no flight compute, VPU or FPGA target exists | `C-20` |
| web:internal/content/en.go:87 | Tiefer Lab tests models "in a virtual orbit simulator and on flight-like hardware" | no simulator exists; no hardware measurement has been made | `C-08`, `C-18` |
| web:internal/content/en.go:88 | Tiefer Ground runs "at the ground station today" | nothing exists in any public repository | `C-19` |
| web:internal/content/en.go:132 | "Every model in orbit is signed, versioned and can be rolled back." | no model is in orbit; no signing exists | `C-15` |
| web:internal/content/en.go:133 | "We publish accuracy, latency and power figures with the method behind them." | accuracy is published; latency and power are not measured | `C-08`, `C-22` |
| web:internal/content/en.go:143 | roadmap, marked "Now": "Cloud filter and three event models, measured on flight-like hardware in a virtual orbit." | contradicts [docs/RESULTS.md](docs/RESULTS.md): the cloud filter was measured on GPUs on CSC Roihu; no event model, no flight-like hardware measurement and no virtual orbit exist | `C-08`, `C-14`, `C-18` |
| web:internal/content/en.go:52 | "about two thirds of Earth's surface is under cloud at any moment" | a number without a source on the page | n/a |
| web:internal/content/en.go:184 | "We will reply within two working days." | [SUPPORT.md](SUPPORT.md) says 3 working days for an e-mail | n/a |
| .github:profile/README.md:14, 20–23 | the onboard pipeline described in the present tense | filter on board, detection, alerts and signed updates are `NOT STARTED` | `C-02`, `C-03`, `C-14` to `C-16` |
| .github:profile/README.md:25 | "Tiefer Lab trains and tests models in a virtual orbit simulator and on flight-like hardware, and Tiefer Ground runs the same models at the ground station." | no simulator, no hardware measurement, no Tiefer Ground | `C-08`, `C-18`, `C-19` |
| .github:profile/README.md:29–31 | filtered frames kept on board; observed and inferred labelled apart; signed updates | stated as facts; `NOT STARTED` | `C-03`, `C-15`, `C-17` |
| .github:profile/README.md:42 | "A public benchmark repository will follow with our first measured results." | it exists: this repository; the table above it lists only `web` and `.github` | `C-23` |
| .github:ACCEPTABLE_USE.md:20, 25–28 | audit trail and design commitments in the present tense | `NOT STARTED`; the Lab copy says that each product documents how far each is implemented | `C-03`, `C-15`, `C-17`, `C-21` |
| .github:SECURITY.md:9–13; lab:SECURITY.md:28 | report through GitHub private vulnerability reporting | not enabled for this repository; a repository setting, not a text change | `C-26` |
| lab:ACCEPTABLE_USE.md:42 | "Audit trail: model versions, updates and alerts are logged for each deployment" | `NOT STARTED`; the Lab copy keeps the organisation's text until the organisation file changes | `C-21` |

---

## Changelog

- 7 October 2026: first version: 27 claims from this repository, the organisation profile and policies, and the website, with status and evidence; the statements that need correction at their source.
