# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Independent datasets: reflectance, labels, tiles and stops, by hand and on synthetic files."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pytest

from tiefer_lab import evaluate, train
from tiefer_lab.config import config_from_dict
from tiefer_lab.data import build_cache, cache, independent
from tiefer_lab.data.source import IGNORE_INDEX, L1C_BAND_NAMES, DataSourceError


def test_landsat_reflectance_by_hand() -> None:
    dn = np.array([0, 10000, 20000], np.uint16)
    out = independent.landsat_toa_reflectance(dn, 2.0e-5, -0.1, 30.0)
    assert math.isnan(out[0])
    # (2e-5 x 10000 - 0.1) / sin(30 degrees) = 0.1 / 0.5 = 0.2
    assert out[1] == pytest.approx(0.2) and out[2] == pytest.approx(0.6)
    mtl = independent.parse_mtl(
        "GROUP = X\n  REFLECTANCE_MULT_BAND_2 = 2.0000E-05\n  REFLECTANCE_ADD_BAND_2 = -0.100000\n"
        '  SUN_ELEVATION = 30.0\n  SPACECRAFT_ID = "LANDSAT_8"\nEND_GROUP = X\n'
    )
    assert independent.landsat_scale(mtl, 2) == (2.0e-5, -0.1, 30.0)
    assert mtl["SPACECRAFT_ID"] == "LANDSAT_8"
    with pytest.raises(DataSourceError, match="REFLECTANCE_MULT_BAND_5"):
        independent.landsat_scale(mtl, 5)


def test_labels_are_harmonised_and_unknown_codes_stop() -> None:
    sparcs = independent.DATASETS["landsat8_sparcs"].label_codes
    assert sparcs is not None
    raw = np.array([[0, 1, 2], [3, 4, 5], [6, 6, 5]])
    np.testing.assert_array_equal(
        independent.harmonise(raw, sparcs, "sparcs"), [[3, 3, 0], [0, 0, 1], [0, 0, 1]]
    )
    with pytest.raises(DataSourceError, match="label codes \\[7\\]"):
        independent.harmonise(np.array([7]), sparcs, "sparcs")
    kappa = independent.DATASETS["kappaset"].label_codes
    assert kappa is not None
    np.testing.assert_array_equal(
        independent.harmonise(np.arange(6), kappa, "kappaset"), [255, 0, 3, 2, 1, 255]
    )


def test_resample_and_tiles_by_hand() -> None:
    image = np.ones((2, 600, 600), np.float32)
    image[0, 0, 0] = np.nan
    label = np.zeros((600, 600), np.uint8)
    out, lab, _ = independent.resample(image, label, 20.0)
    assert out.shape == (2, 1200, 1200) and lab.shape == (1200, 1200)
    assert lab[0, 0] == IGNORE_INDEX and lab[2, 2] == 0
    lab[:509, 509:1018] = IGNORE_INDEX  # one tile all unlabelled
    kept, counts = independent.tiles("s", out, lab, {"x": 1})
    assert counts["kept"] == 3 and counts["dropped_nodata"] == 1
    assert counts["remainder_pixels"] == 1200 * 1200 - 4 * 509 * 509
    assert kept[0].tile_id == "s_r0c0" and kept[0].metadata["tile_col"] == 0


def test_band_mapping_and_unverified_readers_stop(tmp_path: Path) -> None:
    assert independent.LANDSAT8_TO_S2[5] == "B8A"
    assert independent.stored_bands("landsat8_biome", ["B02", "B03", "B04", "B08", "B8A"]) == [
        "B02",
        "B03",
        "B04",
        "B8A",
    ]
    with pytest.raises(DataSourceError, match="not verified yet"):
        list(independent.READERS["kappaset"](tmp_path, ["B02"]))
    for name in ("landsat8_biome", "landsat8_sparcs"):
        with pytest.raises(DataSourceError, match="candidate, no decision yet"):
            list(independent.READERS[name](tmp_path, ["B02"]))
    with pytest.raises(DataSourceError, match="product_naming"):
        independent.s2_baseline("S2A_MSIL1C_20180101T000000_N0206_R001_T31UFU_20180101T000000")


