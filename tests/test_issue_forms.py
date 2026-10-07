# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The issue forms follow docs/STYLE.md, section 12.33, and GitHub's form schema.

The forms are read with a parser for the YAML subset they use, so the tests
need no YAML package: block mappings and sequences, double-quoted strings,
`true`, `false`, integers, plain words and `|` literal blocks. A form that
leaves the subset fails here instead of being read wrongly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.test_text_rules import violations

REPO_ROOT = Path(__file__).resolve().parent.parent
FORMS_DIR = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
LABELS_FILE = REPO_ROOT / ".github" / "labels.yml"

QUESTION_TYPES = {"dropdown", "checkboxes", "input", "textarea"}
CLOSED_TYPES = {"dropdown", "checkboxes"}
ID = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
COMPLIANCE = re.compile(r"\b(compliant|complies)\b", re.IGNORECASE)
REQUIRED_NOTE = (
    "Only the questions marked required must be answered; answer the others when they apply."
)

# The two blocks of AI_ASSISTANCE.md that every form and template carries.
AI_IDS = [
    "ai_used",
    "ai_purposes",
    "ai_provider",
    "ai_developer",
    "ai_product_version",
    "ai_model",
    "ai_model_version_date",
    "ai_access",
    "ai_location",
    "ai_further",
    "ai_content_given",
    "ai_share",
    "ai_review",
    "ai_verification",
    "ai_terms",
    "ai_reproduction",
]
DP_IDS = [
    "dp_personal_data",
    "dp_special_categories",
    "dp_ai_personal_data",
    "dp_ai_system_scope",
    "dp_ai_content_public",
    "dp_ai_act_article5",
    "dp_tdm_reservation",
    "dp_acknowledgement",
]
REQUIRED_IDS = [
    "ai_used",
    "ai_provider",
    "ai_developer",
    "ai_product_version",
    "ai_model",
    "ai_model_version_date",
    "dp_personal_data",
    "dp_acknowledgement",
]
ACKNOWLEDGEMENTS = [
    "I have read AI_ASSISTANCE.md and disclosed every AI-assisted system I used",
    "I have not posted personal data of anyone else, nor any special category of personal data "
    "(GDPR Articles 4(1) and 9)",
    "I have not given credentials, personal data or confidential partner material to an "
    "AI-assisted system",
    "I have read the transparency rule for AI-generated content in AI_ASSISTANCE.md, which "
    "follows the purpose of EU AI Act Article 50",
    "I understand that I am responsible for every line I submit",
]


