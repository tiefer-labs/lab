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
    assert {p.name for p in configs} >= {"smoke.toml", "sieb_base.toml"}
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
    config = load_config(repo_root / "configs" / "sieb_base.toml")
    assert config.data.batch_size == 128
    # Linear scaling from 0.002 at a batch size of 32.
    assert config.train.learning_rate == pytest.approx(0.002 * 128 / 32)
    assert config.train.min_improvement == pytest.approx(0.001)
    assert config.train.patience == 15
    with pytest.raises(ConfigError):
        config_from_dict({"name": "x", "train": {"min_improvement": -0.1}})


def test_l1_full_runs_its_cosine_schedule_to_the_end(repo_root: Path) -> None:
    base = load_config(repo_root / "configs" / "sieb_base.toml")
    full = load_config(repo_root / "configs" / "sieb.toml")
    assert full.name == "sieb"
    assert full.train.patience >= full.train.epochs, "early stopping never ends the schedule"
    assert full.train.warmup_epochs == 5 and full.train.ema_decay == pytest.approx(0.999)
    # Everything else is sieb_base.
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
        "wandler_500k": (0.4e6, 0.6e6),
        "wandler_1m": (0.8e6, 1.2e6),
        "wandler_4m": (3.0e6, 5.0e6),
        "wandler_22m": (20e6, 30e6),
        "wandler_convnext_21m": (20e6, 30e6),
        "lupe_1m": (0.8e6, 1.2e6),
        "lupe_22m": (20e6, 30e6),
    }
    reference = load("wandler_1m")
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
        "wandler_1m_zero_design": ("model", {"flexible_design"}),
        "wandler_1m_class_weights": ("train", {"class_weighting"}),
        "wandler_1m_focal": ("train", {"focal_gamma"}),
        "wandler_1m_no_self_distill": ("train", {"distill_weight"}),
        "wandler_1m_rescale_2x": ("data", {"rescale_min", "rescale_max"}),
        "wandler_1m_gain_offset": ("data", {"gain_jitter", "offset_jitter"}),
        "wandler_1m_noise_blur": ("data", {"noise_std", "blur_sigma"}),
        # Variants of the stability, frame, IoU, rescale and export options.
        "wandler_1m_grad_clip": ("train", {"grad_clip_norm"}),
        "wandler_1m_skip_nonfinite": ("train", {"skip_nonfinite"}),
        "wandler_1m_warmup10": ("train", {"warmup_epochs"}),
        "wandler_1m_best_by_four_bands": ("train", {"select_band_set"}),
        "wandler_1m_frame_loss": ("train", {"frame_loss_weight"}),
        "wandler_1m_lovasz": ("train", {"lovasz_weight"}),
        "wandler_1m_crop384": ("data", {"crop_size"}),
        "wandler_1m_crop512": ("data", {"crop_size"}),
        "wandler_1m_rescale_3x": ("data", {"rescale_min", "rescale_max"}),
        "wandler_1m_landsat_bandsets": ("train", {"band_sets"}),
        "wandler_1m_extra_data": ("data", {"include_extra"}),
        "wandler_1m_distill_22m": ("train", {"teacher_run", "teacher_weight"}),
        "wandler_1m_int8_percentile": ("export", {"calibrate_method"}),
        "wandler_1m_int8_entropy": ("export", {"calibrate_method"}),
        "wandler_1m_int8_calib1024": ("export", {"calibration_patches"}),
        "wandler_1m_int8_calib_stratified": ("export", {"calibration_stratified"}),
        "wandler_1m_int8_float_ends": ("export", {"keep_fp_first_last"}),
        "wandler_1m_int8_input_clip": ("export", {"input_clip_percentile"}),
    }
    for name, (section, keys) in variants.items():
        config = load(name)
        for part in ("data", "model", "train", "evaluation", "export"):
            a = dataclasses.asdict(getattr(config, part))
            b = dataclasses.asdict(getattr(reference, part))
            changed = {k for k in a if a[k] != b[k]}
            assert changed == (keys if part == section else set()), (name, part, changed)


def _changed(config: Config, reference: Config) -> dict[str, set[str]]:
    import dataclasses

    out = {}
    for part in ("data", "model", "train", "evaluation", "export"):
        a = dataclasses.asdict(getattr(config, part))
        b = dataclasses.asdict(getattr(reference, part))
        changed = {k for k in a if a[k] != b[k]}
        if changed:
            out[part] = changed
    return out


def test_l1_and_cloudscout_variants_change_one_setting(repo_root: Path) -> None:
    def load(name: str) -> Config:
        return load_config(repo_root / "configs" / f"{name}.toml")

    l1 = {
        "sieb_rescale_2x": {"data": {"rescale_min", "rescale_max"}},
        "sieb_frame_loss": {"train": {"frame_loss_weight"}},
        "sieb_lovasz": {"train": {"lovasz_weight"}},
        "sieb_grad_clip": {"train": {"grad_clip_norm"}},
        "sieb_int8_percentile": {"export": {"calibrate_method"}},
        "sieb_int8_entropy": {"export": {"calibrate_method"}},
        "sieb_int8_calib1024": {"export": {"calibration_patches"}},
        "sieb_int8_calib_stratified": {"export": {"calibration_stratified"}},
        "sieb_int8_float_ends": {"export": {"keep_fp_first_last"}},
        "sieb_int8_input_clip": {"export": {"input_clip_percentile"}},
    }
    for name, expected in l1.items():
        assert _changed(load(name), load("sieb")) == expected, name
    assert _changed(load("cloudscout_reimpl_th50"), load("cloudscout_reimpl_th70")) == {
        "train": {"frame_label_threshold"}
    }


def test_candidate_references_are_drafts_with_the_stated_changes(repo_root: Path) -> None:
    """A combined candidate is its own reference with its row in docs/ASSUMPTIONS.md."""

    def load(name: str) -> Config:
        return load_config(repo_root / "configs" / f"{name}.toml")

    stated = {
        "data": {"rescale_min", "rescale_max"},
        "train": {"grad_clip_norm", "skip_nonfinite"},
    }
    assert _changed(load("sieb_candidate"), load("sieb")) == stated
    assert _changed(load("wandler_1m_candidate"), load("wandler_1m")) == stated
    assumptions = (repo_root / "docs" / "ASSUMPTIONS.md").read_text(encoding="utf-8")
    for name in (
        "sieb_candidate",
        "wandler_1m_candidate",
        "wandler_1m_candidate_finetune",
        "cloudscout_reimpl_th70",
    ):
        assert f"`{name}`" in assumptions, name
