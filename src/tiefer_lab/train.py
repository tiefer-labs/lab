# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Train the cloud filter.

    python -m tiefer_lab.train --config configs/<name>.toml [--resume <run-dir>] [--device ...]

Every run writes to `$TIEFER_RUNS_DIR/<run-id>/`:

- `config.toml`: the resolved configuration
- `metadata.json`: provenance (git commit, platform, libraries, device,
  Slurm fields), seed, data source, start and end time, status
- `metrics.jsonl`: one JSON line per epoch
- `last.pt`: the latest training state, written every epoch and on SIGTERM
  or SIGUSR1; `--resume <run-dir>` continues from it
- `best.pt`: the model with the best validation mean IoU (early stopping)
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import math
import os
import sys
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, TypeVar

import numpy as np
import torch
from torch.utils.data import DataLoader

from tiefer_lab import decisions, metrics
from tiefer_lab.config import Config, dump_toml, load_config
from tiefer_lab.data import cache, padding, sensor
from tiefer_lab.data.dataset import DeviceTrainBatches, EvalPatches
from tiefer_lab.data.source import L1C_BAND_NAMES
from tiefer_lab.data.transforms import Photometric
from tiefer_lab.models import flexible
from tiefer_lab.models.cloud_filter import (
    count_macs,
    count_parameters,
    predict_masks,
)
from tiefer_lab.models.cloudscout import CloudScoutNet, frame_loss
from tiefer_lab.models.losses import (
    CrossEntropyDice,
    class_weights,
    crop_cloud_fractions,
    distillation,
    frame_fraction_loss,
    lovasz_softmax,
)
from tiefer_lab.reports import add_model_label
from tiefer_lab.utils import checkpoint, devices, metadata, paths
from tiefer_lab.utils.ema import WeightEMA
from tiefer_lab.utils.seeding import seed_everything
from tiefer_lab.utils.signals import StopRequest

T = TypeVar("T")
CONFIG_NAME = "config.toml"
METADATA_NAME = "metadata.json"
METRICS_NAME = "metrics.jsonl"

CONFIG_HEADER = (
    "# Resolved configuration of a training run, written by tiefer_lab.train.\n"
    "# This Source Code Form is subject to the terms of the Mozilla Public\n"
    "# License, v. 2.0. If a copy of the MPL was not distributed with this\n"
    "# file, You can obtain one at https://mozilla.org/MPL/2.0/.\n"
)


class TrainingError(RuntimeError):
    pass


def resolve_run_dir(run: str) -> Path:
    """A run directory given as a path or as a run ID under $TIEFER_RUNS_DIR."""
    candidate = Path(run)
    if candidate.is_dir():
        return candidate.resolve()
    under_runs = paths.runs_dir() / run
    if under_runs.is_dir():
        return under_runs.resolve()
    raise TrainingError(f"run {run!r} not found (looked in $TIEFER_RUNS_DIR)")


def resolve_run_reference(reference: str) -> Path:
    """A run named by its run ID or by a prefix that matches exactly one run.

    Configs that start from another run (`init_checkpoint`, `teacher_run`) are
    committed before that run exists, so they name it by a prefix such as
    "cloudscout_reimpl_step1_th30-seed0"; two matching runs are an error, never a guess.
    """
    candidate = paths.runs_dir() / reference
    if candidate.is_dir():
        return candidate.resolve()
    matches = sorted(
        p for p in paths.runs_dir().glob(f"{reference}*") if (p / checkpoint.BEST).is_file()
    )
    if len(matches) != 1:
        found = ", ".join(p.name for p in matches) or "none"
        raise TrainingError(
            f"{reference!r} must name exactly one finished run in $TIEFER_RUNS_DIR; found {found}"
        )
    return matches[0].resolve()


def load_run_model(reference: str, device: torch.device) -> tuple[torch.nn.Module, Config]:
    """The best.pt model of another run of this repository, in eval mode."""
    run_dir = resolve_run_reference(reference)
    config = load_config(run_dir / CONFIG_NAME)
    model = flexible.build(config.model, config.data.bands)
    state = checkpoint.load_checkpoint(run_dir / checkpoint.BEST, map_location=device)
    model.load_state_dict(state["model"])
    return model.to(device).eval(), config


