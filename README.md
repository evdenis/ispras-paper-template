# ISPRAS Proceedings Paper Template

This repository contains research on various paper protections in OS and userspace applications for the ISPRAS Proceedings.

## Overview

This project uses [ispras/proceedings-md](https://github.com/ispras/proceedings-md) for automatic conversion of markdown to docx format that follows the ISPRAS proceedings design requirements.

## Building the Paper

### Prerequisites

To build the paper locally, you need:

- Node.js
- Pandoc
- Git

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

The following make targets are available:

- `make build`: Builds the paper.docx file from paper.md
- `make open`: Builds and opens the paper.docx file (requires xdg-open)

Example:
```bash
make build
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

## About ISPRAS Proceedings

The Institute for System Programming of the Russian Academy of Sciences (ISPRAS) Proceedings is a collection of academic papers and research articles. This paper follows the required formatting guidelines through the automated conversion process.
