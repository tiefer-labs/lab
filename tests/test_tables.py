# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The house table style helper (docs/STYLE.md, section 9)."""

from __future__ import annotations

import pytest

from tiefer_lab.tables import Group, header_block, house_table


def test_table_structure_alignment_and_colours() -> None:
    html = house_table(
        ["", "Column A", "Column B"], [Group("Category", [["Row name", "82.3", ""]])]
    )
    lines = html.split("\n")
    assert "" not in lines, "no empty lines inside the HTML block"
    assert 'colspan="3"' in html
    assert html.count('align="left"') == 3  # top-left header, category, first cell
    assert html.count('align="center"') == 4
    assert "#0C003D" in html and "rgba(12, 0, 61, 0.1)" in html
    assert "rgba(128, 128, 128, 0.15)" in html
    assert ">not measured</td>" in html, "empty values are written as not measured"


def test_code_and_links_become_html() -> None:
    html = house_table(["Path", "Link"], [Group("", [["`src/`", "[card](https://example.org/x)"]])])
    assert "<code>src/</code>" in html
    assert '<a href="https://example.org/x">card</a>' in html
    assert "colspan" not in html, "no category row when the group has no title"


def test_rows_must_match_header_width() -> None:
    with pytest.raises(ValueError):
        house_table(["A", "B"], [Group("", [["only one"]])])


def test_header_block() -> None:
    block = header_block("Title", "in use", "Purpose.", "assets/header.png")
    assert block.startswith('<img alt="Tiefer Lab" src="assets/header.png" width="100%">')
    assert "Status: in use. Owner: Tiefer. Licence: MPL 2.0." in block
    assert block.endswith("---\n")