def step_gradients_ok(parameters: Sequence[torch.nn.Parameter], settings: Any) -> bool:
    """Clip the global gradient norm when configured; False when the step must be skipped.

    With `grad_clip_norm` > 0 the gradients are scaled to that global norm. With
    `skip_nonfinite`, a step whose gradient norm is not finite is skipped (the
    caller counts it). With neither, nothing is computed and every step is taken,
    as before.
    """
    clip = float(settings.grad_clip_norm)
    if clip <= 0 and not settings.skip_nonfinite:
        return True
    norm = torch.nn.utils.clip_grad_norm_(
        [p for p in parameters if p.grad is not None], clip if clip > 0 else float("inf")
    )
    return not (settings.skip_nonfinite and not bool(torch.isfinite(norm)))


def with_extra_split(
    train: cache.SplitData, directory: Path, bands: Sequence[str]
) -> cache.SplitData:
    """The training split followed by the extra split (scribble and nolabel patches).

    The extra split is built only once its facts are verified (LOCATION_FIELD and
    SCRIBBLE_UNLABELLED_CODE in data/source.py); without it training stops. Both
    splits are held in memory together.
    """
    try:
        extra = cache.load_split(directory, cache.EXTRA_SPLIT, "memory", bands=bands)
    except cache.CacheError as err:
        raise TrainingError(
            f"data.include_extra needs the {cache.EXTRA_SPLIT} split, built only after "
            f"LOCATION_FIELD and SCRIBBLE_UNLABELLED_CODE are verified: {err}"
        ) from None
    if train.reference or extra.reference:
        raise TrainingError("reference masks are not used for training; build without them")
    combined_padding = (
        [
            *(train.padding or [padding.NO_PADDING] * len(train)),
            *(extra.padding or [padding.NO_PADDING] * len(extra)),
        ]
        if train.padding or extra.padding
        else []
    )
    return dataclasses.replace(
        train,
        images=np.concatenate([np.asarray(train.images), np.asarray(extra.images)]),
        labels=np.concatenate([np.asarray(train.labels), np.asarray(extra.labels)]),
        patch_ids=[*train.patch_ids, *extra.patch_ids],
        metadata=[*train.metadata, *extra.metadata],
        in_memory=True,
        padding=combined_padding,
    )


def frame_targets(labels: torch.Tensor, threshold: float) -> tuple[torch.Tensor, torch.Tensor]:
    """1.0 for a crop whose labelled cloud fraction is at least `threshold`, and which crops
    have labelled pixels at all."""
    fraction, has = crop_cloud_fractions(labels)
    return (fraction >= threshold).float(), has


def validate_frames(
    model: torch.nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, int]],
    device: torch.device,
    precision: devices.Precision,
    threshold: float,
) -> dict[str, Any]:
    """Validation of a frame classifier: decision accuracy at its label threshold."""
    true, pred = [], []
    for _, mask, label in predict_masks(model, loader, device, precision):
        f = decisions.frame_fractions(mask, label)
        true.append(f.true_cloud)
        pred.append(f.predicted_cloud)
    accuracy = metrics.decision_accuracy(np.asarray(true), np.asarray(pred), threshold)
    return {
        "mean_iou": None,
        "iou": None,
        "overall_accuracy": None,
        "frame_accuracy": None if not np.isfinite(accuracy) else float(accuracy),
    }


def new_run_id(config: Config, commit: str) -> str:
    """<config>-seed<seed>-<UTC time>-<commit>: runs with different seeds never share a folder."""
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    short = commit[:7] if commit != "unknown" else "nogit"
    return f"{config.name}-seed{config.train.seed}-{stamp}-{short}"


def subset(data: cache.SplitData, limit: int | None) -> cache.SplitData:
    """The first `limit` patches of a split (all of them when limit is None)."""
    if limit is None or limit >= len(data):
        return data
    return dataclasses.replace(
        data,
        images=data.images[:limit],
        labels=data.labels[:limit],
        patch_ids=data.patch_ids[:limit],
        metadata=data.metadata[:limit],
        reference={k: v[:limit] for k, v in data.reference.items()},
        reference_kinds=dict(data.reference_kinds),
        padding=data.padding[:limit],
    )


