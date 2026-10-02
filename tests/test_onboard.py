# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The on-board decision: tiled inference and fail-safe behaviour.

No invalid, missing, saturated or out-of-domain input and no error may end
in a discarded frame ("keep"): such frames are sent and flagged. Random bit
flips in the model file are caught by the hash check before inference.
Radiation effects during inference are not tested here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from tiefer_lab import onboard
from tiefer_lab.data.source import THICK_CLOUD


def _pixel_model() -> nn.Module:
    """A 1 x 1 convolution: thick cloud where band 0 is bright, clear elsewhere."""
    conv = nn.Conv2d(2, 4, 1)
    with torch.no_grad():
        conv.weight.zero_()
        conv.bias.zero_()
        conv.weight[THICK_CLOUD, 0] = 10.0
        conv.bias[THICK_CLOUD] = -5.0
    return conv


ZERO, ONE = np.zeros(2, np.float32), np.ones(2, np.float32)


def _frame(size: int = 300, cloudy: float = 0.75) -> np.ndarray:
    """Digital numbers (scale 0.0001): band 0 at 0.8 reflectance on the cloudy left part."""
    frame = np.full((2, size, size), 1000, np.uint16)
    frame[0, :, : int(size * cloudy)] = 8000
    return frame


def test_tiles_give_the_same_mask_as_the_whole_frame() -> None:
    refl = _frame(700).astype(np.float32) * 1e-4
    model = _pixel_model()
    tiled = onboard.predict_frame(model, refl, ZERO, ONE, 10.0, tile=256, overlap=32)
    with torch.no_grad():
        whole = model(torch.from_numpy(refl)[None]).argmax(1)[0].numpy().astype(np.uint8)
    np.testing.assert_array_equal(tiled, whole)


def test_a_finer_frame_is_resampled_and_its_mask_has_the_frame_size() -> None:
    refl = _frame(400).astype(np.float32) * 1e-4
    mask = onboard.predict_frame(_pixel_model(), refl, ZERO, ONE, gsd_m=2.5, tile=64, overlap=8)
    assert mask.shape == (400, 400)
    assert abs(float((mask == THICK_CLOUD).mean()) - 0.75) < 0.02


def _filter(**kwargs: object) -> onboard.OnboardFilter:
    return onboard.OnboardFilter(
        _pixel_model(), ZERO, ONE, onboard.Domain(bands=2), tile=128, overlap=16, **kwargs
    )  # type: ignore[arg-type]


def test_valid_frames_are_decided_by_their_cloud_fraction() -> None:
    cloudy = _filter().process(_frame(cloudy=0.75))
    assert cloudy.decision == "keep" and cloudy.status == "ok" and not cloudy.flags
    assert cloudy.cloud_fraction == pytest.approx(0.75, abs=0.01)
    assert _filter().process(_frame(cloudy=0.1)).decision == "send"


def _bad_frames() -> dict[str, np.ndarray]:
    frame = _frame()
    nan = frame.astype(np.float32)
    nan[0, 0, 0] = np.nan
    saturated = frame.copy()
    saturated[:, :100] = 65535
    empty = frame.copy()
    empty[:, :50] = 0
    out_of_range = frame.copy()
    out_of_range[0, :60] = 30000  # reflectance 3.0
    return {
        "three bands": np.concatenate([frame, frame[:1]]),
        "one band": frame[:1],
        "non-finite": nan,
        "saturated": saturated,
        "empty": empty,
        "out of range": out_of_range,
        "too small": frame[:, :10, :10],
    }


@pytest.mark.parametrize("name", list(_bad_frames()))
def test_invalid_input_is_sent_and_flagged_never_kept(name: str) -> None:
    result = _filter().process(_bad_frames()[name])
    assert result.decision == "send" and result.status == "outside_domain" and result.flags


def test_a_resolution_outside_the_domain_is_sent_and_flagged() -> None:
    result = _filter().process(_frame(), gsd_m=60.0)
    assert result.decision == "send" and "ground sampling distance" in result.flags[0]


def test_an_error_during_inference_is_sent_and_flagged() -> None:
    class Broken(nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            raise RuntimeError("device lost")

    f = onboard.OnboardFilter(Broken(), ZERO, ONE, onboard.Domain(bands=2))
    result = f.process(_frame())
    assert (
        result.decision == "send" and result.status == "error" and "device lost" in result.flags[0]
    )


def test_corrupted_model_files_stop_inference(tmp_path: Path) -> None:
    path = tmp_path / "model.pt"
    torch.save(_pixel_model().state_dict(), path)
    expected = onboard.sha256_file(path)
    assert _filter(model_path=path, expected_sha256=expected).process(_frame()).status == "ok"
    rng = np.random.default_rng(0)
    data = bytearray(path.read_bytes())
    for _ in range(20):  # 20 single random bit flips, each in a fresh copy
        flipped = bytearray(data)
        position = int(rng.integers(len(flipped)))
        flipped[position] ^= 1 << int(rng.integers(8))
        bad = tmp_path / "flipped.pt"
        bad.write_bytes(bytes(flipped))
        f = _filter(model_path=bad, expected_sha256=expected)
        result = f.process(_frame(cloudy=0.9))
        assert f.status == "model_hash_mismatch"
        assert result.decision == "send" and "differs from the expected" in result.flags[0]
    with pytest.raises(onboard.ModelIntegrityError):
        onboard.verify_model_file(tmp_path / "flipped.pt", expected)
    missing = _filter(model_path=tmp_path / "missing.pt", expected_sha256=expected)
    assert missing.process(_frame()).decision == "send"


def test_failsafe_check_counts_no_discarded_frame() -> None:
    out = onboard.failsafe_check()
    assert out["cases"] == 9 and out["discarded"] == 0
    # The control shows the check would see a discard: a valid cloudy frame is kept.
    assert out["control_valid_cloudy_frame"] == "keep"
