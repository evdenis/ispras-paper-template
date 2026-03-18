# Path to https://github.com/ispras/proceedings-md
PROCEEDINGS_MD ?= proceedings-md/src/main.js

# Path to LanguageTool command-line JAR
LANGUAGETOOL_JAR ?= languagetool-commandline.jar

# Ghostscript PDF optimization preset (/screen, /ebook, /printer, /prepress)
GS_PDFSETTINGS ?= /printer

# qpdf compression level (1-9)
QPDF_COMPRESS_LEVEL ?= 9


default: build

build: paper.docx

paper.docx: paper.md $(wildcard bibliography.bib)
	node $(PROCEEDINGS_MD) $< $@

pdf: paper.docx
	libreoffice --headless --convert-to pdf $<

optimize-pdf-gs: paper.pdf
	@if ! command -v gs >/dev/null 2>&1; then \
		echo "Warning: Ghostscript (gs) not installed, skipping. Install: sudo apt install ghostscript"; \
	else \
		orig_size=$$(stat -c%s paper.pdf); \
		gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=$(GS_PDFSETTINGS) \
			-dCompressFonts=true -dSubsetFonts=true -dDetectDuplicateImages=true \
			-dNOPAUSE -dQUIET -dBATCH -sOutputFile=paper.pdf.tmp paper.pdf; \
		opt_size=$$(stat -c%s paper.pdf.tmp); \
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
		echo "Warning: qpdf not installed, skipping. Install: sudo apt install qpdf"; \
	else \
		orig_size=$$(stat -c%s paper.pdf); \
		qpdf --compress-streams=y --object-streams=generate \
			--recompress-flate --compression-level=$(QPDF_COMPRESS_LEVEL) \
			paper.pdf paper.pdf.tmp; \
		opt_size=$$(stat -c%s paper.pdf.tmp); \
		if [ "$$opt_size" -lt "$$orig_size" ]; then \
			mv paper.pdf.tmp paper.pdf; \
			echo "[qpdf] Optimized: $$orig_size -> $$opt_size bytes (saved $$(( orig_size - opt_size )) bytes)"; \
		else \
			rm -f paper.pdf.tmp; \
			echo "[qpdf] Already optimal: $$orig_size bytes"; \
		fi; \
	fi

optimize-pdf: paper.pdf
	@orig_size=$$(stat -c%s paper.pdf); \
	$(MAKE) --no-print-directory optimize-pdf-gs; \
	$(MAKE) --no-print-directory optimize-pdf-qpdf; \
	final_size=$$(stat -c%s paper.pdf); \
	echo "Total: $$orig_size -> $$final_size bytes (saved $$(( orig_size - final_size )) bytes)"

open: paper.docx
	xdg-open $<

clean:
	rm -f paper.docx paper.docx.tmp paper.pdf paper.pdf.tmp

setup:
	git submodule update --init
	cd proceedings-md && npm install && npm run build

watch:
	@echo "Watching paper.md and bibliography.bib for changes... (press Ctrl+C to stop)"
	@while inotifywait -e modify paper.md bibliography.bib; do \
		$(MAKE) build; \
	done

lint:
	npx markdownlint-cli2 paper.md

spell:
	@misspelled=$$(sed '1,/^---$$/d' paper.md \
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
	@sed '1,/^---$$/d' paper.md \
		| sed '/^<!--/,/-->$$/d' \
		| java -jar $(LANGUAGETOOL_JAR) --autoDetect -

count:
	@sed '1,/^---$$/d' paper.md | sed '/^<!--/,/-->$$/d' | wc -w

validate: lint spell check-links grammar

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
	@echo "  make watch        — Auto-rebuild on paper.md changes (requires inotifywait)"
	@echo "  make lint         — Run markdownlint on paper.md"
	@echo "  make spell        — Run hunspell spell checker on paper.md"
	@echo "  make check-links  — Check links in paper.md"
	@echo "  make grammar      — Run LanguageTool grammar checker on paper.md"
	@echo "  make count        — Word count of paper body (excluding YAML frontmatter)"
	@echo "  make validate     — Run lint + spell + check-links + grammar"
	@echo "  make help         — Show this help message"

.PHONY: default build pdf optimize-pdf optimize-pdf-gs optimize-pdf-qpdf open clean setup watch lint spell grammar check-links count validate help
