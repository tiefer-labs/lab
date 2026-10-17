<img alt="Tiefer Lab" src="../docs/assets/header.png" width="100%">

# Reference models

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

How published third-party cloud masking models are run on the same patches as Tiefer's models, so that both are scored by this repository's code on the same pixels ([POLICY.md](../POLICY.md), gate 5). These models keep their published weights and are never trained further; Tiefer's own models stay trained from random initialisation ([NOTICE.md](../NOTICE.md)). Masks shipped with the dataset are read by `build_cache --references` instead ([docs/DATA.md](../docs/DATA.md), section 9).

---

## Requirements

- The licences of the model's code and of its weights, each read on its primary source, and the maintainer's decision that they allow this use. The record of every model (licences, decision, how it is obtained, its files) is `REFERENCES` of `src/tiefer_lab/reference_models.py`, which imports no torch so the CPU source check can read it; the decisions are also in the table of [docs/DATASETS.md](../docs/DATASETS.md), section 1.1. A model without a recorded decision stops; a model whose weights have no stated licence stops; a refused one stops with its decision and is not offered by `--model`.
- A runner for the model in `references/runners.py`, added in its own pull request after the licence is cleared, with the class mapping of its output recorded in [docs/ASSUMPTIONS.md](../docs/ASSUMPTIONS.md). s2cloudless and both CD-FCNN models have one (17 October 2026).
- The packages of `references/requirements.txt`, pinned and installed with `--no-deps` into `references/.packages`, which comes last on the import path so the environment's own packages win; on CSC Roihu the first `reference_cpu.sbatch` job installs them. The CD-FCNN weights are downloaded from their recorded URL into `references/.weights` and checked against the recorded size. Neither folder is ever committed.
- A complete split of a cache (`python -m tiefer_lab.data.build_cache`).

---

## Steps

1. Check what each reference needs:

   ```bash
   uv run python -c "import runpy; print(runpy.run_path('references/run_reference.py')['describe']())"
   ```

2. Install the packages once:

   ```bash
   uv run python -m pip install --no-deps --target references/.packages -r references/requirements.txt
   ```

3. Run a cleared reference on CloudSEN12+ validation:

   ```bash
   uv run python references/run_reference.py --model <name> --cache cloudsen12-l1c-all --split val
   ```

4. Run it on an independent dataset cache (`build_cache --source`), the path of `evaluate --data`: it reads that cache only, needs a reason, logs the use in `reports/test_log.md` before the tiles are read, never selects, tunes or trains anything, and refuses a CloudSEN12+ cache:

   ```bash
   uv run python references/run_reference.py --model <name> --data <independent cache> --reason "<why>"
   ```

5. On the CloudSEN12+ test split, only for the final comparison, with a reason that is logged in `reports/test_log.md`:

   ```bash
   uv run python references/run_reference.py --model <name> --cache cloudsen12-l1c-all --split test --final --reason "<why>"
   ```

6. Evaluate a run with `--baselines` (with `--data` for an independent dataset): every reference mask of the split is scored next to the model.

Which algorithm is measured on which dataset, and how, is `reports/coverage.md` (`python -m tiefer_lab.paper_models`).

## Licence decisions

