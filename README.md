# ISPRAS Proceedings Paper Template

[![Build Paper](https://github.com/evdenis/ispras-paper-template/actions/workflows/paper.yml/badge.svg)](https://github.com/evdenis/ispras-paper-template/actions/workflows/paper.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

This repository is a template for writing ISPRAS Proceedings papers in Markdown with automatic conversion to DOCX.

## Overview

This project uses [ispras/proceedings-md](https://github.com/ispras/proceedings-md) for automatic conversion of markdown to docx format that follows the ISPRAS proceedings design requirements.

## Building the Paper

### Prerequisites

#### Core (required for `make build`)

| Software | Version | Install (macOS) | Install (Debian/Ubuntu) |
|---|---|---|---|
| Git | any recent | Xcode Command Line Tools (`xcode-select --install`) | `sudo apt install git` |
| Node.js | 22+ | `brew install node` or `nvm install 22` | [nodesource.com](https://github.com/nodesource/distributions) or `nvm install 22` |
| npm | bundled with Node.js | — | — |
| Pandoc | any recent | `brew install pandoc` | `sudo apt install pandoc` or [pandoc.org](https://pandoc.org/installing.html) |
| Make | any | Xcode Command Line Tools (`xcode-select --install`) | `sudo apt install make` |

#### PDF generation (`make pdf`)

| Software | Version | Install (macOS) | Install (Debian/Ubuntu) |
|---|---|---|---|
| LibreOffice | any recent | `brew install --cask libreoffice` | `sudo apt install libreoffice` |

#### Validation (`make validate`)

| Software | Version | Install (macOS) | Install (Debian/Ubuntu) | Used by |
|---|---|---|---|---|
| Python | 3.11+ | Preinstalled, or `brew install python` | `sudo apt install python3` | `make test-layout` |
| hunspell | any recent | `brew install hunspell` (then install dictionaries below) | `sudo apt install hunspell hunspell-en-us hunspell-ru` | `make spell` |
| Java (JRE/JDK) | 17+ | Included by `brew install languagetool`, or `brew install openjdk@17` | `sudo apt install openjdk-17-jre` | `make grammar` with a standalone JAR |
| [LanguageTool](https://languagetool.org/download/) | stable | `brew install languagetool` | Download and unzip [LanguageTool-stable.zip](https://languagetool.org/download/LanguageTool-stable.zip) | `make grammar` |
| markdownlint-cli2 | latest | runs via npx (no global install needed) | runs via npx (no global install needed) | `make lint` |
| markdown-link-check | latest | runs via npx (no global install needed) | runs via npx (no global install needed) | `make check-links` |

#### Optional

| Software | Version | Install (macOS) | Install (Debian/Ubuntu) | Used by |
|---|---|---|---|---|
| ghostscript | any | `brew install ghostscript` | `sudo apt install ghostscript` | `make optimize-pdf`, `make optimize-pdf-gs` |
| qpdf | any | `brew install qpdf` | `sudo apt install qpdf` | `make optimize-pdf`, `make optimize-pdf-qpdf` |
| pdftotext | any | `brew install poppler` | `sudo apt install poppler-utils` | Git diff for PDFs (see below) |
| [uv](https://docs.astral.sh/uv/) | any | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `make check-layout`, which runs `check_layout.py` with `pdfplumber` |

On macOS, Homebrew installs the Hunspell executable without dictionaries. Install the required English and Russian dictionaries in the user dictionary directory:

```bash
mkdir -p "$HOME/Library/Spelling"
curl -fL https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.aff -o "$HOME/Library/Spelling/en_US.aff"
curl -fL https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.dic -o "$HOME/Library/Spelling/en_US.dic"
curl -fL https://raw.githubusercontent.com/LibreOffice/dictionaries/master/ru_RU/ru_RU.aff -o "$HOME/Library/Spelling/ru_RU.aff"
curl -fL https://raw.githubusercontent.com/LibreOffice/dictionaries/master/ru_RU/ru_RU.dic -o "$HOME/Library/Spelling/ru_RU.dic"
printf 'hello\nпривет\nошипка\n' | hunspell -d en_US,ru_RU -l
```

The final command should print only `ошипка`.

> **LanguageTool JAR fallback:** On systems without the `languagetool` command, unzip the standalone archive into the project root, or pass a custom path: `make grammar LANGUAGETOOL_JAR=/path/to/languagetool-commandline.jar`.

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/evdenis/ispras-paper-template.git
   cd ispras-paper-template
   ```

2. Initialize the submodule and build the converter:
   ```bash
   make setup
   ```
   Or manually:
   ```bash
   git submodule update --init
   cd proceedings-md && npm install && npm run build
   ```

### Available Make Targets

| Target | Description |
|---|---|
| `make build` | Force a fresh `paper.docx` build from the current sources |
| `make pdf` | Force fresh DOCX and PDF builds using LibreOffice |
| `make open` | Force a fresh `paper.docx` build, then open it with the platform document opener |
| `make optimize-pdf` | Rebuild `paper.pdf`, then optimize with Ghostscript + qpdf |
| `make optimize-pdf-gs` | Rebuild `paper.pdf`, then optimize with Ghostscript |
| `make optimize-pdf-qpdf` | Rebuild `paper.pdf`, then optimize with qpdf |
| `make clean` | Remove generated files |
| `make setup` | Initialize submodule and install npm dependencies |
| `make watch` | Auto-rebuild on paper, bibliography, image, or converter changes |
| `make lint` | Run markdownlint on `paper.md` |
| `make check-sentence-lines` | Enforce one prose sentence per source line in `paper.md` |
| `make test-layout` | Unit-test the layout report |
| `make check-layout` | Rebuild `paper.pdf` and report page-breaking defects in it |
| `make spell` | Run hunspell spell checker on `paper.md` |
| `make grammar` | Run LanguageTool grammar checker on `paper.md` using its command or standalone JAR |
| `make check-links` | Validate links in `paper.md` |
| `make count` | Word count of paper body (excluding YAML frontmatter) |
| `make validate` | Run all source checks, including sentence-per-line validation |
| `make help` | Print all available targets with descriptions |

Platform commands can be overridden when installed in a non-standard location, for example: `make open OPENER=/path/to/opener`, `make pdf LIBREOFFICE=/path/to/soffice`, or `make grammar LANGUAGETOOL=/path/to/languagetool`.
The converter checkout defaults to `proceedings-md` and can be overridden with
`PROCEEDINGS_MD_DIR=/path/to/proceedings-md`. Both `make build` and `make watch`
track its TypeScript sources, build configuration, and DOCX reference template;
conversion goes through the converter's guarded `npm run convert` command.
The legacy `PROCEEDINGS_MD=/path/to/main.js` override remains supported for
prebuilt external converters, but cannot automatically compile their sources.
Public artifact targets (`make`, `make build`, `make pdf`, `make open`, and the
PDF optimization targets) intentionally force their upstream conversions even
when timestamps say the outputs are current. DOCX and PDF generation stage new
files before replacing the existing artifacts, so a failed conversion preserves
the last successful output and prevents downstream actions from using it as if
it were current.

Example:
```bash
make setup   # first-time setup
make build   # build the paper
```

## Downloading the Latest Build

This repository is configured with GitHub Actions to automatically build the
paper when its Markdown, bibliography, images, build configuration, or converter
revision changes. To download the latest build:

1. Go to the repository's GitHub page
2. Click on the "Actions" tab
3. Select the most recent successful workflow run
4. Scroll down to the "Artifacts" section
5. Click on the "paper" artifact to download the latest built version of the paper

The built document will be available as a ZIP file containing the paper.docx file.

## Viewing Changes in Binary Files (DOCX, PDF)

Git treats documents like DOCX and PDF files as binary by default, making it difficult to see the actual content changes. You can configure Git to show meaningful diffs for these files by adding the following to your `.gitconfig`:

```
[diff "docx"]
        binary=true
        textconv=pandoc --to=rst
[diff "pdf"]
        binary=true
        textconv=sh -c 'pdftotext -nopgbrk -enc UTF-8 -eol unix -layout "$0" -'
```

After setting this up, you can use regular git diff commands to see changes in the content of binary document files:

```bash
git diff -- paper.docx
```

This will show you the textual changes between different versions of your document, making it easier to track the evolution of your research paper.

## Modifying the Paper

To modify the paper:

1. Edit `paper.md` (content) and/or `bibliography.bib` (references)
2. Commit and push your changes
3. GitHub Actions will automatically build the updated document
4. Download the new version following the steps above

## YAML Frontmatter Reference

The `ispras_templates:` block in `paper.md` supports the following fields:

| Field | Required | Description |
|---|---|---|
| `header_ru` / `header_en` | Yes | Paper title in Russian / English |
| `authors` | Yes | List of authors (see below) |
| `organizations` | Yes | List of organizations with `id`, `name_ru`, `name_en` (see below) |
| `bibliography` | Yes | Path to a `.bib` file with BibTeX references (e.g., `bibliography.bib`) |
| `abstract_ru` / `abstract_en` | Yes | Paper abstract in Russian / English |
| `keywords_ru` / `keywords_en` | Yes | Comma-separated keywords. Use `@none` to omit |
| `for_citation_ru` / `for_citation_en` | No | Citation string (auto-generated from authors and title if omitted) |
| `page_header_ru` / `page_header_en` | No | Running page header (auto-generated from authors and title if omitted) |
| `acknowledgements_ru` / `acknowledgements_en` | No | Acknowledgements section |
| `typography` | No | Set to `false` to stop the converter from inserting non-breaking spaces (see [Typography](#typography)) |

Each **author** entry supports: `name_ru`, `name_en`, `orcid`, `email`, `organizations` (list of organization IDs), `details_ru`, `details_en`.

Each **organization** entry has: `id` (unique key), `name_ru` (string or list of strings), `name_en` (string or list of strings). Authors reference organizations by `id`. Multi-line names are supported via YAML arrays.

## Supported Features

The converter supports the following Markdown extensions:

- **Images with captions** — fenced div `::: img-caption` for bilingual captions
- **Tables with captions** — fenced div `::: table-caption` for bilingual captions
- **Code listings with captions** — fenced div `::: listing-caption` for bilingual captions
- **Image sizing** — `![](images/example.png){width="14cm"}`; ISPRAS limits figures to 14 cm
- **Auto-numbered references** — `@ref:fig:label`, `@ref:tab:label`, `@ref:lst:label`, usable both inside captions and in running prose
- **Bibliography** — BibTeX `.bib` file with `[@Key]` citations in text
- **Math formulas** — inline `$...$` and display `$$...$$`; wrap a display formula in `\begin{array}{r} ... \#(1) \end{array}` to get a right-aligned equation number
- **Lists** — bulleted, nested, and both ordered styles (`1.` and `1)`) work as plain Markdown, with no extra markup
- **Bilingual content** — full Russian/English support for all metadata fields
- **Typography** — the non-breaking spaces Russian typography requires are inserted during conversion (see below)

Caption placement matters: **figure** and **listing** captions go *after* the image or
code block, while **table** captions go *before* the table.

Captions are rendered by Pandoc, so they take the same inline markup as body text —
`**bold**`, `_italic_`, `` `code` ``, `$math$`, links — and a caption may span several
source lines.

For complete examples, see `proceedings-md/sample/sample.md` and
`proceedings-md/sample/test-features.md` (listings, formulas, lists), or the commented
example block in `paper.md`.

## Typography

Word breaks a line at any space. Russian typography does not allow that after a
one-letter preposition, between a reference word and its number, in front of a citation
or a dash, inside a numeric group or a name, or before the last short word of a
paragraph. The converter inserts the non-breaking spaces (U+00A0) itself, so `paper.md`
is written as ordinary prose (`_` below stands for the inserted space):

| Rule | Source | Result |
|---|---|---|
| citation | `подход [@kurmus2013]` | `подход_[12]` |
| abbreviation with a number | `на рис. 4`, `см. § 5`, `Fig. 4` | `на_рис._4` |
| reference word with a number | `в разделе 7`, `таблицы 3` | `в_разделе_7` |
| numeric group | `11 131`, `57 %`, `11,1 млн`, `± 0,05` | `11_131` |
| unit | `10 МБ`, `2007 г.` | `10_МБ` |
| initials | `В. П. Иванников`, `Ермаков М. К.` | `В._П._Иванников` |
| one-letter preposition | `в ядре`, `с учетом` | `в_ядре` |
| dash | `охват --- качество` | `охват_— качество` |
| hanging word | the last short word of a paragraph | `составляет_0,05.` |

The rules run on the Pandoc AST rather than on the text: they never look inside code,
formulas or link targets, and a paragraph ends where the paragraph really ends, not
where the source line does — so a pair split by a line break in `paper.md` is bound like
any other. Captions and table cells get every rule except the hanging-word one, because
their wrapping is decided by the column.

The text fields of the metadata — `abstract_*`, `keywords_*`, `header_*`, `details_*`,
`acknowledgements_*`, `for_citation_*`, `page_header_*`, and the `name_*` of authors and
organizations — are typeset by the same rules. An author name still becomes
«Иванов И.И.» in the running head.

A non-breaking space written by hand is kept and never doubled: in body text write a
backslash followed by a space, which Pandoc reads as U+00A0; in the metadata type the
character itself, as the address lines of `paper.md` do for «д. 25». To keep the spaces
of one fragment exactly as typed, or to switch the pass off for the whole document:

```markdown
[текст с обычными пробелами]{.no-typography}
```

```yaml
ispras_templates:
  typography: false
```

Page-breaking defects exist only in the rendered PDF, so they have their own target:

```bash
make check-layout
```

It reports white-space holes, tables split without a repeated header, captions separated
from their block, runt lines and forbidden line breaks. `make test-layout` unit-tests the
report itself and is part of `make validate`.

## Troubleshooting

- **Pandoc not found** — install Pandoc with `brew install pandoc` (macOS), `sudo apt install pandoc` (Debian/Ubuntu), or see [pandoc.org](https://pandoc.org/installing.html)
- **Word shows corruption warning** — this is a known false alarm; click "Yes" to open the file (see [proceedings-md README](https://github.com/ispras/proceedings-md#readme))
- **Submodule not initialized** — run `make setup` or `git submodule update --init`
- **File watcher not found** — install `fswatch` with `brew install fswatch` (macOS) or `inotify-tools` with `sudo apt install inotify-tools` (Debian/Ubuntu)
- **Hunspell or dictionaries not found** — follow the macOS dictionary steps above, or install `hunspell hunspell-en-us hunspell-ru` on Debian/Ubuntu
- **LanguageTool not found** — use `brew install languagetool` on macOS, or download the standalone archive and set `LANGUAGETOOL_JAR=/path/to/languagetool-commandline.jar`

## About ISPRAS Proceedings

The Institute for System Programming of the Russian Academy of Sciences (ISPRAS) Proceedings is a collection of academic papers and research articles. This paper follows the required formatting guidelines through the automated conversion process.
