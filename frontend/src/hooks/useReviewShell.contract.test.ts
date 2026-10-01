import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("C574-01 review shell HITL contract", () => {
  it("does not call a mutable expert-decision setter", () => {
    const src = readFileSync(join(here, "useReviewShell.ts"), "utf8");
    expect(src).not.toContain("setHitlDecisionState");
    expect(src).toContain("changeDraft");
  });
});
