# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Does evaluation on the CPU give the argmax of the training device?

    python -m tiefer_lab.device_check [--device auto]

Every job that does not train runs on CPU nodes (hpc/roihu/plan.md), while the
models are trained on a GPU. This check builds a small model with a fixed
seed, predicts one fixed input with the evaluation path of
`tiefer_lab.evaluate` on the CPU (fp32) and on the training device (with the
precision evaluation uses there, bf16 on GH200), and compares the argmax.

Tolerance: every pixel whose top-two logit margin on the CPU exceeds
MARGIN_SHARE of the largest absolute CPU logit has the same argmax on both
devices. Pixels closer to a tie than that may flip with the rounding of bf16
and are only counted in the reported agreement. On a machine without CUDA the
training device is the CPU, so the check is trivial; the smoke job
(hpc/roihu/smoke.sbatch) runs it on a GH200 node.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

import torch

from tiefer_lab.config import ModelConfig
from tiefer_lab.models import flexible
from tiefer_lab.utils import devices
from tiefer_lab.utils.devices import autocast

# A pixel whose margin is above this share of the largest logit must agree.
MARGIN_SHARE = 0.01
BANDS = ("B02", "B03", "B04", "B08")
INPUT_SHAPE = (2, len(BANDS), 128, 128)
SEED = 0


def _logits(model: torch.nn.Module, images: torch.Tensor, device: torch.device) -> torch.Tensor:
    """Logits as tiefer_lab.evaluate computes them on `device`, returned on the CPU in fp32."""
    model = model.to(device).eval()
    x = images.to(device)
    if device.type == "cuda":
        model = model.to(memory_format=torch.channels_last)
        x = x.contiguous(memory_format=torch.channels_last)
    with torch.no_grad(), autocast(device, devices.precision_for(device)):
        logits: torch.Tensor = model(x)
    return logits.float().cpu()


def compare(device_name: str = "auto") -> dict[str, Any]:
    """Compare the CPU argmax with that of the training device on a fixed input."""
    device = devices.select_device(device_name)
    torch.manual_seed(SEED)
    model = flexible.build(ModelConfig(widths=(8, 16, 32)), BANDS)
    images = torch.randn(INPUT_SHAPE, generator=torch.Generator().manual_seed(SEED))
    on_cpu = _logits(model, images, torch.device("cpu"))
    on_device = _logits(model, images, device)
    top2 = on_cpu.topk(2, dim=1).values
    margin = top2[:, 0] - top2[:, 1]
    decisive = margin > MARGIN_SHARE * float(on_cpu.abs().max())
    same = on_cpu.argmax(dim=1) == on_device.argmax(dim=1)
    return {
        "device": str(device),
        "precision": devices.precision_for(device),
        "pixels": int(same.numel()),
        "agreement": float(same.float().mean()),
        "decisive_pixels": int(decisive.sum()),
        "decisive_agreement": float(same[decisive].float().mean()) if bool(decisive.any()) else 1.0,
        "max_abs_logit_difference": float((on_cpu - on_device).abs().max()),
        "margin_share": MARGIN_SHARE,
        "passed": bool(same[decisive].all()),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.device_check")
    parser.add_argument("--device", default="auto", choices=devices.DEVICE_CHOICES)
    args = parser.parse_args(argv)
    result = compare(args.device)
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
