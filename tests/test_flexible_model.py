# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Band-flexible models, the ConvNeXt-style U-Net and the loss terms."""

from __future__ import annotations

import pytest
import torch
import torch.nn.functional as F  # noqa: N812

from tiefer_lab.config import ConfigError, config_from_dict
from tiefer_lab.data.source import IGNORE_INDEX, L1C_BAND_NAMES, USED_BANDS
from tiefer_lab.models import flexible
from tiefer_lab.models.cloud_filter import count_macs, count_parameters
from tiefer_lab.models.convnext_unet import ConvNeXtUNet
from tiefer_lab.models.losses import CrossEntropyDice, distillation

FLEX = {
    "name": "flex",
    "data": {"bands": list(L1C_BAND_NAMES)},
    "model": {"widths": [8, 16], "input": "flexible"},
    "train": {"band_sets": [["B02", "B03", "B04"], list(L1C_BAND_NAMES)]},
}


@pytest.mark.parametrize("design", flexible.DESIGNS)
def test_unavailable_bands_never_change_the_output(design: str) -> None:
    torch.manual_seed(0)
    raw = {**FLEX, "model": {**FLEX["model"], "flexible_design": design}}
    config = config_from_dict(raw)
    model = flexible.build(config.model, config.data.bands).eval()
    x = torch.randn(2, 13, 32, 32)
    model.set_band_set(USED_BANDS)
    y = x.clone()
    missing = [i for i, b in enumerate(L1C_BAND_NAMES) if b not in USED_BANDS]
    y[:, missing] = torch.randn(2, len(missing), 32, 32) * 100
    with torch.no_grad():
        torch.testing.assert_close(model(x), model(y))
        # The same values with all bands available give another answer.
        model.set_band_set(L1C_BAND_NAMES)
        assert not torch.allclose(model(x), model(y))


def test_flags_separate_a_missing_band_from_a_dark_pixel() -> None:
    layer = flexible.BandInput(3, "zero")
    x = torch.zeros(1, 3, 2, 2)  # band 0 is truly zero (dark) in both cases
    present = layer(x, torch.tensor([[1.0, 1.0, 1.0]]))
    absent = layer(x, torch.tensor([[0.0, 1.0, 1.0]]))
    torch.testing.assert_close(present[:, :3], absent[:, :3])
    assert not torch.equal(present[:, 3:], absent[:, 3:])


def test_availability_and_the_default_band_set() -> None:
    assert flexible.availability(["B02", "B12"]).tolist() == [
        1.0 if b in ("B02", "B12") else 0.0 for b in L1C_BAND_NAMES
    ]
    with pytest.raises(ValueError, match="unknown bands"):
        flexible.availability(["B13"])


def test_convnext_unet_shapes_and_operations() -> None:
    model = ConvNeXtUNet((8, 16, 32), in_channels=4)
    out = model(torch.randn(1, 4, 64, 64))
    assert out.shape == (1, 4, 64, 64)
    assert count_parameters(model) > 0 and count_macs(model) > 0
    assert model.downsampling == 4


def test_flexible_configs_are_checked() -> None:
    config_from_dict(FLEX)
    with pytest.raises(ConfigError, match="all 13 bands"):
        config_from_dict({**FLEX, "data": {"bands": list(USED_BANDS)}})
    with pytest.raises(ConfigError, match=r"needs train\.band_sets"):
        config_from_dict({**FLEX, "train": {}})
    with pytest.raises(ConfigError, match="band_sets need"):
        config_from_dict({"name": "x", "train": {"band_sets": [["B02"]]}})
    with pytest.raises(ConfigError, match="bands must be among"):
        config_from_dict({"name": "x", "data": {"bands": ["B02", "B99"]}})


def test_ignored_pixels_add_nothing_to_the_loss() -> None:
    torch.manual_seed(1)
    logits = torch.randn(1, 4, 4, 4, requires_grad=True)
    target = torch.randint(0, 4, (1, 4, 4))
    partial = target.clone()
    partial[:, :, 2:] = IGNORE_INDEX
    loss_fn = CrossEntropyDice(None, dice_weight=1.0)
    full_left = loss_fn(logits[..., :2], target[..., :2])
    torch.testing.assert_close(loss_fn(logits, partial), full_left)
    nothing = loss_fn(logits, torch.full_like(target, IGNORE_INDEX))
    assert float(nothing.detach()) == 0.0
    nothing.backward()  # the graph stays usable


def test_focal_term() -> None:
    torch.manual_seed(2)
    logits = torch.randn(2, 4, 3, 3)
    target = torch.randint(0, 4, (2, 3, 3))
    plain = CrossEntropyDice(None, dice_weight=0.0)
    torch.testing.assert_close(plain(logits, target), F.cross_entropy(logits, target))
    focal = CrossEntropyDice(None, dice_weight=0.0, focal_gamma=2.0)
    assert float(focal(logits, target)) < float(plain(logits, target))
    weights = torch.tensor([1.0, 2.0, 3.0, 4.0])
    weighted = CrossEntropyDice(weights, dice_weight=0.0, focal_gamma=0.0)
    torch.testing.assert_close(
        weighted(logits, target), F.cross_entropy(logits, target, weight=weights)
    )


def test_distillation_is_zero_for_equal_predictions() -> None:
    torch.manual_seed(3)
    teacher = torch.randn(2, 4, 5, 5)
    assert float(distillation(teacher.clone(), teacher)) == pytest.approx(0.0, abs=1e-6)
    student = torch.randn(2, 4, 5, 5, requires_grad=True)
    loss = distillation(student, teacher)
    assert float(loss.detach()) > 0
    loss.backward()
    assert student.grad is not None


@pytest.mark.parametrize("design", flexible.DESIGNS)
def test_band_set_model_matches_the_flexible_model(design: str) -> None:
    torch.manual_seed(4)
    raw = {**FLEX, "model": {**FLEX["model"], "flexible_design": design}}
    config = config_from_dict(raw)
    model = flexible.build(config.model, config.data.bands).eval()
    assert isinstance(model, flexible.FlexibleModel)
    if model.band_input.placeholder is not None:
        with torch.no_grad():
            model.band_input.placeholder.uniform_(-1, 1)
    bands = ["B04", "B03", "B02", "B11"]
    fixed = flexible.BandSetModel(model, bands).eval()
    x = torch.randn(2, 13, 32, 32)
    positions = [L1C_BAND_NAMES.index(b) for b in bands]
    model.set_band_set(bands)
    with torch.no_grad():
        torch.testing.assert_close(fixed(x[:, positions]), model(x))
    assert fixed.input_bands == 4
