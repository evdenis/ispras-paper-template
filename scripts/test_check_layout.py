"""Unit tests for the layout report. No PDF is read: every rule under test is a
pure function over word boxes and rule positions."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).with_name("check_layout.py")
SPEC = importlib.util.spec_from_file_location("check_layout", SCRIPT_PATH)
assert SPEC and SPEC.loader
LAYOUT = importlib.util.module_from_spec(SPEC)
# @dataclass resolves annotations through sys.modules, so register before exec.
sys.modules[SPEC.name] = LAYOUT
SPEC.loader.exec_module(LAYOUT)

Line = LAYOUT.Line
Page = LAYOUT.Page
Word = LAYOUT.Word
body_lines = LAYOUT.body_lines
chrome_rules = LAYOUT.chrome_rules
content_rules = LAYOUT.content_rules
drop_bibliography = LAYOUT.drop_bibliography
find_break_violations = LAYOUT.find_break_violations
find_gaps = LAYOUT.find_gaps
find_orphan_captions = LAYOUT.find_orphan_captions
find_runts = LAYOUT.find_runts
find_split_blocks = LAYOUT.find_split_blocks
content_spans = LAYOUT.content_spans
group_lines = LAYOUT.group_lines
is_body_text = LAYOUT.is_body_text
report = LAYOUT.report

PAGE_HEIGHT = 680.4
BODY_TOP = 60.0
LINE_HEIGHT = 12.0
CHROME_RULE = 37.0


def word(text: str, top: float, x0: float = 60.0, size: float = 10.0) -> Word:
    return Word(text=text, x0=x0, x1=x0 + len(text) * 5.0, top=top, bottom=top + size)


def line(text: str, top: float, x0: float = 60.0, height: float = 10.0) -> Line:
    words = tuple(text.split())
    return Line(
        top=top,
        bottom=top + height,
        x0=x0,
        x1=x0 + len(text) * 5.0,
        height=height,
        words=words,
    )


def page(
    number: int,
    lines: list[Line],
    rules: list[float] | None = None,
    drawings: list[tuple[float, float]] | None = None,
) -> Page:
    return Page(
        number=number,
        height=PAGE_HEIGHT,
        lines=tuple(lines),
        rules=tuple(sorted(rules if rules is not None else [CHROME_RULE])),
        drawings=tuple(drawings or []),
    )


# Content reaching the foot of the body, so a fixture that is not about trailing
# white space reports none.
FOOT = 630.0


def fills_to_foot(top: float) -> tuple[float, float]:
    return (top, FOOT)


def prose_page(number: int, texts: list[str], start: float = BODY_TOP, fill: bool = False) -> Page:
    lines = [line(text, start + index * LINE_HEIGHT) for index, text in enumerate(texts)]
    return page(number, lines, drawings=[fills_to_foot(start)] if fill else None)


class GroupLinesTest(unittest.TestCase):
    def test_collects_words_sharing_a_baseline(self):
        words = [
            word("вторая", 100.0, x0=100.0),
            word("Первая", 100.0, x0=60.0),
            word("строка", 112.0, x0=60.0),
        ]
        grouped = group_lines(words)
        self.assertEqual([item.words for item in grouped], [("Первая", "вторая"), ("строка",)])
        self.assertEqual(grouped[0].height, 10.0)

    def test_tolerates_baseline_jitter(self):
        grouped = group_lines([word("а", 100.0), word("б", 101.5, x0=80.0)])
        self.assertEqual(len(grouped), 1)


class BodyLinesTest(unittest.TestCase):
    def test_drops_running_head_and_page_number(self):
        lines = [
            line("Ефремов Д.В. Сравнительная оценка", 30.0),
            line("Основной текст", BODY_TOP),
            line("16", 640.0),
        ]
        kept = body_lines(lines, PAGE_HEIGHT)
        self.assertEqual([item.text for item in kept], ["Основной текст"])

    def test_keeps_a_number_standing_in_the_body(self):
        lines = [line("Основной текст", BODY_TOP), line("1", 250.0)]
        kept = body_lines(lines, PAGE_HEIGHT)
        self.assertEqual([item.text for item in kept], ["Основной текст", "1"])


class RulesTest(unittest.TestCase):
    def test_recognizes_the_running_head_border(self):
        pages_rules = [[CHROME_RULE], [CHROME_RULE, 200.0], [CHROME_RULE], [CHROME_RULE, 300.0]]
        self.assertEqual(chrome_rules(pages_rules), [CHROME_RULE])

    def test_counts_neighbouring_rules_on_one_page_once(self):
        pages_rules = [[CHROME_RULE, 200.0, 200.5], [CHROME_RULE], [CHROME_RULE, 300.0]]
        self.assertEqual(chrome_rules(pages_rules), [CHROME_RULE])

    def test_content_rules_exclude_chrome(self):
        self.assertEqual(content_rules([CHROME_RULE, 200.0], [CHROME_RULE]), [200.0])


class BodyTextTest(unittest.TestCase):
    def test_separates_subscripts_and_display_math_from_prose(self):
        lines = [line("обычная строка", 100.0), line("текст", 112.0), line("total", 124.0, height=6.0)]
        display = line("W", 136.0, height=14.0)
        self.assertTrue(is_body_text(lines[0], lines))
        self.assertFalse(is_body_text(lines[2], lines))
        self.assertFalse(is_body_text(display, lines))


class GapTest(unittest.TestCase):
    def test_reports_a_hole_between_blocks(self):
        target = page(
            1,
            [line("до провала", 100.0), line("после провала", 400.0)],
            drawings=[fills_to_foot(410.0)],
        )
        findings = find_gaps(target, max_gap=120.0, is_last_page=False)
        self.assertEqual([item.kind for item in findings], ["whitespace gap"])
        self.assertIn("290 pt after", findings[0].detail)

    def test_reports_a_page_that_ends_early(self):
        target = page(1, [line("единственная строка", 100.0)])
        findings = find_gaps(target, max_gap=120.0, is_last_page=False)
        self.assertEqual(len(findings), 1)
        self.assertIn("at the foot of the page", findings[0].detail)

    def test_allows_the_last_page_to_end_early(self):
        target = page(9, [line("конец", 100.0)])
        self.assertEqual(find_gaps(target, max_gap=120.0, is_last_page=True), [])

    def test_counts_a_figure_as_content(self):
        target = page(
            1,
            [line("текст над рисунком", 100.0), line("подпись под рисунком", 400.0)],
            drawings=[(115.0, 395.0), fills_to_foot(410.0)],
        )
        self.assertEqual(find_gaps(target, max_gap=120.0, is_last_page=False), [])

    def test_merges_text_and_drawings_into_content_spans(self):
        target = page(
            1,
            [line("первая", 100.0), line("вторая", 300.0)],
            drawings=[(105.0, 250.0), (240.0, 301.0)],
        )
        self.assertEqual(content_spans(target), [(100.0, 310.0)])


class SplitBlockTest(unittest.TestCase):
    def test_reports_a_table_that_crosses_the_page_break(self):
        first = page(7, [line("Табл. 1. Категории", 140.0)], rules=[CHROME_RULE, 156.0, 626.0])
        second = page(8, [line("продолжение", 90.0)], rules=[CHROME_RULE, 41.0, 115.0])
        findings = find_split_blocks([first, second], [CHROME_RULE])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].detail, "Табл. 1. continues on page 8")

    def test_accepts_a_split_whose_header_row_repeats(self):
        header = "Система Версия Основание"
        first = page(
            14,
            [line("Табл. 5. Объекты", 520.0), line(header, 556.0), line("Linux 6.12", 576.0)],
            rules=[CHROME_RULE, 553.0, 572.0, 627.0],
        )
        second = page(
            15,
            [line(header, 44.0), line("OpenBSD 7.6", 64.0)],
            rules=[CHROME_RULE, 41.0, 61.0, 485.0],
        )
        self.assertEqual(find_split_blocks([first, second], [CHROME_RULE]), [])

    def test_ignores_blocks_that_end_before_the_foot(self):
        first = page(9, [line("Табл. 2. Измерения", 40.0)], rules=[CHROME_RULE, 61.0, 264.0])
        second = page(10, [line("текст", 90.0)], rules=[CHROME_RULE, 300.0])
        self.assertEqual(find_split_blocks([first, second], [CHROME_RULE]), [])


class RuntTest(unittest.TestCase):
    def test_reports_a_lone_short_word(self):
        target = prose_page(1, ["длинная строка текста здесь", "0,05."])
        findings = find_runts([target], [CHROME_RULE])
        self.assertEqual([item.detail for item in findings], ["«0,05.»"])

    def test_accepts_a_bound_pair_and_a_long_word(self):
        target = prose_page(1, ["длинная строка текста здесь", "подход [21].", "таксономии."])
        self.assertEqual(find_runts([target], [CHROME_RULE]), [])

    def test_ignores_section_headings_and_table_cells(self):
        heading = prose_page(1, ["длинная строка текста здесь", "7. Обсуждение"])
        self.assertEqual(find_runts([heading], [CHROME_RULE]), [])

        cells = page(2, [line("Linux", 200.0), line("83 %", 220.0)], rules=[CHROME_RULE, 190.0, 240.0])
        self.assertEqual(find_runts([cells], [CHROME_RULE]), [])


class BreakViolationTest(unittest.TestCase):
    def test_reports_a_preposition_left_at_the_line_end(self):
        target = prose_page(1, ["оценка вычислена в", "разделе шесть подробно"])
        findings = find_break_violations([target], [CHROME_RULE])
        self.assertEqual([item.kind for item in findings], ["break after preposition"])

    def test_reports_a_reference_word_torn_off_its_number(self):
        target = prose_page(1, ["подробно разобрано в разделе", "7. Далее следует вывод"])
        findings = find_break_violations([target], [CHROME_RULE])
        self.assertEqual([item.kind for item in findings], ["break after reference word"])

    def test_accepts_a_reference_word_ending_a_paragraph(self):
        target = prose_page(1, ["значение задается формулой", "Далее следует вывод"])
        self.assertEqual(find_break_violations([target], [CHROME_RULE]), [])

    def test_reports_a_dash_or_percent_opening_a_line(self):
        target = prose_page(1, ["пара «охват", "— качество» описывает", "% таксономии"])
        kinds = [item.kind for item in find_break_violations([target], [CHROME_RULE])]
        self.assertEqual(kinds, ["line starts with a dash", "line starts with a percent sign"])


class OrphanCaptionTest(unittest.TestCase):
    def test_reports_a_figure_caption_opening_a_page(self):
        target = prose_page(3, ["Рис. 4. Производные показатели", "продолжение текста"])
        findings = find_orphan_captions([target])
        self.assertEqual([item.detail for item in findings], ["Рис. 4."])

    def test_reports_a_table_caption_closing_a_page(self):
        target = prose_page(3, ["обычный текст здесь", "Table 3. Dimension-weight profiles"])
        findings = find_orphan_captions([target])
        self.assertEqual([item.detail for item in findings], ["Table 3."])


class BibliographyTest(unittest.TestCase):
    def test_stops_checking_at_the_reference_list(self):
        pages = [
            prose_page(1, ["обычный текст здесь"]),
            prose_page(2, ["Список литературы / References", "[17]. Afzali H., Mokhtari"]),
            prose_page(3, ["[18]. Song J., Hu"]),
        ]
        trimmed = drop_bibliography(pages)
        self.assertEqual(len(trimmed), 2)
        self.assertEqual([item.text for item in trimmed[-1].lines], [])


class ReportTest(unittest.TestCase):
    def test_sorts_findings_and_keeps_only_real_defects(self):
        pages = [
            prose_page(1, ["длинная строка текста здесь", "оценка вычислена в"], fill=True),
            prose_page(2, ["итог."]),
        ]
        findings = report(pages)
        self.assertEqual(
            [(item.page, item.kind) for item in findings],
            [(1, "break after preposition"), (2, "runt line")],
        )


if __name__ == "__main__":
    unittest.main()
