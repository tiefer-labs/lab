# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Config names follow the scheme of docs/SPEC.md, section 8, and the rename changed no setting."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tiefer_lab.config import config_to_dict, load_config

FAMILIES = ("sieb", "wandler", "lupe", "cloudscout_reimpl", "smoke")
SCHEME = re.compile(r"^(sieb|wandler|lupe|cloudscout_reimpl|smoke)(_[a-z0-9]+)*$")
SIZE = re.compile(r"^\d+(k|m)$")

# The rename of 15 October 2026, fixed here: old config name to new config name.
RENAMED = {
    "l1_base": "sieb_base",
    "l1_full": "sieb",
    "l1_full_clip": "sieb_grad_clip",
    "l1_full_frameloss": "sieb_frame_loss",
    "l1_full_lovasz": "sieb_lovasz",
    "l1_full_rescale": "sieb_rescale_2x",
    "l1_full_cal1024": "sieb_int8_calib1024",
    "l1_full_calstrat": "sieb_int8_calib_stratified",
    "l1_full_fpends": "sieb_int8_float_ends",
    "l1_full_inputclip": "sieb_int8_input_clip",
    "l1_full_int8entropy": "sieb_int8_entropy",
    "l1_full_int8pct": "sieb_int8_percentile",
    "l1_v3": "sieb_candidate",
    "l2_flex_0p5m": "wandler_500k",
    "l2_flex_1m": "wandler_1m",
    "l2_flex_4m": "wandler_4m",
    "l2_flex_22m": "wandler_22m",
    "l2_flex_cnx_21m": "wandler_convnext_21m",
    "l2_flex_1m_zero": "wandler_1m_zero_design",
    "l2_flex_1m_classweights": "wandler_1m_class_weights",
    "l2_flex_1m_focal": "wandler_1m_focal",
    "l2_flex_1m_nodistill": "wandler_1m_no_self_distill",
    "l2_flex_1m_teacher": "wandler_1m_distill_22m",
    "l2_flex_1m_clip": "wandler_1m_grad_clip",
    "l2_flex_1m_guard": "wandler_1m_skip_nonfinite",
    "l2_flex_1m_warmup10": "wandler_1m_warmup10",
    "l2_flex_1m_frameloss": "wandler_1m_frame_loss",
    "l2_flex_1m_lovasz": "wandler_1m_lovasz",
    "l2_flex_1m_crop384": "wandler_1m_crop384",
    "l2_flex_1m_crop512": "wandler_1m_crop512",
    "l2_flex_1m_rescale": "wandler_1m_rescale_2x",
    "l2_flex_1m_rescale3": "wandler_1m_rescale_3x",
    "l2_flex_1m_noiseblur": "wandler_1m_noise_blur",
    "l2_flex_1m_gainoffset": "wandler_1m_gain_offset",
    "l2_flex_1m_bandsets": "wandler_1m_landsat_bandsets",
    "l2_flex_1m_select4": "wandler_1m_best_by_four_bands",
    "l2_flex_1m_extra": "wandler_1m_extra_data",
    "l2_flex_1m_cal1024": "wandler_1m_int8_calib1024",
    "l2_flex_1m_calstrat": "wandler_1m_int8_calib_stratified",
    "l2_flex_1m_fpends": "wandler_1m_int8_float_ends",
    "l2_flex_1m_inputclip": "wandler_1m_int8_input_clip",
    "l2_flex_1m_int8entropy": "wandler_1m_int8_entropy",
    "l2_flex_1m_int8pct": "wandler_1m_int8_percentile",
    "l2_flex_1m_v3": "wandler_1m_candidate",
    "l2_flex_1m_v3_frameft": "wandler_1m_candidate_finetune",
    "l2_spec_1m": "lupe_1m",
    "l2_spec_22m": "lupe_22m",
    "cloudscout_th30": "cloudscout_reimpl_step1_th30",
    "cloudscout": "cloudscout_reimpl_th70",
    "cloudscout_th50": "cloudscout_reimpl_th50",
    "smoke": "smoke",
}
# Every field of every config before the rename, resolved with its defaults.
BEFORE = Path(__file__).resolve().parent / "data" / "configs_before_rename.json"
# Fields that name another run by its config prefix; they follow the rename.
RUN_REFERENCES = (("train", "init_checkpoint"), ("train", "teacher_run"))


def _configs(repo_root: Path) -> dict[str, Path]:
    return {p.stem: p for p in sorted((repo_root / "configs").glob("*.toml"))}


def test_every_config_name_follows_the_scheme(repo_root: Path) -> None:
    for stem, path in _configs(repo_root).items():
        assert SCHEME.match(stem), stem
        assert load_config(path).name == stem, stem
        parts = stem.split("_")
        if parts[0] == "sieb":
            # Sieb has one size and carries none.
            assert not any(SIZE.match(p) for p in parts[1:]), stem
        if parts[0] in ("wandler", "lupe"):
            assert any(SIZE.match(p) for p in parts[1:]), stem
        if "finetune" in parts:
            assert stem.endswith("_candidate_finetune"), stem


def test_int8_names_change_the_export_only(repo_root: Path) -> None:
    configs = _configs(repo_root)
    for stem in configs:
        if "_int8_" not in stem:
            continue
        reference = stem.split("_int8_")[0]
        a = config_to_dict(load_config(configs[reference]))
        b = config_to_dict(load_config(configs[stem]))
        changed = {s for s in a if s != "name" and a[s] != b[s]}
        assert changed == {"export"}, (stem, changed)


def test_every_family_is_explained_in_the_spec(repo_root: Path) -> None:
    spec = (repo_root / "docs" / "SPEC.md").read_text(encoding="utf-8")
    section = spec.split("### Model names", 1)[1].split("\n### ", 1)[0]
    for family in FAMILIES:
        assert re.search(rf"^\| `{family}` \| [^|]+ \| [^|]+ \|$", section, re.M), family
    for german in ("sieve", "converter", "magnifying glass"):
        assert german in section, german


def test_the_rename_changes_no_setting(repo_root: Path) -> None:
    before = json.loads(BEFORE.read_text(encoding="utf-8"))
    configs = _configs(repo_root)
    assert set(RENAMED) == set(before)
    assert set(RENAMED.values()) == set(configs)
    for old, new in RENAMED.items():
        expected = before[old]
        expected["name"] = new
        for section, key in RUN_REFERENCES:
            value = expected[section].get(key)
            if value:
                prefix, _, rest = value.partition("-seed")
                expected[section][key] = f"{RENAMED[prefix]}-seed{rest}"
        actual = config_to_dict(load_config(configs[new]))
        assert actual.keys() == expected.keys(), new
        for section, fields in expected.items():
            if not isinstance(fields, dict):
                assert actual[section] == fields, (new, section)
                continue
            assert actual[section].keys() == fields.keys(), (new, section)
            for key, value in fields.items():
                assert actual[section][key] == value, (new, section, key)
