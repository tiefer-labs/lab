<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Markdown standard

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

The Markdown standard for every Tiefer repository: headers, characters and voice, structure, formatting, numbers, model cards, images and the house table style.

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

Exceptions: `LICENSE` has no header. Files that a script generates (for example `docs/RESULTS.md`) get the header from the generator.

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
- Tables for anything compared across rows, written in the house table style (section 9).
- Numbered lists when order matters, bullets otherwise, at most two levels.
- Bold at most once per paragraph, for the one phrase a reader must not miss. No italics for emphasis.
- Relative links inside the repository, absolute links to other repositories.
- GitHub alerts (`> [!NOTE]`) sparingly, at most one per section.

---

## 6. Numbers and results

- Every result table names its source file in `reports/` and the git commit that produced it.
- A space between number and unit (`12.4 ms`). Confidence intervals in brackets: `0.83 [0.81, 0.85]`. State the rounding rule once per document; never round to flatter a result.

---

## 7. Model cards and results pages

- `models/cloud-filter/<version>/MODEL_CARD.md`: Summary table (task, input, output, parameters, operations, formats, training run and commit, date), Intended use, Out of scope, Training data, Evaluation (table with sources), Quantisation (table), Hardware measurements (table, "not measured" where empty), Limitations, Files (table of SHA-256 hashes), Changelog. A note says the model files are not distributed in this repository.
- `docs/RESULTS.md` (generated): Summary, Environment, Data, Model, Baselines and model (table with sources), Pixel and frame metrics, Quantisation, Hardware, Compute used, Limitations, How to reproduce, Changelog.

---

## 8. Images

- Only the files in `docs/assets/` are used. They are never edited, redrawn, recoloured or stretched, and no other variants are made. Every image has meaningful alt text.
- Any future image in Tiefer's style uses brand blue `#0C003D` as background and one typeface, Mozilla Headline, for all of its text.
- The repository banner is set by the founder in GitHub's "Social preview" setting. It is not part of the repository and not referenced in Markdown.

---

## 9. House table style

Every table in a Markdown file is written as an HTML table in the house style below, in brand blue `#0C003D`: blue column headers with a blue rule, optional blue category rows that group the rows below them, light grey row lines, the first column left-aligned and indented, all other columns centred. Tables written by scripts (for example `docs/RESULTS.md` and model cards) use the same style, produced by one shared helper in `src/tiefer_lab/` so every generated table is identical.

Pattern (one category row and one data row shown; repeat as needed):

```html
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D"></th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Column A</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Column B</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Category</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Row name</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">82.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">79.6</td>
</tr>
</tbody>
</table>
</div>
```

Rules:

- `colspan` of a category row equals the number of columns. Leave out category rows when a table has no groups.
- The top-left header cell is empty when the first column holds row names; otherwise it names the column.
- Keep the colours exactly: `#0C003D` and `rgba(12, 0, 61, ...)` for headers and categories, `rgba(128, 128, 128, 0.15)` for row lines. No other colours, no bold numbers, no highlighting of "best" values.
- A missing value is written `not measured` (or `n/a` when the measure does not apply), never left empty.
- Leave one empty line before and after the HTML block, and no empty lines inside it, so Markdown renderers keep it as one block.
- Also give every `th` and `td` an `align` attribute (`align="left"` for the first column, `align="center"` for the others), because GitHub keeps `align` but removes inline `style` attributes when it renders Markdown. On github.com these tables therefore show as clean tables with the same structure (headers, category rows, alignment) but without the blue colours. The colours appear where inline styles are kept, such as Hugging Face pages and the website. This is expected; do not replace the tables with images to force the colours.

---

## Changelog

- 1 October 2026: first version, written for milestone L1 of Tiefer Lab.
