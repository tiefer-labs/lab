<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Reference models

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How published third-party cloud masking models are run on the same patches as Tiefer's models, so that both are scored by this repository's code on the same pixels ([POLICY.md](../POLICY.md), gate 5). These models keep their published weights and are never trained further; Tiefer's own models stay trained from random initialisation ([NOTICE.md](../NOTICE.md)). Masks shipped with the dataset are read by `build_cache --references` instead ([docs/DATA.md](../docs/DATA.md), section 9).

---

## Requirements

- The licence of the model, read on its primary source, and the maintainer's decision that it allows this use: a `LicenceDecision` in `references/run_reference.py` (`decision`), and the table of [docs/DATASETS.md](../docs/DATASETS.md), section 1.1. A model without a recorded decision stops; a refused one stops with its decision and is not offered by `--model`.
- A runner for the model in `references/run_reference.py`, added in its own pull request after the licence is cleared, with the class mapping of its output recorded in [docs/ASSUMPTIONS.md](../docs/ASSUMPTIONS.md).
- A complete split of a cache (`python -m tiefer_lab.data.build_cache`).

---

## Steps

1. Check what each reference needs:

   ```bash
   uv run python -c "import runpy; print(runpy.run_path('references/run_reference.py')['describe']())"
   ```

2. Run a cleared reference on validation:

   ```bash
   uv run python references/run_reference.py --model <name> --cache cloudsen12-l1c-all --split val
   ```

3. On the test split, only for the final comparison, with a reason that is logged in `reports/test_log.md`:

   ```bash
   uv run python references/run_reference.py --model <name> --cache cloudsen12-l1c-all --split test --final --reason "<why>"
   ```

4. Evaluate a run with `--baselines`: every reference mask of the split is scored next to the model.

Which algorithm is measured on which dataset, and how, is `reports/coverage.md` (`python -m tiefer_lab.paper_models`).

## Licence decisions

| Reference | Decision |
| :--- | :---: |
| dtacs4bands | declined, pending legal review, 15 October 2026 ([docs/DATASETS.md](../docs/DATASETS.md), section 1.1) |
| masks of the CloudSEN12 release of 2022 (`add_release_2022.py`) | declined, pending legal review, 15 October 2026 ([docs/DATASETS.md](../docs/DATASETS.md), section 1.1) |
| UNetMobV2, s2cloudless, KappaMask L1C and L2A, CD-FCNN-RGBI and RGBISWIR, Fmask 4 | no decision recorded; each stops until its licence is read and a decision is recorded |

---

## Files

| File | Purpose |
| :--- | :---: |
| `run_reference.py` | the reference models (UNetMobV2, s2cloudless, KappaMask, CD-FCNN, Fmask, dtacs4bands), their licence state and runners; adds their masks to a cache split |
| `add_release_2022.py` | would add the masks of the CloudSEN12 release of 2022 to a CloudSEN12+ cache split as `2022_<mask>`; kept, and stops with the release's licence decision |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `licence not read yet` | the licence of the model is not recorded | read it on the primary source and record it |
| `has not recorded whether it allows this use` | the maintainer's decision is missing | ask the maintainer; record the decision in `decision` and docs/DATASETS.md, section 1.1 |
| `declined, pending legal review` or `not used` | the maintainer's licence decision refuses the source | nothing to fix here; only a new decision, recorded the same way, changes it |
| `no runner yet` | the runner is added only after the licence is cleared | open a pull request with the runner |
| `the test split is only for final evaluation` | `--split test` without `--final` and `--reason` | use validation, or give the reason for the final comparison |

---

## Changelog

- 15 October 2026: licence decisions: dtacs4bands and the 2022 release masks are declined, pending legal review; a decision is a typed record next to each reference; drafted with an AI-assisted system.
- 14 October 2026: first version: reference models stop until their licence is cleared; masks are added next to those of the dataset; UNetMobV2, s2cloudless and the 2022 release masks; drafted with an AI-assisted system.
