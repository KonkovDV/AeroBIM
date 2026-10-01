import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DirtyLeaveDialog from "./DirtyLeaveDialog";
import { UI_COPY } from "../lib/ui-copy";

const proto = HTMLDialogElement.prototype;
const originalShow = Object.getOwnPropertyDescriptor(proto, "showModal");
const originalClose = Object.getOwnPropertyDescriptor(proto, "close");
beforeEach(() => {
  // jsdom has no top layer; browser smoke covers native containment.
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
const callbacks = () => ({ onSave: vi.fn(), onDiscard: vi.fn(), onStay: vi.fn() });

describe("DirtyLeaveDialog", () => {
  it("describes the decision and initially focuses the safe action", () => {
    const { rerender } = render(<DirtyLeaveDialog {...callbacks()} />);
    const dialog = screen.getByRole("dialog", { name: UI_COPY.dirtyLeaveTitle });
    expect(document.getElementById(dialog.getAttribute("aria-describedby")!)?.textContent)
      .toBe(UI_COPY.dirtyLeaveBody);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: UI_COPY.dirtyLeaveStay }));
    fireEvent.keyDown(document.activeElement!, { key: "Tab" });
    expect(document.activeElement).toBe(screen.getByRole("button", { name: UI_COPY.dirtyLeaveSave }));
    fireEvent.keyDown(document.activeElement!, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(screen.getByRole("button", { name: UI_COPY.dirtyLeaveStay }));
    rerender(<DirtyLeaveDialog {...callbacks()} saveDisabled />);
    expect((screen.getByRole("button", { name: UI_COPY.dirtyLeaveSave }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: UI_COPY.dirtyLeaveStay }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("announces saving and prevents competing navigation until completion", () => {
    const props = callbacks();
    const { rerender } = render(<DirtyLeaveDialog {...props} />);
    fireEvent.click(screen.getByRole("button", { name: UI_COPY.dirtyLeaveSave }));
    expect(props.onSave).toHaveBeenCalledTimes(1);
    rerender(<DirtyLeaveDialog {...props} busy />);
    expect(screen.getByRole("status").textContent).toBe(UI_COPY.savingRemark);
    expect(document.activeElement).toBe(screen.getByRole("dialog"));
    for (const button of screen.getAllByRole("button")) {
      expect((button as HTMLButtonElement).disabled).toBe(true);
      fireEvent.click(button);
    }
    fireEvent(screen.getByRole("dialog"), new Event("cancel", { cancelable: true }));
    expect(props.onSave).toHaveBeenCalledTimes(1);
    expect(props.onStay).not.toHaveBeenCalled();
    expect(props.onDiscard).not.toHaveBeenCalled();
    rerender(<DirtyLeaveDialog {...props} errorMessage={UI_COPY.remarkSaveFailed} />);
    expect(screen.getByRole("alert").textContent).toBe(UI_COPY.remarkSaveFailed);
    expect((screen.getByRole("button", { name: UI_COPY.dirtyLeaveSave }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("keeps shortcuts inside the modal and permits cancel when idle", () => {
    const props = callbacks();
    render(<DirtyLeaveDialog {...props} />);
    const listener = vi.fn();
    window.addEventListener("keydown", listener);
    try {
      fireEvent.keyDown(document.activeElement!, { key: "2", altKey: true });
      fireEvent.keyDown(document.activeElement!, { key: "a", code: "KeyA" });
      expect(listener).not.toHaveBeenCalled();
      fireEvent(screen.getByRole("dialog"), new Event("cancel", { cancelable: true }));
      expect(props.onStay).toHaveBeenCalledTimes(1);
    } finally { window.removeEventListener("keydown", listener); }
  });
});
