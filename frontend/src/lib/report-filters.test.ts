import { describe, expect, it } from "vitest";
import { normalizePresetScope } from "./report-filters";

describe("normalizePresetScope", () => {
  it("maps legacy team/local labels to browser vs JSON file exchange", () => {
    expect(normalizePresetScope("team")).toBe("file");
    expect(normalizePresetScope("file")).toBe("file");
    expect(normalizePresetScope("local")).toBe("browser");
    expect(normalizePresetScope("browser")).toBe("browser");
    expect(normalizePresetScope("cde")).toBe("browser");
  });
});