def parse_yaml_subset(text: str) -> Any:
    """Parse the YAML subset of the forms; raise ValueError on anything else."""
    raw = text.split("\n")
    lines: list[tuple[int, int, str]] = []
    for number, line in enumerate(raw, 1):
        if line.strip() and not line.lstrip().startswith("#"):
            lines.append((number, len(line) - len(line.lstrip(" ")), line.strip()))

    def scalar(token: str, number: int) -> Any:
        if token.startswith('"'):
            try:
                return json.loads(token)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {number}: bad quoted string") from exc
        if token in {"true", "false"}:
            return token == "true"
        if re.fullmatch(r"-?\d+", token):
            return int(token)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", token):
            return token
        raise ValueError(f"line {number}: unsupported scalar {token!r}")

    def literal(start: int, number: int, indent: int) -> tuple[str, int]:
        # the raw lines after the `|` line, up to the first line indented at or below `indent`
        body: list[str] = []
        k = number
        block_indent: int | None = None
        while k < len(raw):
            line = raw[k]
            if line.strip():
                width = len(line) - len(line.lstrip(" "))
                if width <= indent:
                    break
                block_indent = width if block_indent is None else block_indent
                body.append(line[block_indent:])
            else:
                body.append("")
            k += 1
        while body and not body[-1]:
            body.pop()
        consumed = start
        while consumed < len(lines) and lines[consumed][0] <= k:
            consumed += 1
        return "\n".join(body) + "\n", consumed

    def node(i: int, indent: int) -> tuple[Any, int]:
        if lines[i][2].startswith("- "):
            return sequence(i, indent)
        return mapping(i, indent)

    def value_after(rest: str, i: int, indent: int, number: int) -> tuple[Any, int]:
        if rest == "|":
            return literal(i + 1, number, indent)
        if rest:
            return scalar(rest, number), i + 1
        if i + 1 < len(lines) and lines[i + 1][1] > indent:
            return node(i + 1, lines[i + 1][1])
        if i + 1 < len(lines) and lines[i + 1][1] == indent and lines[i + 1][2].startswith("- "):
            return sequence(i + 1, indent)
        raise ValueError(f"line {number}: key without a value")

    def mapping(i: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while i < len(lines) and lines[i][1] == indent and not lines[i][2].startswith("- "):
            number, _, content = lines[i]
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?", content)
            if not match:
                raise ValueError(f"line {number}: expected a key")
            key, rest = match.group(1), (match.group(2) or "").strip()
            if key in result:
                raise ValueError(f"line {number}: duplicate key {key}")
            result[key], i = value_after(rest, i, indent, number)
        if i < len(lines) and lines[i][1] > indent:
            raise ValueError(f"line {lines[i][0]}: unexpected indentation")
        return result, i

    def sequence(i: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while i < len(lines) and lines[i][1] == indent and lines[i][2].startswith("- "):
            number, _, content = lines[i]
            rest = content[2:].strip()
            if re.match(r"[A-Za-z_][A-Za-z0-9_-]*:( |$)", rest):
                # a mapping that starts on the dash line: read it at the inner indent
                lines[i] = (number, indent + 2, rest)
                item, i = mapping(i, indent + 2)
                result.append(item)
            else:
                result.append(scalar(rest, number))
                i += 1
        return result, i

    if not lines:
        raise ValueError("empty file")
    data, end = node(0, lines[0][1])
    if end != len(lines):
        raise ValueError(f"line {lines[end][0]}: unexpected content")
    return data


def form_files() -> list[Path]:
    return sorted(p for p in FORMS_DIR.glob("*.yml") if p.name != "config.yml")


def load(path: Path) -> Any:
    return parse_yaml_subset(path.read_text(encoding="utf-8"))


def questions(form: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in form["body"] if item["type"] in QUESTION_TYPES]


def by_id(form: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in questions(form)}


def is_required(item: dict[str, Any]) -> bool:
    if item["type"] == "checkboxes":
        options = item["attributes"]["options"]
        return all(option.get("required") is True for option in options)
    return item.get("validations", {}).get("required") is True


FORMS = form_files()


def test_parser_reads_the_subset() -> None:
    text = (
        "# comment\n"
        'name: "A"\n'
        "labels:\n"
        '  - "bug"\n'
        "body:\n"
        "  - type: markdown\n"
        "    attributes:\n"
        "      value: |\n"
        "        ### 1. Title\n"
        "\n"
        "        Text.\n"
        "  - type: input\n"
        "    id: x\n"
        "    validations:\n"
        "      required: true\n"
    )
    assert parse_yaml_subset(text) == {
        "name": "A",
        "labels": ["bug"],
        "body": [
            {"type": "markdown", "attributes": {"value": "### 1. Title\n\nText.\n"}},
            {"type": "input", "id": "x", "validations": {"required": True}},
        ],
    }
    for bad in ["key: 'single'\n", "a: [1, 2]\n", "a: 1\na: 2\n", "- x\n  y: 1\n"]:
        with pytest.raises(ValueError):
            parse_yaml_subset(bad)


def test_there_is_a_form_for_every_kind_of_issue() -> None:
    assert len(FORMS) == 19
    assert all(re.fullmatch(r"\d{2}_[a-z_]+\.yml", p.name) for p in FORMS)


@pytest.mark.parametrize("path", FORMS, ids=lambda p: p.name)
def test_form_follows_the_schema_and_the_question_rules(path: Path) -> None:
    form = load(path)
    for key in ("name", "description", "body"):
        assert form.get(key), f"{key} is missing"
    assert len(form["name"]) > 3
    items = questions(form)
    assert 50 <= len(items) <= 60, f"{len(items)} questions"
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids)), "ids are not unique"
    labels = [item["attributes"]["label"] for item in items]
    assert len(labels) == len(set(labels)), "labels are not unique"
    for item in items:
        attributes = item["attributes"]
        where = item["id"]
        assert ID.match(where), f"{where}: id is not lower_snake_case"
        assert attributes.get("label", "").strip(), f"{where}: no label"
        assert attributes.get("description", "").strip(), f"{where}: no description"
        if item["type"] in CLOSED_TYPES:
            options = attributes.get("options", [])
            assert len(options) >= 2, f"{where}: fewer than two options"
            labels = [o["label"] if isinstance(o, dict) else o for o in options]
            assert len(labels) == len(set(labels)), f"{where}: options are not distinct"
            assert all(str(label).strip() for label in labels), f"{where}: empty option"
        else:
            assert "options" not in attributes, f"{where}: an open question has options"
    first = form["body"][0]
    assert first["type"] == "markdown"
    assert REQUIRED_NOTE in first["attributes"]["value"]
    assert "SECURITY.md" in first["attributes"]["value"]
    required = sum(is_required(item) for item in items)
    assert 6 <= required <= 11, f"{required} required questions"


