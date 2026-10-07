<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Markdown standard

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The Markdown standard for every Tiefer repository: headers, characters and voice, vocabulary, structure, numbers, sources, identifiers, tables, images and the required sections of each document type, for documents and README files alike.

---

## 1. Scope

Sections 1 to 12 are the general Tiefer rules and apply to every Markdown file in every Tiefer repository: documents, README files, model cards and generated pages. Section 13, "This repository", holds the parts that only apply to Tiefer Lab: the table helper in `src/tiefer_lab/tables.py`, the parsing of [docs/DEPENDENCIES.md](DEPENDENCIES.md) by `src/tiefer_lab/sbom.py`, the files in `docs/assets/` and the report folders.

A document can be checked against this standard section by section; `tests/test_markdown_style.py` and `tests/test_text_rules.py` check the parts that a script can check.

---

## 2. Header of every Markdown file

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

Exceptions: `LICENSE` has no header. Files that a script generates (for example `reports/acceptance.md`, `reports/experiments.md` and `reports/test_log.md`) get the header from the generator.

---

## 3. Characters, spelling and voice

- No em dash and no U+2015. No emoji, no decorative symbols, no U+FE0F.
- The en dash is used only where it is strictly required, and sparingly: in a range of numbers, dates or times (`2026–2028`, `pages 12–18`), or between two names of equal weight (`Baku–Helsinki link`), always without spaces around it. Never as a pause or sentence dash; use a comma, colon or full stop there. When a plain hyphen is clear enough, use the hyphen.
- Plain, precise English, British spelling (`licence`, `quantise`, `analyse`, `normalise`). Short sentences, one idea per paragraph.
- Spelling exceptions, kept as they are written by their owners: the proper name "Mozilla Public License", the `license` keys of `pyproject.toml` and `CITATION.cff`, SPDX identifiers (`MPL-2.0`, `CC-BY-4.0`), GitHub's term "artifact", and quoted titles of documents and papers.
- Facts over adjectives. No hype words: revolutionary, cutting-edge, game-changing, AI-powered, seamless, unlock, leverage, empower, magic. No adjectives that rank another organisation's system.
- "On board" is the adverb, "onboard" the adjective. "On-board" is not used, except inside a quoted title.
- Dates are written `1 October 2026`.

---

## 4. Vocabulary

One word for each state, defined here once. Other documents link to this table instead of defining the words again.

| Word | Meaning | Where it is allowed |
| :--- | :---: | :---: |
| **Document status line** | | |
| `draft` | written, not yet reviewed or not yet complete | status line of any document |
| `in development` | in use and still changing with the work it describes | status line of any document |
| `in use` | complete for its purpose; changes are recorded in the changelog | status line of any document |
| `superseded` | replaced; the document names its successor | status line of any document |
| **Missing values** | | |
| `not measured` | never measured | any table cell or sentence |
| `pending` | measured, but the value or its report file is not yet in the repository | any table cell or sentence; the document says which file will fill it |
| `n/a` | the measure or field does not apply | any table cell |
| **Requirement status** | | |
| `met`, `not met` | judged against the minimum unless the row says target | requirements matrix |
| `pending`, `not measured` | as for missing values | requirements matrix |
| **Standards status** | | |
| `met`, `partly`, `not met` | self-assessed against clauses that were read | standards matrix |
| `not applicable` | the clause does not apply to this repository | standards matrix only |
| `not read` | the document has not been read yet | standards matrix |
| `no document` | no standard was chosen or found for the area | standards matrix |
| **Assumption status** | | |
| `open`, `confirmed`, `revisit due`, `superseded` | open: not yet tested; confirmed: tested, with evidence; revisit due: the trigger has happened; superseded: replaced by another row | assumptions log |
| **Plan step status** | | |
| `done`, `not run`, `changed` | changed: ran with settings other than planned | plan |
| **Component status** | | |
| `done`, `measured`, `not measured`, `not run`, `draft` | state of a component of the repository | README status tables |

"Not yet measured" and "not applicable" outside the standards matrix are not used; write `not measured` or `n/a`.

---

## 5. Structure, numbering and changelog

