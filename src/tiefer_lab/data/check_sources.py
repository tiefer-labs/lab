# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Check that every data source and reference model can be obtained, without downloading it.

    python -m tiefer_lab.data.check_sources [--interval 1.0]

It reads the existing fact records:

- `TACO_FILES` of data/source.py (CloudSEN12+);
- `DATASETS` of data/independent.py, every dataset that the maintainer's
  licence decisions do not refuse outright (used, or a candidate without a
  decision; a declined or "not used" dataset is not checked);
- `REFERENCES` of reference_models.py, except a declined one.

For every recorded file it sends a HEAD request (a GET of the first byte when
the server refuses HEAD), follows the redirects itself and records the status,
the size and the redirect target, and compares the size and the checksum with
the facts. A checksum is compared when the server states it in a header
(Hugging Face `X-Linked-ETag`) or in the small metadata record that publishes
it (the Zenodo record API, the PyPI JSON API). It never downloads a file,
never sends a credential (no token, cookie or authorization header, whatever
the environment holds) and waits `--interval` seconds between requests.

Each source gets one word for the "obtainable" column of docs/DATASETS.md and
references/README.md:

- `yes`: every file answers, with the recorded size and checksum;
- `credentials needed`: a file answers 401 or 403, or redirects to a login;
- `licence not stated`: a reference model whose weights licence is not stated;
- `not checked`: no file is recorded, or the check failed for another reason
  (the details say which).

Writes `reports/data/sources.json` and prints a short summary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tiefer_lab.data import independent, source
from tiefer_lab.data.source import RemoteFile
from tiefer_lab.utils import paths

REPORT = Path("data") / "sources.json"
USER_AGENT = "tiefer-lab-source-check/1 (+https://github.com/tiefer-labs/lab)"
TIMEOUT_S = 30.0
MAX_REDIRECTS = 8
MAX_METADATA_BYTES = 2_000_000
DEFAULT_INTERVAL_S = 1.0
# A dropped connection (a TLS reset, for example) is tried again this often.
RETRIES = 2
LOGIN_MARKERS = ("login", "signin", "sign-in", "authenticate", "auth/", "sso")
# Headers that would carry a credential; never sent.
FORBIDDEN_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})

OBTAINABLE = ("yes", "credentials needed", "licence not stated", "not checked")


@dataclass(frozen=True)
class Answer:
    """One HTTP answer: status, headers (lower-case names) and the URL asked."""

    url: str
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


# fetch(url, method, max_bytes) -> Answer, without following redirects.
Fetch = Callable[[str, str, int], Answer]


@dataclass(frozen=True)
class Source:
    """One source to check, from the fact records."""

    name: str
    kind: str  # "dataset" or "reference model"
    files: tuple[RemoteFile, ...]
    decision: str
    licence: str | None
    weights_licence: str | None = None  # reference models only
    not_checked: str = ""


@dataclass
class FileResult:
    name: str
    url: str
    status: int | None = None
    size: int | None = None
    redirects: list[str] = field(default_factory=list)
    size_ok: bool | None = None
    checksum_ok: bool | None = None
    login: bool = False
    error: str = ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def http_fetch(url: str, method: str, max_bytes: int) -> Answer:
    """One request without redirects, credentials or cookies; reads at most max_bytes."""
    opener = urllib.request.build_opener(_NoRedirect)
    headers = {"User-Agent": USER_AGENT}
    if method == "RANGE":
        method = "GET"
        headers["Range"] = "bytes=0-0"
    assert not FORBIDDEN_HEADERS & {h.lower() for h in headers}
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError(f"only https URLs are checked: {url}")
    request = urllib.request.Request(url, method=method, headers=headers)  # noqa: S310 (https only)
    try:
        with opener.open(request, timeout=TIMEOUT_S) as response:
            body = response.read(max_bytes) if max_bytes else b""
            return Answer(url, response.status, _lower(response.headers), body)
    except urllib.error.HTTPError as err:
        return Answer(url, err.code, _lower(err.headers))


