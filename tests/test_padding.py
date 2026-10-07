# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The padding of cached patches, and the read-only check of a cache, on synthetic data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tiefer_lab.data import build_cache, cache, padding

SIZE = 64
REAL = 61  # 3 padded rows and columns, as 509 in a 512 x 512 patch
PATCHES = 6


def padded_cache(sides: tuple[str, str] = ("left", "bottom"), label: int = 0) -> Path:
    """A synthetic val split whose patches are padded by 3 pixels on `sides`.

    The padded image pixels are zero in every band and the padded label
    pixels hold `label`; `real_proj_shape` is written into the metadata.
    """
    build_cache.main(
        ["--split", "val", "--synthetic", "--limit", str(PATCHES), "--patch-size", str(SIZE)]
    )
    directory = cache.cache_dir(build_cache.SYNTHETIC_NAME)
    images = np.load(cache.images_path(directory, "val"))
    labels = np.load(cache.labels_path(directory, "val"))
    images[images == 0] = 1  # no zero pixel outside the padding
    pad = padding.padding_of((SIZE, SIZE), (REAL, REAL), sides)
    invalid = np.zeros((SIZE, SIZE), dtype=bool)
    invalid[: pad.top] = invalid[SIZE - pad.bottom :] = True
    invalid[:, : pad.left] = invalid[:, SIZE - pad.right :] = True
    images[:, :, invalid] = 0
    labels[:, invalid] = label
    np.save(cache.images_path(directory, "val"), images)
    np.save(cache.labels_path(directory, "val"), labels)
    index = cache.read_index(directory)
    for m in index["splits"]["val"]["metadata"]:
        m["real_proj_shape"] = REAL
    cache.write_index(directory, index)
    return directory


def test_padding_follows_the_metadata_and_the_sides() -> None:
    assert padding.padding_of((512, 512), (509, 509)) == padding.Padding(bottom=3, left=3)
    assert padding.padding_of((512, 512), (509, 509), ("top", "right")) == padding.Padding(
        top=3, right=3
    )
    assert not padding.padding_of((512, 512), None)
    assert not padding.padding_of((509, 509), (509, 509))
    assert padding.Padding(bottom=3, left=3).pixels(512, 512) == 3_063
    with pytest.raises(ValueError, match="smaller"):
        padding.padding_of((500, 500), (509, 509))
    with pytest.raises(ValueError, match="no side"):
        padding.padding_of((512, 512), (509, 509), ("left",))
    with pytest.raises(ValueError, match="at most one"):
        padding.padding_of((512, 512), (509, 509), ("left", "right", "bottom"))
    assert padding.real_shape({"real_proj_shape": 509}) == (509, 509)
    assert padding.real_shape({"real_proj_shape": "509.0"}) == (509, 509)
    assert padding.real_shape({}) is None
    assert padding.real_shape({"real_proj_shape": "x"}) is None


