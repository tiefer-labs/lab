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
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from tiefer_lab import metrics
from tiefer_lab.config import Config, dump_toml, load_config
from tiefer_lab.data import cache
from tiefer_lab.data.dataset import DeviceTrainBatches, EvalPatches, TrainPatches
from tiefer_lab.data.transforms import Photometric
from tiefer_lab.models.cloud_filter import (
    build_model,
    count_macs,
    count_parameters,
    predict_masks,
)
from tiefer_lab.models.losses import CrossEntropyDice, class_weights
from tiefer_lab.utils import checkpoint, devices, metadata, paths
from tiefer_lab.utils.seeding import seed_everything
from tiefer_lab.utils.signals import StopRequest

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


def new_run_id(config: Config, commit: str) -> str:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    short = commit[:7] if commit != "unknown" else "nogit"
    return f"{config.name}-{stamp}-{short}"


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
    )


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
) -> str:
    """Train into `run_dir`. Returns the final status: completed, early_stopped or interrupted."""
    device = devices.select_device(device_name)
    precision = devices.precision_for(device)
    seed_everything(config.train.seed)
    directory, index = open_cache(config, allow_synthetic)
    mean, std = cache.normalisation(index)
    train_data = subset(
        cache.load_split(directory, "train", config.data.load_mode), config.data.max_train_patches
    )
    val_data = subset(
        cache.load_split(directory, "val", config.data.load_mode), config.data.max_val_patches
    )
    workers = devices.data_workers(config.data.num_workers)

    meta_path = run_dir / METADATA_NAME
    if resume:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("resumed", []).append(metadata.provenance(device))
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / CONFIG_NAME).write_text(dump_toml(config, CONFIG_HEADER), encoding="utf-8")
        model_probe = build_model(config.model.widths)
        meta = {
            "run_id": run_dir.name,
            "seed": config.train.seed,
            "config": CONFIG_NAME,
            "provenance": metadata.provenance(device),
            "precision": precision,
            "data": {
                "cache": paths.portable(directory),
                "source": index.get("source"),
                "dataset": index.get("dataset"),
                "train_patches": len(train_data),
                "val_patches": len(val_data),
                "train_in_memory": train_data.in_memory,
                "data_workers": workers,
            },
            "model": {
                "widths": list(config.model.widths),
                "parameters": count_parameters(model_probe),
                "macs_1x4x512x512": count_macs(model_probe),
            },
            "smoke": bool(cache.is_synthetic(index)) or config.name == "smoke",
            "start_time": metadata.now(),
            "status": "running",
        }
    _write_json(meta_path, meta)

    model = build_model(config.model.widths).to(device)
    if device.type == "cuda":
        model = model.to(memory_format=torch.channels_last)
        torch.backends.cudnn.benchmark = True
    weights = class_weights(index["splits"]["train"]["class_pixels"]).to(device)
    loss_fn = CrossEntropyDice(weights, config.train.dice_weight).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.train.learning_rate, weight_decay=config.train.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.train.epochs)
    scaler = torch.amp.GradScaler("cuda") if precision == "fp16" else None

    start_epoch, best_metric, best_epoch, stale = 0, -1.0, -1, 0
    if resume:
        state = checkpoint.load_checkpoint(run_dir / checkpoint.LAST, map_location=device)
        start_epoch, best_metric, best_epoch, stale = checkpoint.restore_training_state(
            state, model=model, optimizer=optimizer, scheduler=scheduler, scaler=scaler
        )
        print(f"resuming {run_dir.name} after epoch {start_epoch}", flush=True)

    photometric = Photometric(config.data.brightness, config.data.contrast)
    generator = torch.Generator()
    pin = device.type == "cuda"
    device_batches: DeviceTrainBatches | None = None
    train_set: TrainPatches | None = None
    train_loader: DataLoader[tuple[torch.Tensor, torch.Tensor]] | None = None
    if train_data.in_memory:
        # The split fits in memory: hold it once per job (on the GPU when it fits)
        # and augment on the device.
        device_batches = DeviceTrainBatches(
            train_data,
            mean,
            std,
            config.data.crop_size,
            photometric,
            device,
            config.data.batch_size,
            config.train.seed,
        )
        placement = device_batches.placement
    else:
        train_set = TrainPatches(train_data, mean, std, config.data.crop_size, photometric)
        train_loader = DataLoader(
            train_set,
            batch_size=config.data.batch_size,
            shuffle=True,
            num_workers=workers,
            generator=generator,
            drop_last=len(train_set) >= config.data.batch_size,
            pin_memory=pin,
        )
        placement = "data loader (memory-mapped)"
    print(f"training data: {len(train_data)} patches, {placement}", flush=True)
    meta.setdefault("data", {})["train_placement"] = placement
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
                scheduler=scheduler,
                scaler=scaler,
                epochs_done=epochs_done,
                best_metric=best_metric,
                best_epoch=best_epoch,
                epochs_without_improvement=stale,
            ),
        )

    status = "completed"
    with StopRequest() as stop:
        for epoch in range(start_epoch, config.train.epochs):
            # One seed per epoch, so a resumed run sees the same batches.
            generator.manual_seed(config.train.seed * 100_003 + epoch)
            if train_set is not None:
                train_set.set_epoch(epoch)
            batches = device_batches.epoch(epoch) if device_batches is not None else train_loader
            assert batches is not None
            model.train()
            started = time.monotonic()
            losses: list[float] = []
            for step, (images, labels) in enumerate(batches):
                if stop.requested or (
                    config.train.max_steps_per_epoch and step >= config.train.max_steps_per_epoch
                ):
                    break
                images = images.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                if device.type == "cuda":
                    images = images.contiguous(memory_format=torch.channels_last)
                optimizer.zero_grad(set_to_none=True)
                with devices.autocast(device, precision):
                    logits = model(images)
                loss = loss_fn(logits, labels)
                if scaler is not None:
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    optimizer.step()
                losses.append(float(loss.detach()))
                if (step + 1) % config.train.log_every == 0:
                    print(
                        f"epoch {epoch + 1} step {step + 1} loss {np.mean(losses):.4f}", flush=True
                    )
            if stop.requested:
                # The epoch is incomplete: record it as not done, so a resume repeats it.
                save_last(epoch)
                status = "interrupted"
                print(f"{stop.signal_name} received: saved {checkpoint.LAST}", flush=True)
                break
            scheduler.step()
            val = validate(model, val_loader, device, precision)
            val_miou = val["mean_iou"] if val["mean_iou"] is not None else -1.0
            improved = val_miou > best_metric
            if improved:
                best_metric, best_epoch, stale = val_miou, epoch + 1, 0
                checkpoint.save_checkpoint(
                    run_dir / checkpoint.BEST,
                    {"model": model.state_dict(), "epoch": epoch + 1, "val_mean_iou": val_miou},
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
                "best_epoch": best_epoch,
                "seconds": round(time.monotonic() - started, 2),
                "time": metadata.now(),
            }
            with (run_dir / METRICS_NAME).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True) + "\n")
            print(
                f"epoch {epoch + 1}/{config.train.epochs} loss {record['train_loss']} "
                f"val mIoU {val['mean_iou']} best {best_epoch}",
                flush=True,
            )
            if stale >= config.train.patience:
                status = "early_stopped"
                break

    meta["status"] = status
    meta["best_epoch"] = best_epoch
    meta["best_val_mean_iou"] = best_metric if best_epoch > 0 else None
    meta["end_time"] = metadata.now()
    _write_json(meta_path, meta)
    return status


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.train", description="Train the cloud filter."
    )
    parser.add_argument(
        "--config", type=Path, help="configuration file, for example configs/l1_base.toml"
    )
    parser.add_argument("--resume", help="run directory or run ID to continue from last.pt")
    parser.add_argument("--device", default="auto", choices=devices.DEVICE_CHOICES)
    parser.add_argument(
        "--cache-name", help="override data.cache_name (used by the smoke pipeline)"
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
            run_id = args.run_id or new_run_id(config, metadata.git_commit()["commit"])
            run_dir = paths.runs_dir() / run_id
            if run_dir.exists():
                raise TrainingError(f"run {run_id} already exists; use --resume to continue it")
            status = train(
                config, run_dir, device_name=args.device, allow_synthetic=args.allow_synthetic
            )
    except (TrainingError, cache.CacheError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(f"run {run_dir.name}: {status}", flush=True)
    print(f"run directory: {paths.portable(run_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
