import { describe, expect, it } from "vitest";
import { nextPosAfterDecision } from "./useTriageKeyboard";

describe("nextPosAfterDecision", () => {
  it("advances to the next item", () => {
    expect(nextPosAfterDecision(3, 0)).toBe(1);
  });
  it("returns null at end of queue (no wrap back to decided item)", () => {
    expect(nextPosAfterDecision(3, 2)).toBeNull();
    expect(nextPosAfterDecision(0, 0)).toBeNull();
  });
});
