# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Evaluate a trained run, and optionally the baselines.

    python -m tiefer_lab.evaluate --run <run-dir> --split val [--baselines]
    python -m tiefer_lab.evaluate --run <run-dir> --split test --final --reason "<why>"

Test guard: the test split is only for final evaluation. `--split test`
refuses to run without `--final`, and with `--final` it first appends an
entry (date, run ID, git commit, reason) to `$TIEFER_REPORTS_DIR/test_log.md`.

The report is written to `$TIEFER_REPORTS_DIR/evaluation/<run-id>_<split>.json`
with pixel metrics, frame metrics (including the false discard rate),
bootstrap confidence intervals over patches, a breakdown by metadata and the
provenance of the run and of the evaluation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import DataLoader

from tiefer_lab import baselines, binary_metrics, bootstrap, decisions, metrics
from tiefer_lab.config import Config, EvaluationConfig, config_to_dict, load_config
from tiefer_lab.data import cache
from tiefer_lab.data.dataset import EvalPatches
from tiefer_lab.data.source import CLEAR, IGNORE_INDEX, THICK_CLOUD, USED_BANDS
from tiefer_lab.data.transforms import to_reflectance
from tiefer_lab.models import flexible
from tiefer_lab.models.cloud_filter import predict_masks
from tiefer_lab.tables import header_block
from tiefer_lab.train import (
    CONFIG_NAME,
    METADATA_NAME,
    TrainingError,
    band_set_name,
    resolve_run_dir,
)
from tiefer_lab.utils import checkpoint, devices, metadata, paths

TEST_LOG = "test_log.md"
# Metadata fields with at most this many distinct values are used for the breakdown.
MAX_GROUPS = 30


class TestGuardError(RuntimeError):
    """The test split was requested without the final evaluation flag or a reason."""


# Scoring -------------------------------------------------------------------


class Scores:
    """Per-patch confusion matrices and cloud fractions, for metrics and intervals.

    Pixels marked IGNORE_INDEX in the reference or the prediction (no label,
    or no data in a reference mask) are left out and counted. With
    `binary_only`, only the cloud against non-cloud measures are reported
    (for masks that do not separate the four classes).
    """

    def __init__(self, binary_only: bool = False) -> None:
        self.binary_only = binary_only
        self.confusions: list[NDArray[np.int64]] = []
        self.true_fraction: list[float] = []
        self.pred_fraction: list[float] = []
        self.pred_shadow: list[float] = []
        self.ignored_pixels = 0

    def add(
        self, prediction: NDArray[np.integer[Any]], reference: NDArray[np.integer[Any]]
    ) -> None:
        valid = (reference != IGNORE_INDEX) & (prediction != IGNORE_INDEX)
        if not valid.all():
            self.ignored_pixels += int((~valid).sum())
            prediction, reference = prediction[valid], reference[valid]
        self.confusions.append(metrics.confusion_matrix(prediction, reference))
        self.true_fraction.append(decisions.cloud_fraction(reference))
        self.pred_fraction.append(decisions.cloud_fraction(prediction))
        self.pred_shadow.append(decisions.shadow_fraction(prediction))

    def __len__(self) -> int:
        return len(self.confusions)

    def binary_report(self, settings: EvaluationConfig, with_intervals: bool) -> dict[str, Any]:
        cms = np.stack(self.confusions)
        problems = ("cloud",) if self.binary_only else tuple(binary_metrics.PROBLEMS)
        out = binary_metrics.summary(cms, problems)
        if with_intervals:
            for problem in problems:
                values = binary_metrics.per_patch(cms, problem)
                stats = {f"median_{m}": _median_of(values[m]) for m in binary_metrics.MEASURES}
                intervals = bootstrap.bootstrap(
                    len(self),
                    stats,
                    resamples=settings.bootstrap_resamples,
                    seed=settings.bootstrap_seed,
                )
                out[problem]["intervals"] = {k: i.as_dict() for k, i in intervals.items()}
        return out

    def report(self, settings: EvaluationConfig, with_intervals: bool = True) -> dict[str, Any]:
        if not self.confusions:
            raise ValueError("no patches were scored")
        if self.binary_only:
            return {
                "patches": len(self),
                "ignored_pixels": self.ignored_pixels,
                "binary": self.binary_report(settings, with_intervals),
            }
        cms = np.stack(self.confusions)
        true = np.asarray(self.true_fraction)
        pred = np.asarray(self.pred_fraction)
        thresholds = sorted(set(settings.thresholds) | {settings.decision_threshold})
        out: dict[str, Any] = {
            "patches": len(self),
            "pixel": metrics.pixel_metrics(cms.sum(axis=0)),
            "frame": metrics.frame_metrics(true, pred, thresholds),
            "decision_threshold": settings.decision_threshold,
            "mean_predicted_shadow_fraction": float(np.mean(self.pred_shadow)),
            "ignored_pixels": self.ignored_pixels,
            "binary": self.binary_report(settings, with_intervals),
        }
        out["false_discard_rate"] = out["frame"]["thresholds"][
            f"{settings.decision_threshold:.2f}"
        ]["false_discard_rate"]
        if with_intervals:
            out["intervals"] = {
                name: interval.as_dict()
                for name, interval in bootstrap.bootstrap(
                    len(self),
                    _statistics(cms, true, pred, thresholds),
                    resamples=settings.bootstrap_resamples,
                    seed=settings.bootstrap_seed,
                ).items()
            }
        return out


