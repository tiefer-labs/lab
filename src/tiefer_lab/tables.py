# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Markdown tables in the house format (docs/STYLE.md, section 9), from one shared helper.

Every generated table goes through `markdown_table`, so they are identical:
plain GitHub Markdown, first column left-aligned, all other columns centred,
optional category rows in bold, and "not measured" for a missing value.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

NOT_MEASURED = "not measured"


@dataclass(frozen=True)
class Group:
    """Rows under an optional category row. An empty title means no category row."""

    title: str
    rows: Sequence[Sequence[str]] = field(default_factory=list)


def _cell(value: str) -> str:
    text = value if value != "" else NOT_MEASURED
    if "\n" in text:
        raise ValueError(f"a table cell is one line: {value!r}")
    return text.replace("|", "\\|")


def markdown_table(headers: Sequence[str], groups: Sequence[Group]) -> str:
    """Render a table in the house format.

    `headers[0]` is the first column header (empty when the first column holds
    row names). A group with a title gets a category row: the title in bold in
    the first cell, the other cells empty. Empty values are written as
    "not measured". Cells may contain inline code and links.
    """
    width = len(headers)
    if width < 2:
        raise ValueError("a table needs at least two columns")
    lines = [
        "| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |",
        "| :--- | " + " | ".join([":---:"] * (width - 1)) + " |",
    ]
    for group in groups:
        if group.title:
            lines.append(f"| **{_cell(group.title)}** |" + " |" * (width - 1))
        for row in group.rows:
            if len(row) != width:
                raise ValueError(f"row has {len(row)} cells, expected {width}: {row!r}")
            lines.append("| " + " | ".join(_cell(v) for v in row) + " |")
    return "\n".join(lines)


def header_block(title: str, status: str, purpose: str, image_path: str) -> str:
    """The standard Markdown header (docs/STYLE.md, section 1)."""
    return (
        f'<img alt="Tiefer Lab" src="{image_path}" width="100%">\n\n'
        f"# {title}\n\n"
        f"Status: {status}. Owner: Tiefer. Licence: MPL 2.0.\n\n"
        f"{purpose}\n\n---\n"
    )
