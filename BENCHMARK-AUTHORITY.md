<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Benchmark authority

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For evaluators who need to decide which current Tiefer Lab result applies to their question. This document owns which result answers which question, what supersedes what, and how a number is cited; every value and its source are in [docs/RESULTS.md](docs/RESULTS.md), and the rules for quoting a number are in [POLICY.md](POLICY.md).

---

## 1. How to read this page

Each value is copied from the section of [docs/RESULTS.md](docs/RESULTS.md) named next to it, with the same rounding (3 decimals, half up) and the same 95 percent bootstrap interval in brackets. The source keys are defined in [docs/RESULTS.md](docs/RESULTS.md), Appendix A. No value is measured yet: every question waits for the v2 campaign ([hpc/roihu/plan.md](hpc/roihu/plan.md)).

| Status | Meaning on this page |
| :--- | :---: |
| `current` | the value that answers the question now |
| `provisional` | the value that answers the question now, from a single seed, or before a decision that is still open; it may change |
| `superseded` | replaced by a later value (section 5) |
| `pending` | measured, but the value is not yet in the repository, or only in session notes; it may not be cited |
| `not measured` | never measured |
| `pending (v2)` | waits for the v2 campaign; nothing is measured yet |

---

## 2. Which result answers which question

| Question | Authoritative value | Run | Split | Source | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Best four-band result, mean IoU | pending | pending | pending | pending | pending (v2) |
| False discard rate of that model at 50 percent | pending | pending | pending | pending | pending (v2) |
| Selected model and why | pending | pending | pending | pending | pending (v2) |
| Smallest model size, best result | pending | pending | pending | pending | pending (v2) |
| Band-flexible model against the specialist, four bands | pending | pending | pending | pending | pending (v2) |
| Band-flexible model per band set | pending | pending | pending | pending | pending (v2) |
| INT8 effect | pending | pending | pending | pending | pending (v2) |
| FP16 effect | pending | pending | pending | pending | pending (v2) |
| Seed spread | pending | pending | pending | pending | pending (v2) |
| Regional spread | pending | pending | pending | pending | pending (v2) |
| Sensor robustness | pending | pending | pending | pending | pending (v2) |
| Best baseline | pending | pending | pending | pending | pending (v2) |
| Compute cost | pending | pending | pending | pending | pending (v2) |
| Latency, power and energy per tile on a Jetson Orin | pending | pending | pending | pending | pending (v2) |
| Comparison with other systems | pending | pending | pending | pending | pending (v2) |

---

## 3. Caveats that apply to every number now

- **Padded pixels.** The cached patches hold the dataset's padding; it is masked when the labels are loaded, so no metric counts it ([docs/DATA.md](docs/DATA.md), section 5).
- **Seeds.** A difference between two runs is evidence only when it is larger than the spread between seeds of the same configuration ([docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 6).
- **Product decision.** The choice between the band-flexible model and the four-band specialist is taken on validation only, under the rule of [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 7.
- **Data.** Every value is on Sentinel-2 Level-1C at 10 m from CloudSEN12+; nothing is measured on a target sensor, and the hardware is a GPU on CSC Roihu, not flight hardware.

---

## 4. How to cite a number

Cite a number in this form:

```text
<value> [<interval>] <metric>, <split> (<patches> patches), <run>, commit <commit>,
Tiefer Lab, docs/RESULTS.md, section <n>, https://github.com/tiefer-labs/lab/blob/<commit>/docs/RESULTS.md, accessed <date>
```

For example, with neutral values:

```text
0.83 [0.81, 0.85] mean IoU, test split (<patches> patches), run-a s0, commit <commit>,
Tiefer Lab, docs/RESULTS.md, section 6, https://github.com/tiefer-labs/lab/blob/<commit>/docs/RESULTS.md, accessed <date>
```

Name the commit of the page you read; `main` changes. State the caveats of section 3 that apply. Outside the repository, a number may be quoted only when it passes gate 2 of [POLICY.md](POLICY.md).

Never cite:

- a value marked `notes` or `pending`;
- a published value of another system as if this repository had measured it ([docs/LANDSCAPE.md](docs/LANDSCAPE.md));
- a smoke output ([GETTING-STARTED.md](GETTING-STARTED.md), section 5);
- a test value as the reason a model or setting was chosen.

---

## 5. What supersedes what

| Superseded | By | Why | Where |
| :--- | :---: | :---: | :---: |
| none yet | n/a | n/a | n/a |

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: first version: which result answers which question, the caveats that apply to every number, how to cite, and what supersedes what.
