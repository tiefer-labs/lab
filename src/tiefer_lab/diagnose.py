# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Read-only diagnostics on the validation and training splits; never the test split.

    python -m tiefer_lab.diagnose seeds <run-dir> [<run-dir> ...]
    python -m tiefer_lab.diagnose frames <validation report> [--cache <name>]
    python -m tiefer_lab.diagnose int8 --run <run-dir> [--band-set <bands>] [--patches N]

Every command writes `reports/diagnosis/<name>.json` and changes nothing:

- seeds: per run, from `metrics.jsonl` and `metadata.json`: the precision, the
  best epoch, epochs with a non-finite loss, the largest drop of validation
  mean IoU from its running best, the epoch and learning rate where it
  happened, and the per-class IoU at the best and at the last epoch;
- frames: from the `frames` of a validation report: the useful frames that
  would be kept (false discards), the histogram of their true cloud fraction
  in bins of 0.05, how far their predicted fraction lies above the threshold
  (just above it points to a bias, far above to noise) and, with the cache,
  their thin cloud share and the metadata fields of each one;
- int8: the cloud BOA loss on validation patches when only one Conv node is
  quantised, for every Conv node, and the range of the normalised training
  input, to find what the INT8 loss comes from.

A report of a split other than validation is refused.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from tiefer_lab.utils import paths

FRACTION_BINS = tuple(round(0.05 * i, 2) for i in range(21))


def _write(name: str, payload: dict[str, Any]) -> Path:
    out = paths.reports_dir() / "diagnosis" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


# Seeds -------------------------------------------------------------------------


def seed_summary(run_dir: Path) -> dict[str, Any]:
    """What the per-epoch log of one run says about its stability."""
    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (run_dir / "metrics.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    nonfinite = [
        r["epoch"]
        for r in records
        if r.get("train_loss") is None or not math.isfinite(float(r["train_loss"]))
    ]
    best_so_far, drop, drop_epoch, drop_lr = -1.0, 0.0, None, None
    for r in records:
        value = r.get("val_mean_iou")
        if value is None:
            continue
        if best_so_far - value > drop:
            drop, drop_epoch, drop_lr = best_so_far - value, r["epoch"], r.get("learning_rate")
        best_so_far = max(best_so_far, value)
    best = max(
        (r for r in records if r.get("val_mean_iou") is not None),
        key=lambda r: r["val_mean_iou"],
        default=None,
    )
    return {
        "run_id": meta.get("run_id"),
        "seed": meta.get("seed"),
        "precision": meta.get("precision"),
        "status": meta.get("status"),
        "epochs": len(records),
        "best_epoch": meta.get("best_epoch"),
        "best_val_mean_iou": meta.get("best_val_mean_iou"),
        "epochs_with_nonfinite_loss": nonfinite,
        "largest_drop_from_running_best": drop,
        "largest_drop_epoch": drop_epoch,
        "learning_rate_at_largest_drop": drop_lr,
        "val_iou_at_best": best.get("val_iou") if best else None,
        "val_iou_at_last": records[-1].get("val_iou") if records else None,
        "skipped_steps": meta.get("skipped_steps"),
        "curve": [
            {
                "epoch": r["epoch"],
                "train_loss": r.get("train_loss"),
                "val_mean_iou": r.get("val_mean_iou"),
                "learning_rate": r.get("learning_rate"),
            }
            for r in records
        ],
    }


# Frames ------------------------------------------------------------------------


def false_discards(report: dict[str, Any]) -> dict[str, Any]:
    """The useful frames a validation report would keep, and where their fractions lie."""
    if report.get("split") != "val":
        raise ValueError("diagnostics read validation reports only")
    frames = report.get("frames") or []
    useful = [f for f in frames if f["decision_from_reference"] == "send"]
    wrong = [f for f in useful if f["decision"] == "keep"]
    threshold = float(report["model"]["decision_threshold"])
    true = np.asarray([f["true_cloud_fraction"] for f in wrong], dtype=np.float64)
    over = np.asarray([f["predicted_cloud_fraction"] - threshold for f in wrong])
    counts, _ = np.histogram(true, bins=np.asarray(FRACTION_BINS))
    return {
        "useful_frames": len(useful),
        "false_discards": len(wrong),
        "threshold": threshold,
        "true_fraction_bins": [
            {"from": lo, "to": hi, "frames": int(c)}
            for lo, hi, c in zip(FRACTION_BINS[:-1], FRACTION_BINS[1:], counts, strict=True)
        ],
        "predicted_above_threshold": {
            "median": float(np.median(over)) if over.size else None,
            "within_0_05": int((over < 0.05).sum()),
            "within_0_10": int((over < 0.10).sum()),
            "beyond_0_10": int((over >= 0.10).sum()),
        },
        "frames": wrong,
    }


def frame_details(wrong: Sequence[dict[str, Any]], cache_name: str) -> list[dict[str, Any]]:
    """Thin cloud share and the metadata of each false discard, from the validation cache."""
    from tiefer_lab.data import cache
    from tiefer_lab.data.source import IGNORE_INDEX, THIN_CLOUD

    data = cache.load_split(cache.cache_dir(cache_name), "val")
    position = {pid: i for i, pid in enumerate(data.patch_ids)}
    out = []
    for frame in wrong:
        i = position.get(frame["patch_id"])
        if i is None:
            out.append({**frame, "found_in_cache": False})
            continue
        label = np.asarray(data.labels[i])
        labelled = label != IGNORE_INDEX
        cloud = np.isin(label, (1, 2)) & labelled
        thin = float((label == THIN_CLOUD).sum() / max(1, int(cloud.sum())))
        out.append({**frame, "thin_share_of_cloud": thin, "metadata": data.metadata[i]})
    return out


