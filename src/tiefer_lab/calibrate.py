# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Choose the cloud logit bias and the temperature of a run on the validation split only.

    python -m tiefer_lab.calibrate --run <run-dir> [--band-set <bands>]

Two values are chosen on validation and written to
`<run-dir>/calibration_<band set>.json` and `reports/calibration/`:

- the cloud logit bias (a protocol option, issue first): the scalar added to
  the thick and thin cloud logits, the one closest to 0 on a grid of 0.05
  from -5 to 5 whose false discard rate at the decision threshold is at most
  FRM-01's target (0.01) while 1 minus the false send rate stays at least
  FRM-02's target (0.90). When no bias meets both, none is chosen and the
  file says so;
- the temperature of the soft cloud fraction (a protocol option, issue
  first): the T on a grid from 0.25 to 5 that minimises the negative log
  likelihood of the labelled pixels of a fixed sample. The temperature never
  changes the argmax, so it matters only with `evaluate --fraction soft`.

The test split is never read here. A run evaluated with `--cloud-bias auto`
or `--fraction soft` reads these values; the bias is folded into the last
convolution at export (`export --cloud-bias auto`).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from torch.utils.data import DataLoader

from tiefer_lab import metrics
from tiefer_lab.config import load_config
from tiefer_lab.data import cache
from tiefer_lab.data.dataset import EvalPatches
from tiefer_lab.data.source import IGNORE_INDEX
from tiefer_lab.evaluate import load_model
from tiefer_lab.models import flexible
from tiefer_lab.models.cloud_filter import predict_logits
from tiefer_lab.reports import add_model_label
from tiefer_lab.train import (
    CONFIG_NAME,
    METADATA_NAME,
    TrainingError,
    band_set_name,
    band_set_option,
    resolve_run_dir,
)
from tiefer_lab.utils import devices, metadata, paths

# The frame targets the bias is chosen for (src/tiefer_lab/acceptance.py, FRM-01 and FRM-02).
FALSE_DISCARD_TARGET = 0.01
DETECTED_TARGET = 0.90
BIAS_STEP = 0.05
BIAS_GRID = tuple(round(BIAS_STEP * i, 2) for i in range(-100, 101))
MARGIN_LIMIT = 20.0
TEMPERATURES = tuple(round(0.25 + 0.05 * i, 2) for i in range(96))
PIXELS_PER_PATCH = 4096


def margin_histogram(logits: NDArray[np.float32], label: NDArray[np.int64]) -> NDArray[np.int64]:
    """Counts of max(cloud logits) - max(other logits) over labelled pixels, bins of 0.05.

    A pixel is cloud after a bias b exactly when its margin is above -b, so the
    cloud fraction of every bias of the grid follows from these counts.
    """
    valid = label != IGNORE_INDEX
    cloud = np.maximum(logits[1], logits[2])
    other = np.maximum(logits[0], logits[3])
    margin = np.clip((cloud - other)[valid], -MARGIN_LIMIT, MARGIN_LIMIT - 1e-6)
    bins = round(2 * MARGIN_LIMIT / BIAS_STEP)
    index = np.floor((margin + MARGIN_LIMIT) / BIAS_STEP).astype(np.int64)
    return np.bincount(index, minlength=bins)[:bins].astype(np.int64)


def fraction_after_bias(histogram: NDArray[np.int64], bias: float) -> float:
    """Predicted cloud fraction of one patch when `bias` is added to the cloud logits."""
    total = int(histogram.sum())
    if total == 0:
        return float("nan")
    first = round((MARGIN_LIMIT - bias) / BIAS_STEP)
    first = min(max(first, 0), histogram.size)
    return float(histogram[first:].sum() / total)


def choose_bias(
    histograms: Sequence[NDArray[np.int64]],
    true_fraction: NDArray[np.float64],
    threshold: float,
) -> dict[str, Any]:
    """The bias closest to 0 that meets the frame targets on these patches."""
    rows = []
    for bias in sorted(BIAS_GRID, key=lambda b: (abs(b), b)):
        pred = np.asarray([fraction_after_bias(h, bias) for h in histograms])
        fdr = metrics.false_discard_rate(true_fraction, pred, threshold)
        fsr = metrics.false_send_rate(true_fraction, pred, threshold)
        rows.append({"bias": bias, "false_discard_rate": fdr, "detected": 1 - fsr})
    ok = [
        r
        for r in rows
        if r["false_discard_rate"] <= FALSE_DISCARD_TARGET and r["detected"] >= DETECTED_TARGET
    ]
    return {
        "rule": (
            f"closest to 0 on a grid of {BIAS_STEP} from -5 to 5 with false discard rate at most "
            f"{FALSE_DISCARD_TARGET} and 1 - false send rate at least {DETECTED_TARGET}"
        ),
        "bias": ok[0]["bias"] if ok else None,
        "at_zero": next(r for r in rows if r["bias"] == 0.0),
        "chosen": ok[0] if ok else None,
        "grid": sorted(rows, key=lambda r: r["bias"]),
    }