- One `#` heading per file; `##` for sections, `###` for subsections; never skip a level.
- Numbered sections (`## 1. Title`) in every file in `docs/`, in plans and in model cards; not in README files and not in `NOTICE.md`. Sections are numbered 1, 2, 3; a lettered section (`2A`, `5A`) is not used: renumber instead and fix every link to the renumbered sections.
- Appendices come after the numbered sections and are headed `## Appendix A. <name>`.
- Separate major parts with `---`.
- Every Markdown file ends with `## Changelog`, except `LICENSE` and append-only logs such as `reports/test_log.md`. Each line is exactly `- D Month YYYY: text`, one change per line, newest first; several lines on the same day are allowed, the most recent first. Old lines are never edited; a correction is a new line.

---

## 6. Formatting

- Commands, file names, variables and configuration keys in backticks.
- Code blocks always name their language (`bash`, `python`, `toml`, `text`). Commands are copy-ready: no `$` prompt, one command per line, placeholders in angle brackets (`<run-id>`).
- Tables for anything compared across rows, written as plain Markdown tables (section 10).
- Numbered lists when order matters, bullets otherwise, at most two levels.
- Bold at most once per paragraph, for the one phrase a reader must not miss. A bold label at the start of a list item (`**Filter:** ...`) is allowed. No italics for emphasis.
- Relative links inside the repository, absolute links to other repositories. The first mention of a repository file in a document is a link; later mentions are in backticks.
- GitHub alerts (`> [!NOTE]`) sparingly, at most one per section.

---

## 7. Numbers and units

- Rounding: 3 decimals, half up (0.0075 becomes 0.008), stated once per document. Never round to flatter a result, and never round a value twice without saying so.
- Fractions are written as fractions (0.720), not as percent, except where a threshold is named in words ("at 50 percent"). The word "percent" is written out; the sign `%` is not used in prose or tables.
- Thousands separators: commas in counts and sizes of 1,000 and more, in prose and in tables (8,490 patches, 993,280 bytes). No separators in identifiers, job IDs, years, commits, configuration values quoted from code, or code blocks.
- Data sizes in bytes, MiB or GiB (binary units). "GB" or "MB" is used only when a source states a decimal size, and then as the source wrote it.
- Times in UTC, with "UTC" written out (`3 October 2026, 09:39 UTC`); a local time is given only next to its UTC time. Durations as `hh:mm:ss`; CPU time as Slurm prints it. A table column of times or durations names its format in the header.
- A space between number and unit (`12.4 ms`). Confidence intervals in brackets: `0.83 [0.81, 0.85]`.
- Every measured or quoted value has a source (section 8); every physical quantity has a unit.

---

## 8. Sources and citations

Every value names where it comes from. The kinds of source and how each is written:

| Kind | Syntax | Rule |
| :--- | :---: | :---: |
| Report file | `reports/evaluation/<file>.json` | the file the value was copied from |
| Source key | `b0-val` | lowercase, hyphenated, defined once in an appendix of the same document (`## Appendix A. <name>`) with the full path and commit |
| Session notes | `notes` | temporary; every such value is listed in a "values to verify" table with its exit condition: the report file is copied into the repository and the value is checked against it |
| Log | `log` | Slurm or terminal output; the job ID is given next to it |
| Commit | `81ab34b03bcc` | 12-character hash |
| Cited document | `[n]` | numbered list at the end of the document |

- A source column uses one format: `key` or `key (kind)`, for example `b0-val (report)`. No prose in source cells; explanations go below the table.
- External sources are listed at the end of the document, numbered, each as "Title, publisher or authors, date, URL, accessed D Month YYYY". A source that could not be opened is not cited; the fact stays as it was, or is listed as an open fact.
- A published value of another organisation is labelled "published" and is never placed in a table of this repository's own measured values (section 12.8).

---

## 9. Identifiers and markers