def _median_of(values: NDArray[np.float64]) -> bootstrap.Statistic:
    """The median over a resample of patches, leaving out undefined values."""
    return lambda idx: binary_metrics.median(values[idx])


def _statistics(
    cms: NDArray[np.int64],
    true: NDArray[np.float64],
    pred: NDArray[np.float64],
    thresholds: Sequence[float],
) -> dict[str, bootstrap.Statistic]:
    stats: dict[str, bootstrap.Statistic] = {
        "mean_iou": lambda idx: metrics.mean_iou(cms[idx].sum(axis=0)),
        "overall_accuracy": lambda idx: metrics.overall_accuracy(cms[idx].sum(axis=0)),
        "cloud_fraction_mae": lambda idx: float(np.abs(true[idx] - pred[idx]).mean()),
    }

    def class_iou(c: int) -> bootstrap.Statistic:
        return lambda idx: float(metrics.per_class_iou(cms[idx].sum(axis=0))[c])

    def frame_stat(fn: Callable[..., float], t: float) -> bootstrap.Statistic:
        return lambda idx: fn(true[idx], pred[idx], t)

    for c in range(cms.shape[1]):
        stats[f"iou_class_{c}"] = class_iou(c)
    for t in thresholds:
        key = f"{t:.2f}"
        stats[f"false_discard_rate@{key}"] = frame_stat(metrics.false_discard_rate, t)
        stats[f"decision_accuracy@{key}"] = frame_stat(metrics.decision_accuracy, t)
    return stats


def breakdown(
    scores: Scores, patch_metadata: Sequence[dict[str, Any]], settings: EvaluationConfig
) -> dict[str, Any]:
    """Metrics per value of every metadata field with few distinct values, with counts."""
    out: dict[str, Any] = {}
    if not patch_metadata:
        return out
    fields = sorted({k for m in patch_metadata for k in m})
    for field in fields:
        values = [str(m.get(field, "missing")) for m in patch_metadata]
        distinct = sorted(set(values))
        if not 2 <= len(distinct) <= MAX_GROUPS:
            continue
        groups: dict[str, Scores] = defaultdict(Scores)
        for i, value in enumerate(values):
            group = groups[value]
            group.confusions.append(scores.confusions[i])
            group.true_fraction.append(scores.true_fraction[i])
            group.pred_fraction.append(scores.pred_fraction[i])
            group.pred_shadow.append(scores.pred_shadow[i])
        out[field] = {}
        for value, group in sorted(groups.items()):
            summary = group.report(settings, with_intervals=False)
            out[field][value] = {
                "patches": len(group),
                "mean_iou": summary["pixel"]["mean_iou"],
                "false_discard_rate": summary["false_discard_rate"],
            }
    return out


def frame_decisions(
    scores: Scores, positions: Sequence[int], patch_ids: Sequence[str], settings: EvaluationConfig
) -> list[dict[str, Any]]:
    """Per frame: true and predicted cloud fraction, predicted shadow fraction, decision."""
    threshold = settings.decision_threshold
    return [
        {
            "patch_id": patch_ids[position],
            "true_cloud_fraction": scores.true_fraction[i],
            "predicted_cloud_fraction": scores.pred_fraction[i],
            "predicted_shadow_fraction": scores.pred_shadow[i],
            "threshold": threshold,
            "decision": decisions.decide(scores.pred_fraction[i], threshold),
            "decision_from_reference": decisions.decide(scores.true_fraction[i], threshold),
        }
        for i, position in enumerate(positions)
    ]


# Test guard ----------------------------------------------------------------


def test_log_header() -> str:
    """The header of reports/test_log.md, also used when a new log is started elsewhere."""
    return (
        header_block(
            "Test split log",
            "in use",
            "Every evaluation on the test split, appended by `python -m tiefer_lab.evaluate "
            "--split test --final` before the test data is read. Entries are never edited "
            "or removed.",
            "../docs/assets/header.png",
        )
        + "\n## Entries\n\n"
    )