def fit_temperature(logits: NDArray[np.float32], labels: NDArray[np.int64]) -> dict[str, Any]:
    """The temperature with the lowest negative log likelihood of the sampled pixels.

    `logits` are (pixels, classes) and `labels` (pixels,), labelled pixels only.
    """
    best: tuple[float, float] | None = None
    for t in TEMPERATURES:
        z = logits / t
        z = z - z.max(axis=1, keepdims=True)
        log_p = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
        nll = float(-log_p[np.arange(labels.size), labels].mean())
        if best is None or nll < best[1]:
            best = (t, nll)
    assert best is not None
    return {"temperature": best[0], "nll": best[1], "pixels": int(labels.size)}


def calibrate_run(run_dir: Path, band_set: Sequence[str] | None, device_name: str = "auto") -> Path:
    config = load_config(run_dir / CONFIG_NAME)
    run_meta = json.loads((run_dir / METADATA_NAME).read_text(encoding="utf-8"))
    directory = cache.cache_dir(config.data.cache_name)
    index = cache.read_index(directory)
    bands = config.data.bands
    mean, std = cache.normalisation(index, bands)
    device = devices.select_device(device_name)
    precision = devices.precision_for(device)
    model = load_model(run_dir, config, "best", device)
    if isinstance(model, flexible.FlexibleModel):
        if not band_set:
            raise TrainingError("a band-flexible run is calibrated per band set: --band-set")
        model.set_band_set(band_set)
    val = cache.load_split(directory, "val", bands=bands)
    loader: DataLoader[Any] = DataLoader(
        EvalPatches(val, mean, std, multiple=32),
        batch_size=config.data.eval_batch_size,
        num_workers=devices.data_workers(config.data.num_workers),
    )
    rng = np.random.default_rng(0)
    histograms, true, sample_logits, sample_labels = [], [], [], []
    for _, logits, label in predict_logits(model, loader, device, precision):
        valid = label != IGNORE_INDEX
        if not valid.any():
            continue
        histograms.append(margin_histogram(logits, label))
        true.append(float(np.isin(label[valid], (1, 2)).mean()))
        flat_logits = logits[:, valid].T
        flat_labels = label[valid]
        take = rng.choice(
            flat_labels.size, size=min(PIXELS_PER_PATCH, flat_labels.size), replace=False
        )
        sample_logits.append(flat_logits[take])
        sample_labels.append(flat_labels[take])
    threshold = config.evaluation.decision_threshold
    out = {
        "kind": "calibration",
        "split": "val",
        "run_id": run_meta["run_id"],
        "band_set": list(band_set or bands),
        "decision_threshold": threshold,
        "provenance": metadata.provenance(device),
        "cloud_bias": choose_bias(histograms, np.asarray(true), threshold),
        "temperature": fit_temperature(
            np.concatenate(sample_logits), np.concatenate(sample_labels)
        ),
        "patches": len(histograms),
    }
    add_model_label(out, run_meta["run_id"], config.model.architecture)
    name = band_set_name(band_set or bands)
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    (run_dir / f"calibration_{name}.json").write_text(text, encoding="utf-8")
    report = paths.reports_dir() / "calibration" / f"{run_meta['run_id']}_{name}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text, encoding="utf-8")
    return report


def read_calibration(run_dir: Path, bands: Sequence[str]) -> dict[str, Any]:
    """The calibration file of a run and band set, or a clear stop."""
    path = run_dir / f"calibration_{band_set_name(bands)}.json"
    if not path.is_file():
        raise TrainingError(
            f"{path.name} not found: run python -m tiefer_lab.calibrate --run {run_dir.name} first"
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.calibrate")
    parser.add_argument("--run", required=True)
    parser.add_argument("--band-set", default=None)
    parser.add_argument("--device", default="auto", choices=devices.DEVICE_CHOICES)
    args = parser.parse_args(argv)
    try:
        run_dir = resolve_run_dir(args.run)
        outs = [
            calibrate_run(run_dir, band_set, args.device)
            for band_set in band_set_option(run_dir, args.band_set)
        ]
    except (TrainingError, cache.CacheError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    for out in outs:
        data = json.loads(out.read_text(encoding="utf-8"))
        print(f"band set {','.join(data['band_set'])}", flush=True)
        print(f"cloud bias {data['cloud_bias']['bias']}", flush=True)
        print(f"temperature {data['temperature']['temperature']}", flush=True)
        print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
