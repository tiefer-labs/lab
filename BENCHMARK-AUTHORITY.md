<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# Benchmark authority

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For evaluators who need to decide which current Tiefer Lab result applies to their question. This document owns which result answers which question, what supersedes what, and how a number is cited; every value and its source are in [docs/RESULTS.md](docs/RESULTS.md), and the rules for quoting a number are in [POLICY.md](POLICY.md).

---

## 1. How to read this page

Each value is copied from the section of [docs/RESULTS.md](docs/RESULTS.md) named next to it, with the same rounding (3 decimals, half up) and the same 95 percent bootstrap interval in brackets. The source keys (`s-test`, `b0-val` and others) are defined in [docs/RESULTS.md](docs/RESULTS.md), section 2.

| Status | Meaning on this page |
| :--- | :---: |
| `current` | the value that answers the question now |
| `provisional` | the value that answers the question now, from a single seed, or before a decision that is still open; it may change |
| `superseded` | replaced by a later value (section 5) |
| `pending` | measured, but the value is not yet in the repository, or only in session notes; it may not be cited |
| `not measured` | never measured |

---

## 2. Which result answers which question

| Question | Authoritative value | Run | Split | Source | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Best four-band result, mean IoU | 0.720 [0.707, 0.732] | l2_spec_1m s0 | test, 975 patches | docs/RESULTS.md, section 7; `s-test` | provisional |
| False discard rate of that model at 50 percent | 0.042 [0.026, 0.059] | l2_spec_1m s0 | test | docs/RESULTS.md, section 7; `s-test` | provisional |
| Selected model and why | l2_spec_1m s0: highest validation mean IoU, 0.732 [0.714, 0.749] | l2_spec_1m s0 | validation, 535 patches | docs/RESULTS.md, section 7; `s-val` | provisional |
| Smallest model size (0.24 M parameters), best result | 0.689 [0.676, 0.701] mean IoU | l1_full s0 | test | docs/RESULTS.md, section 6; `f0-test` | provisional |
| Band-flexible model against the specialist, four bands | no decision; the rule is applied on validation and `x-val-4` is not in the repository | l2_flex_1m s0, l2_spec_1m s0 | validation | docs/RESULTS.md, section 12 | pending |
| Band-flexible model per band set | test values from session notes only | l2_flex_1m s0 | test | docs/RESULTS.md, section 12 | pending |
| INT8 effect | mean IoU change of -0.070, -0.060 and -0.154 | l1_base s0, l1_base s1, l1_full s0 | validation | docs/RESULTS.md, section 14 | current |
| FP16 effect | 0.000 change in mean IoU, from session notes | l1_base s0 | validation | docs/RESULTS.md, section 14 | pending |
| Seed spread | mean IoU of 0.649 and 0.691 (difference 0.042) on validation; 0.635 and 0.679 (0.044) on test | l1_base s0 and s1 | validation, test | docs/RESULTS.md, sections 6 and 18 | current |
| Regional spread | mean IoU from 0.685 (EU) to 0.561 (OC) | l1_base s0 | validation | docs/RESULTS.md, section 9; `b0-val` | current |
| Sensor robustness | blur of 1 pixel: mean IoU 0.468 [0.447, 0.491] against 0.649 without | l1_base s0 | validation, simulated on Sentinel-2 | docs/RESULTS.md, section 13 | current |
| Best baseline | threshold rule, mean IoU 0.296 [0.285, 0.308] | baseline | test | docs/RESULTS.md, section 6; `s-test` | current |
| Compute cost | 1,510.389 GPU BU or more for 19 GPU jobs (7.552 GPU hours or more); l2_spec_1m s0 training: 124.833 GPU BU | all runs | n/a | docs/RESULTS.md, section 16 | current (lower bound) |
| Latency, power and energy per tile on a Jetson Orin | not measured | n/a | n/a | docs/RESULTS.md, section 15 | not measured |
| Comparison with other systems | no comparison is decided; published values are not results of this repository | n/a | n/a | [docs/LANDSCAPE.md](docs/LANDSCAPE.md), section 5 | not measured |

