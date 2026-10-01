import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import KeyboardHelpDialog from "./KeyboardHelpDialog";

function Harness() {
  const [open, setOpen] = useState(false);
  const [enabled, setEnabled] = useState(true);
  return <>
    <button onClick={() => setOpen(true)}>Справка</button>
    {open ? <KeyboardHelpDialog onClose={() => setOpen(false)}
      shortcutsEnabled={enabled} onShortcutsChange={setEnabled} /> : null}
  </>;
}

describe("KeyboardHelpDialog", () => {
  const proto = HTMLDialogElement.prototype;
  const originalShow = Object.getOwnPropertyDescriptor(proto, "showModal");
  const originalClose = Object.getOwnPropertyDescriptor(proto, "close");
  beforeEach(() => {
    // JSDOM lacks the native top layer; real focus trapping is browser-tested.
    Object.defineProperties(proto, {
      showModal: { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } },
      close: { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } },
    });
  });
  afterEach(() => {
    cleanup();
    if (originalShow) Object.defineProperty(proto, "showModal", originalShow);
    else Reflect.deleteProperty(proto, "showModal");
    if (originalClose) Object.defineProperty(proto, "close", originalClose);
    else Reflect.deleteProperty(proto, "close");
  });

  it("opens as a named modal, focuses close and returns focus", () => {
    render(<Harness />);
    const opener = screen.getByRole("button", { name: "Справка" });
    opener.focus();
    fireEvent.click(opener);
    const dialog = screen.getByRole("dialog", { name: "Справка клавиатуры триажа" });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    const close = screen.getByRole("button", { name: "Закрыть" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(close, { key: "Tab", shiftKey: true });
    const preference = screen.getByRole("checkbox");
    expect(document.activeElement).toBe(preference);
    fireEvent.keyDown(preference, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.click(close);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("handles native cancel and restores scroll", () => {
    document.body.style.overflow = "auto";
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Справка" }));
    expect(document.body.style.overflow).toBe("hidden");
    fireEvent(screen.getByRole("dialog"), new Event("cancel", { bubbles: true, cancelable: true }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.body.style.overflow).toBe("auto");
    document.body.style.overflow = "";
  });

  it("blocks window shortcuts and allows disabling character commands", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Справка" }));
    const listener = vi.fn();
    window.addEventListener("keydown", listener);
    try {
      const close = screen.getByRole("button", { name: "Закрыть" });
      fireEvent.keyDown(close, { key: "a", code: "KeyA" });
      fireEvent.keyDown(close, { key: "2", altKey: true });
      expect(listener).not.toHaveBeenCalled();
      const checkbox = screen.getByRole("checkbox", { name: "Быстрые клавиши триажа" });
      fireEvent.click(checkbox);
      expect((checkbox as HTMLInputElement).checked).toBe(false);
    } finally {
      window.removeEventListener("keydown", listener);
    }
  });
});
