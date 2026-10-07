# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Export, verify and quantise a trained run.

    python -m tiefer_lab.export --run <run-dir> [--final --reason "<why>"]

Writes to `<run-dir>/export/`:

- `cloud_filter_fp32.onnx`: fixed input 1 x 4 x <size> x <size>, batch norm folded
- `cloud_filter_fp32_dynamic.onnx`: the same with a dynamic batch dimension
- `cloud_filter_fp16.onnx`: float16 variant
- `cloud_filter_int8.onnx`: static INT8 (QDQ), calibrated on training patches

and the report `$TIEFER_REPORTS_DIR/export/<run-id>.json` with SHA-256
hashes, parameters, operations, operator types, the ONNX Runtime check
against PyTorch, and the change in mean IoU and false discard rate from FP32
to INT8 on validation (and on test with `--final`, logged in test_log.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import onnx
import torch

from tiefer_lab.config import load_config
from tiefer_lab.data import cache, padding
from tiefer_lab.evaluate import TestGuardError, check_test_guard, load_model, log_test_evaluation
from tiefer_lab.export import onnx_export, quantise, verify
from tiefer_lab.models import flexible
from tiefer_lab.models.cloud_filter import count_macs, count_parameters
from tiefer_lab.train import (
    CONFIG_NAME,
    METADATA_NAME,
    TrainingError,
    band_set_name,
    band_set_option,
    resolve_run_dir,
)
from tiefer_lab.utils import metadata, paths

FILES = {
    "fp32": "cloud_filter_fp32.onnx",
    "fp32_dynamic": "cloud_filter_fp32_dynamic.onnx",
    "fp16": "cloud_filter_fp16.onnx",
    "int8": "cloud_filter_int8.onnx",
}


def export_run(
    run_dir: Path,
    *,
    which: str = "best",
    with_int8: bool = True,
    final: bool = False,
    reason: str | None = None,
    allow_synthetic: bool = False,
    band_set: Sequence[str] | None = None,
) -> Path:
    """Export a run; a band-flexible run is exported for one band set at a time.

    The exported model of a band set takes only those bands (BandSetModel):
    one ONNX file per band set and size, each checked against PyTorch.
    """
    if final:
        check_test_guard("test", final, reason)
    config = load_config(run_dir / CONFIG_NAME)
    run_meta = json.loads((run_dir / METADATA_NAME).read_text(encoding="utf-8"))
    run_id = str(run_meta["run_id"])
    directory = cache.cache_dir(config.data.cache_name)
    index = cache.read_index(directory)
    if cache.is_synthetic(index) and not allow_synthetic:
        raise TrainingError("the cache holds synthetic data; only the smoke pipeline uses it")
    git = metadata.git_commit()
    if final:
        log_test_evaluation(run_id, git["commit"], reason or "", f"{which}, exported ONNX")

    size = config.export.input_size
    cpu = torch.device("cpu")
    loaded = load_model(run_dir, config, which, cpu)
    model: torch.nn.Module
    if isinstance(loaded, flexible.FlexibleModel):
        if not band_set:
            sets = [",".join(b) for b in config.train.band_sets]
            raise TrainingError(f"a band-flexible run is exported per band set: --band-set {sets}")
        bands = tuple(band_set)
        model = flexible.BandSetModel(loaded, bands).eval()
        out_dir = run_dir / "export" / band_set_name(bands)
        report_name = f"{run_id}_{band_set_name(bands)}.json"
    else:
        if band_set and tuple(band_set) != tuple(config.data.bands):
            raise TrainingError(f"this run takes the bands {list(config.data.bands)} only")
        bands = tuple(config.data.bands)
        model = loaded
        out_dir = run_dir / "export"
        report_name = f"{run_id}.json"
    mean, std = cache.normalisation(index, bands)
    files = {k: out_dir / v for k, v in FILES.items()}
    onnx_export.export_fp32(model, files["fp32"], size, config.export.opset)
    onnx_export.export_fp32(
        model, files["fp32_dynamic"], size, config.export.opset, dynamic_batch=True
    )
    onnx_export.export_fp16(files["fp32"], files["fp16"])

    val = cache.load_split(directory, "val", bands=bands)
    limit = config.export.max_verify_patches
    checks: dict[str, Any] = {}
    for key in ("fp32", "fp32_dynamic", "fp16"):
        patches = verify.padded_patches(val, mean, std, size, limit)
        agreement = verify.compare(files[key], model, patches)
        if key != "fp16":
            verify.check(
                agreement, config.export.max_logit_difference, config.export.min_argmax_agreement
            )
        checks[key] = agreement.as_dict()

    report: dict[str, Any] = {
        "kind": "export",
        "smoke": bool(run_meta.get("smoke")) or cache.is_synthetic(index),
        "run_id": run_id,
        "checkpoint": which,
        "final": final,
        "provenance": metadata.provenance(cpu),
        "run": {"provenance": run_meta.get("provenance"), "seed": run_meta.get("seed")},
        "opset": config.export.opset,
        "band_set": list(bands),
        "input_shape": [1, len(bands), size, size],
        "parameters": count_parameters(model),
        "macs_512x512": count_macs(model, (1, len(bands), 512, 512)),
        "operators": {k: onnx_export.operator_types(p) for k, p in files.items() if p.exists()},
        "verification": checks,
        "verification_note": "FP16 agreement is reported, not enforced",
        # Agreement and every metric leave out the dataset's padding (data/padding.py).
        "padding_sides": list(padding.PADDING_SIDES),
        "val_padded_pixels_masked": val.padded_pixels(),
    }

    if with_int8:
        train_data = cache.load_split(directory, "train", bands=bands)
        reader = quantise.CalibrationReader(
            train_data, mean, std, size, config.export.calibration_patches
        )
        quantise.quantise_int8(files["fp32"], files["int8"], reader)
        report["operators"]["int8"] = onnx_export.operator_types(files["int8"])
        report["calibration"] = {"split": "train", "patches": len(reader.positions)}
        quant: dict[str, Any] = {}
        splits = ["val", "test"] if final else ["val"]
        for split in splits:
            data = val if split == "val" else cache.load_split(directory, "test", bands=bands)
            fp32 = quantise.score_onnx(files["fp32"], data, mean, std, size, config.evaluation)
            fp16 = quantise.score_onnx(files["fp16"], data, mean, std, size, config.evaluation)
            int8 = quantise.score_onnx(files["int8"], data, mean, std, size, config.evaluation)
            quant[split] = {
                "fp32": fp32,
                "fp16": fp16,
                "int8": int8,
                "change": quantise.compare_reports(fp32, int8),
                "fp16_change": quantise.compare_reports(fp32, fp16),
            }
        report["quantisation"] = quant

    report["files"] = {
        k: {
            "name": p.name,
            "sha256": onnx_export.sha256(p),
            "bytes": p.stat().st_size,
            "path": paths.portable(p),
        }
        for k, p in files.items()
        if p.exists()
    }
    for p in files.values():
        if p.exists():
            onnx.checker.check_model(str(p))
    out = paths.reports_dir() / "export" / report_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.export", description="Export, verify and quantise a run."
    )
    parser.add_argument("--run", required=True, help="run directory or run ID")
    parser.add_argument("--checkpoint", default="best", choices=["best", "last"])
    parser.add_argument("--skip-int8", action="store_true", help="skip INT8 quantisation")
    parser.add_argument("--final", action="store_true", help="also measure INT8 on the test split")
    parser.add_argument("--reason", help="why the test split is used (with --final)")
    parser.add_argument(
        "--band-set",
        default=None,
        help="bands of a band-flexible run, for example B02,B03,B04, or 'all' for every band set",
    )
    parser.add_argument("--allow-synthetic", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_dir = resolve_run_dir(args.run)
        outs = [
            export_run(
                run_dir,
                which=args.checkpoint,
                with_int8=not args.skip_int8,
                final=args.final,
                reason=args.reason,
                allow_synthetic=args.allow_synthetic,
                band_set=band_set,
            )
            for band_set in band_set_option(run_dir, args.band_set)
        ]
    except (
        TestGuardError,
        TrainingError,
        cache.CacheError,
        verify.VerificationError,
        ValueError,
    ) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    for out in outs:
        report = json.loads(out.read_text(encoding="utf-8"))
        print(f"band set {','.join(report['band_set'])}", flush=True)
        for key, value in report["verification"].items():
            print(
                f"{key}: argmax agreement {value['argmax_agreement']:.5f}, "
                f"max logit difference {value['max_abs_logit_difference']:.3g}",
                flush=True,
            )
        if "quantisation" in report:
            change = report["quantisation"]["val"]["change"]
            print(f"INT8 mean IoU change on val: {change['mean_iou_change']}", flush=True)
            if "note" in change:
                print(change["note"], flush=True)
        print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
