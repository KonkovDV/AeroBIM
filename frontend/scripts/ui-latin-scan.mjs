/**
 * UI3 P0.1: страж латиницы в видимых строках.
 *
 * Что сканируется:
 *  - .tsx: JSX-текст (>текст<) и атрибуты aria-label/title/placeholder/alt;
 *  - .ts из TS_SCAN_FILES: строковые литералы с кириллицей (проза — по-русски;
 *    чисто латинские литералы — это enum/ключи/пути, они не проза);
 *  - api.ts: только литералы new Error(...) — они попадают в баннеры ошибок.
 *
 * Разрешены: акронимы КАПСОМ (IFC, IDS, BCF, PDF, GUID, JSON, HTML, SLA, HITL…),
 * идентификаторы (с `_ . / #` или цифрой: summary.passed, finding_id, RT-001),
 * составные через дефис (review-events, web-ifc), camelCase/PascalCase-типы
 * (DrawingRegionRef) и явный ALLOWED_WORDS.
 *
 * Чанк без кириллицы в .tsx помечается, только если это английская фраза
 * (2+ слова) или единственное «голое» слово (видимый enum вместо перевода).
 */

export const ALLOWED_WORDS = new Set([
  // enum/статусные токены API, показываемые как машинные значения
  "pass", "fail", "passed", "failed", "true", "false",
  // имена собственные и инструменты
  "vite", "aerobim", "navisworks", "autodesk", "tangl", "office", "excel",
  // протокольные и доменные термины проекта
  "bearer", "authorization", "accept", "checkpoint", "bbox",
  // enum-статусы карты покрытия (машинные значения API)
  "findings",
]);

/** .ts-файлы с пользовательски видимыми строками (литералы с кириллицей). */
export const TS_SCAN_FILES = [
  "lib/i18n/ru.ts",
  "lib/ui-copy.ts",
  "lib/intake-gates.ts",
  "lib/tz-ui-screens.ts",
  "lib/tz-requirement-map.ts",
  "lib/capability-copy.ts",
  "lib/pack-kind.ts",
  "lib/issue-triage.ts",
];

/** .ts-файлы, где сканируются только литералы new Error(...). */
export const TS_ERROR_ONLY_FILES = ["lib/api.ts"];

const MIN_LEN = 4;
const ALL_CAPS = /^[A-Z]+$/;
const CAMEL_CASE = /^[a-z]+(?:[A-Z][a-z0-9]*)+$/;
const PASCAL_CASE = /^[A-Z][a-z0-9]*(?:[A-Z][a-z0-9]*)+$/;
const LATIN_TOKEN = /[A-Za-z]+/g;
const CYRILLIC = /[А-Яа-яЁё]/;

function isAllowedToken(token) {
  if (token.length < MIN_LEN) return true;
  if (ALL_CAPS.test(token)) return true;
  if (CAMEL_CASE.test(token) || PASCAL_CASE.test(token)) return true;
  return ALLOWED_WORDS.has(token.toLowerCase());
}

/** Убирает ${...}, составные через дефис и токены-идентификаторы/числа. */
function stripNonProse(text) {
  let out = text.replace(/\$\{[^}]*\}/g, " ");
  out = out.replace(/[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+/g, " ");
  out = out.replace(/\S*[_./\\#\d]\S*/g, " ");
  return out;
}

function violationTokens(text) {
  const cleaned = stripNonProse(text);
  const tokens = [];
  LATIN_TOKEN.lastIndex = 0;
  let match = LATIN_TOKEN.exec(cleaned);
  while (match) {
    if (!isAllowedToken(match[0])) {
      tokens.push(match[0]);
    }
    match = LATIN_TOKEN.exec(cleaned);
  }
  return tokens;
}

function scanChunk(chunk, relPath, line, violations, { cyrillicRequired }) {
  const hasCyrillic = CYRILLIC.test(chunk);
  const tokens = violationTokens(chunk);
  if (tokens.length === 0) {
    return;
  }
  if (hasCyrillic) {
    for (const token of tokens) {
      violations.push(`${relPath}:${line} латиница «${token}» в «${chunk.trim().slice(0, 72)}»`);
    }
    return;
  }
  if (cyrillicRequired) {
    return;
  }
  const bareWord = tokens.length === 1 && chunk.trim() === tokens[0];
  if (tokens.length >= 2 || bareWord) {
    for (const token of tokens) {
      violations.push(`${relPath}:${line} латиница «${token}» в «${chunk.trim().slice(0, 72)}»`);
    }
  }
}

function lineNumberAt(source, index) {
  return source.slice(0, index).split("\n").length;
}

/** JSX-текст (без `=();` — отсекает код) и видимые атрибуты .tsx. */
export function scanTsxSource(source, relPath) {
  const violations = [];
  const patterns = [
    /(?<!=)>([^<>{};=()]+)</g,
    /\b(?:aria-label|title|placeholder|alt)\s*=\s*"([^"]*)"/g,
    /\b(?:aria-label|title|placeholder|alt)\s*=\s*'([^']*)'/g,
  ];
  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    let match = pattern.exec(source);
    while (match) {
      scanChunk(match[1], relPath, lineNumberAt(source, match.index), violations, {
        cyrillicRequired: false,
      });
      match = pattern.exec(source);
    }
  }
  return violations;
}

const STRING_LITERAL = /"([^"\n]*)"|'([^'\n]*)'|`([^`]*)`/g;
const ERROR_LITERAL = /new Error\(\s*(?:"([^"\n]*)"|'([^'\n]*)'|`([^`]*)`)/g;

/** Строковые литералы .ts: проза с кириллицей (или только new Error). */
export function scanTsSource(source, relPath, { errorsOnly = false } = {}) {
  const violations = [];
  const pattern = errorsOnly ? ERROR_LITERAL : STRING_LITERAL;
  pattern.lastIndex = 0;
  let match = pattern.exec(source);
  while (match) {
    const text = match[1] ?? match[2] ?? match[3] ?? "";
    scanChunk(text, relPath, lineNumberAt(source, match.index), violations, {
      cyrillicRequired: !errorsOnly,
    });
    match = pattern.exec(source);
  }
  return violations;
}

/** Сканирование разрешённого значения словаря (живой импорт в vitest). */
export function scanDictionaryValue(value, relPath, key) {
  const violations = [];
  scanChunk(value, `${relPath}#${key}`, 0, violations, { cyrillicRequired: false });
  return violations;
}
