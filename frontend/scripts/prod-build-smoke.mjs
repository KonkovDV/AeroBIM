/**
 * Production-build smoke: opens the seeded IFC fixture in the `vite build`
 * output served by `vite preview`, then asserts the viewer canvas is not
 * blank, the console stayed free of errors and the bundled CSS applied,
 * then visits every main workplace screen (one screenshot each).
 *
 * Usage: node scripts/prod-build-smoke.mjs --base-url http://127.0.0.1:4173 --out <dir> --tag <label>
 */
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import {
  launchChromium,
  unexpectedConsoleErrors,
  unexpectedHttpFailures,
  waitForViewerReady,
} from "./capture-review-smoke-shared.mjs";

function parseCli(argv) {
  const options = { baseUrl: "http://127.0.0.1:4173", out: "prod-smoke", tag: "build" };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const next = argv[i + 1];
    if (flag === "--base-url") options.baseUrl = next;
    else if (flag === "--out") options.out = next;
    else if (flag === "--tag") options.tag = next;
    else continue;
    i += 1;
  }
  return options;
}

/** Decode a PNG in the page and count distinct colours (model pixels vs background). */
async function canvasColourStats(page, pngBuffer) {
  const dataUrl = `data:image/png;base64,${pngBuffer.toString("base64")}`;
  return page.evaluate(async (src) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.naturalWidth;
    c.height = img.naturalHeight;
    const ctx = c.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const { data } = ctx.getImageData(0, 0, c.width, c.height);
    // Background = most frequent quantised colour; "model" pixels differ
    // from it by > 48 on some channel. Grid-only (no geometry) measures ~0.011
    // locally; the two-box fixture ~0.068, so the gate is 0.03.
    const counts = new Map();
    const px = [];
    for (let i = 0; i < data.length; i += 16) {
      const key = `${data[i] >> 3},${data[i + 1] >> 3},${data[i + 2] >> 3}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
      px.push([data[i], data[i + 1], data[i + 2]]);
    }
    const [bgKey] = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    const bg = bgKey.split(",").map((v) => Number(v) * 8 + 4);
    const solid = px.filter((p) => p.some((v, k) => Math.abs(v - bg[k]) > 48)).length;
    return {
      width: c.width,
      height: c.height,
      distinctColours: counts.size,
      modelPixelRatio: Number((solid / px.length).toFixed(4)),
    };
  }, dataUrl);
}

/** Main workplace screens: nav label → a locator that only that screen renders. */
const SCREENS = [
  { id: "projects", label: "Проекты", marker: '[data-testid="projects-index"]' },
  { id: "upload", label: "Загрузка", marker: ".workspace-alt" },
  { id: "run", label: "Прогон", marker: ".workspace-alt" },
  { id: "review", label: "Эксперт", marker: '[data-testid="expert-findings-pane"]' },
  { id: "remark", label: "Замечание", marker: '[data-testid="expert-remark-pane"]' },
  { id: "export", label: "Экспорт", marker: '[data-testid="export-preview"]' },
  { id: "diff", label: "Версии", marker: '[data-testid="version-diff-panel"]' },
  { id: "user", label: "Эффект", marker: ".workspace-alt" },
];

async function visitScreens(page, options) {
  const nav = page.getByTestId("workspace-nav");
  const results = [];
  for (const screen of SCREENS) {
    const button = nav.getByRole("button", { name: screen.label, exact: true });
    await button.click();
    const marker = page.locator(screen.marker).first();
    await marker.waitFor({ state: "visible", timeout: 15_000 });
    const current = await button.getAttribute("aria-current");
    if (current !== "page") {
      throw new Error(`${screen.id}: nav button not marked current (aria-current=${current})`);
    }
    const textLength = (await marker.innerText()).trim().length;
    if (textLength < 20) {
      throw new Error(`${screen.id}: screen marker ${screen.marker} rendered almost no text`);
    }
    const boundaryErrors = await page.locator('.viewer-status-error, [data-testid="ifc-viewer-error-boundary"]').count();
    if (boundaryErrors > 0) {
      throw new Error(`${screen.id}: an error boundary rendered`);
    }
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(options.out, `${options.tag}-screen-${screen.id}.png`) });
    results.push({ id: screen.id, textLength });
  }
  return results;
}

async function main() {
  const options = parseCli(process.argv.slice(2));
  await mkdir(options.out, { recursive: true });
  const consoleErrors = [];
  const failedResponses = [];
  const browser = await launchChromium();
  const checks = {};
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));
    page.on("response", (res) => {
      if (res.status() >= 400) failedResponses.push({ status: res.status(), url: res.url() });
    });

    await page.goto(options.baseUrl, { waitUntil: "load", timeout: 30_000 });

    checks.css = await page.evaluate(() => {
      const sheets = [...document.styleSheets].filter((s) => s.href && s.href.includes("/assets/"));
      const rules = sheets.reduce((n, s) => n + s.cssRules.length, 0);
      return { bundledSheets: sheets.length, rules, bodyFont: getComputedStyle(document.body).fontFamily };
    });
    if (checks.css.bundledSheets === 0 || checks.css.rules === 0) {
      throw new Error(`bundled CSS did not load: ${JSON.stringify(checks.css)}`);
    }

    await page.getByRole("button", { name: "Проекты", exact: true }).click();
    const card = page.locator(".report-card").first();
    await card.waitFor({ state: "visible", timeout: 30_000 });
    await card.click();
    await waitForViewerReady(page);

    const canvas = page.locator("canvas").first();
    await canvas.waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(1_500);
    const canvasPng = await canvas.screenshot();
    checks.canvas = await canvasColourStats(page, canvasPng);
    if (checks.canvas.modelPixelRatio < 0.03) {
      throw new Error(`viewer canvas looks blank: ${JSON.stringify(checks.canvas)}`);
    }

    await page.screenshot({ path: path.join(options.out, `${options.tag}-viewer.png`), fullPage: false });
    await writeFile(path.join(options.out, `${options.tag}-canvas.png`), canvasPng);

    checks.screens = await visitScreens(page, options);

    // Only the documented GET /v1/auth/bff = 501 default is tolerated
    // (shared filter used by the other review-shell smokes).
    const badHttp = unexpectedHttpFailures(failedResponses);
    const badConsole = unexpectedConsoleErrors(consoleErrors);
    if (badHttp.length > 0 || badConsole.length > 0) {
      throw new Error(`console/network errors: ${JSON.stringify({ badHttp, badConsole })}`);
    }
  } finally {
    checks.consoleErrors = consoleErrors;
    checks.failedResponses = failedResponses;
    await writeFile(path.join(options.out, `${options.tag}-checks.json`), JSON.stringify(checks, null, 2));
    await browser.close();
  }
  console.log(JSON.stringify({ tag: options.tag, ok: true, checks }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
