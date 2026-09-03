import { describe, expect, it } from "vitest";
import { computeScrollTopToReveal } from "./finding-scroll";

describe("finding-scroll", () => {
  it("keeps scrollTop when the selected row is already in the window", () => {
    expect(computeScrollTopToReveal(1, 120, 360, 0)).toBe(0);
  });

  it("scrolls down when the selected row sits below the window", () => {
    expect(computeScrollTopToReveal(3, 120, 360, 0)).toBe(120);
  });

  it("scrolls up when the selected row sits above the window", () => {
    expect(computeScrollTopToReveal(0, 120, 360, 240)).toBe(0);
  });
});