def training_class_pixels(data: cache.SplitData, index: dict[str, Any]) -> list[int]:
    """Pixels per class of the training split for the class weights.

    The counts in the index include the dataset's padding; when the split is
    padded, they are counted again over the masked labels, so the padding
    never weighs in (data/padding.py).
    """
    if not data.padding:
        return [int(c) for c in index["splits"]["train"]["class_pixels"]]
    return cache.count_class_pixels(data.labels)


def open_cache(config: Config, allow_synthetic: bool) -> tuple[Path, dict[str, Any]]:
    directory = cache.cache_dir(config.data.cache_name)
    index = cache.read_index(directory)
    if cache.is_synthetic(index) and not allow_synthetic:
        raise TrainingError(
            "the cache holds synthetic data; synthetic data is only used by the smoke pipeline"
        )
    return directory, index


def validate(
    model: torch.nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, int]],
    device: torch.device,
    precision: devices.Precision,
) -> dict[str, Any]:
    cm = np.zeros((4, 4), dtype=np.int64)
    for _, pred, label in predict_masks(model, loader, device, precision):
        cm += metrics.confusion_matrix(pred, label)
    return metrics.pixel_metrics(cm)


def band_set_name(bands: Sequence[str]) -> str:
    return "+".join(bands)


ALL_BAND_SETS = "all"


def band_set_option(run_dir: Path, value: str | None) -> list[list[str] | None]:
    """The band sets that `--band-set` names for a run.

    None: the run's default (a specialist's own bands; a band-flexible run
    then stops with a message naming its sets). "all": every band set of a
    band-flexible run, or the specialist's own bands. Otherwise one
    comma-separated list.
    """
    if value is None:
        return [None]
    if value == ALL_BAND_SETS:
        config = load_config(run_dir / CONFIG_NAME)
        if config.model.input == "flexible":
            return [list(bands) for bands in config.train.band_sets]
        return [None]
    return [value.split(",")]


def validate_band_sets(
    model: torch.nn.Module,
    band_sets: Sequence[Sequence[str]],
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, int]],
    device: torch.device,
    precision: devices.Precision,
    select: Sequence[str] = (),
) -> dict[str, Any]:
    """Validation of a band-flexible model on every band set.

    The mean IoU that chooses best.pt is the mean over the band sets, or, with
    `select` (train.select_band_set), the mean IoU of that band set alone.
    """
    per_set = {}
    for bands in band_sets:
        model.set_band_set(bands)  # type: ignore[operator]
        per_set[band_set_name(bands)] = validate(model, loader, device, precision)
    model.set_band_set(L1C_BAND_NAMES)  # type: ignore[operator]
    values = [v["mean_iou"] for v in per_set.values() if v["mean_iou"] is not None]
    first = next(iter(per_set.values()))
    selected = per_set[band_set_name(select)]["mean_iou"] if select else None
    return {
        "mean_iou": selected if select else (float(np.mean(values)) if values else None),
        "mean_iou_over_band_sets": float(np.mean(values)) if values else None,
        "iou": first["iou"],
        "overall_accuracy": first["overall_accuracy"],
        "band_sets": {k: v["mean_iou"] for k, v in per_set.items()},
    }


def draw_band_set(seed: int, epoch: int, step: int, count: int) -> int:
    """The band set of a training step, fixed by seed, epoch and step (resumable)."""
    generator = torch.Generator().manual_seed(seed * 1_000_003 + epoch * 10_007 + step)
    return int(torch.randint(count, (1,), generator=generator))


def learning_rate_factor(step: int, total_steps: int, warmup_steps: int) -> float:
    """Multiplier of the configured learning rate at optimizer step `step` (from 0).

    Linear warm-up from 1 / warmup_steps to 1 over the first warmup_steps steps,
    then cosine decay from 1 to 0 at total_steps.
    """
    if warmup_steps > 0 and step < warmup_steps:
        return (step + 1) / warmup_steps
    progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
    return 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))