def log_test_evaluation(run_id: str, commit: str, reason: str, checkpoint_name: str) -> Path:
    """Append an entry to the test log before the test split is touched."""
    if not reason.strip():
        raise TestGuardError("--final needs --reason: say why the test split is evaluated")
    log = paths.reports_dir() / TEST_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text(test_log_header(), encoding="utf-8")
    now = dt.datetime.now(dt.UTC)
    when = f"{now.day} {now:%B %Y}, {now:%H:%M} UTC"
    clean = " ".join(reason.split())
    entry = (
        f"- {when}: run `{run_id}`, commit `{commit}`, checkpoint `{checkpoint_name}`. "
        f"Reason: {clean}\n"
    )
    with log.open("a", encoding="utf-8") as fh:
        fh.write(entry)
    return log


def check_test_guard(split: str, final: bool, reason: str | None) -> None:
    if split == "test" and not final:
        raise TestGuardError(
            "the test split is only for final evaluation: add --final and --reason, "
            "and tune on the validation split instead"
        )
    if split == "test" and not (reason and reason.strip()):
        raise TestGuardError("--final needs --reason: say why the test split is evaluated")
    if final and split != "test":
        raise TestGuardError("--final is only used with --split test")


# Evaluation ----------------------------------------------------------------


def load_model(run_dir: Path, config: Config, which: str, device: torch.device) -> flexible.Model:
    name = checkpoint.BEST if which == "best" else checkpoint.LAST
    state = checkpoint.load_checkpoint(run_dir / name, map_location=device)
    model = flexible.build(config.model, config.data.bands).to(device)
    model.load_state_dict(state["model"])
    model.eval()
    if device.type == "cuda":
        model = model.to(memory_format=torch.channels_last)
    return model


def score_mask_function(
    data: cache.SplitData, predict: Callable[[int], NDArray[np.uint8]], binary_only: bool = False
) -> Scores:
    scores = Scores(binary_only=binary_only)
    for i in range(len(data)):
        scores.add(predict(i), np.asarray(data.labels[i]))
    return scores


def tuned_threshold_rule(val: cache.SplitData) -> tuple[baselines.ThresholdRule, float]:
    """Tune the threshold rule on the validation split only."""
    hist = baselines.RuleHistogram()
    for i in range(len(val)):
        hist.add(to_reflectance(np.asarray(val.images[i])), np.asarray(val.labels[i]))
    return baselines.tune_threshold_rule(hist)