| Reference | Decision |
| :--- | :---: |
| dtacs4bands | declined, pending legal review, 15 October 2026 ([docs/DATASETS.md](../docs/DATASETS.md), section 1.1) |
| masks of the CloudSEN12 release of 2022 (`add_release_2022.py`) | declined, pending legal review, 15 October 2026 ([docs/DATASETS.md](../docs/DATASETS.md), section 1.1) |
| s2cloudless | used, 16 October 2026 ([comment on issue 7](https://github.com/tiefer-labs/lab/issues/7#issuecomment-6208121401)); run only from its installed package under `references/`, never copied into this repository; runner added 17 October 2026: the package's own cloud mask at its class defaults ([docs/ASSUMPTIONS.md](../docs/ASSUMPTIONS.md), `A-6.15`) |
| CD-FCNN-RGBI and RGBISWIR | used, 16 October 2026 ([comment on issue 7](https://github.com/tiefer-labs/lab/issues/7#issuecomment-6208121401)): the repository-wide MIT LICENSE covers every file in that repository, weights included, as no other licence is stated; runner added 17 October 2026: the published network rebuilt in PyTorch with the published weights, checked against TensorFlow (`A-6.14`) |
| KappaMask L1C and L2A, Fmask | stay stopped, 16 October 2026: no licence is stated for the weights |
| UNetMobV2 | no decision recorded; its masks are in the CloudSEN12+ extra table |

## Licences and whether each model can be obtained

Read on 16 October 2026 from each model's primary source (`source` in `src/tiefer_lab/reference_models.py`); "obtainable" is the word of the source check (`python -m tiefer_lab.data.check_sources`, [docs/DATASETS.md](../docs/DATASETS.md), section 1.2): yes, credentials needed, licence not stated, or not checked. A licence of the weights that is not stated stops that model. Declined models are not checked.

| Reference | Code licence | Weights licence | How it is obtained | Obtainable | What limits it |
| :--- | :---: | :---: | :---: | :---: | :---: |
| UNetMobV2 | not read | not read | not checked | not checked | its masks are already in the CloudSEN12+ extra table (`cloudmask_unetmobv2_v1` and `cloudmask_unetmobv2_v2`) |
| s2cloudless 1.7.3 | CC BY-SA 4.0 | CC BY-SA 4.0; the model file ships in the package | `pip install s2cloudless==1.7.3` from PyPI; wheel of 4,768,896 bytes with its SHA-256 on PyPI | yes | runs from its installed package under `references/` and is never copied into this repository; reads 10 bands, so only 13-band caches feed it |
| KappaMask L1C and L2A | Apache 2.0 | not stated | the weights are not in the repository; the public Docker image `kappazeta/kappamask:v2.4` carries them | licence not stated | needs whole Level-1C or Level-2A products, not 509 x 509 patches |
| CD-FCNN-RGBI and RGBISWIR | MIT | MIT: the repository-wide MIT LICENSE covers every file of that repository, weights included, as no other licence is stated (the maintainer's reading of 16 October 2026) | raw files of the repository, 1,418,400 and 1,418,160 bytes; no checksum published | yes | trained on L8 Biome, so a result on L8 Biome is not independent |
| Fmask 5 | MIT | not stated | the repository holds the code only; the complete package (about 3 GB) is on a university SharePoint that redirected to a login | licence not stated | the package also needs credentials; needs whole products with their metadata; the MATLAB Fmask 4 of the CloudSEN12 paper is not checked |

---

## Files

| File | Purpose |
| :--- | :---: |
| `run_reference.py` | runs a reference model whose record in `src/tiefer_lab/reference_models.py` is complete; adds its masks to a cache split, or with `--data` to an independent dataset cache, logged |
| `runners.py` | the runners of the cleared models: the bands each reads and how it runs |
| `cd_fcnn.py` | the CD-FCNN network in PyTorch and the reading of its published Keras weights |
| `requirements.txt` | the pinned packages of the reference models that the environment does not have |
| `add_release_2022.py` | would add the masks of the CloudSEN12 release of 2022 to a CloudSEN12+ cache split as `2022_<mask>`; kept, and stops with the release's licence decision |

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| `licence not read yet` | the licence of the model is not recorded | read it on the primary source and record it |
| `no licence is stated for its weights` | the weights have no stated licence | nothing to fix here until one is read and recorded in `src/tiefer_lab/reference_models.py` |
| `has not recorded whether it allows this use` | the maintainer's decision is missing | ask the maintainer; record the decision in `decision` and docs/DATASETS.md, section 1.1 |
| `declined, pending legal review` or `not used` | the maintainer's licence decision refuses the source | nothing to fix here; only a new decision, recorded the same way, changes it |
| `no runner yet` | the runner is added only after the licence is cleared | open a pull request with the runner |
| `install the pinned packages` | `references/.packages` is missing | install `references/requirements.txt` as step 2 shows |
| `is not an independent dataset cache` | `--data` names a CloudSEN12+ cache | use `--cache` and `--split val`; the test split needs `--final` |
| `the record says` | the downloaded weights do not have the recorded size | delete the file in `references/.weights` and run again |
| `the test split is only for final evaluation` | `--split test` without `--final` and `--reason` | use validation, or give the reason for the final comparison |

---

## Changelog

- 17 October 2026: runners of s2cloudless and both CD-FCNN models, their pinned packages under `references/.packages`, and the logged path for independent dataset caches (`--data` with `--reason`); drafted with an AI-assisted system.
- 16 October 2026: licence decisions of 16 October 2026 (comment on issue 7): L8 Biome, L8 SPARCS, s2cloudless and CD-FCNN used; WHUS2-CD+ not used, for scope; KappaMask and Fmask stay stopped; drafted with an AI-assisted system.
- 16 October 2026: the record of every model moves to src/tiefer_lab/reference_models.py; licences of code and weights and whether each model can be obtained; a model whose weights have no stated licence stops; drafted with an AI-assisted system.
- 15 October 2026: licence decisions: dtacs4bands and the 2022 release masks are declined, pending legal review; a decision is a typed record next to each reference; drafted with an AI-assisted system.
- 14 October 2026: first version: reference models stop until their licence is cleared; masks are added next to those of the dataset; UNetMobV2, s2cloudless and the 2022 release masks; drafted with an AI-assisted system.
