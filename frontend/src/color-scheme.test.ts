import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SRC_ROOT = dirname(fileURLToPath(import.meta.url));
const STYLES_ROOT = join(SRC_ROOT, "styles");
const ROOT_CSS = join(SRC_ROOT, "styles.css");
const MAIN_TSX = join(SRC_ROOT, "main.tsx");
const FORCE_LIGHT = join(STYLES_ROOT, "force-light.css");

function walkCss(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      walkCss(full, out);
    } else if (name.endsWith(".css")) {
      out.push(full);
    }
  }
  return out;
}

function stripComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, " ");
}

/** CSS property `color-scheme`, not the `prefers-color-scheme` media feature. */
function colorSchemePropertyValues(text: string): string[] {
  const values: string[] = [];
  const re = /(?:^|[\s;{])color-scheme\s*:\s*([^;}]+)/g;
  let match: RegExpExecArray | null = re.exec(text);
  while (match) {
    values.push(match[1].trim());
    match = re.exec(text);
  }
  return values;
}

describe("forced light color-scheme for jury laptops", () => {
  it("does not advertise dark color-scheme on the color-scheme property", () => {
    const files = [ROOT_CSS, ...walkCss(STYLES_ROOT)];
    const hits: string[] = [];
    for (const file of files) {
      const values = colorSchemePropertyValues(stripComments(readFileSync(file, "utf8")));
      if (values.some((value) => value !== "light")) {
        hits.push(`${file.replace(/\\/g, "/")} → ${values.join(", ")}`);
      }
    }
    expect(hits).toEqual([]);
  });

  it("loads force-light.css last so OS dark media queries cannot mix palettes", () => {
    const main = readFileSync(MAIN_TSX, "utf8");
    const cssImports = [...main.matchAll(/import "([^"]+\.css)";/g)].map((row) => row[1]);
    expect(cssImports.at(-1)).toBe("./styles/force-light.css");
    const lock = readFileSync(FORCE_LIGHT, "utf8");
    expect(lock).toContain("color-scheme: light");
    expect(lock).toContain(".nav-badge");
    expect(lock).toContain(".toolbar-button.toolbar-button-primary");
    expect(lock).toContain(".pack-cycle-step-current");
    expect(lock).toContain(".keyboard-help-dialog.dirty-leave-dialog");
  });
});
