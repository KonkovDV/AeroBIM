import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { ERGONOMICS_COPY } from "./lib/i18n/ergonomics";

/**
 * Контракт эргономики оболочки.
 *
 * Проверяется не картинка, а решения, которые легко сломать в рефакторинге:
 * порядок слоёв, минимальный размер цели, пропуск навигации, запрет на сжатие
 * панелей честности и русские подписи.
 */
const SRC_ROOT = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(SRC_ROOT, relativePath), "utf8");
}

const LAYER = "styles/visual-language/10-ergonomics.css";

describe("эргономика оболочки", () => {
  it("слой подключён после экранных частей и до печати", () => {
    const barrel = read("styles/visual-language.css");
    const ergonomics = barrel.indexOf("./visual-language/10-ergonomics.css");
    const polish = barrel.indexOf("./visual-language/08-polish.css");
    const print = barrel.indexOf("./visual-language/09-print.css");

    expect(ergonomics).toBeGreaterThan(polish);
    expect(ergonomics).toBeLessThan(print);
  });

  it("не трогает блокировку светлой темы", () => {
    const layer = read(LAYER);

    expect(layer).not.toMatch(/prefers-color-scheme/);
    expect(layer).not.toMatch(/color-scheme\s*:/);
  });

  it("держит минимальный размер цели и крупную цель для сенсора", () => {
    const layer = read(LAYER);

    expect(layer).toMatch(/--vl-target-min:\s*24px/);
    expect(layer).toMatch(/--vl-target-touch:\s*44px/);
    expect(layer).toMatch(/min-block-size:\s*var\(--vl-target-min\)/);
    expect(layer).toMatch(/@media \(pointer: coarse\)/);
  });

  it("даёт пропуск навигации с целью в рабочей области", () => {
    const layer = read(LAYER);

    expect(layer).toMatch(/\.skip-to-work:not\(:focus\):not\(:active\)/);
    expect(layer).toMatch(/\.skip-to-work-target/);
    expect(read("features/shell/ShellHeader.tsx")).toContain('href="#work-area"');
    expect(read("App.tsx")).toContain('id="work-area"');
  });

  it("не сжимает и не скрывает панели честности", () => {
    const layer = read(LAYER);
    const honestyRule = layer.slice(layer.indexOf(".role-honesty-banner"));

    expect(honestyRule).toMatch(/padding-block:\s*var\(--vl-space-3\)/);
    expect(layer).not.toMatch(/display:\s*none/);
    expect(layer).not.toMatch(/visibility:\s*hidden/);
  });

  it("переключатель плотности встроен в шапку", () => {
    const header = read("features/shell/ShellHeader.tsx");

    expect(header).toContain("<DensityToggle />");
    expect(read("main.tsx")).toContain("initDensity(documentDensityTarget(), browserDensityStore())");
  });

  it("подписи эргономики только русские", () => {
    const values = Object.values(ERGONOMICS_COPY).map((value) =>
      typeof value === "function" ? value("Плотная") : value,
    );

    expect(values.length).toBeGreaterThanOrEqual(6);
    for (const value of values) {
      expect(value).not.toMatch(/[A-Za-z]/);
    }
  });
});