def _lower(headers: Any) -> dict[str, str]:
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _is_login(url: str) -> bool:
    lowered = url.lower()
    return any(marker in lowered for marker in LOGIN_MARKERS)


def _size(answer: Answer) -> int | None:
    """The size of the whole file: the total of a 206 range answer, else the length."""
    content_range = answer.headers.get("content-range", "")
    if answer.status == 206 and "/" in content_range:
        total = content_range.rsplit("/", 1)[1]
        return int(total) if total.isdigit() else None
    for key in ("x-linked-size", "content-length"):
        value = answer.headers.get(key, "").strip()
        if value.isdigit():
            return int(value)
    return None


def _with_retry(
    fetch: Fetch, url: str, method: str, max_bytes: int, wait: Callable[[], None]
) -> Answer:
    """One request, tried again up to RETRIES times when the connection fails."""
    for attempt in range(RETRIES + 1):
        wait()
        try:
            return fetch(url, method, max_bytes)
        except OSError:
            if attempt == RETRIES:
                raise
    raise AssertionError("unreachable")


def head_file(
    remote: RemoteFile, fetch: Fetch, wait: Callable[[], None]
) -> tuple[FileResult, list[Answer]]:
    """HEAD the file (or its first byte), following redirects by hand."""
    result = FileResult(remote.name, remote.url)
    answers: list[Answer] = []
    url = remote.url
    method = "HEAD"
    for _ in range(MAX_REDIRECTS + 1):
        try:
            answer = _with_retry(fetch, url, method, 0, wait)
        except (OSError, ValueError) as err:
            result.error = f"{type(err).__name__}: {err}"
            return result, answers
        answers.append(answer)
        if answer.status in (301, 302, 303, 307, 308) and answer.headers.get("location"):
            url = urllib.parse.urljoin(url, answer.headers["location"])
            result.redirects.append(url)
            if _is_login(url):
                result.login = True
                result.status = answer.status
                return result, answers
            continue
        if answer.status in (405, 501) and method == "HEAD":
            method = "RANGE"
            continue
        result.status = answer.status
        result.size = _size(answer)
        break
    else:
        result.error = "too many redirects"
    if result.status in (401, 403):
        result.login = True
    if result.size is not None and remote.size is not None:
        result.size_ok = result.size == remote.size
    linked = next(
        (a.headers["x-linked-etag"] for a in answers if "x-linked-etag" in a.headers), None
    )
    if linked and remote.checksum and remote.checksum.startswith("sha256:"):
        result.checksum_ok = linked.strip('"') == remote.checksum.split(":", 1)[1]
    return result, answers


def metadata_checksums(
    files: Sequence[RemoteFile], fetch: Fetch, wait: Callable[[], None]
) -> dict[str, bool]:
    """Compare checksums with the small metadata record that publishes them.

    Zenodo publishes "md5:<hex>" per file in its record API, PyPI "sha256" per
    distribution in its JSON API. Only these JSON records are read, never a file.
    """
    out: dict[str, bool] = {}
    records: dict[str, Any] = {}
    for remote in files:
        if not remote.checksum or not remote.source.startswith(
            ("https://zenodo.org/api/records/", "https://pypi.org/pypi/")
        ):
            continue
        if remote.source not in records:
            try:
                answer = _with_retry(fetch, remote.source, "GET", MAX_METADATA_BYTES, wait)
                records[remote.source] = json.loads(answer.body) if answer.status == 200 else None
            except (OSError, ValueError):
                records[remote.source] = None
        record = records[remote.source]
        if not record:
            continue
        published: str | None = None
        if "zenodo.org" in remote.source:
            published = next(
                (f.get("checksum") for f in record.get("files", []) if f.get("key") == remote.name),
                None,
            )
        else:
            published = next(
                (
                    "sha256:" + u["digests"]["sha256"]
                    for u in record.get("urls", [])
                    if u.get("filename") == remote.name
                ),
                None,
            )
        if published is not None:
            out[remote.name] = published == remote.checksum
    return out


