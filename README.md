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
| hunspell | any recent | `brew install hunspell` (then install dictionaries below) | `sudo apt install hunspell hunspell-en-us hunspell-ru` | `make spell` |
| Java (JRE/JDK) | 17+ | Included by `brew install languagetool`, or `brew install openjdk@17` | `sudo apt install openjdk-17-jre` | `make grammar` with a standalone JAR |
| [LanguageTool](https://languagetool.org/download/) | stable | `brew install languagetool` | Download and unzip [LanguageTool-stable.zip](https://languagetool.org/download/LanguageTool-stable.zip) | `make grammar` |
| markdownlint-cli2 | latest | runs via npx (no global install needed) | runs via npx (no global install needed) | `make lint` |
| markdown-link-check | latest | runs via npx (no global install needed) | runs via npx (no global install needed) | `make check-links` |

#### Optional

| Software | Version | Install (macOS) | Install (Debian/Ubuntu) | Used by |
|---|---|---|---|---|
| File watcher | any | `brew install fswatch` | `sudo apt install inotify-tools` | `make watch` |
| ghostscript | any | `brew install ghostscript` | `sudo apt install ghostscript` | `make optimize-pdf`, `make optimize-pdf-gs` |
| qpdf | any | `brew install qpdf` | `sudo apt install qpdf` | `make optimize-pdf`, `make optimize-pdf-qpdf` |
| pdftotext | any | `brew install poppler` | `sudo apt install poppler-utils` | Git diff for PDFs (see below) |

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
| `make build` | Build `paper.docx` from `paper.md` |
| `make pdf` | Build `paper.pdf` from `paper.docx` using LibreOffice |
| `make open` | Build and open `paper.docx` using the platform document opener |
| `make optimize-pdf` | Optimize `paper.pdf` with Ghostscript + qpdf pipeline (reduces file size) |
| `make optimize-pdf-gs` | Optimize `paper.pdf` with Ghostscript only |
| `make optimize-pdf-qpdf` | Optimize `paper.pdf` with qpdf only |
| `make clean` | Remove generated files |
| `make setup` | Initialize submodule and install npm dependencies |
| `make watch` | Auto-rebuild on `paper.md` / `bibliography.bib` changes (requires `fswatch` or `inotifywait`) |
| `make lint` | Run markdownlint on `paper.md` |
| `make spell` | Run hunspell spell checker on `paper.md` |
| `make grammar` | Run LanguageTool grammar checker on `paper.md` using its command or standalone JAR |
| `make check-links` | Validate links in `paper.md` |
| `make count` | Word count of paper body (excluding YAML frontmatter) |
| `make validate` | Run `lint` + `spell` + `check-links` + `grammar` together |
| `make help` | Print all available targets with descriptions |

Platform commands can be overridden when installed in a non-standard location, for example: `make open OPENER=/path/to/opener`, `make pdf LIBREOFFICE=/path/to/soffice`, or `make grammar LANGUAGETOOL=/path/to/languagetool`.

Example:
```bash
make setup   # first-time setup
make build   # build the paper
```

## Downloading the Latest Build

This repository is configured with GitHub Actions to automatically build the paper when changes are made to `paper.md` or `bibliography.bib`. To download the latest build:

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

Each **author** entry supports: `name_ru`, `name_en`, `orcid`, `email`, `organizations` (list of organization IDs), `details_ru`, `details_en`.

Each **organization** entry has: `id` (unique key), `name_ru` (string or list of strings), `name_en` (string or list of strings). Authors reference organizations by `id`. Multi-line names are supported via YAML arrays.

## Supported Features

The converter supports the following Markdown extensions:

- **Images with captions** — fenced div `::: img-caption` for bilingual captions
- **Tables with captions** — fenced div `::: table-caption` for bilingual captions
- **Code listings with captions** — fenced div `::: listing-caption` for bilingual captions
- **Auto-numbered references** — `@ref:fig:label`, `@ref:tab:label`, `@ref:lst:label` for cross-references
- **Bibliography** — BibTeX `.bib` file with `[@Key]` citations in text
- **Math formulas** — LaTeX via `$$...$$` blocks
- **Nested lists** — use `<!-- ListMode -->` comments to switch list rendering mode
- **Bilingual content** — full Russian/English support for all metadata fields

For a complete example, see `proceedings-md/sample/sample.md`.

## Troubleshooting

- **Pandoc not found** — install Pandoc with `brew install pandoc` (macOS), `sudo apt install pandoc` (Debian/Ubuntu), or see [pandoc.org](https://pandoc.org/installing.html)
- **Word shows corruption warning** — this is a known false alarm; click "Yes" to open the file (see [proceedings-md README](https://github.com/ispras/proceedings-md#readme))
- **Submodule not initialized** — run `make setup` or `git submodule update --init`
- **File watcher not found** — install `fswatch` with `brew install fswatch` (macOS) or `inotify-tools` with `sudo apt install inotify-tools` (Debian/Ubuntu)
- **Hunspell or dictionaries not found** — follow the macOS dictionary steps above, or install `hunspell hunspell-en-us hunspell-ru` on Debian/Ubuntu
- **LanguageTool not found** — use `brew install languagetool` on macOS, or download the standalone archive and set `LANGUAGETOOL_JAR=/path/to/languagetool-commandline.jar`

## About ISPRAS Proceedings

The Institute for System Programming of the Russian Academy of Sciences (ISPRAS) Proceedings is a collection of academic papers and research articles. This paper follows the required formatting guidelines through the automated conversion process.
