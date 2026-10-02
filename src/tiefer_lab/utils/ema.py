# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Exponential moving average (EMA) of model weights.

After every optimizer step: ema = d * ema + (1 - d) * weights, for every
floating-point parameter and buffer; integer buffers (batch norm counters) are
copied. The decay starts low and rises to its configured value,
d = min(decay, (1 + n) / (10 + n)) after n updates, so a short run is not
dominated by the random initial weights.
"""

from __future__ import annotations

import copy
from typing import Any

import torch


class WeightEMA:
    def __init__(self, model: torch.nn.Module, decay: float) -> None:
        if not 0.0 < decay < 1.0:
            raise ValueError("decay must be in (0, 1)")
        self.decay = decay
        self.updates = 0
        self.module = copy.deepcopy(model).eval()
        for p in self.module.parameters():
            p.requires_grad_(False)

    def current_decay(self) -> float:
        return min(self.decay, (1 + self.updates) / (10 + self.updates))

    @torch.no_grad()
    def update(self, model: torch.nn.Module) -> None:
        self.updates += 1
        d = self.current_decay()
        source = model.state_dict()
        for name, value in self.module.state_dict().items():
            new = source[name].detach()
            if value.dtype.is_floating_point:
                value.mul_(d).add_(new.to(value.dtype), alpha=1.0 - d)
            else:
                value.copy_(new)

    def state_dict(self) -> dict[str, Any]:
        return {"module": self.module.state_dict(), "updates": self.updates, "decay": self.decay}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.module.load_state_dict(state["module"])
        self.updates = int(state["updates"])
