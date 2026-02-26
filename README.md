# ISPRAS Proceedings Paper Template

[![Build Paper](https://github.com/evdenis/ispras-paper-template/actions/workflows/paper.yml/badge.svg)](https://github.com/evdenis/ispras-paper-template/actions/workflows/paper.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

This repository is a template for writing ISPRAS Proceedings papers in Markdown with automatic conversion to DOCX.

## Overview

This project uses [ispras/proceedings-md](https://github.com/ispras/proceedings-md) for automatic conversion of markdown to docx format that follows the ISPRAS proceedings design requirements.

## Building the Paper

### Prerequisites

To build the paper locally, you need:

- Node.js
- Pandoc
- Git
- hunspell with `en_US` and `ru_RU` dictionaries (`sudo apt install hunspell hunspell-en-us hunspell-ru`)
- Java 17+ and [LanguageTool](https://languagetool.org/download/) CLI JAR (for `make grammar`)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/evdenis/ispras-paper-template.git
   cd ispras-paper-template
   ```

2. Clone the proceedings-md repository (required for the conversion process):
   ```bash
   git submodule update --init
   cd proceedings-md
   npm install
   ```

### Available Make Targets

| Target | Description |
|---|---|
| `make build` | Build `paper.docx` from `paper.md` |
| `make open` | Build and open `paper.docx` (requires `xdg-open`) |
| `make clean` | Remove generated files |
| `make setup` | Initialize submodule and install npm dependencies |
| `make watch` | Auto-rebuild on `paper.md` changes (requires `inotifywait`) |
| `make lint` | Run markdownlint on `paper.md` |
| `make spell` | Run hunspell spell checker on `paper.md` |
| `make grammar` | Run LanguageTool grammar checker on `paper.md` (requires Java + LanguageTool JAR) |
| `make check-links` | Validate links in `paper.md` |
| `make count` | Word count of paper body (excluding YAML frontmatter) |
| `make validate` | Run `lint` + `spell` + `check-links` + `grammar` together |
| `make help` | Print all available targets with descriptions |

Example:
```bash
make setup   # first-time setup
make build   # build the paper
```

## Downloading the Latest Build

This repository is configured with GitHub Actions to automatically build the paper when changes are made to `paper.md`. To download the latest build:

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

1. Edit the `paper.md` file
2. Commit and push your changes
3. GitHub Actions will automatically build the updated document
4. Download the new version following the steps above

## YAML Frontmatter Reference

The `ispras_templates:` block in `paper.md` supports the following fields:

| Field | Required | Description |
|---|---|---|
| `header_ru` / `header_en` | Yes | Paper title in Russian / English |
| `authors` | Yes | List of authors (see below) |
| `organizations_ru` / `organizations_en` | Yes | Affiliated organizations |
| `abstract_ru` / `abstract_en` | Yes | Paper abstract in Russian / English |
| `keywords_ru` / `keywords_en` | Yes | Comma-separated keywords. Use `@none` to omit |
| `links` | Yes | Numbered references list |
| `for_citation_ru` / `for_citation_en` | Yes | Citation string |
| `page_header_ru` / `page_header_en` | Yes | Running page header. Use `@use_citation` to reuse citation string |
| `acknowledgements_ru` / `acknowledgements_en` | No | Acknowledgements section |

Each author entry supports: `name_ru`, `name_en`, `orcid`, `email`, `details_ru`, `details_en`.

## Supported Features

The converter supports the following Markdown extensions:

- **Images with captions** — `<div class="img-caption">` for bilingual captions
- **Tables with captions** — `<div class="table-caption">` for bilingual captions
- **Code listings with captions** — `<div class="listing-caption">` for bilingual captions
- **Math formulas** — LaTeX via `$$...$$` blocks
- **Nested lists** — use `<!-- ListMode -->` comments to switch list rendering mode
- **In-text citations** — `[1]`, `[2, 3]` reference links
- **Bilingual content** — full Russian/English support for all metadata fields

For a complete example, see `proceedings-md/sample/sample.md`.

## Troubleshooting

- **Pandoc not found** — install Pandoc: `sudo apt install pandoc` or see [pandoc.org](https://pandoc.org/installing.html)
- **Word shows corruption warning** — this is a known false alarm; click "Yes" to open the file (see [proceedings-md README](https://github.com/ispras/proceedings-md#readme))
- **Submodule not initialized** — run `make setup` or `git submodule update --init`
- **inotifywait not found** — install `inotify-tools`: `sudo apt install inotify-tools` (needed for `make watch`)
- **hunspell not found** — install hunspell with dictionaries: `sudo apt install hunspell hunspell-en-us hunspell-ru`
- **LanguageTool JAR not found** — download from [languagetool.org](https://languagetool.org/download/LanguageTool-stable.zip), unzip, and either place `languagetool-commandline.jar` in the project root or pass the path: `make grammar LANGUAGETOOL_JAR=/path/to/languagetool-commandline.jar`

## About ISPRAS Proceedings

The Institute for System Programming of the Russian Academy of Sciences (ISPRAS) Proceedings is a collection of academic papers and research articles. This paper follows the required formatting guidelines through the automated conversion process.
