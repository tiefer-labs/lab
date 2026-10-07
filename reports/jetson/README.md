<img alt="Tiefer Lab" src="../../docs/assets/header.png" width="100%">

# Jetson reports

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

Where the Jetson Orin benchmark results land. Each file is written by `jetson/bench.py` on the board and copied here unchanged.

---

## Requirements

- Results from `python3 jetson/bench.py` on an NVIDIA Jetson Orin, as described in [jetson/README.md](../../jetson/README.md).

---

## Steps

1. Run the benchmark on the board; it writes `reports/jetson/<label>_<UTC time>.json`.
2. Copy the files into this folder of the repository and commit them.
3. Copy the values by hand into [docs/RESULTS.md](../../docs/RESULTS.md), section 15, naming the file of each value.

---

## Files

| File | Contents |
| :--- | :---: |
| `<label>_<UTC time>.json` | device, latency percentiles, throughput, power, energy per tile, temperatures, out of scope note |

No Jetson measurements exist yet: every hardware value in [docs/RESULTS.md](../../docs/RESULTS.md), section 15, is `not measured`.

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :---: | :---: |
| A Jetson report is missing from `docs/RESULTS.md` | the file is not in `reports/jetson/` of the repository, or its values were not copied | copy it from the board unchanged and copy its values into `docs/RESULTS.md`, section 15, by hand |
| The commit in a report is `unknown` | the scripts ran from a copy without git history | run them from a `git clone` of the repository on the board |

---

## Changelog

- 7 October 2026: hardware values are `not measured` in docs/RESULTS.md, section 15.
- 7 October 2026: Jetson values are copied into docs/RESULTS.md by hand; `make results` is removed.
