# Path to https://github.com/ispras/proceedings-md
PROCEEDINGS_MD ?= proceedings-md/src/main.js

# Path to LanguageTool command-line JAR
LANGUAGETOOL_JAR ?= languagetool-commandline.jar

# LanguageTool executable (used when available, e.g. from Homebrew)
LANGUAGETOOL ?= languagetool

# Detect platform-specific desktop and office-suite commands. All may be
# overridden on the make command line when installed in a non-standard path.
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
OPENER ?= open
else
OPENER ?= xdg-open
endif

LIBREOFFICE ?= $(shell command -v libreoffice 2>/dev/null || command -v soffice 2>/dev/null || if [ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ]; then printf '%s\n' /Applications/LibreOffice.app/Contents/MacOS/soffice; fi)

# Ghostscript PDF optimization preset (/screen, /ebook, /printer, /prepress)
GS_PDFSETTINGS ?= /printer

# qpdf compression level (1-9)
QPDF_COMPRESS_LEVEL ?= 9


default: build

build: paper.docx

paper.docx: paper.md $(wildcard bibliography.bib)
	node "$(PROCEEDINGS_MD)" "$<" "$@"

pdf: paper.pdf

paper.pdf: paper.docx
	@if [ -z "$(LIBREOFFICE)" ]; then \
		echo "Error: LibreOffice not found. Install with 'brew install --cask libreoffice' (macOS) or 'sudo apt install libreoffice' (Debian/Ubuntu)." >&2; \
		exit 1; \
	fi
	"$(LIBREOFFICE)" --headless --convert-to pdf --outdir . "$<"
	@test -f "$@" || { echo "Error: LibreOffice did not create $@." >&2; exit 1; }

optimize-pdf-gs: paper.pdf
	@if ! command -v gs >/dev/null 2>&1; then \
		echo "Warning: Ghostscript (gs) not installed, skipping. Install with 'brew install ghostscript' (macOS) or 'sudo apt install ghostscript' (Debian/Ubuntu)."; \
	else \
		orig_size=$$(wc -c < paper.pdf | tr -d '[:space:]'); \
		gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=$(GS_PDFSETTINGS) \
			-dCompressFonts=true -dSubsetFonts=true -dDetectDuplicateImages=true \
			-dNOPAUSE -dQUIET -dBATCH -sOutputFile=paper.pdf.tmp paper.pdf; \
		opt_size=$$(wc -c < paper.pdf.tmp | tr -d '[:space:]'); \
		if [ "$$opt_size" -lt "$$orig_size" ]; then \
			mv paper.pdf.tmp paper.pdf; \
			echo "[gs] Optimized: $$orig_size -> $$opt_size bytes (saved $$(( orig_size - opt_size )) bytes)"; \
		else \
			rm -f paper.pdf.tmp; \
			echo "[gs] Already optimal: $$orig_size bytes"; \
		fi; \
	fi

optimize-pdf-qpdf: paper.pdf
	@if ! command -v qpdf >/dev/null 2>&1; then \
		echo "Warning: qpdf not installed, skipping. Install with 'brew install qpdf' (macOS) or 'sudo apt install qpdf' (Debian/Ubuntu)."; \
	else \
		orig_size=$$(wc -c < paper.pdf | tr -d '[:space:]'); \
		qpdf --compress-streams=y --object-streams=generate \
			--recompress-flate --compression-level=$(QPDF_COMPRESS_LEVEL) \
			paper.pdf paper.pdf.tmp; \
		opt_size=$$(wc -c < paper.pdf.tmp | tr -d '[:space:]'); \
		if [ "$$opt_size" -lt "$$orig_size" ]; then \
			mv paper.pdf.tmp paper.pdf; \
			echo "[qpdf] Optimized: $$orig_size -> $$opt_size bytes (saved $$(( orig_size - opt_size )) bytes)"; \
		else \
			rm -f paper.pdf.tmp; \
			echo "[qpdf] Already optimal: $$orig_size bytes"; \
		fi; \
	fi

optimize-pdf: paper.pdf
	@orig_size=$$(wc -c < paper.pdf | tr -d '[:space:]'); \
	$(MAKE) --no-print-directory optimize-pdf-gs; \
	$(MAKE) --no-print-directory optimize-pdf-qpdf; \
	final_size=$$(wc -c < paper.pdf | tr -d '[:space:]'); \
	echo "Total: $$orig_size -> $$final_size bytes (saved $$(( orig_size - final_size )) bytes)"

open: paper.docx
	@if ! command -v "$(OPENER)" >/dev/null 2>&1; then \
		echo "Error: document opener '$(OPENER)' not found. Set OPENER=/path/to/command to override." >&2; \
		exit 1; \
	fi
	"$(OPENER)" "$<"

clean:
	rm -f paper.docx paper.docx.tmp paper.pdf paper.pdf.tmp

