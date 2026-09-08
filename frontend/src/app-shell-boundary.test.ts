import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

it("keeps App within the review-shell composition boundary", () => {
  const source = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "App.tsx"), "utf8");
  expect(source.trimEnd().split(/\r?\n/).length).toBeLessThanOrEqual(300);
  expect(source).toContain('lazy(() => import("./components/IfcViewerPanel"))');
});