def evaluate_baselines(
    data: cache.SplitData, val: cache.SplitData, settings: EvaluationConfig
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    always = score_mask_function(data, lambda i: baselines.always_send(data.labels[i].shape))
    out["always_send"] = {"description": "every frame is sent", **always.report(settings)}
    rule, val_score = tuned_threshold_rule(val)
    scored = score_mask_function(
        data, lambda i: rule.predict(to_reflectance(np.asarray(data.images[i])))
    )
    out["threshold_rule"] = {
        "description": "brightness and whiteness of the visible bands, tuned on validation",
        "parameters": rule.as_dict(),
        "validation_mean_iou_when_tuned": val_score,
        **scored.report(settings),
    }
    for name, masks in data.reference.items():
        if data.reference_kinds.get(name, "four_class") != "four_class":
            # A cloud against non-cloud mask (1 cloud, 0 not) is scored on the
            # cloud problem only: cloud is shown as thick cloud, the rest as clear.
            def binary_mask(i: int, m: NDArray[np.uint8] = masks) -> NDArray[np.uint8]:
                raw = np.asarray(m[i])
                out_mask = np.where(raw == 1, THICK_CLOUD, CLEAR).astype(np.uint8)
                out_mask[raw == IGNORE_INDEX] = IGNORE_INDEX
                return out_mask

            ref = score_mask_function(data, binary_mask, binary_only=True)
            out[f"reference_{name}"] = {
                "description": "mask shipped with the dataset; cloud against non-cloud only",
                "kind": data.reference_kinds[name],
                **ref.report(settings),
            }
            continue

        def reference_mask(i: int, m: NDArray[np.uint8] = masks) -> NDArray[np.uint8]:
            return np.asarray(m[i])

        ref = score_mask_function(data, reference_mask)
        out[f"reference_{name}"] = {
            "description": "mask shipped with the dataset; uses more spectral bands",
            **ref.report(settings),
        }
    return out


def evaluate_run(
    run_dir: Path,
    split: str,
    *,
    with_baselines: bool = False,
    final: bool = False,
    reason: str | None = None,
    which: str = "best",
    device_name: str = "auto",
    allow_synthetic: bool = False,
    band_set: Sequence[str] | None = None,
) -> Path:
    """Evaluate a run on one split; a band-flexible run on one band set."""
    check_test_guard(split, final, reason)
    config = load_config(run_dir / CONFIG_NAME)
    run_meta = json.loads((run_dir / METADATA_NAME).read_text(encoding="utf-8"))
    run_id = str(run_meta["run_id"])
    git = metadata.git_commit()
    directory = cache.cache_dir(config.data.cache_name)
    index = cache.read_index(directory)
    if cache.is_synthetic(index) and not allow_synthetic:
        raise TrainingError("the cache holds synthetic data; only the smoke pipeline uses it")
    if split == "test":
        log_test_evaluation(run_id, git["commit"], reason or "", which)

    if config.model.input == "flexible":
        if not band_set:
            sets = [",".join(b) for b in config.train.band_sets]
            raise TrainingError(f"a band-flexible run needs --band-set, for example {sets}")
    elif band_set and tuple(band_set) != tuple(config.data.bands):
        raise TrainingError(f"this run takes the bands {list(config.data.bands)} only")
    device = devices.select_device(device_name)
    precision = devices.precision_for(device)
    bands = config.data.bands
    mean, std = cache.normalisation(index, bands)
    data = cache.load_split(directory, split, bands=bands)
    model = load_model(run_dir, config, which, device)
    if isinstance(model, flexible.FlexibleModel):
        model.set_band_set(band_set or bands)
    evaluated_bands = list(band_set or bands)
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, int]] = DataLoader(
        EvalPatches(data, mean, std, multiple=32),
        batch_size=config.data.eval_batch_size,
        num_workers=devices.data_workers(config.data.num_workers),
    )
    scores = Scores()
    positions: list[int] = []
    for position, pred, label in predict_masks(model, loader, device, precision):
        scores.add(pred, label)
        positions.append(position)

    report: dict[str, Any] = {
        "kind": "evaluation",
        "smoke": bool(run_meta.get("smoke")) or cache.is_synthetic(index),
        "run_id": run_id,
        "split": split,
        "final": final,
        "checkpoint": which,
        "provenance": metadata.provenance(device),
        "run": {
            "provenance": run_meta.get("provenance"),
            "seed": run_meta.get("seed"),
            "best_epoch": run_meta.get("best_epoch"),
            "status": run_meta.get("status"),
            "model": run_meta.get("model"),
        },
        "config": config_to_dict(config),
        "band_set": evaluated_bands,
        "data": {
            "cache": paths.portable(directory),
            "source": index.get("source"),
            "dataset": index.get("dataset"),
            "split_count": len(data),
            "split_build_date": index["splits"][split].get("build_date"),
        },
        "model": scores.report(config.evaluation),
        "breakdown": breakdown(scores, data.metadata, config.evaluation),
        "frames": frame_decisions(scores, positions, data.patch_ids, config.evaluation),
    }
    if with_baselines:
        # The baselines read blue, green, red and near infrared, in that order.
        base = cache.load_split(directory, split, bands=USED_BANDS)
        val = base if split == "val" else cache.load_split(directory, "val", bands=USED_BANDS)
        report["baselines"] = evaluate_baselines(base, val, config.evaluation)

    suffix = "" if config.model.input == "fixed" else "_" + band_set_name(evaluated_bands)
    out = paths.reports_dir() / "evaluation" / f"{run_id}_{split}{suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.evaluate", description="Evaluate a trained run."
    )
    parser.add_argument("--run", required=True, help="run directory or run ID")
    parser.add_argument("--split", required=True, choices=["val", "test"])
    parser.add_argument("--baselines", action="store_true", help="also evaluate the baselines")
    parser.add_argument("--final", action="store_true", help="required for --split test")
    parser.add_argument("--reason", help="why the test split is evaluated (with --final)")
    parser.add_argument("--checkpoint", default="best", choices=["best", "last"])
    parser.add_argument(
        "--band-set", default=None, help="bands of a band-flexible run, for example B02,B03,B04"
    )
    parser.add_argument("--device", default="auto", choices=devices.DEVICE_CHOICES)
    parser.add_argument("--allow-synthetic", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        check_test_guard(args.split, args.final, args.reason)
        run_dir = resolve_run_dir(args.run)
        out = evaluate_run(
            run_dir,
            args.split,
            with_baselines=args.baselines,
            final=args.final,
            reason=args.reason,
            which=args.checkpoint,
            device_name=args.device,
            allow_synthetic=args.allow_synthetic,
            band_set=args.band_set.split(",") if args.band_set else None,
        )
    except (TestGuardError, TrainingError, cache.CacheError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    report = json.loads(out.read_text(encoding="utf-8"))
    model = report["model"]
    print(f"mean IoU {model['pixel']['mean_iou']}", flush=True)
    print(
        f"false discard rate at {model['decision_threshold']}: {model['false_discard_rate']}",
        flush=True,
    )
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
