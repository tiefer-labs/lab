<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Markdown standard

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The Markdown standard for every Tiefer repository: headers, characters and voice, structure, formatting, numbers, model cards, images and tables.

---

## 1. Header of every Markdown file

Every Markdown file starts with the header image, then the title and a status line. Image paths are relative to the file (from `docs/` use `assets/...`, from a subfolder such as `hpc/roihu/` use `../../docs/assets/...`):

```html
<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">
```

The header is in brand blue and is the same in GitHub's light and dark mode; do not add a second variant.

```markdown
# Title in sentence case

Status: draft | in development | in use | superseded. Owner: Tiefer. Licence: MPL 2.0.

One or two sentences that say what this document is for.

---
```

Exceptions: `LICENSE` has no header. Files that a script generates (for example `reports/acceptance.md` and `reports/experiments.md`) get the header from the generator.

---

## 2. Characters and voice

- No em dash and no U+2015. No emoji, no decorative symbols, no U+FE0F. Status is written in words: "in progress", "done", "not measured".
- The en dash is used only where it is strictly required, and sparingly: in a range of numbers, dates or times (`2026–2028`, `pages 12–18`), or between two names of equal weight (`Baku–Helsinki link`), always without spaces around it. Never as a pause or sentence dash; use a comma, colon or full stop there. When a plain hyphen is clear enough, use the hyphen.
- Plain, precise English, British spelling (`licence`, `quantise`, `analyse`). Short sentences, one idea per paragraph.
- Facts over adjectives. Every number has a unit and a source (a script, a report file or a cited document).
- No hype words: revolutionary, cutting-edge, game-changing, AI-powered, seamless, unlock, leverage, empower, magic.
- "On board" is the adverb, "onboard" the adjective. Dates are written `1 October 2026`.

---

## 3. Structure

- One `#` heading per file; `##` for sections, `###` for subsections; never skip a level.
- Number sections in specifications and long documents (`## 1. Data`), not in short READMEs.
- Separate major parts with `---`. Long documents end with "Changelog" (newest first, one line per change).

---

## 4. README files

The root `README.md`: header image, one sentence saying what the repository is, a plain link row (website, specification, results, licence; no badges loaded from third-party services), then About, Status, Quick start, Repository layout, Documentation, Principles, Licence, Contact. Security and contributing link to `https://github.com/tiefer-labs/.github`.

A README inside a folder (`hpc/roihu/`, `jetson/`, `models/cloud-filter/`, `reports/`, `reports/jetson/`): header image, title, status line, purpose, Requirements, Steps (copy-ready commands), Files (table), Troubleshooting (table: symptom, cause, fix) where useful.

---

## 5. Formatting

- Commands, file names, variables and configuration keys in backticks.
- Code blocks always name their language (`bash`, `python`, `toml`, `text`). Commands are copy-ready: no `$` prompt, one command per line, placeholders in angle brackets (`<run-id>`).
- Tables for anything compared across rows, written as plain Markdown tables (section 9).
- Numbered lists when order matters, bullets otherwise, at most two levels.
- Bold at most once per paragraph, for the one phrase a reader must not miss. No italics for emphasis.
- Relative links inside the repository, absolute links to other repositories.
- GitHub alerts (`> [!NOTE]`) sparingly, at most one per section.

---

## 6. Numbers and results

- Every result table names its source file in `reports/` and the git commit that produced it. A table may name its source with a short key instead, when the full path of each report file and its commit are listed once in an appendix of the same document.
- A space between number and unit (`12.4 ms`). Confidence intervals in brackets: `0.83 [0.81, 0.85]`. State the rounding rule once per document; never round to flatter a result.

---

## 7. Model cards and results pages

- `models/cloud-filter/<version>/MODEL_CARD.md`: Summary table (task, input, output, parameters, operations, formats, training run and commit, date), Intended use, Out of scope, Training data, Evaluation (table with sources), Quantisation (table), Hardware measurements (table, "not measured" where empty), Limitations, Files (table of SHA-256 hashes), Changelog. A note says the model files are not distributed in this repository.
- `docs/RESULTS.md` (written by hand): Summary, How to read this page, Runs, Environment and provenance, Data, results by topic (each table with sources), Quantisation, Hardware, Compute used, Training notes, Limitations, How to reproduce, Values to verify and values pending, an appendix of report files, Changelog.

---

## 8. Images

- Only the files in `docs/assets/` are used. They are never edited, redrawn, recoloured or stretched, and no other variants are made. Every image has meaningful alt text.
- Any future image in Tiefer's style uses brand blue `#0C003D` as background and one typeface, Mozilla Headline, for all of its text.
- The repository banner is set by the founder in GitHub's "Social preview" setting. It is not part of the repository and not referenced in Markdown.

---

## 9. Tables

Every table is a plain GitHub Markdown table. It renders the same on github.com, on Hugging Face and on the website, in light and dark mode, and it stays readable as plain text. HTML tables, inline styles and colours are not used: GitHub removes inline styles, so a styled table looks different on every site.

Tables written by scripts (for example `reports/acceptance.md` and `reports/experiments.md`) are produced by one shared helper, `markdown_table` in `src/tiefer_lab/tables.py`, so every generated table is identical. Tables written by hand, such as those of `docs/RESULTS.md` and the model cards, follow the same pattern.

Pattern (one category row and one data row shown; repeat as needed):

```markdown
|  | Column A | Column B |
| :--- | :---: | :---: |
| **Category** | | |
| Row name | 82.3 | 79.6 |
```

Rules:

- The first column is left-aligned (`:---`), all other columns are centred (`:---:`).
- The top-left header cell is empty when the first column holds row names; otherwise it names the column.
- Category rows are optional and group the rows below them: the category in bold in the first cell, the other cells empty. Leave them out when a table has no groups.
- A missing value is written `not measured` (never measured), `pending` (measured, but the report file is not yet in the repository) or `n/a` (the measure does not apply), never left empty. Category rows are the only rows with empty cells.
- Cells hold one line each. Inline code and links are allowed; a `|` inside a cell is written `\|`.
- No bold numbers and no highlighting of "best" values.
- Leave one empty line before and after a table.

---

## Changelog

- 7 October 2026: `docs/RESULTS.md` is written by hand; a table may use short source keys listed in an appendix (section 6); `pending` marks a measured value whose report file is not yet in the repository (section 9).
- 1 October 2026: tables are plain Markdown tables; the HTML house table style with inline colours is removed, because GitHub removes inline styles.
- 1 October 2026: first version, written for milestone L1 of Tiefer Lab.
