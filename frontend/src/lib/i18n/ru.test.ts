import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { RU_COPY } from "./ru";
import {
  TS_ERROR_ONLY_FILES,
  TS_SCAN_FILES,
  scanDictionaryValue,
  scanTsSource,
  scanTsxSource,
} from "../../../scripts/ui-latin-scan.mjs";

const SRC_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SKIP_NAME = /\.(test|spec)\.(ts|tsx)$/;

function walkTsx(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "dist") continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      walkTsx(full, out);
    } else if (/\.tsx$/.test(name) && !SKIP_NAME.test(name)) {
      out.push(full);
    }
  }
  return out;
}

/** Значения-функции вызываем с образцами, чтобы проверить шаблоны целиком. */
function resolveCopyValue(value: unknown): string {
  if (typeof value === "function") {
    const fn = value as (...args: string[]) => string;
    return fn(...Array.from({ length: fn.length }, () => "42"));
  }
  return String(value);
}

describe("UI3 P0.1: русификация — страж латиницы", () => {
  it("словарь i18n/ru.ts не содержит латинской прозы", () => {
    const violations: string[] = [];
    for (const [key, value] of Object.entries(RU_COPY)) {
      violations.push(...scanDictionaryValue(resolveCopyValue(value), "lib/i18n/ru.ts", key));
    }
    expect(violations).toEqual([]);
  });

  it("JSX-текст и aria/title/placeholder/alt в .tsx — без латинской прозы", () => {
    const violations: string[] = [];
    for (const file of walkTsx(SRC_ROOT)) {
      const rel = relative(SRC_ROOT, file).replaceAll("\\", "/");
      violations.push(...(scanTsxSource(readFileSync(file, "utf8"), rel) as string[]));
    }
    expect(violations).toEqual([]);
  });

  it("словарные .ts (копирайт, гейты, ТЗ-карты) — без латинской прозы", () => {
    const violations: string[] = [];
    for (const rel of TS_SCAN_FILES as string[]) {
      violations.push(...(scanTsSource(readFileSync(join(SRC_ROOT, rel), "utf8"), rel) as string[]));
    }
    for (const rel of TS_ERROR_ONLY_FILES as string[]) {
      violations.push(
        ...(scanTsSource(readFileSync(join(SRC_ROOT, rel), "utf8"), rel, { errorsOnly: true }) as string[]),
      );
    }
    expect(violations).toEqual([]);
  });

  it("severity подписаны по-русски: Блокирующее / Существенное / Информация", () => {
    expect(RU_COPY.severityError).toBe("Блокирующее");
    expect(RU_COPY.severityWarning).toBe("Существенное");
    expect(RU_COPY.severityInfo).toBe("Информация");
  });

  it("таймер честный: цель ТЗ без заявленного SLA", () => {
    expect(RU_COPY.runTimer("01:23")).toContain("Цель ТЗ записана как 30:00");
    expect(RU_COPY.runTimer("01:23")).toContain("SLA не заявляем");
    expect(RU_COPY.runTimerIdle).toContain("SLA не заявляем");
    expect(RU_COPY.runTimer("01:23")).not.toMatch(/до\s*30\s*мин/);
  });
});
