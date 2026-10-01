# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Typed configuration loaded from TOML.

Every section is a frozen dataclass. Unknown sections or keys, wrong types
and out-of-range values are errors, so a typo never silently falls back to a
default. `dump_toml` writes the resolved configuration of a run.
"""

from __future__ import annotations

import dataclasses
import math
import tomllib
import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


class ConfigError(ValueError):
    """The configuration file is invalid."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigError(message)


@dataclass(frozen=True)
class DataConfig:
    cache_name: str = "cloudsen12-l1c-high"
    crop_size: int = 256
    batch_size: int = 16
    eval_batch_size: int = 4
    num_workers: int = 4
    load_mode: Literal["auto", "memory", "mmap"] = "auto"
    brightness: float = 0.1
    contrast: float = 0.1
    max_train_patches: int | None = None
    max_val_patches: int | None = None

    def __post_init__(self) -> None:
        _check(self.crop_size >= 32 and self.crop_size % 32 == 0, "crop_size: multiple of 32")
        _check(self.batch_size >= 1 and self.eval_batch_size >= 1, "batch sizes must be >= 1")
        _check(self.num_workers >= 0, "num_workers must be >= 0")
        _check(self.load_mode in ("auto", "memory", "mmap"), "load_mode: auto, memory or mmap")
        _check(0.0 <= self.brightness < 0.5 and 0.0 <= self.contrast < 0.5, "jitter in [0, 0.5)")
        for name in ("max_train_patches", "max_val_patches"):
            value = getattr(self, name)
            _check(value is None or value >= 1, f"{name} must be >= 1")


@dataclass(frozen=True)
class ModelConfig:
    widths: tuple[int, ...] = (16, 32, 64, 128, 256)

    def __post_init__(self) -> None:
        _check(2 <= len(self.widths) <= 6, "widths: 2 to 6 stages")
        _check(all(w >= 4 for w in self.widths), "widths must be >= 4")


@dataclass(frozen=True)
class TrainConfig:
    seed: int = 0
    epochs: int = 100
    learning_rate: float = 2e-3
    weight_decay: float = 1e-4
    dice_weight: float = 1.0
    patience: int = 15
    max_steps_per_epoch: int | None = None
    log_every: int = 50

    def __post_init__(self) -> None:
        _check(self.epochs >= 1, "epochs must be >= 1")
        _check(self.learning_rate > 0 and self.weight_decay >= 0, "learning rate and decay")
        _check(self.dice_weight >= 0, "dice_weight must be >= 0")
        _check(self.patience >= 1, "patience must be >= 1")
        _check(self.max_steps_per_epoch is None or self.max_steps_per_epoch >= 1, "max_steps")
        _check(self.log_every >= 1, "log_every must be >= 1")


@dataclass(frozen=True)
class EvaluationConfig:
    thresholds: tuple[float, ...] = (0.3, 0.5, 0.7)
    decision_threshold: float = 0.5
    bootstrap_resamples: int = 1000
    bootstrap_seed: int = 0

    def __post_init__(self) -> None:
        _check(all(0 < t <= 1 for t in self.thresholds), "thresholds in (0, 1]")
        _check(0 < self.decision_threshold <= 1, "decision_threshold in (0, 1]")
        _check(self.bootstrap_resamples >= 100, "bootstrap_resamples must be >= 100")


@dataclass(frozen=True)
class ExportConfig:
    opset: int = 17
    input_size: int = 512
    calibration_patches: int = 256
    max_logit_difference: float = 1e-2
    min_argmax_agreement: float = 0.999
    max_verify_patches: int | None = None

    def __post_init__(self) -> None:
        _check(13 <= self.opset <= 21, "opset in [13, 21]")
        _check(self.input_size % 32 == 0, "input_size must be a multiple of 32")
        _check(self.calibration_patches >= 1, "calibration_patches must be >= 1")
        _check(self.max_logit_difference > 0, "max_logit_difference must be > 0")
        _check(0 < self.min_argmax_agreement <= 1, "min_argmax_agreement in (0, 1]")
        _check(self.max_verify_patches is None or self.max_verify_patches >= 1, "verify patches")


@dataclass(frozen=True)
class Config:
    name: str
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    def __post_init__(self) -> None:
        _check(bool(self.name) and self.name.replace("_", "").replace("-", "").isalnum(), "name")


SECTIONS: dict[str, type[Any]] = {
    "data": DataConfig,
    "model": ModelConfig,
    "train": TrainConfig,
    "evaluation": EvaluationConfig,
    "export": ExportConfig,
}


def _convert(value: Any, annotation: Any, where: str) -> Any:
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin in (types.UnionType, typing.Union):
        if value is None and type(None) in args:
            return None
        inner = [a for a in args if a is not type(None)]
        return _convert(value, inner[0], where)
    if origin is Literal:
        _check(value in args, f"{where}: must be one of {args}, got {value!r}")
        return value
    if origin is tuple:
        _check(isinstance(value, list), f"{where}: expected a list")
        return tuple(_convert(v, args[0], f"{where}[]") for v in value)
    if annotation is bool:
        _check(isinstance(value, bool), f"{where}: expected true or false")
        return value
    if annotation is int:
        _check(isinstance(value, int) and not isinstance(value, bool), f"{where}: expected int")
        return value
    if annotation is float:
        ok = isinstance(value, int | float) and not isinstance(value, bool)
        _check(ok and math.isfinite(value), f"{where}: expected a number")
        return float(value)
    if annotation is str:
        _check(isinstance(value, str), f"{where}: expected a string")
        return value
    raise ConfigError(f"{where}: unsupported type {annotation}")


def _build(cls: type[Any], table: dict[str, Any], section: str) -> Any:
    hints = typing.get_type_hints(cls)
    names = {f.name for f in dataclasses.fields(cls)}
    unknown = sorted(set(table) - names)
    _check(not unknown, f"[{section}]: unknown keys {unknown}")
    kwargs = {k: _convert(v, hints[k], f"{section}.{k}") for k, v in table.items()}
    try:
        return cls(**kwargs)
    except ConfigError as err:
        raise ConfigError(f"[{section}] {err}") from None


def config_from_dict(raw: dict[str, Any]) -> Config:
    unknown = sorted(set(raw) - set(SECTIONS) - {"name"})
    _check(not unknown, f"unknown top-level keys {unknown}")
    _check(isinstance(raw.get("name"), str), "name: required string")
    sections = {}
    for key, cls in SECTIONS.items():
        table = raw.get(key, {})
        _check(isinstance(table, dict), f"[{key}] must be a table")
        sections[key] = _build(cls, table, key)
    return Config(name=raw["name"], **sections)


def load_config(path: Path) -> Config:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"{path.name}: {err}") from None
    return config_from_dict(raw)


def config_to_dict(config: Config) -> dict[str, Any]:
    out: dict[str, Any] = {"name": config.name}
    for key in SECTIONS:
        section = dataclasses.asdict(getattr(config, key))
        out[key] = {k: list(v) if isinstance(v, tuple) else v for k, v in section.items()}
    return out


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise ConfigError(f"cannot write {value!r} to TOML")


def dump_toml(config: Config, header: str = "") -> str:
    """TOML for a resolved configuration. Keys set to None are left out (TOML has no null)."""
    data = config_to_dict(config)
    lines = [header.rstrip("\n")] if header else []
    lines.append(f"name = {_toml_value(data['name'])}")
    for key in SECTIONS:
        lines.append("")
        lines.append(f"[{key}]")
        for name, value in data[key].items():
            if value is not None:
                lines.append(f"{name} = {_toml_value(value)}")
    return "\n".join(lines) + "\n"