setup:
	git submodule update --init
	cd proceedings-md && npm install && npm run build

watch:
	@echo "Watching paper.md and bibliography.bib for changes... (press Ctrl+C to stop)"
	@if command -v fswatch >/dev/null 2>&1; then \
		while fswatch -1 paper.md bibliography.bib >/dev/null; do $(MAKE) build; done; \
	elif command -v inotifywait >/dev/null 2>&1; then \
		while inotifywait -q -e modify paper.md bibliography.bib; do $(MAKE) build; done; \
	else \
		echo "Error: no file watcher found. Install with 'brew install fswatch' (macOS) or 'sudo apt install inotify-tools' (Debian/Ubuntu)." >&2; \
		exit 1; \
	fi

lint:
	npx markdownlint-cli2 paper.md

check-sentence-lines:
	node --test scripts/check-sentence-lines.test.mjs
	node scripts/check-sentence-lines.mjs paper.md

spell:
	@if ! command -v hunspell >/dev/null 2>&1; then \
		echo "Error: hunspell not found. Install with 'brew install hunspell' (macOS) or 'sudo apt install hunspell hunspell-en-us hunspell-ru' (Debian/Ubuntu)." >&2; \
		exit 1; \
	fi; \
	if ! hunspell -d en_US,ru_RU -D </dev/null >/dev/null 2>&1; then \
		echo "Error: Hunspell dictionaries en_US and ru_RU were not found. On macOS, install both .aff/.dic pairs in ~/Library/Spelling (see README.md)." >&2; \
		exit 1; \
	fi; \
	misspelled=$$(sed '1,/^---$$/d' paper.md \
		| sed '/^<!--/,/-->$$/d' \
		| sed -E 's|https?://[^ ]*||g' \
		| sed -E 's|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+||g' \
		| sed -E 's|[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9X]{4}||g' \
		| hunspell -d en_US,ru_RU -l \
		| sort -u); \
	if [ -n "$$misspelled" ]; then \
		echo "Misspelled words found:"; \
		echo "$$misspelled"; \
		exit 1; \
	else \
		echo "No misspelled words found."; \
	fi

check-links:
	npx markdown-link-check paper.md --config .markdown-link-check.json

grammar:
	@if command -v "$(LANGUAGETOOL)" >/dev/null 2>&1; then \
		sed '1,/^---$$/d' paper.md \
			| sed '/^<!--/,/-->$$/d' \
			| "$(LANGUAGETOOL)" --autoDetect -; \
	elif [ -f "$(LANGUAGETOOL_JAR)" ]; then \
		if ! command -v java >/dev/null 2>&1; then \
			echo "Error: Java not found. Install Java 17+ or install LanguageTool with 'brew install languagetool'." >&2; \
			exit 1; \
		fi; \
		sed '1,/^---$$/d' paper.md \
			| sed '/^<!--/,/-->$$/d' \
			| java -jar "$(LANGUAGETOOL_JAR)" --autoDetect -; \
	else \
		echo "Error: LanguageTool not found. Install with 'brew install languagetool' or set LANGUAGETOOL_JAR=/path/to/languagetool-commandline.jar." >&2; \
		exit 1; \
	fi

count:
	@sed '1,/^---$$/d' paper.md | sed '/^<!--/,/-->$$/d' | wc -w

validate: lint check-sentence-lines spell check-links grammar

help:
	@echo "Available targets:"
	@echo "  make build        — Build paper.docx from paper.md"
	@echo "  make pdf          — Build paper.pdf from paper.docx (requires LibreOffice)"
	@echo "  make optimize-pdf    — Optimize paper.pdf with Ghostscript + qpdf pipeline"
	@echo "  make optimize-pdf-gs — Optimize paper.pdf with Ghostscript only"
	@echo "  make optimize-pdf-qpdf — Optimize paper.pdf with qpdf only"
	@echo "  make open         — Build and open paper.docx"
	@echo "  make clean        — Remove generated files"
	@echo "  make setup        — Initialize submodule and install dependencies"
	@echo "  make watch        — Auto-rebuild on paper.md changes (requires fswatch or inotifywait)"
	@echo "  make lint         — Run markdownlint on paper.md"
	@echo "  make check-sentence-lines — Enforce one prose sentence per source line"
	@echo "  make spell        — Run hunspell spell checker on paper.md"
	@echo "  make check-links  — Check links in paper.md"
	@echo "  make grammar      — Run LanguageTool grammar checker on paper.md"
	@echo "  make count        — Word count of paper body (excluding YAML frontmatter)"
	@echo "  make validate     — Run all source checks listed above"
	@echo "  make help         — Show this help message"

.PHONY: default build pdf optimize-pdf optimize-pdf-gs optimize-pdf-qpdf open clean setup watch lint check-sentence-lines spell grammar check-links count validate help
