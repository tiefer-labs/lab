# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Sensor robustness augmentations and fixed evaluation perturbations."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from tests.test_transforms import _aligned_split
from tiefer_lab.data import sensor, transforms
from tiefer_lab.data.dataset import DeviceTrainBatches


def _batches(robustness: sensor.Robustness, seed: int = 0) -> DeviceTrainBatches:
    return DeviceTrainBatches(
        _aligned_split(8, 64),
        np.zeros(4, np.float32),
        np.ones(4, np.float32),
        32,
        transforms.Photometric(0.0, 0.0),
        torch.device("cpu"),
        batch_size=4,
        seed=seed,
        robustness=robustness,
    )


def test_rescaled_batches_keep_the_crop_size_and_label_codes() -> None:
    r = sensor.Robustness(rescale_min=0.5, rescale_max=2.0)
    for image, label in _batches(r).epoch(0):
        assert image.shape == (4, 4, 32, 32) and label.shape == (4, 32, 32)
        assert set(label.unique().tolist()) <= {0, 1, 2, 3}
    a = [x for x, _ in _batches(r, 1).epoch(3)]
    b = [x for x, _ in _batches(r, 1).epoch(3)]
    for x, y in zip(a, b, strict=True):
        torch.testing.assert_close(x, y)


def test_switched_off_augmentations_change_nothing() -> None:
    plain = [x for x, _ in _batches(sensor.Robustness()).epoch(2)]
    default = [x for x, _ in _batches(sensor.Robustness(1.0, 1.0, 0.0, 0.0, 0.0, 0.0)).epoch(2)]
    for x, y in zip(plain, default, strict=True):
        torch.testing.assert_close(x, y)


def test_gain_offset_noise_blur_stay_in_range() -> None:
    g = torch.Generator().manual_seed(0)
    image = torch.full((2, 3, 16, 16), 0.3)
    r = sensor.Robustness(gain_jitter=0.2, offset_jitter=0.05, noise_std=0.02, blur_sigma=1.0)
    out = sensor.augment(image, r, g)
    assert out.shape == image.shape and float(out.min()) >= 0
    assert float(out.max()) <= transforms.MAX_REFLECTANCE
    assert not torch.equal(out, image)


def test_blur_keeps_constant_images_and_spreads_an_edge() -> None:
    flat = torch.full((1, 2, 9, 9), 0.4)
    torch.testing.assert_close(sensor.gaussian_blur(flat, 1.5), flat)
    edge = torch.zeros(1, 1, 9, 9)
    edge[..., 5:] = 1.0
    blurred = sensor.gaussian_blur(edge, 1.0)
    assert 0 < float(blurred[0, 0, 4, 4]) < 1 and float(blurred.sum()) == pytest.approx(
        36.0, rel=1e-4
    )


def test_perturbations_parse_and_apply() -> None:
    image = torch.rand(4, 20, 20) * 0.5
    label = torch.randint(0, 4, (20, 20))
    half = sensor.Perturbation.parse("rescale=0.5")
    x, y = half.apply(image, label, seed=0)
    assert x.shape == (4, 10, 10) and y.shape == (10, 10)
    assert set(y.unique().tolist()) <= set(label.unique().tolist())
    noise = sensor.Perturbation.parse("noise=0.01")
    torch.testing.assert_close(noise.apply(image, label, 3)[0], noise.apply(image, label, 3)[0])
    gain = sensor.Perturbation.parse("gain=1.1")
    expected = (image * 1.1).clamp(0, transforms.MAX_REFLECTANCE)
    torch.testing.assert_close(gain.apply(image, label, 0)[0], expected)
    assert gain.name == "gain=1.1"
    for bad in ("zoom=2", "rescale=", "rescale=9", "noise=-1"):
        with pytest.raises(ValueError):
            sensor.Perturbation.parse(bad)
