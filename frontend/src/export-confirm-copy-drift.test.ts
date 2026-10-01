import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { UI_COPY } from "./lib/ui-copy";

/**
 * FE-DRIFT-01: предупреждение о несохранённом черновике перед выгрузкой живёт в
 * двух местах одновременно.
 *
 * 1. `UI_COPY.exportUnsavedConfirm` и `UI_COPY.exportUnsavedContinue` — словарь
 *    копирайта, единственный источник текста для оболочки.
 * 2. `EXPORT_UNSAVED_CONFIRM` и `EXPORT_UNSAVED_CONTINUE` в
 *    `scripts/capture-review-smoke-shared.mjs` — руками скопированные дубли.
 *    Репетиционный помощник `assertUnsavedDialogs` сверяет прочитанное
 *    предупреждение с этим дублем **дословно** и падает на любом расхождении.
 *
 * Дубль неизбежен: репетиция запускается в Node через Playwright и не может
 * импортировать модуль оболочки на TypeScript. Но до этой проверки связка
 * держалась только на комментарии. Правка одной запятой в словаре красила
 * браузерную репетицию накануне показа, причём с текстом ошибки про расхождение
 * копирайта, который легко принять за дефект продукта.
 *
 * После FE-CRUFT-02 предупреждение показывает не браузер, а сама оболочка,
 * поэтому репетиция ищет его по идентификаторам разметки. Эти идентификаторы —
 * такой же дубль, как и текст: если разметку переименуют, репетиция перестанет
 * видеть предупреждение и молча признает выгрузку чистой.
 *
 * Проверка читает скрипты как текст, а не импортирует их: файл на верхнем уровне
 * подключает Playwright, и его загрузка в vitest тянула бы браузерный стек в
 * обычный прогон тестов.
 */
const SRC_ROOT = dirname(fileURLToPath(import.meta.url));
const SHARED_SMOKE_PATH = join(SRC_ROOT, "..", "scripts", "capture-review-smoke-shared.mjs");
const DECISION_SMOKE_PATH = join(SRC_ROOT, "..", "scripts", "capture-review-decision-smoke.mjs");
const DIALOG_PATH = join(SRC_ROOT, "features", "export", "ExportUnsavedDialog.tsx");

/** Объявление константы: перевод строки после `=` допускается. */
const CONSTANT_PATTERN = /export const EXPORT_UNSAVED_CONFIRM\s*=\s*"([^"]*)"\s*;/;
const CONTINUE_PATTERN = /export const EXPORT_UNSAVED_CONTINUE\s*=\s*"([^"]*)"\s*;/;
const DIALOG_ID_PATTERN = /export const EXPORT_UNSAVED_DIALOG\s*=\s*"([^"]*)"\s*;/;
const MESSAGE_ID_PATTERN = /export const EXPORT_UNSAVED_MESSAGE\s*=\s*"([^"]*)"\s*;/;

const sharedSmokeSource = readFileSync(SHARED_SMOKE_PATH, "utf8");
const decisionSmokeSource = readFileSync(DECISION_SMOKE_PATH, "utf8");
const dialogSource = readFileSync(DIALOG_PATH, "utf8");

describe("FE-DRIFT-01 unsaved-export warning copy", () => {
  it("keeps the rehearsal constants byte-identical to the product dictionary", () => {
    const match = CONSTANT_PATTERN.exec(sharedSmokeSource);
    expect(
      match,
      "EXPORT_UNSAVED_CONFIRM не найдена в capture-review-smoke-shared.mjs — обновите проверку вместе со скриптом",
    ).toBeTruthy();
    expect(match?.[1]).toBe(UI_COPY.exportUnsavedConfirm);

    const continueMatch = CONTINUE_PATTERN.exec(sharedSmokeSource);
    expect(
      continueMatch,
      "EXPORT_UNSAVED_CONTINUE не найдена в capture-review-smoke-shared.mjs — репетиция не сможет подтвердить выгрузку",
    ).toBeTruthy();
    expect(continueMatch?.[1]).toBe(UI_COPY.exportUnsavedContinue);
  });

  it("keeps the drift assertion wired into the rehearsal helper", () => {
    expect(sharedSmokeSource).toContain("assertUnsavedDialogs");
    expect(sharedSmokeSource).toContain("EXPORT_UNSAVED_CONFIRM");
    expect(sharedSmokeSource).toMatch(/message !== EXPORT_UNSAVED_CONFIRM/);
    expect(sharedSmokeSource).toContain("unsaved confirm copy drifted");
    expect(sharedSmokeSource).toContain("settleUnsavedExportDialog");
  });

  it("keeps the rehearsal reading the in-app dialog, not a browser modal (FE-CRUFT-02)", () => {
    const dialogId = DIALOG_ID_PATTERN.exec(sharedSmokeSource)?.[1];
    const messageId = MESSAGE_ID_PATTERN.exec(sharedSmokeSource)?.[1];
    expect(dialogId, "EXPORT_UNSAVED_DIALOG не найдена в репетиционном помощнике").toBeTruthy();
    expect(messageId, "EXPORT_UNSAVED_MESSAGE не найдена в репетиционном помощнике").toBeTruthy();
    expect(dialogSource).toContain(`data-testid="${dialogId}"`);
    expect(dialogSource).toContain(`data-testid="${messageId}"`);
    // Нативная модалка теперь не шаг сценария, а причина падения репетиции.
    expect(decisionSmokeSource).toContain("assertNoNativeDialogs");
  });

  it("keeps the warning honest about what lands in the file", () => {
    expect(UI_COPY.exportUnsavedConfirm).not.toMatch(/исправлено/);
    expect(UI_COPY.exportUnsavedConfirm.length).toBeGreaterThan(40);
  });
});
