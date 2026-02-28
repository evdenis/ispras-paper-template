# Path to https://github.com/ispras/proceedings-md
PROCEEDINGS_MD ?= proceedings-md/src/main.js

# Path to LanguageTool command-line JAR
LANGUAGETOOL_JAR ?= languagetool-commandline.jar


default: build

build: paper.docx

paper.docx: paper.md
	node $(PROCEEDINGS_MD) $< $@

pdf: paper.docx
	libreoffice --headless --convert-to pdf $<

open: paper.docx
	xdg-open $<

clean:
	rm -f paper.docx paper.docx.tmp paper.pdf

setup:
	git submodule update --init
	cd proceedings-md && npm install

watch:
	@echo "Watching paper.md for changes... (press Ctrl+C to stop)"
	@while inotifywait -e modify paper.md; do \
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

.PHONY: default build pdf open clean setup watch lint spell grammar check-links count validate help
