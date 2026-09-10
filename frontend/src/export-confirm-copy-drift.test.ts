import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { UI_COPY } from "./lib/ui-copy";

/**
 * FE-DRIFT-01: предупреждение о несохранённом черновике перед выгрузкой живёт в
 * двух местах одновременно.
 *
 * 1. `UI_COPY.exportUnsavedConfirm` — словарь копирайта, единственный источник
 *    текста для оболочки.
 * 2. `EXPORT_UNSAVED_CONFIRM` в `scripts/capture-review-smoke-shared.mjs` —
 *    руками скопированный дубль. Репетиционный помощник `assertUnsavedDialogs`
 *    сверяет перехваченное окно браузера с этим дублем **дословно** и падает на
 *    любом расхождении.
 *
 * Дубль неизбежен: репетиция запускается в Node через Playwright и не может
 * импортировать модуль оболочки на TypeScript. Но до этой проверки связка
 * держалась только на комментарии. Правка одной запятой в словаре красила
 * браузерную репетицию накануне показа, причём с текстом ошибки про расхождение
 * копирайта, который легко принять за дефект продукта.
 *
 * Проверка читает скрипт как текст, а не импортирует его: файл на верхнем уровне
 * подключает Playwright, и его загрузка в vitest тянула бы браузерный стек в
 * обычный прогон тестов.
 */
const SRC_ROOT = dirname(fileURLToPath(import.meta.url));
const SHARED_SMOKE_PATH = join(SRC_ROOT, "..", "scripts", "capture-review-smoke-shared.mjs");

/** Объявление константы: перевод строки после `=` допускается. */
const CONSTANT_PATTERN = /export const EXPORT_UNSAVED_CONFIRM\s*=\s*"([^"]*)"\s*;/;

const sharedSmokeSource = readFileSync(SHARED_SMOKE_PATH, "utf8");

describe("FE-DRIFT-01 unsaved-export warning copy", () => {
  it("keeps the rehearsal constant byte-identical to the product dictionary", () => {
    const match = CONSTANT_PATTERN.exec(sharedSmokeSource);
    expect(
      match,
      "EXPORT_UNSAVED_CONFIRM не найдена в capture-review-smoke-shared.mjs — обновите проверку вместе со скриптом",
    ).toBeTruthy();
    expect(match?.[1]).toBe(UI_COPY.exportUnsavedConfirm);
  });

  it("keeps the drift assertion wired into the rehearsal helper", () => {
    expect(sharedSmokeSource).toContain("assertUnsavedDialogs");
    expect(sharedSmokeSource).toContain("EXPORT_UNSAVED_CONFIRM");
  });

  it("keeps the warning honest about what lands in the file", () => {
    expect(UI_COPY.exportUnsavedConfirm).not.toMatch(/исправлено/);
    expect(UI_COPY.exportUnsavedConfirm.length).toBeGreaterThan(40);
  });
});
