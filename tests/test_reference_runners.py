# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Reference runners and the logged path of run_reference.py for independent caches."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from tiefer_lab.data import build_cache, cache

# The Keras layers of the CD-FCNN network with their weights, in the order and with
# the shapes of the repository's own model.py (four bands), as TensorFlow lists them.
KERAS_LAYERS: list[tuple[str, str, list[tuple[int, ...]]]] = [
    ("Conv2D", "normalization", [(1, 1, 4, 4), (4,)]),
    ("SeparableConv2D", "input_conv_1", [(3, 3, 4, 1), (1, 1, 4, 32), (32,)]),
    ("BatchNormalization", "input_bn_1", [(32,)] * 4),
    ("SeparableConv2D", "input_conv_2", [(3, 3, 32, 1), (1, 1, 32, 32), (32,)]),
    ("BatchNormalization", "input_bn_2", [(32,)] * 4),
    ("SeparableConv2D", "pool1_conv_1", [(3, 3, 32, 1), (1, 1, 32, 64), (64,)]),
    ("BatchNormalization", "pool1_bn_1", [(64,)] * 4),
    ("SeparableConv2D", "pool1_conv_2", [(3, 3, 64, 1), (1, 1, 64, 64), (64,)]),
    ("BatchNormalization", "pool1_bn_2", [(64,)] * 4),
    ("SeparableConv2D", "pool2_conv_1", [(3, 3, 64, 1), (1, 1, 64, 128), (128,)]),
    ("BatchNormalization", "pool2_bn_1", [(128,)] * 4),
    ("SeparableConv2D", "pool2_conv_2", [(3, 3, 128, 1), (1, 1, 128, 128), (128,)]),
    ("BatchNormalization", "pool2_bn_2", [(128,)] * 4),
    ("Conv2DTranspose", "upconv1", [(2, 2, 64, 128), (64,)]),
    ("SeparableConv2D", "up1_conv_1", [(3, 3, 128, 1), (1, 1, 128, 64), (64,)]),
    ("BatchNormalization", "up1_bn_1", [(64,)] * 4),
    ("SeparableConv2D", "up1_conv_2", [(3, 3, 64, 1), (1, 1, 64, 64), (64,)]),
    ("BatchNormalization", "up1_bn_2", [(64,)] * 4),
    ("Conv2DTranspose", "upconv2", [(2, 2, 32, 64), (32,)]),
    ("SeparableConv2D", "up2_conv_1", [(3, 3, 64, 1), (1, 1, 64, 32), (32,)]),
    ("BatchNormalization", "up2_bn_1", [(32,)] * 4),
    ("SeparableConv2D", "up2_conv_2", [(3, 3, 32, 1), (1, 1, 32, 32), (32,)]),
    ("BatchNormalization", "up2_bn_2", [(32,)] * 4),
    ("Conv2D", "linear_model", [(1, 1, 32, 1), (1,)]),
]
NAMES = {
    "SeparableConv2D": ["depthwise_kernel", "pointwise_kernel", "bias"],
    "BatchNormalization": ["gamma", "beta", "moving_mean", "moving_variance"],
    "Conv2D": ["kernel", "bias"],
    "Conv2DTranspose": ["kernel", "bias"],
}


