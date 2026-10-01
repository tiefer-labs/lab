# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Fixed seeds for Python, NumPy and PyTorch."""

from __future__ import annotations

import os
import random

import numpy as np
import torch


def seed_everything(seed: int, deterministic: bool = False) -> None:
    """Seed every generator. With deterministic=True, also ask PyTorch for
    deterministic kernels (slower, and some operations then raise)."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    if deterministic:
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False