- Run names: `l1_base s0` style (configuration and seed) in prose and tables; the full run ID is written once, in a runs table.
- Requirement IDs (`REQ-DAT-11`, `ACC-01`) and assumption IDs (`A-1.1`: section 1, row 1) are written in backticks. Standards are named by identifier and revision (`ECSS-E-ST-40C Rev.1`).
- `TODO(verify)` marks a fact that needs a source not yet read, and names what would resolve it. It is not used inside table cells: such facts are listed in an "Open facts" table (fact, what resolves it, where it is used).

---

## 10. Tables

Every table is a plain GitHub Markdown table. It renders the same on github.com, on Hugging Face and on the website, in light and dark mode, and it stays readable as plain text. HTML tables, inline styles and colours are not used: GitHub removes inline styles, so a styled table looks different on every site.

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
- A missing value is written with a word of section 4 (`not measured`, `pending`, `n/a`), never left empty. Category rows are the only rows with empty cells.
- Cells hold one line each. Inline code and links are allowed; a `|` inside a cell is written `\|`.
- At most eight columns where possible; split a wider table by topic or by split.
- No bold numbers and no highlighting of "best" values.
- Leave one empty line before and after a table.

---

## 11. Images

- Only the files in `docs/assets/` are used. They are never edited, redrawn, recoloured or stretched, and no other variants are made. Every image has meaningful alt text.
- Any future image in Tiefer's style uses brand blue `#0C003D` as background and one typeface, Mozilla Headline, for all of its text.
- The repository banner is set by the founder in GitHub's "Social preview" setting. It is not part of the repository and not referenced in Markdown.

---

## 12. Document types

Each document type has required sections, in this order. A document may add sections after the required ones.

### 12.1 Specification

`docs/SPEC.md`: purpose, principles, definition of done per milestone, one section per component, file tree, Makefile targets, continuous integration, changelog.

### 12.2 Results page

`docs/RESULTS.md`, written by hand: summary; how to read this page (rounding rule, source-key grammar, the words of section 4, metric definitions); runs; environment and provenance; data; results by topic, each table with a source column; quantisation; hardware; compute used; training notes; limitations; how to reproduce; values to verify and values pending; Appendix A of report files; changelog. Published values of other systems are not on this page.

### 12.3 Requirements matrix

`docs/REQUIREMENTS.md`: every requirement and acceptance target with columns ID, Requirement, Minimum, Target, Measured value, Run, Status, Evidence, and the verification that the traceability check reads. The meaning of each status is stated once.

### 12.4 Assumptions log

`docs/ASSUMPTIONS.md`: columns ID, Assumption, Reason, Evidence (a source, or "none, design choice"), Revisit when, Status (section 4), Last checked.

### 12.5 Data card

`docs/DATA.md`: the datasheet questions, each answered with a source: motivation, composition, collection and labelling, preprocessing by the dataset authors, preprocessing in this repository, uses, distribution, maintenance; then the facts the code depends on and the caches built.

### 12.6 Dataset catalogue

`docs/DATASETS.md`: one table with columns Dataset, Version or revision, Licence, URL, Role, Used by, Status, Checked on.

### 12.7 Dependency list

`docs/DEPENDENCIES.md`: direct dependencies with their range and locked version, CI-only tools, all locked packages, decisions, vulnerability audit. The section of all locked packages keeps the heading and three-column format that `src/tiefer_lab/sbom.py` parses (section 13).

### 12.8 Landscape page

`docs/LANDSCAPE.md`: published values of other systems only, each with its source and labelled "published"; a separate table of head-to-head status with this repository's values and their RESULTS.md sections. No comparative claim unless both systems were measured by this repository on the same data or the same hardware; otherwise the page names the measurement that would decide it.

### 12.9 Standards matrix

`docs/STANDARDS.md`: columns Identifier and revision, Title, Issue date, URL, Clause, Status, Evidence, Date read, Owner, Next review, and the status definitions of section 4.

### 12.10 Plan

`hpc/roihu/plan.md`: basis, budget, steps with status (`done`, `not run`, `changed`) and measured cost, next steps, open measurements. A plan that is replaced stays in the file, marked superseded, as the record.

### 12.11 Model card and template

