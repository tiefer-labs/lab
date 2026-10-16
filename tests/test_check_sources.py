# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The source check on recorded responses: no network, no credentials, no download."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from tiefer_lab.data import check_sources as cs
from tiefer_lab.data import independent, source
from tiefer_lab.data.source import RemoteFile
from tiefer_lab.reference_models import REFERENCES

HF = RemoteFile(
    "part.taco",
    "https://huggingface.co/datasets/x/y/resolve/main/part.taco",
    100,
    "sha256:abc",
    "16 October 2026",
    "https://huggingface.co/api/datasets/x/y/tree/main",
)
ZENODO = RemoteFile(
    "a.zip",
    "https://zenodo.org/records/1/files/a.zip?download=1",
    50,
    "md5:feed",
    "16 October 2026",
    "https://zenodo.org/api/records/1",
)


class Recorded:
    """Recorded answers by URL; each call is logged with its method and byte cap."""

    def __init__(self, answers: Mapping[str, Any]) -> None:
        self.answers = dict(answers)
        self.calls: list[tuple[str, str, int]] = []

    def __call__(self, url: str, method: str, max_bytes: int) -> cs.Answer:
        self.calls.append((url, method, max_bytes))
        answer = self.answers[(url, method)] if (url, method) in self.answers else self.answers[url]
        if isinstance(answer, list):
            answer = answer.pop(0)
        if isinstance(answer, Exception):
            raise answer
        assert isinstance(answer, cs.Answer)
        return answer


def _ok(url: str, **headers: str) -> cs.Answer:
    return cs.Answer(url, 200, headers)


def _wait() -> None:
    return None


def test_hugging_face_size_and_checksum_from_the_redirect_headers() -> None:
    cdn = "https://cdn.example/part"
    fetch = Recorded(
        {
            HF.url: cs.Answer(
                HF.url,
                302,
                {"location": cdn, "x-linked-size": "100", "x-linked-etag": '"abc"'},
            ),
            cdn: _ok(cdn, **{"content-length": "100"}),
        }
    )
    result, _ = cs.head_file(HF, fetch, _wait)
    assert result.status == 200 and result.size == 100
    assert result.size_ok and result.checksum_ok and result.redirects == [cdn]
    # Only HEAD requests, and no body is read.
    assert {(m, b) for _, m, b in fetch.calls} == {("HEAD", 0)}


def test_zenodo_checksum_from_the_record_and_a_mismatch_fails() -> None:
    record = {"files": [{"key": "a.zip", "checksum": "md5:feed"}]}
    fetch = Recorded(
        {
            ZENODO.url: _ok(ZENODO.url, **{"content-length": "50"}),
            ZENODO.source: cs.Answer(ZENODO.source, 200, {}, json.dumps(record).encode()),
        }
    )
    result, _ = cs.head_file(ZENODO, fetch, _wait)
    assert result.size_ok and result.checksum_ok is None
    assert cs.metadata_checksums([ZENODO], fetch, _wait) == {"a.zip": True}
    # The metadata record is the only GET, capped in size.
    assert (ZENODO.source, "GET", cs.MAX_METADATA_BYTES) in fetch.calls
    record["files"][0]["checksum"] = "md5:other"
    fetch.answers[ZENODO.source] = cs.Answer(ZENODO.source, 200, {}, json.dumps(record).encode())
    assert cs.metadata_checksums([ZENODO], fetch, _wait) == {"a.zip": False}


def test_a_login_redirect_means_credentials_needed() -> None:
    login = "https://example.sharepoint.com/_layouts/15/Authenticate.aspx?Source=x"
    remote = dataclasses.replace(ZENODO, url="https://example.sharepoint.com/:u:/g/f", size=None)
    fetch = Recorded({remote.url: cs.Answer(remote.url, 302, {"location": login})})
    result, _ = cs.head_file(remote, fetch, _wait)
    assert result.login
    src = cs.Source("m", "reference model", (remote,), "no decision", "MIT", None)
    word, why = cs.obtainable(src, [result])
    assert word == "credentials needed" and "weights" in why
    forbidden = cs.Answer(ZENODO.url, 403, {})
    result, _ = cs.head_file(ZENODO, Recorded({ZENODO.url: forbidden}), _wait)
    assert cs.obtainable(cs.Source("d", "dataset", (ZENODO,), "used", "x"), [result])[0] == (
        "credentials needed"
    )


