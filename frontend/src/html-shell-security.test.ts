import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const FRONTEND_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("review shell html security", () => {
  const html = readFileSync(join(FRONTEND_ROOT, "index.html"), "utf8");
  const viteConfig = readFileSync(join(FRONTEND_ROOT, "vite.config.ts"), "utf8");

  it("declares Russian as the document language", () => {
    expect(html).toMatch(/<html lang="ru">/);
    expect(html).not.toMatch(/<html lang="en">/);
    expect(html).toMatch(/<title>AeroBIM — проверка комплекта<\/title>/);
    expect(html).toMatch(/name="color-scheme" content="light"/);
  });

  it("pins referrer, nosniff, permissions, and a self CSP with wasm-unsafe-eval only", () => {
    expect(html).toMatch(/<meta name="referrer" content="no-referrer" \/>/);
    expect(html).toMatch(/http-equiv="X-Content-Type-Options" content="nosniff"/);
    expect(html).toMatch(/http-equiv="Permissions-Policy"/);
    expect(html).toMatch(/http-equiv="Content-Security-Policy"/);
    const csp = html.match(/http-equiv="Content-Security-Policy"\s+content="([^"]*)"/);
    expect(csp?.[1]).toContain("default-src 'self'");
    expect(csp?.[1]).toContain("script-src 'self' 'wasm-unsafe-eval'");
    expect(csp?.[1]).not.toContain("unsafe-inline");
    expect(csp?.[1]).not.toContain("script-src 'self' 'unsafe-eval'");
  });

  it("documents that Vite HMR may add unsafe-eval only in the dev transform", () => {
    expect(viteConfig).toContain("wasm-unsafe-eval");
    expect(viteConfig).toContain("aerobim-html-security");
  });

  it("allows Vite's injected style tag in DEV_CSP only", () => {
    expect(viteConfig).toMatch(/style-src 'self' 'unsafe-inline'/);
    expect(html).not.toMatch(/style-src 'self' 'unsafe-inline'/);
  });
});
