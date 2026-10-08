<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Run plan on CSC Roihu

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The plan of the v2 campaign on CSC Roihu: its basis, the budget it starts from, the stop line for new training and its steps. GPU BU are GPU billing units of CSC.

---

## 1. Basis

The campaign restarts from zero (v2). Every run starts from one tagged, clean commit, after the code fixes that precede it. Nothing of the first campaign is used as a result, a source or a cost estimate. Before a run is submitted, its config is committed and it is added to section 3 with its estimated cost ([POLICY.md](../../POLICY.md), gate 7).

---

## 2. Budget

Remaining on 8 October 2026, from the `csc-projects` output of that day:

| Resource | Remaining | Granted | Source |
| :--- | :---: | :---: | :---: |
| GPU billing units | 3,321 | 10,000 | `csc-projects`, 8 October 2026 |
| CPU billing units | 59,882 | 60,000 | `csc-projects`, 8 October 2026 |
| Storage billing units | 29,150 | 30,000 | `csc-projects`, 8 October 2026 |

Stop line: new training stops when the GPU billing units spent on it in the v2 campaign reach 2,800.

---

## 3. Steps

Steps: see the next prompt.

---

## Changelog

- 8 October 2026: results and run details of the campaign of 1 to 3 October 2026 removed; the campaign restarts from zero (v2).
- 7 October 2026: links to docs/DATA.md follow its new section numbers.