def test_check_finds_the_padded_sides(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    padded_cache()
    capsys.readouterr()
    assert cache.main(["padding", build_cache.SYNTHETIC_NAME, "--split", "val"]) == 0
    out = capsys.readouterr().out
    shapes = f"stored images ({PATCHES}, 4, {SIZE}, {SIZE}), labels ({PATCHES}, {SIZE}, {SIZE})"
    assert shapes in out
    assert f"real_proj_shape: {REAL} x {REAL}: {PATCHES}" in out
    strip_pixels = PATCHES * 3 * SIZE
    assert f"| left | 3 | 0: {strip_pixels:,} | {PATCHES} of {PATCHES} |" in out
    assert f"| bottom | 3 | 0: {strip_pixels:,} | {PATCHES} of {PATCHES} |" in out
    assert "| right | 3 |" in out and "| top | 3 |" in out
    assert "zero sides found: left, bottom; this agrees with PADDING_SIDES" in out


def test_check_reports_padding_on_other_sides(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    padded_cache(("top", "right"), label=3)
    capsys.readouterr()
    code = cache.main(["padding", build_cache.SYNTHETIC_NAME, "--split", "val", "--patches", "2"])
    out = capsys.readouterr().out
    assert code == 1
    assert "patches read: 2" in out
    assert f"| top | 3 | 3: {2 * 3 * SIZE:,} | 2 of 2 |" in out
    assert "zero sides found: right, top; this differs from PADDING_SIDES" in out


def test_check_writes_nothing(tiefer_env: dict[str, Path]) -> None:
    directory = padded_cache()
    before = {p.name: p.stat().st_mtime_ns for p in directory.iterdir()}
    cache.main(["padding", build_cache.SYNTHETIC_NAME])
    assert {p.name: p.stat().st_mtime_ns for p in directory.iterdir()} == before


def test_without_real_size_there_is_no_padding(
    tiefer_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    build_cache.main(["--split", "val", "--synthetic", "--limit", "2", "--patch-size", "32"])
    assert cache.main(["padding", build_cache.SYNTHETIC_NAME]) in (0, 1)
    out = capsys.readouterr().out
    assert "real_proj_shape: not in the metadata: 2" in out


def test_sample_positions_spread_over_the_split() -> None:
    assert cache.sample_positions(10, 3) == [0, 4, 9]  # 4.5 rounds to the even 4
    assert cache.sample_positions(3, 50) == [0, 1, 2]
    assert cache.sample_positions(0, 5) == []


# Masking at load time ------------------------------------------------------


def _hand_example() -> tuple[np.ndarray, np.ndarray, padding.Padding]:
    """A 4 x 4 patch of a 3 x 3 image, padded by one column on the left and one row at the bottom.

    Real area (rows 0 to 2, columns 1 to 3), label and prediction:

        label   1 1 1     prediction  1 1 1
                1 1 0                 1 0 0
                0 0 0                 0 0 0

    The 7 padded pixels hold label 0 (clear) and are predicted clear.
    """
    pad = padding.padding_of((4, 4), (3, 3))
    assert pad == padding.Padding(bottom=1, left=1)
    label = np.zeros((4, 4), dtype=np.uint8)
    label[0:3, 1:4] = [[1, 1, 1], [1, 1, 0], [0, 0, 0]]
    prediction = np.zeros((4, 4), dtype=np.uint8)
    prediction[0:3, 1:4] = [[1, 1, 1], [1, 0, 0], [0, 0, 0]]
    return label, prediction, pad


def test_masking_changes_the_numbers_as_computed_by_hand() -> None:
    from tiefer_lab.config import EvaluationConfig
    from tiefer_lab.evaluate import Scores

    label, prediction, pad = _hand_example()
    settings = EvaluationConfig()

    old = Scores()
    old.add(prediction, label)
    old_report = old.report(settings, with_intervals=False)
    # Old: the padding counts as 7 correctly predicted clear pixels.
    # clear IoU 11 / 12, thick cloud IoU 4 / 5, overall accuracy 15 / 16.
    assert old_report["pixel"]["pixels"] == 16
    assert old_report["pixel"]["iou"][:2] == pytest.approx([11 / 12, 4 / 5])
    assert old_report["pixel"]["mean_iou"] == pytest.approx((11 / 12 + 4 / 5) / 2)
    assert old_report["pixel"]["overall_accuracy"] == pytest.approx(15 / 16)
    assert old.true_fraction == [pytest.approx(5 / 16)]
    assert old.pred_fraction == [pytest.approx(4 / 16)]

    new = Scores()
    new.add(prediction, padding.mask_label(label.copy(), pad))
    new_report = new.report(settings, with_intervals=False)
    # New: only the 9 real pixels. clear IoU 4 / 5, thick cloud IoU 4 / 5,
    # overall accuracy 8 / 9, cloud fractions 5 / 9 and 4 / 9.
    assert new_report["pixel"]["pixels"] == 9
    assert new_report["ignored_pixels"] == 7
    assert new_report["pixel"]["iou"][:2] == pytest.approx([4 / 5, 4 / 5])
    assert new_report["pixel"]["mean_iou"] == pytest.approx(4 / 5)
    assert new_report["pixel"]["overall_accuracy"] == pytest.approx(8 / 9)
    assert new.true_fraction == [pytest.approx(5 / 9)]
    assert new.pred_fraction == [pytest.approx(4 / 9)]


def test_reference_and_predicted_fractions_use_the_same_pixels() -> None:
    from tiefer_lab import decisions

    label, _, pad = _hand_example()
    masked = padding.mask_label(label.copy(), pad)
    # Cloud on every real pixel, clear on the padding.
    prediction = np.zeros((4, 4), dtype=np.uint8)
    prediction[0:3, 1:4] = 1
    fractions = decisions.frame_fractions(prediction, masked)
    assert fractions.pixels == 9 == int((masked != 255).sum())
    assert fractions.true_cloud == pytest.approx(5 / 9)
    assert fractions.predicted_cloud == pytest.approx(9 / 9)
    # Over the whole patch the prediction would read 9 / 16.
    assert decisions.cloud_fraction(prediction) == pytest.approx(9 / 16)
    assert decisions.cloud_fraction(masked) == pytest.approx(5 / 9)
    assert decisions.shadow_fraction(masked) == 0.0
    stack = np.stack([masked, np.full((4, 4), 255, np.uint8)])
    np.testing.assert_allclose(decisions.cloud_fractions(stack), [5 / 9, np.nan])


@pytest.mark.parametrize("mode", ["memory", "mmap"])
def test_load_split_masks_the_padding_and_the_confusion_matrix_counts_labelled_pixels(
    tiefer_env: dict[str, Path], mode: str
) -> None:
    from tiefer_lab.config import EvaluationConfig
    from tiefer_lab.evaluate import Scores

    directory = padded_cache()
    stored_labels = np.load(cache.labels_path(directory, "val"))
    data = cache.load_split(directory, "val", mode=mode)  # type: ignore[arg-type]
    assert data.in_memory == (mode == "memory")
    assert data.padding == [padding.Padding(bottom=3, left=3)] * PATCHES
    padded = PATCHES * (SIZE * SIZE - REAL * REAL)
    assert data.padded_pixels() == padded
    labels = np.asarray(data.labels)
    assert (labels[:, :, :3] == 255).all() and (labels[:, SIZE - 3 :, :] == 255).all()
    np.testing.assert_array_equal(labels[:, : SIZE - 3, 3:], stored_labels[:, : SIZE - 3, 3:])
    np.testing.assert_array_equal(np.asarray(data.labels[2]), labels[2])
    np.testing.assert_array_equal(np.asarray(data.labels[1:3]), labels[1:3])
    np.testing.assert_array_equal(data.labels[[0, 4], 0], labels[[0, 4], 0])
    # The file on disk and the images are not changed.
    np.testing.assert_array_equal(np.load(cache.labels_path(directory, "val")), stored_labels)
    assert not np.asarray(data.images)[:, :, :, :3].any()
    assert data.valid_area(0).sum() == REAL * REAL

    scores = Scores()
    for i in range(len(data)):
        scores.add(np.zeros((SIZE, SIZE), dtype=np.uint8), np.asarray(data.labels[i]))
    report = scores.report(EvaluationConfig(), with_intervals=False)
    assert report["pixel"]["pixels"] == PATCHES * REAL * REAL
    assert report["ignored_pixels"] == padded


def test_class_weights_leave_the_padding_out(tiefer_env: dict[str, Path]) -> None:
    from tiefer_lab.train import training_class_pixels

    directory = padded_cache()
    index = cache.read_index(directory)
    index["splits"]["train"] = index["splits"]["val"]
    data = cache.load_split(directory, "val")
    counted = training_class_pixels(data, index)
    assert sum(counted) == PATCHES * REAL * REAL
    labels = np.asarray(data.labels)
    assert counted == [int((labels == c).sum()) for c in range(4)]
    unpadded = cache.load_split(directory, "val")
    unpadded.padding = []
    assert training_class_pixels(unpadded, index) == index["splits"]["val"]["class_pixels"]


def test_threshold_rule_histogram_leaves_the_padding_out() -> None:
    from tiefer_lab import baselines

    label, _, pad = _hand_example()
    masked = padding.mask_label(label.copy(), pad)
    reflectance = np.full((4, 4, 4), 0.1, dtype=np.float32)
    histogram = baselines.RuleHistogram()
    histogram.add(reflectance, masked)
    assert int(histogram.counts.sum()) == 9
    assert histogram.counts.sum(axis=(1, 2)).tolist() == [4, 5, 0, 0]


def test_mask_labels_handles_mixed_paddings() -> None:
    labels = np.zeros((3, 4, 4), dtype=np.uint8)
    pads = [padding.Padding(left=1), padding.NO_PADDING, padding.Padding(top=2, right=1)]
    padding.mask_labels(labels, pads)
    assert (labels[0, :, 0] == 255).all() and (labels[0, :, 1:] == 0).all()
    assert (labels[1] == 0).all()
    assert (labels[2, :2] == 255).all() and (labels[2, :, 3] == 255).all()
    assert int((labels[2] == 255).sum()) == pads[2].pixels(4, 4) == 10