`models/cloud-filter/<version>/MODEL_CARD.md` and `models/cloud-filter/MODEL_CARD_TEMPLATE.md`: Summary table (task, input, output, parameters, operations, formats, training run and commit, training settings, dataset revision and cache, selected model or not, weight licence, date), Intended use, Out of scope, Training data, Evaluation (table with split and source per row, commit per table), Quantisation (FP32, FP16 and INT8 rows with file size and change), Hardware measurements (latency p50 and p99, energy per tile; `not measured` where empty), Limitations, Files (SHA-256 of every file named, or an explicit exclusion), Changelog. The rounding rule is stated once. A note says the model files are not distributed in this repository and that no licence is granted for them.

### 12.12 Notice

`NOTICE.md`: licence of the repository, what the licence does not cover, third-party data and software, trademarks, changelog. No numbered sections.

### 12.13 Append-only log

`reports/test_log.md`: the header written by the code that appends to it, then the entries. No changelog; entries are never edited or removed.

### 12.14 README files

The root `README.md`: header image, one sentence saying what the repository is, a plain link row (website, specification, results, licence; no badges loaded from third-party services), then About, Status, Quick start, Repository layout, Documentation, Principles, Licence, Contact, Changelog. Security and contributing link to `https://github.com/tiefer-labs/.github`.

A README inside a folder (`hpc/roihu/`, `jetson/`, `models/cloud-filter/`, `reports/`, `reports/jetson/`): header image, title, status line, purpose, Requirements, Steps (copy-ready commands), Files (table), Troubleshooting (table: symptom, cause, fix) where useful, Changelog. Extra sections are allowed after Steps.

---

## 13. This repository

- **Table helper:** tables written by scripts (`reports/acceptance.md`, `reports/experiments.md`, the entries of `reports/test_log.md`) are produced by one shared helper, `markdown_table` in `src/tiefer_lab/tables.py`, so every generated table is identical. Tables written by hand follow the same pattern.
- **Dependency table:** `src/tiefer_lab/sbom.py` reads the licence of every locked package from the section headed exactly `## 3. All locked packages` of `docs/DEPENDENCIES.md`, from rows of three cells (package, version, licence). The heading and the row format change only together with `sbom.py` and `tests/test_sbom.py`.
- **Assets:** `docs/assets/` holds the header image and the logos (section 11). They are excluded from the character checks and from the MPL 2.0 grant ([NOTICE.md](../NOTICE.md)).
- **Report folders:** `reports/evaluation/`, `reports/export/`, `reports/compute/`, `reports/jetson/` and `reports/data/` hold report files copied unchanged from the machine that wrote them; `docs/RESULTS.md` names each one by a source key in its Appendix A.
- **Checks:** `tests/test_markdown_style.py` checks headers, status lines, heading levels, changelog lines and table layout; `tests/test_text_rules.py` checks characters and the forbidden hyphenated spelling of "onboard"; `tests/test_wording.py` checks compliance wording and the statuses of the standards matrix.

---

## Changelog

- 7 October 2026: section 12, the required sections of every document type.
- 7 October 2026: sections 8 and 9, source kinds and their syntax, cited documents, run names, identifiers and `TODO(verify)` only outside table cells.
- 7 October 2026: section 7, numbers and units: rounding half up, fractions, "percent", thousands separators, binary data sizes, UTC and durations.
- 7 October 2026: section 4, one vocabulary table for every status and missing-value word, with `no document` for the standards matrix.
- 7 October 2026: section 1, scope, and section 13, the repository-specific parts; numbered sections in every document, changelog rules and spelling exceptions in sections 3 and 5; sections renumbered.
- 7 October 2026: correction: the line below holds three changes of the same day, which are: `docs/RESULTS.md` is written by hand; a table may use short source keys listed in an appendix; `pending` marks a measured value whose report file is not yet in the repository.
- 7 October 2026: `docs/RESULTS.md` is written by hand; a table may use short source keys listed in an appendix (section 6); `pending` marks a measured value whose report file is not yet in the repository (section 9).
- 1 October 2026: tables are plain Markdown tables; the HTML house table style with inline colours is removed, because GitHub removes inline styles.
- 1 October 2026: first version, written for milestone L1 of Tiefer Lab.
