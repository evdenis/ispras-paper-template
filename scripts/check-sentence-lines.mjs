#!/usr/bin/env node

import fs from 'node:fs';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

const segmenter = new Intl.Segmenter('ru', { granularity: 'sentence' });

function concealRange(match) {
  return match.replace(/[^\s]/gu, '\u2060');
}

function concealDots(match) {
  return match.replaceAll('.', '\u2060');
}

function concealUrl(match) {
  const trailingPunctuation = match.match(/[)\]}>»"'.,!?;:]+$/u)?.[0] ?? '';
  const url = match.slice(0, match.length - trailingPunctuation.length);
  return concealRange(url) + trailingPunctuation;
}

function maskedForSegmentation(text) {
  let masked = text;

  // These constructs may contain sentence punctuation but cannot end a prose
  // sentence on their own.
  masked = masked.replace(/`[^`]*`/gu, concealRange);
  masked = masked.replace(/<https?:\/\/[^>]+>/gu, concealRange);
  masked = masked.replace(/https?:\/\/\S+/gu, concealUrl);
  masked = masked.replace(/\[@[^\]]+\]/gu, concealRange);
  masked = masked.replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/gu, concealRange);
  masked = masked.replace(/\b[\w-]+\.(?:bib|js|json|md|mjs|py|tex|yaml|yml)\b/giu, concealDots);
  masked = masked.replace(/\b[\p{L}]\d+\.\.[\p{L}]\d+\b/gu, concealDots);
  masked = masked.replace(/\b\d+(?:[.,]\d+)+\b/gu, concealDots);
  masked = masked.replace(/(?<![\p{L}\p{N}_])(?:[A-ZА-ЯЁ]\.){1,4}/gu, concealDots);
  masked = masked.replace(/(?<![\p{L}\p{N}_])(?:им|г|ул|стр|рис|табл|см|др|т\.д|т\.п|т\.е)\./giu, concealDots);
  masked = masked.replace(/(?<![\p{L}\p{N}_])(?:Dr|Mr|Mrs|Ms|Prof|Sci)\./gu, concealDots);

  return masked;
}

export function sentenceSegments(text) {
  const masked = maskedForSegmentation(text);
  const segments = [];

  for (const part of segmenter.segment(masked)) {
    const original = text.slice(part.index, part.index + part.segment.length).trim();
    if (original !== '') {
      segments.push(original);
    }
  }

  // Intl.Segmenter may put Markdown emphasis closers after the sentence
  // boundary. Keep those delimiters with the sentence they close.
  for (let index = 1; index < segments.length; index += 1) {
    const closingMarkup = segments[index].match(/^(\*{1,3}|_{1,3})(?:\s+|$)/u);
    if (closingMarkup) {
      segments[index - 1] += closingMarkup[1];
      segments[index] = segments[index].slice(closingMarkup[0].length);
    }
  }

  return segments.filter((segment) => segment !== '');
}

function contentParts(line) {
  const list = line.match(/^(\s*(?:[-+*]|\d+\.)\s+)(.*)$/u);
  if (list) {
    return {
      content: list[2],
      firstPrefix: list[1],
      continuationPrefix: ' '.repeat(list[1].length),
      startsListItem: true,
    };
  }

  const indentation = line.match(/^\s*/u)[0];
  return {
    content: line.slice(indentation.length),
    firstPrefix: indentation,
    continuationPrefix: indentation,
    startsListItem: false,
  };
}

function lineClassifier(lines) {
  let inFrontmatter = lines[0] === '---';
  let frontmatterDelimiterCount = 0;
  let foldedIndent = null;
  let fence = null;
  let inMath = false;

  return lines.map((line) => {
    if (line === '---' && inFrontmatter) {
      frontmatterDelimiterCount += 1;
      if (frontmatterDelimiterCount === 2) {
        inFrontmatter = false;
      }
      return { eligible: false, reset: true };
    }

    if (inFrontmatter) {
      const blockStart = line.match(/^(\s*)[^:#][^:]*:\s*>-?\s*$/u);
      if (blockStart) {
        foldedIndent = blockStart[1].length;
        return { eligible: false, reset: true };
      }

      if (foldedIndent !== null) {
        if (line.trim() === '') {
          return { eligible: false, reset: true };
        }
        const indentation = line.match(/^\s*/u)[0].length;
        if (indentation > foldedIndent) {
          return { eligible: true, reset: false };
        }
        foldedIndent = null;
      }

      return { eligible: false, reset: true };
    }

    const fenceMarker = line.trimStart().match(/^(`{3,}|~{3,})/u)?.[1] ?? null;
    if (fence !== null) {
      const closesFence = fenceMarker !== null
        && fenceMarker[0] === fence.character
        && fenceMarker.length >= fence.length
        && line.trimStart().slice(fenceMarker.length).trim() === '';
      if (closesFence) {
        fence = null;
      }
      return { eligible: false, reset: true };
    }

    if (fenceMarker !== null) {
      fence = { character: fenceMarker[0], length: fenceMarker.length };
      return { eligible: false, reset: true };
    }

    if (inMath) {
      if (/^\s*\$\$\s*$/u.test(line)) {
        inMath = false;
      }
      return { eligible: false, reset: true };
    }

    if (/^\s*\$\$\s*$/u.test(line)) {
      inMath = true;
      return { eligible: false, reset: true };
    }

    if (/^\s*\$\$.*\$\$\s*$/u.test(line)) {
      return { eligible: false, reset: true };
    }

    const structural = line.trim() === ''
      || /^\s*#/u.test(line)
      || /^\s*\|/u.test(line)
      || /^\s*:::/u.test(line)
      || /^\s*===.*===\s*$/u.test(line)
      || /^\s*!\[[^\]]*\]\([^)]+\)\s*$/u.test(line)
      || /^\s*<!--\s*$/u.test(line)
      || /^\s*-->\s*$/u.test(line);

    return { eligible: !structural, reset: structural };
  });
}

