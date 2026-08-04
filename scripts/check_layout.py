"""Report layout defects in the rendered paper: page-breaking artefacts that
neither the Markdown source nor the DOCX structure can show.

The PDF is only read in :func:`report_pdf`; every rule below is a pure function
over word boxes and rule positions, so the unit tests need no PDF at all.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# Points of vertical white space that read as a hole in the page rather than as
# ordinary paragraph spacing.
DEFAULT_MAX_GAP = 120.0

# Running head and page number, measured from the page edges.
DEFAULT_HEADER_HEIGHT = 50.0
DEFAULT_FOOTER_HEIGHT = 45.0

# A rule this close to the body edge belongs to a block that continues on the
# neighbouring page.
EDGE_TOLERANCE = 30.0

# A horizontal rule repeated on this share of the pages is page chrome, not
# content: the running head carries a bottom border.
CHROME_PAGE_SHARE = 0.6

# A paragraph tail of a single short word left alone on the last line. The
# threshold matches the runt rule proceedings-md applies while converting.
RUNT_MAX_CHARACTERS = 6

# Subscripts, chart labels and display math are set away from the body size;
# comparing against the page median keeps them out of the prose rules.
BODY_TEXT_RANGE = (0.8, 1.15)

SINGLE_LETTER_WORDS = frozenset("аиоуявкс")

# Both lists mirror proceedings-md's typography pass, which binds the same
# words to their number while converting.
TRAILING_ABBREVIATIONS = re.compile(r"^(?:рис|табл|разд|гл|стр|пп|п)\.$", re.IGNORECASE)
TRAILING_WORDS = re.compile(
    r"^(?:раздел|глав|таблиц|рисун|формул|пункт|уравнени)\w*$", re.IGNORECASE)
LEADING_DASH = re.compile(r"^[—–]")
SECTION_HEADING = re.compile(r"^\d+(?:\.\d+)*\.?$")
BIBLIOGRAPHY_HEADING = re.compile(r"^Список литературы")
FIGURE_CAPTION = re.compile(r"^(?:Рис|Fig)\.$")
TABLE_CAPTION = re.compile(r"^(?:Табл|Table)\.?$")


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float


@dataclass(frozen=True)
class Line:
    top: float
    bottom: float
    x0: float
    x1: float
    height: float
    words: tuple[str, ...]

    @property
    def text(self) -> str:
        return " ".join(self.words)

    @property
    def width(self) -> float:
        return self.x1 - self.x0


@dataclass(frozen=True)
class Page:
    number: int
    height: float
    lines: tuple[Line, ...]
    rules: tuple[float, ...]
    # Vertical extents of images, chart vectors and table rules: page space that
    # is filled even though no text line covers it.
    drawings: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class Finding:
    page: int
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"page {self.page}: {self.kind}: {self.detail}"


def group_lines(words: list[Word], tolerance: float = 2.0) -> list[Line]:
    """Collect word boxes into text lines, ordered down the page."""
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda item: (item.top, item.x0)):
        if lines and abs(lines[-1][0].top - word.top) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])

    return [
        Line(
            top=min(word.top for word in group),
            bottom=max(word.bottom for word in group),
            x0=min(word.x0 for word in group),
            x1=max(word.x1 for word in group),
            height=max(word.bottom - word.top for word in group),
            words=tuple(word.text for word in sorted(group, key=lambda item: item.x0)),
        )
        for group in lines
    ]


def body_lines(
    lines: list[Line],
    page_height: float,
    header_height: float = DEFAULT_HEADER_HEIGHT,
    footer_height: float = DEFAULT_FOOTER_HEIGHT,
) -> list[Line]:
    """Drop the running head and the page number."""
    bottom_limit = page_height - footer_height
    # The page number can sit a fraction of a point inside the body band, so a
    # lone number is also dropped near the edges. In the middle of the page it
    # is content — a formula numerator or a table cell — and must be kept.
    margin_top = 2 * header_height
    margin_bottom = page_height - 2 * footer_height
    kept = []
    for line in lines:
        if line.bottom <= header_height or line.top >= bottom_limit:
            continue
        near_edge = line.bottom <= margin_top or line.top >= margin_bottom
        if near_edge and len(line.words) == 1 and line.words[0].isdigit():
            continue
        kept.append(line)
    return kept


def chrome_rules(pages_rules: list[list[float]], tolerance: float = 1.0) -> list[float]:
    """Rule positions that repeat on most pages: the running-head border."""
    if not pages_rules:
        return []

    candidates: dict[float, int] = {}
    for rules in pages_rules:
        # A count is a number of pages: two rules a tolerance apart on the same
        # page must not look like a rule repeated across two pages.
        counted: set[float] = set()
        for position in {round(value, 1) for value in rules}:
            match = next(
                (known for known in candidates if abs(known - position) <= tolerance),
                position,
            )
            if match in counted:
                continue
            counted.add(match)
            candidates[match] = candidates.get(match, 0) + 1

    threshold = max(2, int(len(pages_rules) * CHROME_PAGE_SHARE))
    return sorted(position for position, count in candidates.items() if count >= threshold)


def content_rules(rules: list[float], chrome: list[float], tolerance: float = 1.0) -> list[float]:
    return sorted(
        position
        for position in rules
        if not any(abs(position - known) <= tolerance for known in chrome)
    )


def content_spans(page: Page) -> list[tuple[float, float]]:
    """Vertical extents the page actually fills, text and graphics alike."""
    spans = [(line.top, line.bottom) for line in page.lines]
    spans.extend(page.drawings)

    merged: list[tuple[float, float]] = []
    for top, bottom in sorted(spans):
        if merged and top <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], bottom))
        else:
            merged.append((top, bottom))
    return merged


def line_above(page: Page, position: float) -> str:
    for line in reversed(page.lines):
        if line.bottom <= position:
            return line.text[:60]
    return "the top of the page"


def find_gaps(page: Page, max_gap: float, is_last_page: bool) -> list[Finding]:
    """White space that no content fills, either between blocks or at the foot."""
    findings = []
    spans = content_spans(page)
    for (_, bottom), (top, _) in zip(spans, spans[1:]):
        if top - bottom > max_gap:
            findings.append(Finding(
                page.number,
                "whitespace gap",
                f"{top - bottom:.0f} pt after «{line_above(page, bottom + 1)}»",
            ))

    if spans and not is_last_page:
        trailing = page.height - DEFAULT_FOOTER_HEIGHT - spans[-1][1]
        if trailing > max_gap:
            findings.append(Finding(
                page.number,
                "whitespace gap",
                f"{trailing:.0f} pt at the foot of the page",
            ))

    return findings


def rows_between(page: Page, top: float, bottom: float) -> str:
    """Text of the cells framed by two rules, i.e. one table row."""
    return " ".join(
        line.text for line in page.lines if top <= line.top and line.bottom <= bottom)


def repeats_its_header(page: Page, following: Page, rules: list[float],
                       next_rules: list[float]) -> bool:
    """A split is acceptable when w:tblHeader carried the header row over."""
    if len(next_rules) < 2:
        return False

    carried = rows_between(following, next_rules[0], next_rules[1])
    if carried == "":
        return False

    return any(
        rows_between(page, top, bottom) == carried
        for top, bottom in zip(rules, rules[1:])
    )


def find_split_blocks(pages: list[Page], chrome: list[float]) -> list[Finding]:
    """A ruled block — a table or a chart — that runs over a page break."""
    findings = []
    for page, following in zip(pages, pages[1:]):
        rules = content_rules(list(page.rules), chrome)
        next_rules = content_rules(list(following.rules), chrome)
        if not rules or not next_rules:
            continue

        reaches_bottom = rules[-1] >= page.height - DEFAULT_FOOTER_HEIGHT - EDGE_TOLERANCE
        starts_at_top = next_rules[0] <= DEFAULT_HEADER_HEIGHT + EDGE_TOLERANCE
        if not (reaches_bottom and starts_at_top):
            continue
        if repeats_its_header(page, following, rules, next_rules):
            continue

        findings.append(Finding(
            page.number,
            "split block",
            f"{nearest_caption(page, rules[0])} continues on page {following.number}",
        ))

    return findings


def nearest_caption(page: Page, rule_top: float) -> str:
    """The caption above a ruled block, used to name it in the report."""
    for line in reversed(page.lines):
        if line.bottom <= rule_top and (
            FIGURE_CAPTION.match(line.words[0]) or TABLE_CAPTION.match(line.words[0])
        ):
            return " ".join(line.words[:2])
    return "ruled block"


def body_height_band(lines: Sequence[Line]) -> tuple[float, float]:
    """Height range of running prose on a page, taken from its median line."""
    heights = sorted(item.height for item in lines)
    if not heights:
        return (0.0, float("inf"))
    median = heights[len(heights) // 2]
    low, high = BODY_TEXT_RANGE
    return (median * low, median * high)


def in_band(line: Line, band: tuple[float, float]) -> bool:
    return band[0] <= line.height <= band[1]


def is_body_text(line: Line, lines: Sequence[Line]) -> bool:
    """Running prose, as opposed to subscripts, chart labels or display math."""
    return in_band(line, body_height_band(lines))


def inside_rules(line: Line, rules: list[float], padding: float = 4.0) -> bool:
    """Cell text and chart labels sit between the first and the last rule."""
    if len(rules) < 2:
        return False
    return rules[0] - padding <= line.top <= rules[-1] + padding


def find_runts(pages: list[Page], chrome: list[float]) -> list[Finding]:
    """A paragraph tail left alone on the last line."""
    findings = []
    for page in pages:
        rules = content_rules(list(page.rules), chrome)
        band = body_height_band(page.lines)
        for line in page.lines:
            if len(line.words) != 1 or len(line.words[0]) >= RUNT_MAX_CHARACTERS:
                continue
            if inside_rules(line, rules) or SECTION_HEADING.match(line.words[0]):
                continue
            if not in_band(line, band):
                continue
            findings.append(Finding(page.number, "runt line", f"«{line.text}»"))
    return findings


def find_break_violations(pages: list[Page], chrome: list[float]) -> list[Finding]:
    """Line breaks that Russian typography does not allow."""
    findings = []
    for page in pages:
        rules = content_rules(list(page.rules), chrome)
        band = body_height_band(page.lines)
        for line, following in zip(page.lines, [*page.lines[1:], None]):
            if inside_rules(line, rules) or not in_band(line, band):
                continue

            last = line.words[-1]
            if len(last) == 1 and last.lower() in SINGLE_LETTER_WORDS:
                findings.append(Finding(page.number, "break after preposition", f"«…{last}»"))
            elif TRAILING_ABBREVIATIONS.match(last) or TRAILING_WORDS.match(last):
                # Only a number torn off its reference word is a defect; a
                # paragraph that simply ends on «формулой» is not.
                carried = following.words[0] if following is not None else ""
                if carried[:1].isdigit() or carried.startswith("["):
                    findings.append(
                        Finding(page.number, "break after reference word", f"«…{last}»"))

            first = line.words[0]
            if LEADING_DASH.match(first):
                findings.append(Finding(page.number, "line starts with a dash", f"«{first}…»"))
            elif first == "%":
                findings.append(Finding(page.number, "line starts with a percent sign", "«%…»"))

    return findings


def find_orphan_captions(pages: list[Page]) -> list[Finding]:
    """A figure caption opening a page, or a table caption closing one."""
    findings = []
    for page in pages:
        if not page.lines:
            continue

        first = page.lines[0]
        if FIGURE_CAPTION.match(first.words[0]):
            findings.append(Finding(
                page.number,
                "caption separated from its figure",
                " ".join(first.words[:2]),
            ))

        last = page.lines[-1]
        if TABLE_CAPTION.match(last.words[0]):
            findings.append(Finding(
                page.number,
                "caption separated from its table",
                " ".join(last.words[:2]),
            ))

    return findings


def drop_bibliography(pages: list[Page]) -> list[Page]:
    """Reference entries end on short lines by design; stop checking there."""
    for index, page in enumerate(pages):
        for position, line in enumerate(page.lines):
            if BIBLIOGRAPHY_HEADING.match(line.text):
                trimmed = Page(
                    page.number,
                    page.height,
                    tuple(page.lines[:position]),
                    page.rules,
                    page.drawings,
                )
                return [*pages[:index], trimmed]
    return pages


def report(pages: list[Page], max_gap: float = DEFAULT_MAX_GAP) -> list[Finding]:
    chrome = chrome_rules([list(page.rules) for page in pages])
    prose = drop_bibliography(pages)

    findings: list[Finding] = []
    for page in pages:
        findings.extend(find_gaps(page, max_gap, is_last_page=page is pages[-1]))
    findings.extend(find_split_blocks(pages, chrome))
    findings.extend(find_runts(prose, chrome))
    findings.extend(find_break_violations(prose, chrome))
    findings.extend(find_orphan_captions(pages))

    return sorted(findings, key=lambda item: (item.page, item.kind, item.detail))


def read_pdf(path: Path) -> list[Page]:
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise SystemExit(
            "pdfplumber is required; run this through "
            "'uv run --with pdfplumber python scripts/check_layout.py'"
        ) from exc

    pages = []
    with pdfplumber.open(path) as document:
        for number, page in enumerate(document.pages, start=1):
            words = [
                Word(item["text"], item["x0"], item["x1"], item["top"], item["bottom"])
                for item in page.extract_words()
            ]
            marks = [*page.rects, *page.lines, *page.curves, *page.images]
            rules = {
                round(item["top"], 1)
                for item in marks
                if item["width"] > 50 and item["height"] < 3
            }
            bottom_limit = page.height - DEFAULT_FOOTER_HEIGHT
            drawings = tuple(
                (item["top"], item["bottom"])
                for item in marks
                if item["bottom"] > DEFAULT_HEADER_HEIGHT and item["top"] < bottom_limit
            )
            pages.append(Page(
                number=number,
                height=page.height,
                lines=tuple(body_lines(group_lines(words), page.height)),
                rules=tuple(sorted(rules)),
                drawings=drawings,
            ))
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="?", default="paper.pdf", type=Path)
    parser.add_argument("--max-gap", type=float, default=DEFAULT_MAX_GAP)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when anything is reported",
    )
    args = parser.parse_args(argv)

    findings = report(read_pdf(args.pdf), max_gap=args.max_gap)
    if not findings:
        print(f"{args.pdf}: no layout defects found")
        return 0

    for finding in findings:
        print(finding)

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.kind] = counts.get(finding.kind, 0) + 1
    print()
    for kind, count in sorted(counts.items()):
        print(f"{count:4d}  {kind}")
    print(f"{len(findings):4d}  total")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
