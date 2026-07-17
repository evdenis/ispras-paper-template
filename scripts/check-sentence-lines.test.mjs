import assert from 'node:assert/strict';
import test from 'node:test';

import {
  checkMarkdown,
  formatMarkdown,
  sentenceSegments,
} from './check-sentence-lines.mjs';

test('segments Russian and English sentences', () => {
  assert.deepEqual(
    sentenceSegments('Первое предложение. Второе предложение?'),
    ['Первое предложение.', 'Второе предложение?'],
  );
  assert.deepEqual(
    sentenceSegments('First sentence. Second sentence!'),
    ['First sentence.', 'Second sentence!'],
  );
});

test('does not split protected punctuation', () => {
  const text = 'Институт им. В.П. Иванникова использует compute_scores.py версии 3.5.';
  assert.deepEqual(sentenceSegments(text), [text]);
  const range = 'Категории C1..C7 образуют таксономию.';
  assert.deepEqual(sentenceSegments(range), [range]);
  const credentials = 'Professor, Dr. Sci. (Phys.-Math.), Head of Department.';
  assert.deepEqual(sentenceSegments(credentials), [credentials]);
});

test('does not split citations, code, or URLs', () => {
  const text = 'См. `evaluation.yaml` и <https://example.org/a.b> [@doe2025].';
  assert.deepEqual(sentenceSegments(text), [text]);
  assert.deepEqual(
    sentenceSegments('See https://example.com. Next sentence.'),
    ['See https://example.com.', 'Next sentence.'],
  );
  assert.deepEqual(
    sentenceSegments('See [the site](https://example.com). Next sentence.'),
    ['See [the site](https://example.com).', 'Next sentence.'],
  );
});

test('keeps Markdown emphasis closers with the preceding segment', () => {
  assert.deepEqual(
    sentenceSegments('**Название.** Следующее предложение.'),
    ['**Название.**', 'Следующее предложение.'],
  );
  assert.deepEqual(
    sentenceSegments('**Название.**'),
    ['**Название.**'],
  );
});

test('reports multiple sentences and wrapped sentences', () => {
  const diagnostics = checkMarkdown([
    '---',
    'abstract_ru: >-',
    '  Первое предложение. Второе предложение.',
    '---',
    '',
    'Одно предложение, которое',
    'перенесено на другую строку.',
  ].join('\n'));

  assert.deepEqual(diagnostics, [
    { line: 3, message: 'contains 2 sentences' },
    { line: 6, message: 'sentence continues on the next source line' },
  ]);
});

test('ignores Markdown structures that cannot be reflowed', () => {
  const text = [
    '=== TEMPLATE EXAMPLES ===',
    '![](images/example.png)',
    '| Ячейка. Еще текст. |',
    '$$',
    'H(M) = P.',
    '$$',
    '```text',
    'One. Two.',
    '```',
    '~~~~text',
    'Three. Four.',
    '~~~~',
    '$$x. y.$$ ',
  ].join('\n');
  assert.deepEqual(checkMarkdown(text), []);
});

test('formats paragraphs and keeps list continuation indentation', () => {
  const input = 'Первое. Второе.\n\n- Один пункт. Еще предложение.\n';
  const expected = 'Первое.\nВторое.\n\n- Один пункт.\n  Еще предложение.\n';
  assert.equal(formatMarkdown(input), expected);
  assert.deepEqual(checkMarkdown(expected), []);
});