function closesSentenceUnit(content) {
  return /[.!?…:](?:[\])}"'»*_]+)?$/u.test(content.trim());
}

export function formatMarkdown(text) {
  const hadFinalNewline = text.endsWith('\n');
  const lines = text.replace(/\n$/u, '').split('\n');
  const classifications = lineClassifier(lines);
  const output = [];

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!classifications[index].eligible) {
      output.push(line);
      continue;
    }

    const parts = contentParts(line);
    const segments = sentenceSegments(parts.content);
    if (segments.length <= 1) {
      output.push(line);
      continue;
    }

    segments.forEach((segment, segmentIndex) => {
      const prefix = segmentIndex === 0 ? parts.firstPrefix : parts.continuationPrefix;
      output.push(prefix + segment);
    });
  }

  return output.join('\n') + (hadFinalNewline ? '\n' : '');
}

export function checkMarkdown(text) {
  const lines = text.replace(/\n$/u, '').split('\n');
  const classifications = lineClassifier(lines);
  const diagnostics = [];
  let previous = null;

  for (let index = 0; index < lines.length; index += 1) {
    const classification = classifications[index];
    if (!classification.eligible) {
      previous = null;
      continue;
    }

    const parts = contentParts(lines[index]);
    const segments = sentenceSegments(parts.content);
    if (segments.length > 1) {
      diagnostics.push({
        line: index + 1,
        message: `contains ${segments.length} sentences`,
      });
    }

    if (previous !== null
        && !parts.startsListItem
        && !closesSentenceUnit(previous.content)) {
      diagnostics.push({
        line: previous.line,
        message: 'sentence continues on the next source line',
      });
    }

    previous = { line: index + 1, content: parts.content };
  }

  return diagnostics;
}

function main() {
  const filename = process.argv[2];
  if (!filename || process.argv.length !== 3) {
    console.error('Usage: node scripts/check-sentence-lines.mjs <markdown-file>');
    process.exitCode = 2;
    return;
  }

  const text = fs.readFileSync(filename, 'utf8');
  const diagnostics = checkMarkdown(text);
  if (diagnostics.length === 0) {
    console.log(`${filename}: every prose sentence is on a separate line`);
    return;
  }

  diagnostics.forEach(({ line, message }) => {
    console.error(`${filename}:${line}: ${message}`);
  });
  process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
