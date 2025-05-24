# Path to https://github.com/ispras/proceedings-md
PROCEEDINGS_MD ?= proceedings-md/src/main.js


default: build

build: paper.docx

paper.docx: paper.md
	node $(PROCEEDINGS_MD) $< $@

open: paper.docx
	xdg-open $<

clean:
	rm -f paper.docx paper.docx.tmp

.PHONY: open build clean
