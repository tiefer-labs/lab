# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import numpy as np
import pytest

from tiefer_lab.data import transforms as tf


def test_reflectance_uses_scale_and_offset() -> None:
    dn = np.array([[[0, 1000, 10000]]], dtype=np.uint16)
    refl = tf.to_reflectance(dn, scale=1e-4, offset=0.0)
    np.testing.assert_allclose(refl, [[[0.0, 0.1, 1.0]]], rtol=1e-6)
    shifted = tf.to_reflectance(dn, scale=1e-4, offset=-0.1)
    np.testing.assert_allclose(shifted, [[[-0.1, 0.0, 0.9]]], rtol=1e-5, atol=1e-7)
    assert refl.dtype == np.float32


def test_band_statistics_match_numpy_and_normalise_standardises() -> None:
    rng = np.random.default_rng(1)
    images = rng.integers(0, 6000, size=(7, 4, 9, 11), dtype=np.uint16)
    mean, std = tf.band_statistics(images, chunk=3)
    refl = tf.to_reflectance(images).astype(np.float64)
    np.testing.assert_allclose(mean, refl.mean(axis=(0, 2, 3)), rtol=1e-9)
    np.testing.assert_allclose(std, refl.std(axis=(0, 2, 3)), rtol=1e-6)
    normed = np.stack([tf.normalise(tf.to_reflectance(img), mean, std) for img in images])
    np.testing.assert_allclose(normed.mean(axis=(0, 2, 3)), 0.0, atol=1e-5)
    np.testing.assert_allclose(normed.std(axis=(0, 2, 3)), 1.0, atol=1e-4)


def test_band_statistics_rejects_constant_band() -> None:
    images = np.ones((2, 4, 3, 3), dtype=np.uint16)
    with pytest.raises(ValueError, match="zero variance"):
        tf.band_statistics(images)