@pytest.mark.parametrize("path", FORMS, ids=lambda p: p.name)
def test_form_sections_are_numbered(path: Path) -> None:
    headings = [
        item["attributes"]["value"].split("\n", 1)[0]
        for item in load(path)["body"][1:]
        if item["type"] == "markdown"
    ]
    numbers = [int(m.group(1)) for h in headings if (m := re.match(r"^### (\d+)\. \S", h))]
    assert numbers == list(range(1, len(headings) + 1)), headings


def test_every_label_is_listed(repo_root: Path) -> None:
    labels = parse_yaml_subset(LABELS_FILE.read_text(encoding="utf-8"))
    names = [label["name"] for label in labels]
    assert len(names) == len(set(names))
    for label in labels:
        assert re.fullmatch(r"[0-9a-f]{6}", label["color"]), label
        assert label["description"].strip(), label
    used = {name for path in FORMS for name in load(path).get("labels", [])}
    assert used <= set(names), sorted(used - set(names))
    assert set(names) <= used, sorted(set(names) - used)


def test_config_disables_blank_issues() -> None:
    config = parse_yaml_subset((FORMS_DIR / "config.yml").read_text(encoding="utf-8"))
    assert config["blank_issues_enabled"] is False
    for link in config["contact_links"]:
        assert link["name"].strip() and link["about"].strip()
        assert link["url"].startswith("https://")


def test_ai_and_data_protection_blocks_are_the_same_everywhere() -> None:
    reference = by_id(load(FORMS[0]))
    for path in FORMS:
        found = by_id(load(path))
        for qid in AI_IDS + DP_IDS:
            assert qid in found, f"{path.name}: {qid} is missing"
            assert found[qid] == reference[qid], f"{path.name}: {qid} differs from {FORMS[0].name}"
        for qid in REQUIRED_IDS:
            assert is_required(found[qid]), f"{path.name}: {qid} must be required"
    options = [o["label"] for o in reference["dp_acknowledgement"]["attributes"]["options"]]
    assert options == ACKNOWLEDGEMENTS


@pytest.mark.parametrize("path", [*FORMS, FORMS_DIR / "config.yml", LABELS_FILE], ids=str)
def test_form_text_rules(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# This Source Code Form is subject to the terms of the Mozilla Public")
    assert not violations(text)
    assert not COMPLIANCE.search(text)