def sources() -> list[Source]:
    """Every source to check, from the fact records; declined ones are left out."""
    from tiefer_lab.reference_models import REFERENCES

    out = [
        Source(
            "cloudsen12plus",
            "dataset",
            source.TACO_FILES,
            "used",
            source.DATASET_LICENCE,
        )
    ]
    for name, info in independent.DATASETS.items():
        if info.decision.status not in ("used", "candidate, no decision yet"):
            continue
        out.append(Source(name, "dataset", info.files, info.decision.status, info.licence))
    for name, ref in REFERENCES.items():
        if ref.decision.refused:
            continue
        out.append(
            Source(
                name,
                "reference model",
                ref.files,
                ref.decision.status,
                ref.licence,
                ref.weights_licence,
                ref.not_checked,
            )
        )
    return out


def obtainable(src: Source, results: Sequence[FileResult]) -> tuple[str, str]:
    """The word of the "obtainable" column, and why."""
    if src.not_checked:
        return "not checked", src.not_checked
    no_licence = src.kind == "reference model" and src.weights_licence is None
    if any(r.login for r in results):
        also = "; no licence is stated for the weights either" if no_licence else ""
        return "credentials needed", f"a file answers 401 or 403, or redirects to a login{also}"
    if no_licence:
        return "licence not stated", "no licence is stated for the weights"
    if not results:
        return "not checked", "no file is recorded for this source"
    failed = [
        r
        for r in results
        if r.error or r.status not in (200, 206) or r.size_ok is False or r.checksum_ok is False
    ]
    if failed:
        first = failed[0]
        why = first.error or (
            f"{first.name}: status {first.status}, size_ok {first.size_ok}, "
            f"checksum_ok {first.checksum_ok}"
        )
        return "not checked", f"the check failed: {why}"
    return "yes", "every recorded file answers with the recorded size and checksum"


def check(
    fetch: Fetch = http_fetch,
    interval_s: float = DEFAULT_INTERVAL_S,
    sleep: Callable[[float], None] = time.sleep,
    today: dt.date | None = None,
) -> dict[str, Any]:
    def wait() -> None:
        sleep(interval_s)

    out_sources = []
    for src in sources():
        results: list[FileResult] = []
        if not src.not_checked:
            for remote in src.files:
                result, _ = head_file(remote, fetch, wait)
                results.append(result)
            for name, ok in metadata_checksums(src.files, fetch, wait).items():
                for r in results:
                    if r.name == name:
                        r.checksum_ok = ok
        word, why = obtainable(src, results)
        out_sources.append(
            {
                "name": src.name,
                "kind": src.kind,
                "decision": src.decision,
                "licence": src.licence,
                "weights_licence": src.weights_licence,
                "obtainable": word,
                "why": why,
                "files": len(results),
                "bytes": sum(r.size or 0 for r in results),
                "results": [vars(r) for r in results],
            }
        )
    day = today or dt.date.today()
    return {
        "kind": "source check",
        "date": f"{day.day} {day:%B %Y}",
        "credentials_sent": False,
        "interval_s": interval_s,
        "sources": out_sources,
        "summary": summary_lines(out_sources),
    }


def summary_lines(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        f"{r['name']}: {r['obtainable']} ({r['files']} files, {r['bytes']:,} bytes); {r['why']}"
        for r in rows
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tiefer_lab.data.check_sources")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_S)
    args = parser.parse_args(argv)
    if args.interval < 0.5:
        parser.error("--interval is at least 0.5 seconds")
    report = check(interval_s=args.interval)
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for line in report["summary"]:
        print(line, flush=True)
    print(f"report: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
