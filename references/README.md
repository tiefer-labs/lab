<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Reference models

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How published third-party cloud masking models are run on the same patches as Tiefer's models, so that both are scored by this repository's code on the same pixels ([POLICY.md](../POLICY.md), gate 5). These models keep their published weights and are never trained further; Tiefer's own models stay trained from random initialisation ([NOTICE.md](../NOTICE.md)). Masks shipped with the dataset are read by `build_cache --references` instead ([docs/DATA.md](../docs/DATA.md), section 9).

---

## Requirements

- The licence of the model, read on its primary source, and the maintainer's decision that it allows this use, both recorded in `references/run_reference.py` and in the catalogue of [docs/DATASETS.md](../docs/DATASETS.md). A non-commercial licence, such as CC BY-NC 4.0 of dtacs4bands, needs that decision before any run.
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

For KappaMask and the CD-FCNN models, the masks of the CloudSEN12 release of 2022 come first (`src/tiefer_lab/data/cloudsen12_2022.py`); running the models is the fallback; `add_release_2022.py` adds them. Which algorithm is measured on which dataset, and how, is `reports/coverage.md` (`python -m tiefer_lab.paper_models`). That release is CC BY-NC 4.0 on its record page, so it needs the same decision.

---

## Files

| File | Purpose |
| :--- | :---: |
| `run_reference.py` | the reference models (UNetMobV2, s2cloudless, KappaMask, CD-FCNN, Fmask, dtacs4bands), their licence state and runners; adds their masks to a cache split |
| `add_release_2022.py` | adds the masks of the CloudSEN12 release of 2022 to a CloudSEN12+ cache split as `2022_<mask>`; stops until the licence decision and the release facts |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `licence not read yet` | the licence of the model is not recorded | read it on the primary source and record it |
| `has not recorded whether it allows this use` | the maintainer's decision is missing | ask the maintainer; record the decision in docs/DATASETS.md |
| `no runner yet` | the runner is added only after the licence is cleared | open a pull request with the runner |
| `the test split is only for final evaluation` | `--split test` without `--final` and `--reason` | use validation, or give the reason for the final comparison |

---

## Changelog

- 14 October 2026: first version: reference models stop until their licence is cleared; masks are added next to those of the dataset; UNetMobV2, s2cloudless and the 2022 release masks; drafted with an AI-assisted system.
