import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ResizableWorkplace from "./ResizableWorkplace";
import { DEFAULT_COLS, MIN_PCT, normalizeCols, resizeCols, type Side } from "./workspace-columns";

const KEY = "aerobim-workspace-cols-v1";
const mount = () => render(<ResizableWorkplace left={<section id="findings-pane">Список</section>}
  center={<section>Доказательство</section>} right={<section>Карточка</section>} />);
const value = (index: number) => Number(screen.getAllByRole("separator")[index].getAttribute("aria-valuenow"));
beforeEach(() => localStorage.clear());
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });

describe("workspace columns", () => {
  it("rejects invalid storage and preserves all three minimum widths", () => {
    for (const raw of [null, [], "bad", {}, { left: Infinity, right: NaN },
      { left: 1000, right: 1000 }, { left: -1, right: 0 }, { left: 28.1, right: 35.7 }]) {
      const cols = normalizeCols(raw);
      expect(Object.values(cols).every((n) => Number.isFinite(n) && n >= MIN_PCT)).toBe(true);
      expect(cols.left + cols.mid + cols.right).toBeCloseTo(100, 8);
    }
  });
  it("resizes only adjacent panes", () => {
    for (const side of ["left", "right"] as Side[]) for (const amount of [-1000, 0, 16, 31.7, 1000, Infinity, NaN]) {
      const result = resizeCols(DEFAULT_COLS, side, amount);
      expect(result[side === "left" ? "right" : "left"]).toBe(DEFAULT_COLS[side === "left" ? "right" : "left"]);
      expect(Math.min(result.left, result.mid, result.right)).toBeGreaterThanOrEqual(MIN_PCT);
      expect(result.left + result.mid + result.right).toBeCloseTo(100, 8);
    }
  });
  it("bounds keyboard resize and preserves pane ids", () => {
    mount();
    const [left, right] = screen.getAllByRole("separator");
    expect(left.tabIndex).toBe(0);
    expect(left.getAttribute("aria-controls")).toBe("findings-pane");
    expect(document.getElementById(right.getAttribute("aria-controls")!)).not.toBeNull();
    fireEvent.keyDown(left, { key: "ArrowRight" });
    expect(value(0)).toBe(30);
    fireEvent.keyDown(right, { key: "ArrowLeft", shiftKey: true });
    expect(value(1)).toBe(46);
    fireEvent.keyDown(left, { key: "End" });
    expect(value(0)).toBe(38);
    fireEvent.keyDown(left, { key: "Home" });
    expect(value(0)).toBe(16);
  });
  it("ignores modified and composing keys", () => {
    mount();
    for (const modifier of [{ ctrlKey: true }, { metaKey: true }, { altKey: true }, { isComposing: true }]) {
      fireEvent.keyDown(screen.getAllByRole("separator")[0], { key: "ArrowRight", ...modifier });
      expect(value(0)).toBe(28);
    }
  });
  it("exposes range controls and a reversible reset", () => {
    mount();
    const details = document.querySelector(".workspace-layout-controls");
    expect(details?.hasAttribute("open")).toBe(false);
    fireEvent.click(screen.getByText("Ширина панелей"));
    expect(details?.hasAttribute("open")).toBe(true);
    fireEvent.change(screen.getByLabelText("Ширина списка, проценты"), { target: { value: "40.5" } });
    expect(value(0)).toBe(40.5);
    fireEvent.click(screen.getByRole("button", { name: "Сбросить ширину" }));
    expect(JSON.parse(localStorage.getItem(KEY)!)).toEqual(DEFAULT_COLS);
  });
  it("survives malformed JSON and blocked storage writes", () => {
    localStorage.setItem(KEY, "{");
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    mount();
    fireEvent.keyDown(screen.getAllByRole("separator")[0], { key: "ArrowRight" });
    expect(value(0)).toBe(30);
  });
});
