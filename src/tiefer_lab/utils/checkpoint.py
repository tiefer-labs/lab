# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Checkpoints: atomic save, safe load (weights_only=True), resume.

A checkpoint is a dictionary of tensors, numbers and strings only, so it
loads with `torch.load(..., weights_only=True)` and never unpickles code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import torch

LAST = "last.pt"
BEST = "best.pt"


def save_checkpoint(path: Path, state: dict[str, Any]) -> None:
    """Write to a temporary file first, then rename, so a stop never leaves a broken file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(state, tmp)
    os.replace(tmp, path)


def load_checkpoint(path: Path, map_location: str | torch.device = "cpu") -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"no checkpoint at {path.name}")
    state: dict[str, Any] = torch.load(path, map_location=map_location, weights_only=True)
    return state


# The learning rate is computed from the step number (warm-up, then cosine),
# so no scheduler state is stored. Checkpoints of the earlier per-epoch
# scheduler cannot be resumed with this version.
SCHEDULE = "per-step warm-up and cosine"


def training_state(
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    epochs_done: int,
    best_metric: float,
    best_epoch: int,
    epochs_without_improvement: int,
    ema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything needed to continue training exactly where it stopped."""
    return {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "schedule": SCHEDULE,
        "ema": ema or {},
        "scaler": scaler.state_dict() if scaler is not None else {},
        "epochs_done": epochs_done,
        "best_metric": best_metric,
        "best_epoch": best_epoch,
        "epochs_without_improvement": epochs_without_improvement,
        "torch_rng": torch.get_rng_state(),
    }


def restore_training_state(
    state: dict[str, Any],
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
) -> tuple[int, float, int, int]:
    """Load a training state; returns (epochs_done, best_metric, best_epoch, patience)."""
    if state.get("schedule") != SCHEDULE:
        raise ValueError(
            "this checkpoint was written with the earlier per-epoch learning rate schedule; "
            "resume it with the commit recorded in its metadata.json, or start a new run"
        )
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    if scaler is not None and state.get("scaler"):
        scaler.load_state_dict(state["scaler"])
    torch.set_rng_state(state["torch_rng"])
    return (
        int(state["epochs_done"]),
        float(state["best_metric"]),
        int(state["best_epoch"]),
        int(state["epochs_without_improvement"]),
    )