# INT8 --------------------------------------------------------------------------


def int8_sensitivity(run_dir: Path, band_set: Sequence[str] | None, patches: int) -> dict[str, Any]:
    """Cloud BOA loss of the validation patches when one Conv node at a time is INT8."""
    import onnx
    import torch
    from onnxruntime import quantization as ortq

    from tiefer_lab.config import load_config
    from tiefer_lab.data import cache
    from tiefer_lab.evaluate import load_model
    from tiefer_lab.export import onnx_export, quantise
    from tiefer_lab.models import flexible
    from tiefer_lab.train import CONFIG_NAME, subset

    config = load_config(run_dir / CONFIG_NAME)
    directory = cache.cache_dir(config.data.cache_name)
    index = cache.read_index(directory)
    model: torch.nn.Module = load_model(run_dir, config, "best", torch.device("cpu"))
    bands = tuple(config.data.bands)
    if isinstance(model, flexible.FlexibleModel):
        if not band_set:
            raise ValueError("a band-flexible run is diagnosed per band set: --band-set")
        bands = tuple(band_set)
        model = flexible.BandSetModel(model, bands).eval()
    mean, std = cache.normalisation(index, bands)
    size = config.export.input_size
    val = subset(cache.load_split(directory, "val", bands=bands), patches)
    train = cache.load_split(directory, "train", bands=bands)
    reader = quantise.CalibrationReader(train, mean, std, size, config.export.calibration_patches)
    with tempfile.TemporaryDirectory() as tmp:
        fp32 = onnx_export.export_fp32(model, Path(tmp) / "fp32.onnx", size, config.export.opset)
        base = quantise.score_onnx(fp32, val, mean, std, size, config.evaluation)
        base_boa = base["binary"]["cloud"]["median_boa"]
        convs = [n.name for n in onnx.load(str(fp32)).graph.node if n.op_type == "Conv"]
        rows = []
        for name in convs:
            out = Path(tmp) / "one.onnx"
            reader.rewind()
            ortq.quantize_static(
                fp32,
                out,
                reader,
                quant_format=ortq.QuantFormat.QDQ,
                per_channel=True,
                activation_type=ortq.QuantType.QInt8,
                weight_type=ortq.QuantType.QInt8,
                calibrate_method=ortq.CalibrationMethod.MinMax,
                nodes_to_quantize=[name],
                extra_options={"ActivationSymmetric": True, "WeightSymmetric": True},
            )
            scored = quantise.score_onnx(out, val, mean, std, size, config.evaluation)
            boa = scored["binary"]["cloud"]["median_boa"]
            rows.append(
                {
                    "node": name,
                    "cloud_boa_loss": None if boa is None or base_boa is None else base_boa - boa,
                }
            )
    from tiefer_lab.data.dataset import normalised_patch

    values = np.concatenate(
        [np.asarray(normalised_patch(train, i, mean, std)).ravel()[::97] for i in reader.positions]
    )
    percentiles = (0.0, 0.1, 1.0, 50.0, 99.0, 99.9, 100.0)
    return {
        "run_dir": run_dir.name,
        "band_set": list(bands),
        "validation_patches": len(val),
        "fp32_cloud_boa": base_boa,
        "nodes": sorted(rows, key=lambda r: -(r["cloud_boa_loss"] or 0.0)),
        "normalised_input_percentiles": {
            f"{p:g}": float(v)
            for p, v in zip(percentiles, np.percentile(values, percentiles), strict=True)
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.diagnose")
    sub = parser.add_subparsers(dest="command", required=True)
    seeds = sub.add_parser("seeds")
    seeds.add_argument("runs", nargs="+", type=Path)
    frames = sub.add_parser("frames")
    frames.add_argument("report", type=Path)
    frames.add_argument("--cache", default=None)
    int8 = sub.add_parser("int8")
    int8.add_argument("--run", required=True)
    int8.add_argument("--band-set", default=None)
    int8.add_argument("--patches", type=int, default=64)
    args = parser.parse_args(argv)
    try:
        if args.command == "seeds":
            payload = {"runs": [seed_summary(r) for r in args.runs]}
            out = _write(
                "seeds_" + "_".join(sorted({r.name.split("-seed")[0] for r in args.runs})), payload
            )
        elif args.command == "frames":
            report = json.loads(args.report.read_text(encoding="utf-8"))
            payload = false_discards(report)
            if args.cache:
                payload["frames"] = frame_details(payload["frames"], args.cache)
            out = _write(f"frames_{args.report.stem}", payload)
        else:
            from tiefer_lab.train import resolve_run_dir

            run_dir = resolve_run_dir(args.run)
            bands = args.band_set.split(",") if args.band_set else None
            payload = int8_sensitivity(run_dir, bands, args.patches)
            suffix = "_" + "+".join(bands) if bands else ""
            out = _write(f"int8_{run_dir.name}{suffix}", payload)
    except (ValueError, OSError, KeyError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
