# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Turn .github/audit-exceptions.toml into pip-audit arguments, or fail.

    python3 .github/scripts/audit_exceptions.py [path] [--today YYYY-MM-DD]

Prints one `--ignore-vuln <id>` pair per line for every valid entry. Exits 1
with a message for every entry that is expired, has no reason, or expires more
than MAX_DAYS ahead, so an exception can never be silent or permanent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import tomllib
from pathlib import Path
from typing import Any

MAX_DAYS = 90
FIELDS = ("id", "package", "reason", "expires")


def problems(entries: list[dict[str, Any]], today: dt.date) -> list[str]:
    out = []
    seen: set[str] = set()
    for n, entry in enumerate(entries, start=1):
        name = str(entry.get("id", f"entry {n}"))
        missing = [f for f in FIELDS if not str(entry.get(f, "")).strip()]
        if missing:
            out.append(f"{name}: missing {', '.join(missing)}")
            continue
        expires = entry["expires"]
        if not isinstance(expires, dt.date) or isinstance(expires, dt.datetime):
            out.append(f"{name}: expires must be a date such as 2026-12-31")
            continue
        if expires < today:
            out.append(f"{name}: expired on {expires}; renew it with a new reason or remove it")
        elif (expires - today).days > MAX_DAYS:
            out.append(f"{name}: expires more than {MAX_DAYS} days ahead ({expires})")
        if name in seen:
            out.append(f"{name}: listed twice")
        seen.add(name)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", default=".github/audit-exceptions.toml", type=Path)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    args = parser.parse_args(argv)
    entries = tomllib.loads(args.path.read_text(encoding="utf-8")).get("exception", [])
    found = problems(entries, args.today)
    for line in found:
        print(f"error: {line}", file=sys.stderr)
    if found:
        return 1
    for entry in entries:
        print(f"--ignore-vuln\n{entry['id']}")
        accepted = f"{entry['id']} ({entry['package']}) until {entry['expires']}"
        print(f"accepted: {accepted}: {entry['reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
