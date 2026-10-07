# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Check an ONNX model against PyTorch on validation patches.

Reports the maximum absolute logit difference and the share of pixels with
the same predicted class. Fails loudly when the agreement is below the
configured minimum (99.9 percent by default) or the difference above the
configured maximum. Only the real image area of each patch is compared: the
dataset's padding of a cached patch (data/padding.py) is left out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import torch
from numpy.typing import NDArray

from tiefer_lab.data import cache
from tiefer_lab.data.dataset import normalised_patch
from tiefer_lab.data.transforms import crop_back, pad_to_shape
from tiefer_lab.export.onnx_export import INPUT_NAME


class VerificationError(RuntimeError):
    """The ONNX model does not reproduce the PyTorch model."""


@dataclass(frozen=True)
class Agreement:
    max_abs_logit_difference: float
    argmax_agreement: float
    pixels: int
    patches: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_abs_logit_difference": self.max_abs_logit_difference,
            "argmax_agreement": self.argmax_agreement,
            "pixels": self.pixels,
            "patches": self.patches,
        }


def session(path: Path) -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.log_severity_level = 3
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


# A model input, the size to crop its output back to, the patch position and,
# optionally, the real image area of the patch (True) without its padding.
PatchInput = (
    tuple[NDArray[np.float32], tuple[int, int], int]
    | tuple[NDArray[np.float32], tuple[int, int], int, NDArray[np.bool_]]
)


def padded_patches(
    data: cache.SplitData,
    mean: NDArray[np.float32],
    std: NDArray[np.float32],
    input_size: int,
    limit: int | None = None,
) -> Iterable[tuple[NDArray[np.float32], tuple[int, int], int, NDArray[np.bool_]]]:
    """Normalised patches reflect-padded to the fixed export input size, with their real area."""
    count = len(data) if limit is None else min(limit, len(data))
    for i in range(count):
        image = normalised_patch(data, i, mean, std)
        size = (int(image.shape[1]), int(image.shape[2]))
        yield pad_to_shape(image, (input_size, input_size))[None], size, i, data.valid_area(i)


def compare(onnx_path: Path, model: torch.nn.Module, patches: Iterable[PatchInput]) -> Agreement:
    """Run both models on the same inputs (PyTorch on CPU in float32).

    With a real image area per patch, only its pixels are compared.
    """
    sess = session(onnx_path)
    dtype = np.float16 if "float16" in sess.get_inputs()[0].type else np.float32
    model = model.cpu().float().eval()
    max_diff, same, pixels, count = 0.0, 0, 0, 0
    with torch.no_grad():
        for item in patches:
            batch, size = item[0], item[1]
            area = item[3] if len(item) == 4 else np.ones(size, dtype=bool)
            reference = model(torch.from_numpy(batch)).numpy()
            outputs = sess.run(None, {INPUT_NAME: batch.astype(dtype)})
            candidate = np.asarray(outputs[0], dtype=np.float32)
            reference = crop_back(reference, size)
            candidate = crop_back(candidate, size)
            difference = np.abs(reference - candidate)[..., area]
            if difference.size:
                max_diff = max(max_diff, float(difference.max()))
            agree = reference.argmax(axis=1) == candidate.argmax(axis=1)
            same += int(agree[:, area].sum())
            pixels += int(area.sum()) * int(batch.shape[0])
            count += 1
    if count == 0:
        raise VerificationError("no patches to verify")
    return Agreement(max_diff, same / pixels, pixels, count)


def check(agreement: Agreement, max_difference: float, min_agreement: float) -> None:
    if agreement.argmax_agreement < min_agreement:
        raise VerificationError(
            f"ONNX and PyTorch agree on {agreement.argmax_agreement:.5f} of pixels, "
            f"below the required {min_agreement}"
        )
    if agreement.max_abs_logit_difference > max_difference:
        raise VerificationError(
            f"maximum absolute logit difference {agreement.max_abs_logit_difference:.3g} "
            f"is above {max_difference}"
        )
