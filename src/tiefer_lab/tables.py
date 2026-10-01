# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The house table style (docs/STYLE.md, section 9) as one shared helper.

Every generated table goes through `house_table` so they are identical.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from html import escape

NOT_MEASURED = "not measured"
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

_WRAP_OPEN = (
    "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
    'max-width:1000px;margin:0 auto;padding:16px 0">\n'
    '<table style="width:100%;border-collapse:collapse;font-size:13px">'
)
_WRAP_CLOSE = "</tbody>\n</table>\n</div>"
_TH_FIRST = (
    '<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;'
    'border-bottom:2px solid #0C003D;color:#0C003D">{}</th>'
)
_TH = (
    '<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;'
    'border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">{}</th>'
)
_CATEGORY = (
    '<tr><td colspan="{}" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;'
    'border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">{}</td></tr>'
)
_TD_FIRST = (
    '<td align="left" style="padding:7px 7px;padding-left:20px;'
    'border-bottom:1px solid rgba(128, 128, 128, 0.15)">{}</td>'
)
_TD = (
    '<td align="center" style="padding:7px 7px;text-align:center;'
    'border-bottom:1px solid rgba(128, 128, 128, 0.15)">{}</td>'
)


@dataclass(frozen=True)
class Group:
    """Rows under an optional category row. An empty title means no category row."""

    title: str
    rows: Sequence[Sequence[str]] = field(default_factory=list)


def _cell(value: str, *, code: bool) -> str:
    text = value if value != "" else NOT_MEASURED
    text = escape(text, quote=False)
    if code:
        # Backticks are not rendered inside HTML blocks, so use <code>.
        parts = text.split("`")
        text = "".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(parts))
    # Markdown links are not rendered inside HTML blocks either.
    return _LINK.sub(r'<a href="\2">\1</a>', text)


def house_table(headers: Sequence[str], groups: Sequence[Group]) -> str:
    """Render a table in the house style.

    `headers[0]` is the first column header (empty when the first column holds
    row names). Empty cell values are written as "not measured". Text between
    backticks becomes inline code and Markdown links become HTML links.
    """
    width = len(headers)
    if width < 2:
        raise ValueError("a house table needs at least two columns")
    lines = [_WRAP_OPEN, "<thead><tr>"]
    lines.append(_TH_FIRST.format(_cell(headers[0], code=True) if headers[0] else ""))
    lines.extend(_TH.format(_cell(h, code=True)) for h in headers[1:])
    lines.append("</tr></thead>")
    lines.append("<tbody>")
    for group in groups:
        if group.title:
            lines.append(_CATEGORY.format(width, _cell(group.title, code=True)))
        for row in group.rows:
            if len(row) != width:
                raise ValueError(f"row has {len(row)} cells, expected {width}: {row!r}")
            lines.append("<tr>")
            lines.append(_TD_FIRST.format(_cell(row[0], code=True)))
            lines.extend(_TD.format(_cell(v, code=True)) for v in row[1:])
            lines.append("</tr>")
    lines.append(_WRAP_CLOSE)
    return "\n".join(lines)


def header_block(title: str, status: str, purpose: str, image_path: str) -> str:
    """The standard Markdown header (docs/STYLE.md, section 1)."""
    return (
        f'<img alt="Tiefer Lab" src="{image_path}" width="100%">\n\n'
        f"# {title}\n\n"
        f"Status: {status}. Owner: Tiefer. Licence: MPL 2.0.\n\n"
        f"{purpose}\n\n---\n"
    )
