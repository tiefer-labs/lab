# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""SIGTERM and SIGUSR1 handling for clean, resumable stops.

Slurm sends SIGUSR1 before the time limit (`--signal=B:USR1@300` in
train.sbatch) and SIGTERM on cancellation. The handler only records the
request; the training loop checks it after each step, saves a checkpoint
and exits.
"""

from __future__ import annotations

import signal
from types import FrameType, TracebackType


class StopRequest:
    """Context manager that turns SIGTERM and SIGUSR1 into a flag."""

    def __init__(self) -> None:
        self.signal_name: str | None = None
        self._previous: dict[signal.Signals, object] = {}

    @property
    def requested(self) -> bool:
        return self.signal_name is not None

    def _handle(self, signum: int, _frame: FrameType | None) -> None:
        self.signal_name = signal.Signals(signum).name

    def __enter__(self) -> StopRequest:
        for sig in self._signals():
            self._previous[sig] = signal.signal(sig, self._handle)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        for sig, previous in self._previous.items():
            signal.signal(sig, previous)  # type: ignore[arg-type]
        self._previous.clear()

    @staticmethod
    def _signals() -> list[signal.Signals]:
        sigs = [signal.SIGTERM]
        if hasattr(signal, "SIGUSR1"):
            sigs.append(signal.SIGUSR1)
        return sigs
