import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * HD13-FE-01: source-scan (not runtime). UI may display server
 * ``summary.passed`` / ``summary.outcome`` and mention them in honesty copy.
 * It must not assign them. Covers MachineGatewayStrip, PackCycleStrip, App,
 * and every other production ``.ts`` / ``.tsx`` under ``src/``.
 */
const SRC_ROOT = dirname(fileURLToPath(import.meta.url));

const SKIP_NAME = /\.(test|spec)\.(ts|tsx)$/;
const SOURCE_NAME = /\.(ts|tsx)$/;

/** Statement-like assignment to summary.passed / summary.outcome. */
const ASSIGN_FIELD =
  /(?:^|[;\n{}()])\s*(?:[A-Za-z_$][\w$]*\.)*summary\s*\.\s*(?:passed|outcome)\s*=(?!=)/g;

/** Replacing the whole summary object (``report.summary = { ... }``). */
const ASSIGN_OBJECT = /(?:^|[;\n{}()])\s*(?:[A-Za-z_$][\w$]*\.)+summary\s*=(?!=)/g;

/** Bracket assignment: summary["passed"] = / summary['outcome'] = */
const ASSIGN_BRACKET =
  /summary\s*\[\s*['"](?:passed|outcome)['"]\s*\]\s*=(?!=)/g;
const LITERAL_SUMMARY_PASSED =
  /\bsummary\s*:\s*\{(?:[^{}]*)\bpassed\s*:\s*(?:true|false)/g;
const LITERAL_SUMMARY_OUTCOME =
  /\bsummary\s*:\s*\{(?:[^{}]*)\boutcome\s*:\s*["'`]/g;

function walkSourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "dist") {
      continue;
    }
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      out.push(...walkSourceFiles(full));
      continue;
    }
    if (SKIP_NAME.test(name) || !SOURCE_NAME.test(name)) {
      continue;
    }
    out.push(full);
  }
  return out;
}

function collectMatches(source: string, pattern: RegExp): number[] {
  const hits: number[] = [];
  const re = new RegExp(pattern.source, pattern.flags);
  let match: RegExpExecArray | null = re.exec(source);
  while (match) {
    hits.push(match.index);
    match = re.exec(source);
  }
  return hits;
}

function lineOf(source: string, index: number): number {
  return source.slice(0, index).split("\n").length;
}

describe("HD13-FE-01 summary.passed source-scan", () => {
  const files = walkSourceFiles(SRC_ROOT);

  it("walks production ts/tsx including workplace strips", () => {
    const rel = files.map((file) => relative(SRC_ROOT, file).replaceAll("\\", "/"));
    expect(rel.length).toBeGreaterThan(20);
    expect(rel).toContain("App.tsx");
    expect(rel).toContain("components/VerticalSliceKt2.tsx");
    expect(rel).toContain("features/workplace/MachineGatewayStrip.tsx");
    expect(rel).toContain("features/workplace/PackCycleStrip.tsx");
    expect(rel).toContain("features/honesty/RoleHonestyBanner.tsx");
    expect(rel).toContain("lib/ui-copy.ts");
    expect(rel).toContain("hooks/usePackDraft.ts");
    expect(rel.every((path) => !path.includes(".test."))).toBe(true);
  });

  it("does not assign summary.passed or summary.outcome in production UI", () => {
    const violations: string[] = [];
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      const rel = relative(SRC_ROOT, file).replaceAll("\\", "/");
      for (const [label, pattern] of [
        ["field assignment", ASSIGN_FIELD],
        ["summary object replacement", ASSIGN_OBJECT],
        ["literal summary.passed", LITERAL_SUMMARY_PASSED],
        ["literal summary.outcome", LITERAL_SUMMARY_OUTCOME],
        ["bracket assignment", ASSIGN_BRACKET],
      ] as const) {
        for (const index of collectMatches(source, pattern)) {
          violations.push(`${rel}:${lineOf(source, index)} ${label}`);
        }
      }
    }
    expect(violations).toEqual([]);
  });
});