def _catalogue(root: Path, scene: str, size: int = 600) -> None:
    rng = np.random.default_rng(0)
    (root / "subscenes").mkdir(parents=True)
    (root / "masks").mkdir()
    cube = rng.uniform(0.0, 0.3, (size, size, 13)).astype(np.float32)
    classes = np.zeros((size, size), np.int64)
    classes[: size // 2] = 1
    cube[: size // 2] += 0.5
    classes[size // 2 :, : size // 4] = 2
    np.save(root / "subscenes" / f"{scene}.npy", cube)
    np.save(root / "masks" / f"{scene}.npy", np.eye(3, dtype=bool)[classes])
    tags = independent.DATASETS["s2_cloud_catalogue"].strata_fields
    with (root / "classification_tags.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, ["scene", "difficulty", "shadows_marked", *tags])
        writer.writeheader()
        writer.writerow(
            {"scene": scene, "difficulty": 1, "shadows_marked": 1, **{t: 0 for t in tags}}
        )


def test_catalogue_builds_tiles_and_is_evaluated_as_independent(
    tiefer_env: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scene = "S2A_MSIL1C_20180501T101031_N0206_R022_T32TQM_20180501T121528"
    root = tmp_path / "download"
    _catalogue(root, scene)
    build_cache.main(["--split", "all", "--synthetic", "--limit", "6", "--patch-size", "64"])
    # Without the verified naming convention and the CloudSEN12+ product field, it stops.
    args = ["--split", "test", "--source", "s2_cloud_catalogue", "--root", str(root)]
    with pytest.raises(DataSourceError):
        build_cache.main([*args, "--cloudsen12-cache", "synthetic"])
    monkeypatch.setitem(independent.OPEN_FACTS["s2_cloud_catalogue"], "product_naming", "ESA")
    monkeypatch.setattr(independent, "CLOUDSEN12_PRODUCT_FIELD", "synthetic_group")
    with pytest.raises(cache.CacheError, match="cloudsen12-cache"):
        build_cache.main(args)
    assert build_cache.main([*args, "--cloudsen12-cache", "synthetic"]) == 0
    directory = cache.cache_dir("s2_cloud_catalogue")
    index = cache.read_index(directory)
    assert index["bands"] == ["B02", "B03", "B04", "B08", "B8A"]
    assert index["splits"]["test"]["count"] == 4  # 600 px at 20 m: 1200 at 10 m, 2 x 2 tiles
    assert index["independent"]["sensor"] == independent.SENTINEL2
    # Resumable: a second build reuses the scene files.
    assert build_cache.main([*args, "--cloudsen12-cache", "synthetic"]) == 0

    raw = {
        "name": "tiny",
        "data": {
            "cache_name": "synthetic",
            "crop_size": 32,
            "batch_size": 4,
            "eval_batch_size": 2,
            "num_workers": 0,
        },
        "model": {"widths": [8, 16]},
        "train": {"epochs": 1, "max_steps_per_epoch": 1, "log_every": 1},
        "evaluation": {"bootstrap_resamples": 100},
    }
    run = tiefer_env["TIEFER_RUNS_DIR"] / "tiny-seed0-x"
    train.train(config_from_dict(raw), run, device_name="cpu", allow_synthetic=True)
    with pytest.raises(evaluate.TestGuardError, match="--reason"):
        evaluate.evaluate_run(
            run, "independent", data_cache="s2_cloud_catalogue", allow_synthetic=True
        )
    out = evaluate.evaluate_run(
        run,
        "independent",
        data_cache="s2_cloud_catalogue",
        reason="clean check of the frozen candidate",
        allow_synthetic=True,
        with_baselines=True,
    )
    report = json.loads(out.read_text())
    assert out.name == "tiny-seed0-x_independent_s2_cloud_catalogue.json"
    assert report["independent"]["dataset"] == "s2_cloud_catalogue"
    assert report["data"]["source"] == "s2_cloud_catalogue"
    assert report["model"]["shadow_on_marked_tiles"]["tiles"] == 4
    assert "always_send" in report["baselines"] and "threshold_rule" not in report["baselines"]
    log = (tiefer_env["TIEFER_REPORTS_DIR"] / "test_log.md").read_text()
    assert "independent dataset s2_cloud_catalogue" in log


def test_composed_bands_fill_and_substitute() -> None:
    base = np.arange(2 * 3 * 2 * 2, dtype=np.uint16).reshape(2, 3, 2, 2)
    view = cache.ComposedBands(base, ["B02", "B03", "B8A"], ["B02", "B08", "B05"], {"B08": "B8A"})
    out = view[1]
    np.testing.assert_array_equal(out[0], base[1, 0])
    np.testing.assert_array_equal(out[1], base[1, 2])
    assert not out[2].any() and view.shape == (2, 3, 2, 2)
    assert L1C_BAND_NAMES.index("B8A") == 8
