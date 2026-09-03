/**
 * npm run lint — UI3 P0.1: ни одной английской надписи в интерфейсе.
 * Сканирует все .tsx в src (JSX-текст и aria/title/placeholder/alt) и словарные
 * .ts (строковые литералы). Без новых зависимостей; выход 1 при нарушениях.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import {
  TS_ERROR_ONLY_FILES,
  TS_SCAN_FILES,
  scanTsSource,
  scanTsxSource,
} from "./ui-latin-scan.mjs";

const SRC_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const SKIP_NAME = /\.(test|spec)\.(ts|tsx)$/;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "dist") continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      walk(full, out);
    } else if (/\.tsx$/.test(name) && !SKIP_NAME.test(name)) {
      out.push(full);
    }
  }
  return out;
}

const violations = [];

for (const file of walk(SRC_ROOT)) {
  const rel = relative(SRC_ROOT, file).replaceAll("\\", "/");
  violations.push(...scanTsxSource(readFileSync(file, "utf8"), rel));
}

for (const rel of TS_SCAN_FILES) {
  violations.push(...scanTsSource(readFileSync(join(SRC_ROOT, rel), "utf8"), rel));
}

for (const rel of TS_ERROR_ONLY_FILES) {
  violations.push(
    ...scanTsSource(readFileSync(join(SRC_ROOT, rel), "utf8"), rel, { errorsOnly: true }),
  );
}

if (violations.length > 0) {
  console.error(`lint-ui-strings: ${violations.length} нарушений (латиница в видимых строках):`);
  for (const violation of violations) {
    console.error(`  ${violation}`);
  }
  process.exit(1);
}

console.log("lint-ui-strings: латиницы в видимых строках не найдено");
