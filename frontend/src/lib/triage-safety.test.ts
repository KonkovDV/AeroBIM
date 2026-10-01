import { describe, expect, it } from "vitest";
import { isTextEntryTarget, resolveTriageHotkey } from "./triage-hotkeys";

describe("triage input ownership", () => {
  it.each(["a", "r", "e", "?"])("does not repeat %s", (key) => {
    expect(resolveTriageHotkey({ key, repeat: true })).toBeNull();
  });
  it.each(["j", "ArrowDown"])("keeps repeated navigation: %s", (key) => {
    expect(resolveTriageHotkey({ key, repeat: true })).toBe("next");
  });
  it.each(["k", "ArrowUp"])("keeps repeated navigation: %s", (key) => {
    expect(resolveTriageHotkey({ key, repeat: true })).toBe("prev");
  });
  it("does not commit a composing or consumed event", () => {
    expect(resolveTriageHotkey({ key: "a", isComposing: true })).toBeNull();
    expect(resolveTriageHotkey({ key: "r", defaultPrevented: true })).toBeNull();
    expect(resolveTriageHotkey({ key: "Escape", defaultPrevented: true })).toBeNull();
  });
  it("retains physical Russian-layout keys and browser shortcuts", () => {
    expect(resolveTriageHotkey({ key: "ф", code: "KeyA" })).toBe("accept");
    expect(resolveTriageHotkey({ key: "к", code: "KeyR", repeat: true })).toBeNull();
    expect(resolveTriageHotkey({ key: "r", ctrlKey: true })).toBeNull();
    expect(resolveTriageHotkey({ key: "a", metaKey: true })).toBeNull();
  });
  it.each(['dialog open', 'div aria-modal="true"', 'div role="slider"',
    'div role="separator"', 'div role="combobox"', 'div contenteditable="true"'])
  ("lets a focused widget own its events: %s", (attributes) => {
    const container = document.createElement("div");
    const tag = attributes.split(" ")[0];
    container.innerHTML = `<${attributes}><span>target</span></${tag}>`;
    expect(isTextEntryTarget(container.querySelector("span"))).toBe(true);
  });
  it("does not block ordinary finding cards", () => {
    const button = document.createElement("button");
    button.setAttribute("role", "option");
    expect(isTextEntryTarget(button)).toBe(false);
    expect(isTextEntryTarget(null)).toBe(false);
  });
});
