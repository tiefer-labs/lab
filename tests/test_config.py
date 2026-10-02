# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tiefer_lab.config import (
    Config,
    ConfigError,
    config_from_dict,
    dump_toml,
    load_config,
)


def test_repository_configs_load(repo_root: Path) -> None:
    configs = sorted((repo_root / "configs").glob("*.toml"))
    assert {p.name for p in configs} >= {"smoke.toml", "l1_base.toml"}
    for path in configs:
        config = load_config(path)
        assert config.name == path.stem


def test_defaults_and_types() -> None:
    config = config_from_dict({"name": "x", "model": {"widths": [8, 16]}, "train": {"epochs": 2}})
    assert config.model.widths == (8, 16)
    assert config.train.epochs == 2
    assert config.train.learning_rate == pytest.approx(2e-3)
    assert config.evaluation.thresholds == (0.3, 0.5, 0.7)


@pytest.mark.parametrize(
    "raw, message",
    [
        ({"name": "x", "train": {"epoch": 3}}, "unknown keys"),
        ({"name": "x", "trian": {}}, "unknown top-level"),
        ({"name": "x", "train": {"epochs": "3"}}, "expected int"),
        ({"name": "x", "train": {"epochs": 0}}, "epochs"),
        ({"name": "x", "data": {"crop_size": 100}}, "multiple of 32"),
        ({"name": "x", "data": {"load_mode": "disk"}}, "must be one of"),
        ({"name": "x", "evaluation": {"thresholds": [0.0]}}, "thresholds"),
        ({"train": {}}, "name"),
    ],
)
def test_invalid_configs_are_rejected(raw: dict, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        config_from_dict(raw)


def test_dump_round_trip(tmp_path: Path) -> None:
    config = config_from_dict(
        {"name": "round-trip", "data": {"max_train_patches": 5}, "train": {"seed": 7}}
    )
    path = tmp_path / "config.toml"
    path.write_text(dump_toml(config, header="# resolved"), encoding="utf-8")
    assert tomllib.loads(path.read_text())["train"]["seed"] == 7
    again = load_config(path)
    assert again == config
    assert isinstance(again, Config)


def test_data_workers_follow_slurm(monkeypatch: pytest.MonkeyPatch) -> None:
    from tiefer_lab.utils.devices import data_workers

    monkeypatch.delenv("SLURM_CPUS_PER_TASK", raising=False)
    assert data_workers(4) == 4
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "72")
    assert data_workers(4) == 71
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "1")
    assert data_workers(4) == 4


def test_l1_base_scales_learning_rate_with_batch_size(repo_root: Path) -> None:
    config = load_config(repo_root / "configs" / "l1_base.toml")
    assert config.data.batch_size == 128
    # Linear scaling from 0.002 at a batch size of 32.
    assert config.train.learning_rate == pytest.approx(0.002 * 128 / 32)
    assert config.train.min_improvement == pytest.approx(0.001)
    assert config.train.patience == 15
    with pytest.raises(ConfigError):
        config_from_dict({"name": "x", "train": {"min_improvement": -0.1}})


def test_l1_full_runs_its_cosine_schedule_to_the_end(repo_root: Path) -> None:
    base = load_config(repo_root / "configs" / "l1_base.toml")
    full = load_config(repo_root / "configs" / "l1_full.toml")
    assert full.name == "l1_full"
    assert full.train.patience >= full.train.epochs, "early stopping never ends the schedule"
    assert full.train.warmup_epochs == 5 and full.train.ema_decay == pytest.approx(0.999)
    # Everything else is l1_base.
    import dataclasses

    same = dataclasses.replace(
        full.train, patience=base.train.patience, warmup_epochs=0, ema_decay=0.0
    )
    assert same == base.train
    assert (full.data, full.model, full.evaluation, full.export) == (
        base.data,
        base.model,
        base.evaluation,
        base.export,
    )
    with pytest.raises(ConfigError):
        config_from_dict({"name": "x", "train": {"ema_decay": 0.5}})
    with pytest.raises(ConfigError):
        config_from_dict({"name": "x", "train": {"epochs": 3, "warmup_epochs": 3}})


def test_l2_ladder_sizes_and_one_change_per_variant(repo_root: Path) -> None:
    import dataclasses

    from tiefer_lab.models import flexible
    from tiefer_lab.models.cloud_filter import count_parameters

    def load(name: str) -> Config:
        return load_config(repo_root / "configs" / f"{name}.toml")

    targets = {
        "l2_flex_0p5m": (0.4e6, 0.6e6),
        "l2_flex_1m": (0.8e6, 1.2e6),
        "l2_flex_4m": (3.0e6, 5.0e6),
        "l2_flex_22m": (20e6, 30e6),
        "l2_flex_cnx_21m": (20e6, 30e6),
        "l2_spec_1m": (0.8e6, 1.2e6),
        "l2_spec_22m": (20e6, 30e6),
    }
    reference = load("l2_flex_1m")
    for name, (low, high) in targets.items():
        config = load(name)
        n = count_parameters(flexible.build(config.model, config.data.bands))
        assert low <= n <= high, f"{name}: {n} parameters"
        # The ladder shares every training setting with the reference run.
        expected_train = (
            reference.train
            if config.model.input == "flexible"
            else dataclasses.replace(reference.train, band_sets=(), distill_weight=0.0)
        )
        assert config.train == expected_train, name
    variants = {
        "l2_flex_1m_zero": ("model", {"flexible_design"}),
        "l2_flex_1m_classweights": ("train", {"class_weighting"}),
        "l2_flex_1m_focal": ("train", {"focal_gamma"}),
        "l2_flex_1m_nodistill": ("train", {"distill_weight"}),
        "l2_flex_1m_rescale": ("data", {"rescale_min", "rescale_max"}),
        "l2_flex_1m_gainoffset": ("data", {"gain_jitter", "offset_jitter"}),
        "l2_flex_1m_noiseblur": ("data", {"noise_std", "blur_sigma"}),
    }
    for name, (section, keys) in variants.items():
        config = load(name)
        for part in ("data", "model", "train", "evaluation", "export"):
            a = dataclasses.asdict(getattr(config, part))
            b = dataclasses.asdict(getattr(reference, part))
            changed = {k for k in a if a[k] != b[k]}
            assert changed == (keys if part == section else set()), (name, part, changed)