class WaitClock:
    """Seconds the training loop spends waiting for the next batch of an epoch."""

    def __init__(self) -> None:
        self.seconds = 0.0

    def timed(self, batches: Iterator[T]) -> Iterator[T]:
        iterator = iter(batches)
        while True:
            started = time.monotonic()
            try:
                item = next(iterator)
            except StopIteration:
                return
            self.seconds += time.monotonic() - started
            yield item


def epoch_timing(
    train_seconds: float, val_seconds: float, steps: int, full_steps: int, batch_size: int
) -> dict[str, Any]:
    """Wall-clock time of one epoch, and the time a full epoch would take.

    When an epoch is cut short (max_steps_per_epoch), the full epoch is
    estimated from the measured time per step; otherwise it is the measured time.
    """
    per_step = train_seconds / steps if steps else None
    full_train = per_step * full_steps if per_step is not None else None
    return {
        "train_seconds": round(train_seconds, 2),
        "val_seconds": round(val_seconds, 2),
        "steps_per_full_epoch": full_steps,
        "patches_per_second": round(steps * batch_size / train_seconds, 1)
        if steps and train_seconds > 0
        else None,
        # Same rounding as the parts, so the estimate is never below val_seconds.
        "full_epoch_seconds": round(full_train + val_seconds, 2)
        if full_train is not None
        else None,
        "full_epoch_estimated": steps < full_steps,
    }