def _aligned_pair(h: int = 12, w: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """An image whose band 0 equals the label, so alignment can be checked."""
    label = (np.arange(h * w).reshape(h, w) % 4).astype(np.uint8)
    image = np.stack([label.astype(np.float32)] * 4) + np.arange(4, dtype=np.float32)[:, None, None]
    return image, label


def test_crop_and_geometry_keep_image_and_label_aligned() -> None:
    rng = np.random.default_rng(0)
    for _ in range(20):
        image, label = _aligned_pair()
        image, label = tf.random_crop(image, label, 6, rng)
        assert image.shape == (4, 6, 6) and label.shape == (6, 6)
        image, label = tf.random_flip_rotate(image, label, rng)
        np.testing.assert_array_equal(image[0], label.astype(np.float32))
        np.testing.assert_array_equal(image[3], label.astype(np.float32) + 3)


def test_crop_returns_full_patch_when_smaller_than_crop() -> None:
    image, label = _aligned_pair(5, 5)
    out_image, out_label = tf.random_crop(image, label, 8, np.random.default_rng(0))
    assert out_image.shape == (4, 5, 5) and out_label.shape == (5, 5)


def test_brightness_contrast_stays_in_plausible_range() -> None:
    rng = np.random.default_rng(3)
    refl = rng.uniform(0.0, 1.2, size=(4, 16, 16)).astype(np.float32)
    change = tf.Photometric(brightness=0.1, contrast=0.1)
    for _ in range(50):
        out = tf.brightness_contrast(refl, rng, change)
        assert out.min() >= 0.0 and out.max() <= tf.MAX_REFLECTANCE
        ratio = out.mean() / refl.mean()
        assert 0.85 <= ratio <= 1.15
    with pytest.raises(ValueError):
        tf.Photometric(brightness=0.6)


def test_reflect_padding_to_multiple_of_32_and_crop_back() -> None:
    rng = np.random.default_rng(5)
    image = rng.normal(size=(4, 509, 500)).astype(np.float32)
    padded, size = tf.pad_to_multiple(image, 32)
    assert padded.shape == (4, 512, 512)
    assert size == (509, 500)
    # Reflect padding mirrors the rows next to the edge, without repeating it.
    np.testing.assert_array_equal(padded[:, 509, :500], image[:, 507, :])
    np.testing.assert_array_equal(tf.crop_back(padded, size), image)


def test_pad_to_shape_rejects_larger_image() -> None:
    with pytest.raises(ValueError):
        tf.pad_to_shape(np.zeros((4, 600, 600), dtype=np.float32), (512, 512))


def test_datasets_return_normalised_crops_and_padded_patches(tiefer_env: dict) -> None:
    import torch

    from tiefer_lab.data import build_cache, cache
    from tiefer_lab.data.dataset import EvalPatches, TrainPatches

    build_cache.main(["--split", "all", "--synthetic", "--limit", "4", "--patch-size", "40"])
    directory = cache.cache_dir(build_cache.SYNTHETIC_NAME)
    mean, std = cache.normalisation(cache.read_index(directory))
    train = TrainPatches(cache.load_split(directory, "train"), mean, std, 32, tf.Photometric())
    torch.manual_seed(0)
    image, label = train[0]
    assert image.shape == (4, 32, 32) and image.dtype == torch.float32
    assert label.shape == (32, 32) and label.dtype == torch.int64
    evaluation = EvalPatches(cache.load_split(directory, "val"), mean, std, multiple=32)
    image, label, index = evaluation[1]
    assert image.shape == (4, 64, 64) and label.shape == (40, 40) and index == 1


def _aligned_split(n: int = 6, size: int = 40):  # type: ignore[no-untyped-def]
    """Synthetic split whose every band holds 1000 x (label + 1), so alignment can be checked."""
    from tiefer_lab.data.cache import SplitData

    rng = np.random.default_rng(0)
    labels = rng.integers(0, 4, size=(n, size, size)).astype(np.uint8)
    images = np.repeat(((labels.astype(np.uint16) + 1) * 1000)[:, None], 4, axis=1)
    return SplitData("train", images, labels, [str(i) for i in range(n)], [], in_memory=True)


def test_device_batches_keep_labels_aligned_and_values_exact() -> None:
    import torch

    from tiefer_lab.data.dataset import DeviceTrainBatches

    batches = DeviceTrainBatches(
        _aligned_split(),
        np.zeros(4, np.float32),
        np.ones(4, np.float32),
        crop_size=32,
        photometric=tf.Photometric(brightness=0.0, contrast=0.0),
        device=torch.device("cpu"),
        batch_size=4,
        seed=0,
    )
    assert batches.placement == "cpu" and len(batches) == 1
    for epoch in range(5):
        for image, label in batches.epoch(epoch):
            assert image.shape == (4, 4, 32, 32) and label.shape == (4, 32, 32)
            assert label.dtype == torch.int64
            expected = 0.1 * (label.to(torch.float32) + 1)
            for band in range(4):
                torch.testing.assert_close(image[:, band], expected)


def test_device_batches_repeat_per_epoch_and_stay_in_range() -> None:
    import torch

    from tiefer_lab.data.dataset import DeviceTrainBatches

    def make() -> DeviceTrainBatches:
        return DeviceTrainBatches(
            _aligned_split(8),
            np.zeros(4, np.float32),
            np.ones(4, np.float32),
            32,
            tf.Photometric(0.1, 0.1),
            torch.device("cpu"),
            batch_size=4,
            seed=3,
        )

    a = [img for img, _ in make().epoch(2)]
    b = [img for img, _ in make().epoch(2)]
    c = [img for img, _ in make().epoch(3)]
    assert len(a) == 2
    for x, y in zip(a, b, strict=True):
        torch.testing.assert_close(x, y)
    assert not torch.equal(a[0], c[0])
    assert float(min(x.min() for x in a)) >= 0.0
    assert float(max(x.max() for x in a)) <= tf.MAX_REFLECTANCE