def test_head_refused_falls_back_to_the_first_byte() -> None:
    fetch = Recorded(
        {
            (ZENODO.url, "HEAD"): cs.Answer(ZENODO.url, 405, {}),
            (ZENODO.url, "RANGE"): cs.Answer(
                ZENODO.url, 206, {"content-range": "bytes 0-0/50", "content-length": "1"}
            ),
        }
    )
    result, _ = cs.head_file(ZENODO, fetch, _wait)
    assert result.status == 206 and result.size == 50 and result.size_ok


def test_a_dropped_connection_is_tried_again_then_reported() -> None:
    fetch = Recorded({ZENODO.url: [OSError("reset"), _ok(ZENODO.url, **{"content-length": "50"})]})
    result, _ = cs.head_file(ZENODO, fetch, _wait)
    assert result.size_ok and not result.error
    fetch = Recorded({ZENODO.url: [OSError("reset")] * (cs.RETRIES + 1)})
    result, _ = cs.head_file(ZENODO, fetch, _wait)
    assert "OSError" in result.error
    word, _ = cs.obtainable(cs.Source("d", "dataset", (ZENODO,), "used", "x"), [result])
    assert word == "not checked"


def test_only_allowed_or_undecided_sources_are_checked() -> None:
    names = {s.name for s in cs.sources()}
    assert {"cloudsen12plus", "s2_cloud_catalogue", "kappaset", "landsat8_biome"} <= names
    assert {"landsat8_sparcs", "s2cloudless", "fmask4", "cd_fcnn_rgbi"} <= names
    for declined in ("s2_hollstein", "landsat8_38cloud", "landsat8_95cloud", "s2_cesbio"):
        assert declined not in names
    assert "dtacs4bands" not in names
    kappamask = next(s for s in cs.sources() if s.name == "kappamask_l1c")
    assert cs.obtainable(kappamask, [])[0] == "licence not stated"
    unet = next(s for s in cs.sources() if s.name == "unetmobv2")
    assert cs.obtainable(unet, [])[0] == "not checked"


def test_the_fact_records_hold_what_the_check_compares() -> None:
    assert len(source.TACO_FILES) == 8
    assert all(f.checksum and f.checksum.startswith("sha256:") for f in source.TACO_FILES)
    assert len(independent.DATASETS["landsat8_biome"].files) == 96
    assert all(f.size for f in independent.DATASETS["landsat8_biome"].files)
    assert REFERENCES["s2cloudless"].weights_licence is not None
    assert REFERENCES["kappamask_l1c"].weights_licence is None


def test_a_full_check_waits_between_requests_and_writes_no_credential() -> None:
    def fetch(url: str, method: str, max_bytes: int) -> cs.Answer:
        if method == "GET":
            return cs.Answer(url, 404, {})
        return cs.Answer(url, 200, {"content-length": "1"})

    pauses: list[float] = []
    report = cs.check(fetch, interval_s=2.0, sleep=pauses.append, today=dt.date(2026, 10, 16))
    assert report["credentials_sent"] is False and report["date"] == "16 October 2026"
    assert pauses and set(pauses) == {2.0}
    words = {r["name"]: r["obtainable"] for r in report["sources"]}
    assert set(words.values()) <= set(cs.OBTAINABLE)
    # Size 1 differs from every recorded size, so nothing is "yes".
    assert "yes" not in words.values()
    assert len(report["summary"]) == len(report["sources"])


def test_http_fetch_sends_no_credential_and_only_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "secret-value")
    seen: list[Any] = []

    class Response:
        status = 200
        headers: Mapping[str, str] = {"Content-Length": "3"}

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self, n: int) -> bytes:
            return b""

    class Opener:
        def open(self, request: Any, timeout: float) -> Response:
            seen.append(request)
            return Response()

    monkeypatch.setattr(cs.urllib.request, "build_opener", lambda *a: Opener())
    answer = cs.http_fetch("https://example.org/f", "HEAD", 0)
    assert answer.status == 200 and answer.headers["content-length"] == "3"
    sent = {k.lower(): v for k, v in seen[0].header_items()}
    assert not cs.FORBIDDEN_HEADERS & set(sent)
    assert "secret-value" not in json.dumps(sent)
    with pytest.raises(ValueError, match="only https"):
        cs.http_fetch("http://example.org/f", "HEAD", 0)


def test_main_writes_the_report(
    tiefer_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        cs,
        "check",
        lambda interval_s: {"sources": [], "summary": ["x: yes"], "credentials_sent": False},
    )
    assert cs.main(["--interval", "1"]) == 0
    out = tiefer_env["TIEFER_REPORTS_DIR"] / "data" / "sources.json"
    assert json.loads(out.read_text())["credentials_sent"] is False
    with pytest.raises(SystemExit):
        cs.main(["--interval", "0.1"])