def timing_line(record: dict[str, Any]) -> str:
    estimate = record["full_epoch_seconds"]
    kind = "estimated" if record["full_epoch_estimated"] else "measured"
    return (
        f"epoch {record['epoch']} time: train {record['train_seconds']} s for "
        f"{record['steps']} of {record['steps_per_full_epoch']} steps "
        f"({record['patches_per_second']} patches/s), validation {record['val_seconds']} s; "
        f"full epoch {estimate} s ({kind})"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def train(
    config: Config,
    run_dir: Path,
    *,
    device_name: str = "auto",
    resume: bool = False,
    allow_synthetic: bool = False,
    timing: bool = False,
    seed_override: bool = False,
) -> str:
    """Train into `run_dir`. Returns the final status: completed, early_stopped or interrupted."""
    device = devices.select_device(device_name)
    precision = devices.precision_for(device, config.train.precision)
    cpu_threads = devices.set_cpu_threads()
    runs_per_gpu = cache.runs_per_gpu()
    seed_everything(config.train.seed)
    directory, index = open_cache(config, allow_synthetic)
    bands = config.data.bands
    mean, std = cache.normalisation(index, bands)
    load_started = time.monotonic()
    full_train = cache.load_split(directory, "train", config.data.load_mode, bands=bands)
    if config.data.include_extra:
        full_train = with_extra_split(full_train, directory, bands)
    train_data = subset(full_train, config.data.max_train_patches)
    val_data = subset(
        cache.load_split(directory, "val", config.data.load_mode, bands=bands),
        config.data.max_val_patches,
    )
    flexible_input = config.model.input == "flexible"
    workers = devices.data_workers(config.data.num_workers)

    meta_path = run_dir / METADATA_NAME
    if resume:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("resumed", []).append(metadata.provenance(device))
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / CONFIG_NAME).write_text(dump_toml(config, CONFIG_HEADER), encoding="utf-8")
        model_probe = flexible.build(config.model, bands)
        meta = {
            "run_id": run_dir.name,
            "seed": config.train.seed,
            "seed_from_command_line": seed_override,
            "config": CONFIG_NAME,
            "provenance": metadata.provenance(device),
            "precision": precision,
            "precision_setting": config.train.precision,
            # Runs that shared this job's GPU, cores and memory (train_packed.sbatch).
            "runs_per_gpu": runs_per_gpu,
            "data": {
                "cache": paths.portable(directory),
                "source": index.get("source"),
                "dataset": index.get("dataset"),
                "train_patches": len(train_data),
                # The dataset's padding, set to IGNORE_INDEX in the labels (data/padding.py).
                "padding_sides": list(padding.PADDING_SIDES),
                "padded_pixels_masked": {
                    "train": train_data.padded_pixels(),
                    "val": val_data.padded_pixels(),
                },
                "val_patches": len(val_data),
                "train_in_memory": train_data.in_memory,
                "load_mode": config.data.load_mode,
                # Set by tiefer_stage_cache when the cache was copied to the job's local disk.
                "cache_staged_local": os.environ.get("TIEFER_CACHE_STAGED") == "1",
                "data_workers": workers,
                "cpu_threads": cpu_threads,
            },
            "model": {
                "widths": list(config.model.widths),
                "architecture": config.model.architecture,
                "input": config.model.input,
                "bands": list(bands),
                "parameters": count_parameters(model_probe),
                "macs_512x512": count_macs(model_probe),
            },
            # Smoke and timing runs (cut short from the command line) are never results.
            "smoke": bool(cache.is_synthetic(index)) or config.name == "smoke" or timing,
            "timing_run": timing,
            "start_time": metadata.now(),
            "status": "running",
        }
    slurm = meta["resumed"][-1] if resume else meta["provenance"]
    meta.setdefault("sessions", []).append(
        {
            "start": metadata.now(),
            "end": None,
            "job_id": slurm.get("slurm", {}).get("job_id"),
            "gpus": 1 if device.type == "cuda" else 0,
            "runs_per_gpu": runs_per_gpu,
        }
    )
    add_model_label(meta, run_dir.name, config.model.architecture)
    _write_json(meta_path, meta)

    model = flexible.build(config.model, bands).to(device)
    if device.type == "cuda":
        model = model.to(memory_format=torch.channels_last)
        torch.backends.cudnn.benchmark = True
    if config.train.init_checkpoint and not resume:
        source_dir = resolve_run_reference(config.train.init_checkpoint)
        state0 = checkpoint.load_checkpoint(source_dir / checkpoint.BEST, map_location=device)
        model.load_state_dict(state0["model"])
        meta["init_checkpoint"] = source_dir.name
        print(f"initialised from {source_dir.name}/{checkpoint.BEST}", flush=True)
    if config.train.train_only == "decision":
        if not isinstance(model, CloudScoutNet):
            raise TrainingError("train_only = decision needs the cloudscout architecture")
        for name, parameter in model.named_parameters():
            parameter.requires_grad_(name.startswith("decision."))
    teacher: torch.nn.Module | None = None
    teacher_flexible = False
    if config.train.teacher_run:
        teacher, teacher_config = load_run_model(config.train.teacher_run, device)
        teacher_flexible = teacher_config.model.input == "flexible"
        if tuple(teacher_config.data.bands) != tuple(bands):
            raise TrainingError("the teacher must read the same bands from the same cache")
        for parameter in teacher.parameters():
            parameter.requires_grad_(False)
        meta["teacher_run"] = resolve_run_reference(config.train.teacher_run).name
    weights = (
        class_weights(training_class_pixels(full_train, index)).to(device)
        if config.train.class_weighting == "median_frequency"
        else None
    )
    loss_fn = CrossEntropyDice(
        weights, config.train.dice_weight, focal_gamma=config.train.focal_gamma
    ).to(device)
    band_sets = [tuple(b) for b in config.train.band_sets]
    all_bands = torch.ones(len(bands), device=device)
    set_masks = [flexible.availability(b).to(device) for b in band_sets]
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable, lr=config.train.learning_rate, weight_decay=config.train.weight_decay
    )
    scaler = torch.amp.GradScaler("cuda") if precision == "fp16" else None

    ema = WeightEMA(model, config.train.ema_decay) if config.train.ema_decay > 0 else None
    start_epoch, best_metric, best_epoch, stale = 0, -1.0, -1, 0
    if resume:
        state = checkpoint.load_checkpoint(run_dir / checkpoint.LAST, map_location=device)
        try:
            start_epoch, best_metric, best_epoch, stale = checkpoint.restore_training_state(
                state, model=model, optimizer=optimizer, scaler=scaler
            )
        except ValueError as err:
            raise TrainingError(str(err)) from None
        if ema is not None:
            ema.load_state_dict(state["ema"])
        print(f"resuming {run_dir.name} after epoch {start_epoch}", flush=True)

    photometric = Photometric(config.data.brightness, config.data.contrast)
    robustness = sensor.Robustness(
        config.data.rescale_min,
        config.data.rescale_max,
        config.data.gain_jitter,
        config.data.offset_jitter,
        config.data.noise_std,
        config.data.blur_sigma,
    )
    pin = device.type == "cuda"
    # One sampler for every placement: in memory (GPU, pinned or CPU) or memory-mapped
    # from the cache files, so the placement and the worker count never change the
    # batches a config and seed draw (tests/test_data_feeding.py).
    device_batches = DeviceTrainBatches(
        train_data,
        mean,
        std,
        config.data.crop_size,
        photometric,
        device,
        config.data.batch_size,
        config.train.seed,
        robustness=robustness,
    )
    placement = device_batches.placement
    full_steps = len(device_batches)
    steps_per_epoch = min(full_steps, config.train.max_steps_per_epoch or full_steps)
    total_steps = steps_per_epoch * config.train.epochs
    warmup_steps = steps_per_epoch * config.train.warmup_epochs
    load_seconds = round(time.monotonic() - load_started, 1)
    print(
        f"training data: {len(train_data)} patches, {placement}, ready in {load_seconds} s",
        flush=True,
    )
    meta.setdefault("data", {})["train_placement"] = placement
    meta["data"]["ready_seconds"] = load_seconds
    _write_json(meta_path, meta)
    val_loader = DataLoader(
        EvalPatches(val_data, mean, std, multiple=max(32, model.downsampling)),
        batch_size=config.data.eval_batch_size,
        num_workers=workers,
        pin_memory=pin,
    )

    def save_last(epochs_done: int) -> None:
        checkpoint.save_checkpoint(
            run_dir / checkpoint.LAST,
            checkpoint.training_state(
                model=model,
                optimizer=optimizer,
                scaler=scaler,
                epochs_done=epochs_done,
                best_metric=best_metric,
                best_epoch=best_epoch,
                epochs_without_improvement=stale,
                ema=ema.state_dict() if ema is not None else None,
            ),
        )

    status = "completed"
    skipped_total = 0
    with StopRequest() as stop:
        for epoch in range(start_epoch, config.train.epochs):
            # One seed per epoch (DeviceTrainBatches.epoch), so a resumed run sees the
            # same batches.
            wait = WaitClock()
            batches = wait.timed(device_batches.epoch(epoch))
            model.train()
            if device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(device)
            started = time.monotonic()
            losses: list[float] = []
            skipped = 0
            for step, (images, labels) in enumerate(batches):
                if stop.requested or (
                    config.train.max_steps_per_epoch and step >= config.train.max_steps_per_epoch
                ):
                    break
                images = images.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                if device.type == "cuda":
                    images = images.contiguous(memory_format=torch.channels_last)
                factor = learning_rate_factor(
                    epoch * steps_per_epoch + step, total_steps, warmup_steps
                )
                for group in optimizer.param_groups:
                    group["lr"] = config.train.learning_rate * factor
                optimizer.zero_grad(set_to_none=True)
                with devices.autocast(device, precision):
                    if config.train.task == "frame":
                        assert isinstance(model, CloudScoutNet)
                        logits = model.frame_logits(images)
                    elif flexible_input:
                        choice = draw_band_set(config.train.seed, epoch, step, len(band_sets))
                        drawn = set_masks[choice].expand(images.shape[0], -1)
                        logits = model(images, drawn)
                    else:
                        logits = model(images)
                loss: Any
                if config.train.task == "frame":
                    cloudy, has = frame_targets(labels, config.train.frame_label_threshold)
                    loss = (
                        frame_loss(logits[has], cloudy[has], config.train.false_positive_weight)
                        if bool(has.any())
                        else logits.sum() * 0.0
                    )
                else:
                    loss = loss_fn(logits, labels)
                    if config.train.frame_loss_weight > 0:
                        loss = loss + config.train.frame_loss_weight * frame_fraction_loss(
                            logits, labels
                        )
                    if config.train.lovasz_weight > 0:
                        loss = loss + config.train.lovasz_weight * lovasz_softmax(logits, labels)
                if (
                    flexible_input
                    and config.train.distill_weight > 0
                    and band_sets[choice] != tuple(bands)
                ):
                    with torch.no_grad(), devices.autocast(device, precision):
                        self_teacher = model(images, all_bands.expand(images.shape[0], -1))
                    loss = loss + config.train.distill_weight * distillation(logits, self_teacher)
                if teacher is not None:
                    with torch.no_grad(), devices.autocast(device, precision):
                        soft = (
                            teacher(images, all_bands.expand(images.shape[0], -1))
                            if teacher_flexible
                            else teacher(images)
                        )
                    loss = loss + config.train.teacher_weight * distillation(logits, soft)
                if config.train.skip_nonfinite and not bool(torch.isfinite(loss.detach())):
                    skipped += 1
                    optimizer.zero_grad(set_to_none=True)
                    continue
                if scaler is not None:
                    scaler.scale(loss).backward()
                    if config.train.grad_clip_norm > 0 or config.train.skip_nonfinite:
                        scaler.unscale_(optimizer)
                else:
                    loss.backward()
                if not step_gradients_ok(trainable, config.train):
                    skipped += 1
                    optimizer.zero_grad(set_to_none=True)
                    if scaler is not None:
                        scaler.update()
                    continue
                if scaler is not None:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                if ema is not None:
                    ema.update(model)
                losses.append(float(loss.detach()))
                if (step + 1) % config.train.log_every == 0:
                    print(
                        f"epoch {epoch + 1} step {step + 1} loss {np.mean(losses):.4f}", flush=True
                    )
            skipped_total += skipped
            if stop.requested:
                # The epoch is incomplete: record it as not done, so a resume repeats it.
                save_last(epoch)
                status = "interrupted"
                print(f"{stop.signal_name} received: saved {checkpoint.LAST}", flush=True)
                break
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            train_seconds = time.monotonic() - started
            val_started = time.monotonic()
            # With EMA, validation and best.pt use the averaged weights.
            eval_model = ema.module if ema is not None else model
            if config.train.task == "frame":
                val = validate_frames(
                    eval_model, val_loader, device, precision, config.train.frame_label_threshold
                )
                selection = val["frame_accuracy"]
            elif flexible_input:
                val = validate_band_sets(
                    eval_model,
                    band_sets,
                    val_loader,
                    device,
                    precision,
                    config.train.select_band_set,
                )
                selection = val["mean_iou"]
            else:
                val = validate(eval_model, val_loader, device, precision)
                selection = val["mean_iou"]
            val_seconds = time.monotonic() - val_started
            # The validation value that chooses best.pt: mean IoU, or the frame decision
            # accuracy of a frame classifier.
            val_miou = selection if selection is not None else -1.0
            # Early stopping on validation mean IoU: only a gain of at least
            # min_improvement counts, so noise does not keep training alive.
            improved = val_miou > best_metric + config.train.min_improvement
            if improved:
                best_metric, best_epoch, stale = val_miou, epoch + 1, 0
                checkpoint.save_checkpoint(
                    run_dir / checkpoint.BEST,
                    {
                        "model": eval_model.state_dict(),
                        "weights": "ema" if ema is not None else "model",
                        "epoch": epoch + 1,
                        "val_mean_iou": val_miou,
                    },
                )
            else:
                stale += 1
            save_last(epoch + 1)
            record = {
                "epoch": epoch + 1,
                "train_loss": float(np.mean(losses)) if losses else None,
                "steps": len(losses),
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
                "val_mean_iou": val["mean_iou"],
                "val_iou": val["iou"],
                "val_overall_accuracy": val["overall_accuracy"],
                "val_mean_iou_by_band_set": val.get("band_sets"),
                "val_frame_accuracy": val.get("frame_accuracy"),
                "skipped_steps": skipped,
                "best_epoch": best_epoch,
                "seconds": round(time.monotonic() - started, 2),
                # Time the training loop waited for its batches, and the peak GPU memory.
                "data_wait_seconds": round(wait.seconds, 3),
                "gpu_memory_peak_bytes": (
                    int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
                ),
                "time": metadata.now(),
                **epoch_timing(
                    train_seconds, val_seconds, len(losses), full_steps, config.data.batch_size
                ),
            }
            with (run_dir / METRICS_NAME).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True) + "\n")
            print(
                f"epoch {epoch + 1}/{config.train.epochs} loss {record['train_loss']} "
                f"val mIoU {val['mean_iou']} best {best_epoch}",
                flush=True,
            )
            print(timing_line(record), flush=True)
            if stale >= config.train.patience:
                status = "early_stopped"
                break

    meta["status"] = status
    meta["skipped_steps"] = int(meta.get("skipped_steps", 0)) + skipped_total
    meta["best_epoch"] = best_epoch
    meta["best_val_mean_iou"] = best_metric if best_epoch > 0 else None
    meta["end_time"] = metadata.now()
    meta["sessions"][-1]["end"] = meta["end_time"]
    _write_json(meta_path, meta)
    return status


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.train", description="Train the cloud filter."
    )
    parser.add_argument(
        "--config", type=Path, help="configuration file, for example configs/sieb_base.toml"
    )
    parser.add_argument("--resume", help="run directory or run ID to continue from last.pt")
    parser.add_argument("--device", default="auto", choices=devices.DEVICE_CHOICES)
    parser.add_argument(
        "--cache-name", help="override data.cache_name (used by the smoke pipeline)"
    )
    parser.add_argument(
        "--seed", type=int, help="override train.seed; recorded in the metadata and the run ID"
    )
    parser.add_argument(
        "--epochs", type=int, help="override train.epochs (timing runs; marked as smoke)"
    )
    parser.add_argument(
        "--max-steps-per-epoch",
        type=int,
        help="override train.max_steps_per_epoch (timing runs; marked as smoke)",
    )
    parser.add_argument("--allow-synthetic", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--run-id", help="name of a new run (default: <config>-<UTC time>-<commit>)"
    )
    args = parser.parse_args(argv)
    if bool(args.config) == bool(args.resume):
        parser.error("give either --config for a new run or --resume for an existing one")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.resume:
            run_dir = resolve_run_dir(args.resume)
            config = load_config(run_dir / CONFIG_NAME)
            meta = json.loads((run_dir / METADATA_NAME).read_text(encoding="utf-8"))
            if meta.get("status") in ("completed", "early_stopped"):
                print(f"run {run_dir.name} is already {meta['status']}", flush=True)
                return 0
            allow = args.allow_synthetic
            status = train(
                config, run_dir, device_name=args.device, resume=True, allow_synthetic=allow
            )
        else:
            config = load_config(args.config)
            if args.cache_name:
                config = dataclasses.replace(
                    config, data=dataclasses.replace(config.data, cache_name=args.cache_name)
                )
            timing = args.epochs is not None or args.max_steps_per_epoch is not None
            if timing:
                train_cfg = dataclasses.replace(
                    config.train,
                    epochs=args.epochs or config.train.epochs,
                    max_steps_per_epoch=args.max_steps_per_epoch
                    or config.train.max_steps_per_epoch,
                )
                config = dataclasses.replace(config, train=train_cfg)
            if args.seed is not None:
                config = dataclasses.replace(
                    config, train=dataclasses.replace(config.train, seed=args.seed)
                )
            run_id = args.run_id or new_run_id(config, metadata.git_commit()["commit"])
            run_dir = paths.runs_dir() / run_id
            if run_dir.exists():
                raise TrainingError(f"run {run_id} already exists; use --resume to continue it")
            status = train(
                config,
                run_dir,
                device_name=args.device,
                allow_synthetic=args.allow_synthetic,
                timing=timing,
                seed_override=args.seed is not None,
            )
    except (TrainingError, cache.CacheError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"run {run_dir.name}: {status}", flush=True)
    print(f"run directory: {paths.portable(run_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
