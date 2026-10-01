import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { isLabDemoSeedUiEnabled } from "./lab-demo";

const SRC_ROOT = dirname(fileURLToPath(import.meta.url));

describe("isLabDemoSeedUiEnabled", () => {
  it("is true in the vitest (DEV) run", () => {
    expect(isLabDemoSeedUiEnabled()).toBe(true);
  });

  it("gates only on import.meta.env.DEV in source", () => {
    const src = readFileSync(join(SRC_ROOT, "lab-demo.ts"), "utf8");
    expect(src).toMatch(/import\.meta\.env\.DEV === true/);
    expect(src).not.toMatch(/VITE_/);
  });

  it("keeps App.tsx from mounting the seed panel outside DEV", () => {
    const app = readFileSync(join(SRC_ROOT, "..", "App.tsx"), "utf8");
    expect(app).toMatch(/import\.meta\.env\.DEV\s*\?\s*\(/);
    expect(app).toContain("DemoFixturePanel");
  });
});
