# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The shared Markdown table helper (docs/STYLE.md, section 10)."""

from __future__ import annotations

import pytest

from tiefer_lab.tables import Group, header_block, markdown_table


def test_table_layout_alignment_and_category_rows() -> None:
    table = markdown_table(
        ["", "Column A", "Column B"], [Group("Category", [["Row name", "82.3", ""]])]
    )
    assert table.split("\n") == [
        "|  | Column A | Column B |",
        "| :--- | :---: | :---: |",
        "| **Category** | | |",
        "| Row name | 82.3 | not measured |",
    ]


def test_code_links_and_pipes_are_kept() -> None:
    table = markdown_table(
        ["Path", "Link"], [Group("", [["`src/`", "[card](https://example.org/x) a|b"]])]
    )
    assert "| `src/` | [card](https://example.org/x) a\\|b |" in table
    assert "**" not in table, "no category row when the group has no title"


def test_invalid_tables_are_rejected() -> None:
    with pytest.raises(ValueError):
        markdown_table(["A", "B"], [Group("", [["only one"]])])
    with pytest.raises(ValueError):
        markdown_table(["A"], [])
    with pytest.raises(ValueError):
        markdown_table(["A", "B"], [Group("", [["x", "two\nlines"]])])


def test_header_block() -> None:
    block = header_block("Title", "in use", "Purpose.", "assets/header.png")
    assert block.startswith('<img alt="Tiefer Lab" src="assets/header.png" width="100%">')
    assert "Status: in use. Owner: Tiefer. Licence: MPL 2.0." in block
    assert block.endswith("---\n")
