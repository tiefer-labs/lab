# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import email.message
import random
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from tiefer_lab.data import http


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _backoff(clock: _Clock, **kwargs: Any) -> http.Backoff:
    return http.Backoff(sleep=clock.sleep, clock=clock.time, rng=random.Random(0), **kwargs)


def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://example.invalid", code, "x", headers, None)


def test_rate_limited_reads_back_off_exponentially_with_jitter_and_continue() -> None:
    clock = _Clock()
    backoff = _backoff(clock, base_s=10.0, max_s=300.0)
    failures = iter([RuntimeError("HTTP response code: 429"), RuntimeError("429")])

    def read() -> str:
        error = next(failures, None)
        if error is not None:
            raise error
        return "patch"

    assert backoff.call(read) == "patch"
    assert len(backoff.waits) == 2
    assert 5.0 <= backoff.waits[0] <= 10.0 and 10.0 <= backoff.waits[1] <= 20.0
    assert clock.sleeps == backoff.waits


def test_backoff_is_capped_and_honours_retry_after() -> None:
    clock = _Clock()
    backoff = _backoff(clock, base_s=10.0, max_s=60.0)
    assert backoff.delay(10, RuntimeError("429")) <= 60.0
    assert backoff.delay(0, _http_error(429, "42")) == 42.0
    assert backoff.delay(0, _http_error(429, "9999")) == 60.0


def test_a_pause_holds_every_reader() -> None:
    clock = _Clock()
    backoff = _backoff(clock)
    calls = {"n": 0}

    def limited_once() -> int:
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_error(429, "30")
        return 1

    backoff._paused_until = 0.0
    with pytest.raises(urllib.error.HTTPError):
        _backoff(clock, attempts=1).call(limited_once)
    calls["n"] = 0
    assert backoff.call(limited_once) == 1
    # Another reader arriving during the pause waits for the rest of it.
    backoff._paused_until = clock.now + 12.0
    clock.sleeps.clear()
    assert backoff.call(lambda: 2) == 2
    assert clock.sleeps == [12.0]


def test_other_errors_are_not_retried_and_retries_end() -> None:
    clock = _Clock()
    backoff = _backoff(clock, attempts=3)
    with pytest.raises(ValueError):
        backoff.call(lambda: (_ for _ in ()).throw(ValueError("bad band")))
    assert clock.sleeps == []

    def always_limited() -> None:
        raise _http_error(429)

    with pytest.raises(urllib.error.HTTPError):
        backoff.call(always_limited)
    assert len(clock.sleeps) == 2


def test_token_goes_to_gdal_and_is_never_printed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tiefer_env: dict[str, Path]
) -> None:
    from tiefer_lab.data import build_cache, source

    secret = "hf_" + "TESTTOKEN" + "0123456789"
    monkeypatch.setenv(http.TOKEN_ENV, secret)
    monkeypatch.delenv("GDAL_HTTP_BEARER", raising=False)
    assert http.configure_token()
    import os

    assert os.environ["GDAL_HTTP_AUTH"] == "BEARER" and os.environ["GDAL_HTTP_BEARER"] == secret
    assert http.auth_headers() == {"Authorization": f"Bearer {secret}"}

    def no_table(_: Any) -> Any:
        raise source.DataSourceError("no dataset in tests")

    monkeypatch.setattr(source, "open_table", no_table)
    with pytest.raises(source.DataSourceError):
        build_cache.main(["--split", "train", "--revision", "r", "--taco", "x.taco"])
    out = capsys.readouterr()
    assert "Hugging Face token: set" in out.out
    assert secret not in out.out + out.err
    assert not any(
        secret in p.read_text(errors="ignore")
        for p in tiefer_env["TIEFER_DATA_DIR"].rglob("*")
        if p.is_file()
    )

    monkeypatch.delenv(http.TOKEN_ENV)
    assert not http.configure_token() and http.auth_headers() == {}
