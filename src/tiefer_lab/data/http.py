# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Polite access to the dataset over HTTPS: rate-limit backoff and the token.

Hugging Face answers HTTP 429 (too many requests) when a client reads too
fast. Every read goes through one `Backoff`: when any read fails for a
transient reason, all reader threads pause together, for the server's
`Retry-After` when the error carries it, otherwise for an exponential backoff
with jitter, capped, and the read is tried again.

Transient means: HTTP 429, an HTTP 5xx answer, or a rasterio I/O error at open
or during the read. When the server answers a range request with an error page
instead of data, GDAL reports the file as "not recognized as being in a
supported file format" and rasterio raises `RasterioIOError: Read failed`,
without the status code; GDAL errors do not carry response headers either.
Errors that a retry cannot fix, such as a missing band or a wrong shape
(`DataSourceError`), are raised at once.

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


TRANSIENT_HTTP_CODES = frozenset({429, 500, 502, 503, 504})


def _is_rasterio_io_error(error: BaseException) -> bool:
    """True for rasterio.errors.RasterioIOError, matched by name so rasterio is not imported."""
    return any(
        cls.__name__ == "RasterioIOError" and cls.__module__.startswith("rasterio")
        for cls in type(error).__mro__
    )


def is_transient(error: BaseException) -> bool:
    """True when the same read may succeed later: rate limit, server error, GDAL I/O error."""
    if isinstance(error, urllib.error.HTTPError):
        return error.code in TRANSIENT_HTTP_CODES
    return is_rate_limited(error) or _is_rasterio_io_error(error)


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
class RateLimiter:
    """At most `per_minute` reads per minute, shared by all threads of a job.

    Reads are spaced evenly: each waits until 60 / per_minute seconds after
    the previous one was allowed.
    """

    per_minute: float
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    _next: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        if self.per_minute <= 0:
            raise ValueError("per_minute must be positive")

    def acquire(self) -> None:
        interval = 60.0 / self.per_minute
        with self._lock:
            now = self.clock()
            start = max(now, self._next)
            self._next = start + interval
        if start > now:
            self.sleep(start - now)


@dataclass
class Backoff:
    """Shared pause for all reader threads after a read that failed for a transient reason."""

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
        """Run fn(*args); on a transient error pause every reader and try again.

        After `attempts` tries the last error is raised.
        """
        for attempt in range(self.attempts):
            self._wait_for_pause()
            try:
                return fn(*args)
            except Exception as error:
                if not is_transient(error) or attempt == self.attempts - 1:
                    raise
                wait = self.delay(attempt, error)
                with self._lock:
                    self._paused_until = max(self._paused_until, self.clock() + wait)
                    self.waits.append(wait)
                if is_rate_limited(error):
                    reason = "rate limited (HTTP 429)"
                else:
                    reason = f"read failed ({type(error).__name__}: {_first_line(error)})"
                print(
                    f"{reason}; all readers pause {wait:.0f} s "
                    f"(attempt {attempt + 1} of {self.attempts})",
                    flush=True,
                )
        raise AssertionError("unreachable")


def _first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0][:200] if text else "no message"
