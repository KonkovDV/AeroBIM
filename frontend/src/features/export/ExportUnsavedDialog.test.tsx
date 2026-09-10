import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ExportUnsavedDialog from "./ExportUnsavedDialog";
import { UI_COPY } from "../../lib/ui-copy";

/**
 * FE-CRUFT-02. Проверяется не «красиво ли», а четыре свойства, без которых
 * замена нативного окна была бы регрессом доступности:
 * 1) диалог назван и описан (заголовок + текст предупреждения);
 * 2) фокус начинается с безопасного действия и не покидает диалог;
 * 3) клавиша выхода равна отказу, а горячие клавиши триажа не срабатывают
 *    за спиной у модального окна;
 * 4) решение возвращается вызывающей стороне ровно один раз.
 */
const dialogProto = HTMLDialogElement.prototype;
const nativeShowModal = Object.getOwnPropertyDescriptor(dialogProto, "showModal");
const nativeClose = Object.getOwnPropertyDescriptor(dialogProto, "close");

beforeEach(() => {
  // jsdom не строит верхний слой; подменяются только два метода открытия.
  Object.defineProperties(dialogProto, {
    showModal: {
      configurable: true,
      value: function showModal(this: HTMLDialogElement) {
        this.setAttribute("open", "");
      },
    },
    close: {
      configurable: true,
      value: function close(this: HTMLDialogElement) {
        this.removeAttribute("open");
      },
    },
  });
});

afterEach(() => {
  cleanup();
  if (nativeShowModal) {
    Object.defineProperty(dialogProto, "showModal", nativeShowModal);
  }
  if (nativeClose) {
    Object.defineProperty(dialogProto, "close", nativeClose);
  }
});

function handlers() {
  return { onConfirm: vi.fn(), onCancel: vi.fn() };
}

describe("ExportUnsavedDialog", () => {
  it("names the decision and starts from the safe button", () => {
    const props = handlers();
    render(<ExportUnsavedDialog formatLabel="JSON" {...props} />);
    const dialog = screen.getByRole("alertdialog", { name: UI_COPY.exportUnsavedTitle });
    const messageId = dialog.getAttribute("aria-describedby");
    expect(document.getElementById(messageId as string)?.textContent).toBe(
      UI_COPY.exportUnsavedConfirm,
    );
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: UI_COPY.exportUnsavedCancel }),
    );
    expect(props.onConfirm).not.toHaveBeenCalled();
    expect(props.onCancel).not.toHaveBeenCalled();
  });

  it("keeps the tab ring inside the dialog", () => {
    const props = handlers();
    render(<ExportUnsavedDialog formatLabel="JSON" {...props} />);
    const cancel = screen.getByRole("button", { name: UI_COPY.exportUnsavedCancel });
    const proceed = screen.getByRole("button", { name: UI_COPY.exportUnsavedContinue });

    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(proceed);

    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Tab" });
    expect(document.activeElement).toBe(cancel);
  });

  it("treats the escape key as a refusal and hides triage hotkeys", () => {
    const props = handlers();
    render(<ExportUnsavedDialog formatLabel="BCF" {...props} />);
    const escaped = vi.fn();
    document.addEventListener("keydown", escaped);
    try {
      fireEvent.keyDown(document.activeElement as HTMLElement, { key: "j" });
      expect(escaped).not.toHaveBeenCalled();
    } finally {
      document.removeEventListener("keydown", escaped);
    }

    fireEvent(screen.getByRole("alertdialog"), new Event("cancel", { cancelable: true }));
    expect(props.onCancel).toHaveBeenCalledTimes(1);
    expect(props.onConfirm).not.toHaveBeenCalled();
  });

  it("reports the decision once and names the format in question", () => {
    const props = handlers();
    render(<ExportUnsavedDialog formatLabel="BCF 3.0" {...props} />);
    expect(screen.getByTestId("export-unsaved-format").textContent).toBe(
      UI_COPY.exportUnsavedFormat("BCF 3.0"),
    );
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.exportUnsavedContinue }));
    expect(props.onConfirm).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.exportUnsavedCancel }));
    expect(props.onCancel).toHaveBeenCalledTimes(1);
  });
});
