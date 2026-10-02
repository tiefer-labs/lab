# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Polite access to the dataset over HTTPS: rate-limit backoff and the token.

Hugging Face answers HTTP 429 (too many requests) when a client reads too
fast. Every read goes through one `Backoff`: when any read is rate limited,
all reader threads pause together, for the server's `Retry-After` when the
error carries it, otherwise for an exponential backoff with jitter, capped.
GDAL errors do not carry response headers, so reads through rasterio always
use the backoff.

A Hugging Face token raises the limit. It is read from `HF_TOKEN` and passed
to GDAL as a bearer token (`GDAL_HTTP_AUTH=BEARER`, `GDAL_HTTP_BEARER`). The
token is never printed, logged or written to a file.
"""

from __future__ import annotations

import os
import random
import threading
import time
import urllib.error
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")

TOKEN_ENV = "HF_TOKEN"  # noqa: S105 (the name of the variable, not a token)

# Retry schedule for rate-limited reads: 10 s, 20 s, 40 s, ... capped at 300 s,
# each multiplied by a random factor in [0.5, 1.0].
BASE_DELAY_S = 10.0
MAX_DELAY_S = 300.0
MAX_ATTEMPTS = 12


def configure_token() -> bool:
    """Pass HF_TOKEN to GDAL as a bearer token. Returns whether a token is set."""
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        return False
    os.environ["GDAL_HTTP_AUTH"] = "BEARER"
    os.environ["GDAL_HTTP_BEARER"] = token
    return True


def auth_headers() -> dict[str, str]:
    """HTTP headers for direct requests to Hugging Face (empty without a token)."""
    token = os.environ.get(TOKEN_ENV, "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def is_rate_limited(error: BaseException) -> bool:
    """True for HTTP 429, from urllib or from a GDAL error message."""
    if isinstance(error, urllib.error.HTTPError):
        return error.code == 429
    text = str(error)
    return "429" in text or "Too Many Requests" in text


def retry_after_seconds(error: BaseException) -> float | None:
    """The server's Retry-After in seconds, when the error carries it."""
    if isinstance(error, urllib.error.HTTPError) and error.headers is not None:
        value = error.headers.get("Retry-After")
        if value is not None:
            try:
                return max(0.0, float(value))
            except ValueError:
                return None
    return None


@dataclass
class Backoff:
    """Shared pause for all reader threads after a rate-limited read."""

    base_s: float = BASE_DELAY_S
    max_s: float = MAX_DELAY_S
    attempts: int = MAX_ATTEMPTS
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    rng: random.Random = field(default_factory=random.Random)
    waits: list[float] = field(default_factory=list)
    _paused_until: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def delay(self, attempt: int, error: BaseException) -> float:
        server = retry_after_seconds(error)
        if server is not None:
            return min(server, self.max_s)
        return min(self.base_s * 2.0**attempt, self.max_s) * self.rng.uniform(0.5, 1.0)

    def _wait_for_pause(self) -> None:
        with self._lock:
            remaining = self._paused_until - self.clock()
        if remaining > 0:
            self.sleep(remaining)

    def call(self, fn: Callable[..., T], *args: object) -> T:
        """Run fn(*args); on HTTP 429 pause every reader and try again."""
        for attempt in range(self.attempts):
            self._wait_for_pause()
            try:
                return fn(*args)
            except Exception as error:
                if not is_rate_limited(error) or attempt == self.attempts - 1:
                    raise
                wait = self.delay(attempt, error)
                with self._lock:
                    self._paused_until = max(self._paused_until, self.clock() + wait)
                    self.waits.append(wait)
                print(
                    f"rate limited (HTTP 429); all readers pause {wait:.0f} s "
                    f"(attempt {attempt + 1} of {self.attempts})",
                    flush=True,
                )
        raise AssertionError("unreachable")
