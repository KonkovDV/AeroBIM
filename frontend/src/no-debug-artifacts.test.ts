import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * HD24-FE-01: демо-гигиена оболочки (source-scan, не runtime).
 *
 * Показ ИТ-ментору идёт по живой оболочке, поэтому в продуктовом коде не должно
 * остаться служебных следов: отладочной консоли, точек останова, нативных
 * браузерных модалок и вшитых адресов стенда. Отдельно закрепляется, что
 * лабораторный посев фикстуры не попадает в производственную сборку.
 *
 * Сканер строковый и намеренно грубый: он дешевле ревью и ловит регресс до CI.
 */
const SRC_ROOT = dirname(fileURLToPath(import.meta.url));

/** Файл-охранник исключается из обхода: иначе он находит собственные шаблоны. */
const SELF_NAME = "no-debug-artifacts.test.ts";
const SOURCE_NAME = /\.(ts|tsx)$/;
const TEST_NAME = /\.(test|spec)\.(ts|tsx)$/;
const SKIP_DIRS = new Set(["node_modules", "dist", "coverage"]);

/** Отладочная консоль. `console.error` разбирается отдельным правилом. */
const DEBUG_CONSOLE = /\bconsole\s*\.\s*(?:log|debug|info|table|trace|dir|group|groupEnd)\s*\(/g;
/** Диагностическая консоль: допустима только в зарегистрированных файлах. */
const DIAGNOSTIC_CONSOLE = /\bconsole\s*\.\s*(?:error|warn)\s*\(/g;
/** Точка останова. Собирается из частей, чтобы grep по репозиторию был чистым. */
const BREAKPOINT = new RegExp(`(?:^|[;\\s{}])${"debug" + "ger"}\\s*(?:;|$)`, "m");
/** Нативные модалки: невозможно оформить, читают origin в заголовке окна. */
const NATIVE_BLOCKING = /\bwindow\s*\.\s*(?:alert|prompt)\s*\(/g;
const NATIVE_CONFIRM = /\bwindow\s*\.\s*confirm\s*\(/g;
/** Вшитый адрес стенда в строковом литерале (комментарии не считаются). */
const HARDCODED_HOST = /["'`]https?:\/\/(?:localhost|127\.0\.0\.1)/g;

/**
 * `console.error` / `console.warn` разрешены только там, где иначе теряется
 * причина сбоя, и только под `import.meta.env.DEV`.
 */
const DIAGNOSTIC_CONSOLE_ALLOWED = new Set(["features/shell/IfcViewerErrorBoundary.tsx"]);

/**
 * Зарегистрированный долг: подтверждение экспорта при несохранённом черновике
 * всё ещё нативное. Список закрывает распространение паттерна по коду.
 * План замены — FE-CRUFT-02 в docs/quality/FRONTEND_MENTOR_DEMO_2026_09_11.md.
 */
const NATIVE_CONFIRM_ALLOWED = new Set(["features/export/ExportActionsBar.tsx"]);

/** Исключительный запуск: один `.only` тихо отключает остальной набор. */
const EXCLUSIVE_RUN = ["describe", "it", "test"].map(
  (fn) => new RegExp(`\\b${fn}\\s*\\.\\s*only\\s*[(<]`),
);

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) {
      continue;
    }
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...walk(full));
      continue;
    }
    if (name === SELF_NAME || !SOURCE_NAME.test(name)) {
      continue;
    }
    out.push(full);
  }
  return out;
}

function rel(file: string): string {
  return relative(SRC_ROOT, file).replaceAll("\\\\", "/");
}

function hits(source: string, pattern: RegExp): number {
  const re = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : `${pattern.flags}g`);
  let count = 0;
  while (re.exec(source) !== null) {
    count += 1;
  }
  return count;
}

const files = walk(SRC_ROOT).map((file) => ({
  path: rel(file),
  source: readFileSync(file, "utf8"),
}));
const production = files.filter((file) => !TEST_NAME.test(file.path));

function read(path: string): string {
  const found = files.find((file) => file.path === path);
  expect(found, `ожидался файл ${path}`).toBeTruthy();
  return found ? found.source : "";
}

describe("HD24-FE-01 demo hygiene source-scan", () => {
  it("walks production and test sources", () => {
    expect(production.length).toBeGreaterThan(25);
    expect(files.length - production.length).toBeGreaterThan(15);
    expect(files.some((file) => file.path === "App.tsx")).toBe(true);
    expect(files.every((file) => !file.path.endsWith(SELF_NAME))).toBe(true);
  });

  it("keeps debugging consoles and breakpoints out of product code", () => {
    const violations: string[] = [];
    for (const file of production) {
      if (hits(file.source, DEBUG_CONSOLE) > 0) {
        violations.push(`${file.path} debug console`);
      }
      if (BREAKPOINT.test(file.source)) {
        violations.push(`${file.path} breakpoint`);
      }
      if (
        hits(file.source, DIAGNOSTIC_CONSOLE) > 0 &&
        !DIAGNOSTIC_CONSOLE_ALLOWED.has(file.path)
      ) {
        violations.push(`${file.path} unregistered diagnostic console`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("gates every registered diagnostic console behind the dev flag", () => {
    for (const path of DIAGNOSTIC_CONSOLE_ALLOWED) {
      const source = read(path);
      expect(hits(source, DIAGNOSTIC_CONSOLE), path).toBeGreaterThan(0);
      expect(source, path).toContain("import.meta.env.DEV");
    }
  });

  it("keeps native blocking dialogs out and confirms only where registered", () => {
    const violations: string[] = [];
    for (const file of production) {
      if (hits(file.source, NATIVE_BLOCKING) > 0) {
        violations.push(`${file.path} native alert/prompt`);
      }
      if (hits(file.source, NATIVE_CONFIRM) > 0 && !NATIVE_CONFIRM_ALLOWED.has(file.path)) {
        violations.push(`${file.path} unregistered native confirm`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("never hardcodes a bench address in product code", () => {
    const violations = production
      .filter((file) => hits(file.source, HARDCODED_HOST) > 0)
      .map((file) => `${file.path} hardcoded bench host`);
    expect(violations).toEqual([]);
  });

  it("leaves no exclusive test run behind", () => {
    const violations: string[] = [];
    for (const file of files) {
      if (EXCLUSIVE_RUN.some((pattern) => pattern.test(file.source))) {
        violations.push(`${file.path} exclusive run`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("keeps the lab fixture seeding out of production builds", () => {
    expect(read("App.tsx")).toMatch(
      /import\.meta\.env\.DEV\s*\?\s*\(\s*<DemoFixturePanel\b/,
    );
    expect(read("lib/lab-demo.ts")).toContain("import.meta.env.DEV");
  });

  it("keeps the service address out of the presentational shell (FE-CRUFT-01)", () => {
    expect(read("features/shell/ShellHeader.tsx")).not.toContain("apiBase");
    expect(read("App.tsx")).not.toContain("getApiBaseUrl");
  });
});
