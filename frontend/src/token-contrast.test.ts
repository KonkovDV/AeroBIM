import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const DESIGN_SYSTEM = join(dirname(fileURLToPath(import.meta.url)), "styles", "design-system.css");

function stripComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, " ");
}

function firstRootBlock(css: string): string {
  const start = css.search(/:root\s*\{/);
  if (start < 0) {
    throw new Error("missing :root");
  }
  const open = css.indexOf("{", start);
  let depth = 0;
  for (let index = open; index < css.length; index += 1) {
    const ch = css[index];
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) {
        return css.slice(open + 1, index);
      }
    }
  }
  throw new Error("unclosed :root");
}

function parseDecls(block: string): Map<string, string> {
  const decls = new Map<string, string>();
  for (const part of block.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith("--")) continue;
    const colon = trimmed.indexOf(":");
    if (colon < 0) continue;
    decls.set(trimmed.slice(0, colon).trim(), trimmed.slice(colon + 1).trim());
  }
  return decls;
}

function resolve(name: string, decls: Map<string, string>, seen = new Set<string>()): string {
  if (seen.has(name)) {
    throw new Error(`cycle ${name}`);
  }
  seen.add(name);
  const raw = decls.get(name);
  if (!raw) {
    throw new Error(`missing ${name}`);
  }
  const varMatch = raw.match(/^var\(\s*(--[\w-]+)(?:\s*,\s*(.+))?\s*\)$/);
  if (!varMatch) {
    return raw;
  }
  const inner = varMatch[1];
  if (decls.has(inner)) {
    return resolve(inner, decls, seen);
  }
  if (varMatch[2]) {
    return varMatch[2].trim();
  }
  throw new Error(`unresolved ${name}`);
}

function hexToRgb(hex: string): readonly [number, number, number] {
  const value = hex.trim();
  const match = /^#([\da-f]{3}|[\da-f]{6})$/i.exec(value);
  if (!match) {
    throw new Error(`not hex: ${hex}`);
  }
  const body = match[1];
  if (body.length === 3) {
    return [
      Number.parseInt(body[0] + body[0], 16),
      Number.parseInt(body[1] + body[1], 16),
      Number.parseInt(body[2] + body[2], 16),
    ];
  }
  return [
    Number.parseInt(body.slice(0, 2), 16),
    Number.parseInt(body.slice(2, 4), 16),
    Number.parseInt(body.slice(4, 6), 16),
  ];
}

function channel(value: number): number {
  const scaled = value / 255;
  return scaled <= 0.04045 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4;
}

function luminance(rgb: readonly [number, number, number]): number {
  return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
}

function contrastRatio(foreground: string, background: string): number {
  const left = luminance(hexToRgb(foreground));
  const right = luminance(hexToRgb(background));
  const [hi, lo] = left >= right ? [left, right] : [right, left];
  return (hi + 0.05) / (lo + 0.05);
}

describe("light token contrast (tokens only, not a WCAG certificate)", () => {
  it("keeps text and control pairs above the internal floor on the light :root", () => {
    const decls = parseDecls(firstRootBlock(stripComments(readFileSync(DESIGN_SYSTEM, "utf8"))));
    const hex = (name: string) => resolve(name, decls);
    const textOnCanvas = contrastRatio(hex("--ds-text"), hex("--ds-canvas"));
    const textOnSurface = contrastRatio(hex("--ds-text"), hex("--ds-surface"));
    const mutedOnSurface = contrastRatio(hex("--ds-text-muted"), hex("--ds-surface"));
    const accentOnCanvas = contrastRatio(hex("--ds-accent-text"), hex("--ds-canvas"));
    const onBrand = contrastRatio(hex("--ds-text-on-brand"), hex("--ds-accent"));
    const controlOnSurface = contrastRatio(hex("--ds-border-control"), hex("--ds-surface"));
    expect(textOnCanvas).toBeGreaterThanOrEqual(4.5);
    expect(textOnSurface).toBeGreaterThanOrEqual(4.5);
    expect(mutedOnSurface).toBeGreaterThanOrEqual(4.5);
    expect(accentOnCanvas).toBeGreaterThanOrEqual(4.5);
    expect(onBrand).toBeGreaterThanOrEqual(4.5);
    expect(controlOnSurface).toBeGreaterThanOrEqual(3);
  });
});