Every measured value of this table counts padded pixels; re-evaluation pending ([docs/RESULTS.md](docs/RESULTS.md), section 21). Until a value is evaluated again, it may not be quoted outside the repository ([POLICY.md](POLICY.md), gate 2).

---

## 3. Caveats that apply to every number now

- **Seeds.** l1_full and every L2 run are single seeds. l1_base has two seeds, whose mean IoU differs by 0.042 on validation and 0.044 on test; a smaller difference between two single-seed runs is not evidence of a better model ([docs/RESULTS.md](docs/RESULTS.md), section 18).
- **Provenance.** l1_base s0 ran from a working tree with uncommitted changes at commit `81ab34b03bcc`; the L2 runs used a batch size and learning rate that are not in their committed configs ([docs/RESULTS.md](docs/RESULTS.md), section 4).
- **Report files.** The report files of the runs of 2 and 3 October 2026 are on CSC Roihu and pending a copy into the repository; most values are copied from the generated pages of earlier commits or from job logs ([docs/RESULTS.md](docs/RESULTS.md), section 20 and Appendix A).
- **Padded pixels.** The cached patches are 512 x 512 and hold the dataset's padding of 3 rows and 3 columns; every value on this page counts those pixels ([docs/RESULTS.md](docs/RESULTS.md), section 18; [docs/DATA.md](docs/DATA.md), section 5). Since 7 October 2026 the padding is masked at load time; every value is evaluated again with the same checkpoints, and until then it keeps its number, carries the caveat "counts padded pixels; re-evaluation pending" and is not quoted outside the repository ([docs/RESULTS.md](docs/RESULTS.md), section 21; [POLICY.md](POLICY.md), gate 2).
- **Product decision.** The choice between the band-flexible model and the four-band specialist is not taken on validation yet ([docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md), section 7).
- **Data.** Every value is on Sentinel-2 Level-1C at 10 m from CloudSEN12+; nothing is measured on a target sensor, and the hardware is a GPU on CSC Roihu, not flight hardware.

---

## 4. How to cite a number

Cite a number in this form:

```text
<value> [<interval>] <metric>, <split> (<patches> patches), <run>, commit <commit>,
Tiefer Lab, docs/RESULTS.md, section <n>, https://github.com/tiefer-labs/lab/blob/<commit>/docs/RESULTS.md, accessed <date>
```

For example:

```text
0.720 [0.707, 0.732] mean IoU, test split (975 patches), l2_spec_1m seed 0, commit 0f0984d76116,
Tiefer Lab, docs/RESULTS.md, section 7, https://github.com/tiefer-labs/lab/blob/main/docs/RESULTS.md, accessed 7 October 2026
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
| l1_base s0 as the best L1 result (test mean IoU 0.635) | l1_full s0 (0.689) | l1_full runs the whole 150-epoch schedule with warm-up and a moving average; l1_base s0 stopped early at its best epoch 32. l1_full s0 has a higher test false discard rate (0.069 against 0.039) | docs/RESULTS.md, sections 6 and 17 |
| Every L1 run as the selected model | l2_spec_1m s0 | highest validation mean IoU of the runs measured so far | docs/RESULTS.md, section 7 |
| The l1_base runs of 2 October 2026 | the runs of 3 October 2026 | the earlier runs stopped early; only training-loop values exist and they are not results | docs/RESULTS.md, section 3 |
| The generated results pages of commits c3e861a, 5ba4585 and 0f0984d | the hand-written [docs/RESULTS.md](docs/RESULTS.md) | the generator was removed on 7 October 2026; values from those pages are kept with source kinds `h-<commit>` | docs/RESULTS.md, section 2 |

The v0.1.0 model card describes l1_base s0 and stays as its record; it is not the selected model ([models/cloud-filter/v0.1.0/MODEL_CARD.md](models/cloud-filter/v0.1.0/MODEL_CARD.md)).

---

## Changelog

- 7 October 2026: every value counts padded pixels; re-evaluation is pending, and until then no value is quoted outside the repository.
- 7 October 2026: first version: which result answers which question, the caveats that apply to every number, how to cite, and what supersedes what.