def _module(repo_root: Path, name: str) -> ModuleType:
    sys.path.insert(0, str(repo_root / "references"))
    spec = importlib.util.spec_from_file_location(name, repo_root / "references" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _seeded_weights() -> tuple[dict[str, np.ndarray], np.ndarray]:
    """The weights and input the fixture was made with in TensorFlow (seed 20261017)."""
    rng = np.random.default_rng(20261017)
    weights = {}
    for kind, layer, shapes in KERAS_LAYERS:
        for weight, shape in zip(NAMES[kind], shapes, strict=True):
            value = rng.standard_normal(shape).astype(np.float32) * 0.2
            if weight == "moving_variance":
                value = np.abs(value) + 0.5
            if weight == "gamma":
                value = 1.0 + value
            weights[f"{layer}/{weight}"] = value
    image = rng.uniform(0, 1, size=(32, 32, 4)).astype(np.float32)
    return weights, image


def test_cd_fcnn_matches_tensorflow_for_the_same_weights(repo_root: Path) -> None:
    cd_fcnn = _module(repo_root, "cd_fcnn")
    weights, image = _seeded_weights()
    model = cd_fcnn.load(cd_fcnn.CDFCNN(4), weights)
    ours = cd_fcnn.probability(model, image.transpose(2, 0, 1))
    # TensorFlow 2.21 with model.py of IPL-UV/DL-L8S2-UV, 17 October 2026.
    expected = np.load(repo_root / "tests" / "fixtures" / "cd_fcnn_keras_output.npz")["output"]
    assert np.abs(ours - expected).max() < 1e-5
    assert expected.min() > 0.2 and expected.max() < 0.8
    assert ((ours >= 0.5) == (expected >= 0.5)).all()


def test_cd_fcnn_pads_like_the_published_tool_and_uses_every_weight(repo_root: Path) -> None:
    cd_fcnn = _module(repo_root, "cd_fcnn")
    assert cd_fcnn._pad(509) == (1, 2) and cd_fcnn._pad(512) == (0, 0)
    weights, _ = _seeded_weights()
    model = cd_fcnn.load(cd_fcnn.CDFCNN(4), weights)
    numbers = np.full((4, 509, 509), 1200, np.uint16)
    mask = cd_fcnn.cloud_mask(model, numbers)
    assert mask.shape == (509, 509) and mask.dtype == np.uint8 and set(np.unique(mask)) <= {0, 1}
    with pytest.raises(ValueError, match="not used"):
        cd_fcnn.load(cd_fcnn.CDFCNN(4), {**weights, "extra/kernel": np.zeros(1, np.float32)})
    assert cd_fcnn.BANDS["cd_fcnn_rgbiswir"] == ("B02", "B03", "B04", "B08", "B11", "B12")


def test_cd_fcnn_runs_at_the_published_30m_and_returns_the_10m_grid(
    repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cd_fcnn = _module(repo_root, "cd_fcnn")
    # A constant band stays constant through the cubic spline; 37 x 40 is
    # padded to 39 x 42 and becomes 13 x 14 at 30 m.
    numbers = np.full((2, 37, 40), 1234, np.uint16)
    coarse = cd_fcnn.resample_30m(numbers)
    assert coarse.shape == (2, 13, 14) and coarse.dtype == np.uint16
    assert (coarse == 1234).all()
    seen: list[tuple[int, ...]] = []

    def probability(_model: object, reflectance: np.ndarray) -> np.ndarray:
        seen.append(reflectance.shape)
        out = np.zeros(reflectance.shape[1:], np.float32)
        out[0, 0] = 0.5  # cloud at the threshold
        return out

    monkeypatch.setattr(cd_fcnn, "probability", probability)
    at_30m = cd_fcnn.cloud_mask(None, numbers)
    assert seen[-1] == (2, 13, 14) and at_30m.shape == (37, 40)
    # The one cloudy 30 m pixel covers 3 x 3 pixels of the 10 m grid.
    assert at_30m[:3, :3].all() and at_30m.sum() == 9
    at_10m = cd_fcnn.cloud_mask(None, numbers, 10)
    assert seen[-1] == (2, 37, 40) and at_10m.sum() == 1
    with pytest.raises(ValueError, match="10 or 30"):
        cd_fcnn.cloud_mask(None, numbers, 20)


def test_s2cloudless_reads_reflectance_in_its_layout(
    repo_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runners = _module(repo_root, "runners")
    seen: list[np.ndarray] = []

    class Detector:
        def get_cloud_masks(self, data: np.ndarray) -> np.ndarray:
            seen.append(data)
            return (data[..., 0] > 0.5).astype(np.uint8)

    monkeypatch.setitem(sys.modules, "s2cloudless", SimpleNamespace(S2PixelCloudDetector=Detector))
    monkeypatch.setattr(runners, "PACKAGES", tmp_path)
    images = np.full((2, 10, 4, 4), 1000, np.uint16)
    images[1, 0] = 9000
    masks = runners.s2cloudless_masks(_Split(images))
    assert seen[0].shape == (1, 4, 4, 10) and np.isclose(seen[0].max(), 0.1)
    assert masks[0].sum() == 0 and masks[1].all()
    missing = tmp_path / "absent"
    monkeypatch.setattr(runners, "PACKAGES", missing)
    with pytest.raises(runners.RunnerError, match="install the pinned packages"):
        runners.s2cloudless_masks(_Split(images))


class _Split:
    def __init__(self, images: np.ndarray) -> None:
        self.images = images
        self.labels = np.zeros((images.shape[0], *images.shape[2:]), np.uint8)

    def __len__(self) -> int:
        return int(self.images.shape[0])


def test_weights_are_checked_against_their_record(
    repo_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runners = _module(repo_root, "runners")
    monkeypatch.setattr(runners, "WEIGHTS", tmp_path)
    record = runners.REFERENCES["cd_fcnn_rgbi"].files[0]
    (tmp_path / record.name).write_bytes(b"0" * record.size)
    assert runners.weights_file("cd_fcnn_rgbi") == tmp_path / record.name
    (tmp_path / record.name).write_bytes(b"0" * 10)
    with pytest.raises(runners.RunnerError, match="the record says"):
        runners.weights_file("cd_fcnn_rgbi")


def _independent_cache(dataset: str) -> None:
    build_cache.main(["--split", "all", "--synthetic", "--limit", "3", "--patch-size", "32"])
    directory = cache.cache_dir("synthetic")
    index = cache.read_index(directory)
    index["source"] = dataset
    index["independent"] = {"dataset": dataset, "sensor": "Sentinel-2 MSI"}
    cache.write_index(directory, index)


def test_an_independent_cache_is_run_and_logged(
    repo_root: Path, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    ref = _module(repo_root, "run_reference")
    _independent_cache("kappaset")
    stub = ref.Runner(("B02", "B08"), lambda data: np.ones(data.labels.shape, np.uint8))
    monkeypatch.setattr(ref, "runners", lambda: {"s2cloudless": stub})
    with pytest.raises(ref.TestGuardError, match="--data needs --reason"):
        ref.run_independent("s2cloudless", "synthetic", "")
    assert ref.main(["--model", "s2cloudless", "--data", "synthetic", "--reason", "clean"]) == 0
    data = cache.load_independent(cache.cache_dir("synthetic"), ["B02"])
    assert data.reference_kinds == {"s2cloudless": "cloud"}
    assert data.reference["s2cloudless"].all()
    log = (tiefer_env["TIEFER_REPORTS_DIR"] / "test_log.md").read_text()
    assert "run `reference-s2cloudless`" in log and "independent dataset kappaset: clean" in log
    # The --cache path refuses an independent cache, and --data a split or --final.
    with pytest.raises(ref.ReferenceError, match="use --data"):
        ref.run("s2cloudless", "synthetic", "val")
    with pytest.raises(SystemExit):
        ref.main(["--model", "s2cloudless", "--data", "synthetic", "--split", "test"])


def test_a_cloudsen12_cache_is_never_read_as_independent(
    repo_root: Path, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    ref = _module(repo_root, "run_reference")
    build_cache.main(["--split", "all", "--synthetic", "--limit", "3", "--patch-size", "32"])
    stub = ref.Runner(("B02",), lambda data: np.ones(data.labels.shape, np.uint8))
    monkeypatch.setattr(ref, "runners", lambda: {"s2cloudless": stub})
    with pytest.raises(ref.ReferenceError, match="not an independent dataset cache"):
        ref.run_independent("s2cloudless", "synthetic", "a reason")
    # Its test split stays behind --final, as before.
    assert ref.main(["--model", "s2cloudless", "--cache", "synthetic", "--split", "test"]) == 2
    assert not (tiefer_env["TIEFER_REPORTS_DIR"] / "test_log.md").exists()


def test_the_10m_run_is_stored_under_its_own_label(
    repo_root: Path, tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    ref = _module(repo_root, "run_reference")
    _independent_cache("kappaset")
    stub = ref.Runner(
        ("B02",),
        lambda data: np.ones(data.labels.shape, np.uint8),
        {"10m": lambda data: np.zeros(data.labels.shape, np.uint8)},
    )
    monkeypatch.setattr(ref, "runners", lambda: {"cd_fcnn_rgbi": stub})
    added = ref.run_independent("cd_fcnn_rgbi", "synthetic", "clean")
    assert added == ["cd_fcnn_rgbi", "cd_fcnn_rgbi_10m"]
    data = cache.load_independent(cache.cache_dir("synthetic"), ["B02"])
    assert data.reference_kinds == {"cd_fcnn_rgbi": "cloud", "cd_fcnn_rgbi_10m": "cloud"}
    assert data.reference["cd_fcnn_rgbi"].all() and not data.reference["cd_fcnn_rgbi_10m"].any()
    runners = _module(repo_root, "runners")
    assert set(runners.cd_fcnn_runner("cd_fcnn_rgbiswir").labelled) == {"10m"}
