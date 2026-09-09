/**
 * Second half of the expert-workplace rehearsal, after
 * capture-review-shell-smoke.mjs has proved the list -> drawing -> card path:
 * the decision itself, plus the draft-vs-confirmed export pair (OA-21) and the
 * jury-laptop checks from WP-FE-26 (loopback-only traffic, 1366x768 / 1280x800,
 * print stylesheet).
 *
 * Local rehearsal against a throwaway dev stack. Not a customer SLA, not a
 * measurement of product accuracy.
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

const COPY = {
  projects: "Проекты",
  saveRemark: "Сохранить правку",
  confirmRemark: "Подтвердить замечание",
  remarkSaved: "Правка сохранена",
  remarkSaveFailed: "Не удалось сохранить",
  confirmed: "Подтверждено",
};

const PANE_TEST_IDS = ["expert-findings-pane", "expert-spatial-pane", "expert-remark-pane"];

export function parseArgs(argv) {
  const options = {
    baseUrl: "http://127.0.0.1:5173",
    outputDir: path.resolve(process.cwd(), "artifacts", "review-decision"),
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const next = argv[index + 1];
    if ((token === "--base-url" || token === "-u") && next) {
      options.baseUrl = next;
      index += 1;
    } else if ((token === "--output-dir" || token === "-o") && next) {
      options.outputDir = path.resolve(next);
      index += 1;
    }
  }
  return options;
}

/** Value paths that differ, so the draft/confirmed delta is reported, not assumed. */
export function diffPaths(left, right, prefix = "<root>") {
  if (Object.is(left, right)) {
    return [];
  }
  const bothObjects =
    typeof left === "object" && left !== null && typeof right === "object" && right !== null;
  if (!bothObjects || Array.isArray(left) !== Array.isArray(right)) {
    return [prefix];
  }
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  const changed = [];
  for (const key of keys) {
    changed.push(...diffPaths(left[key], right[key], `${prefix}.${key}`));
  }
  return changed;
}

/**
 * Only network schemes can leave the laptop. `blob:` (the export download) and
 * `data:` carry an empty host and must not be read as an external origin.
 */
export function externalOrigins(origins) {
  return [...origins].filter((origin) => {
    if (!origin.startsWith("http:") && !origin.startsWith("https:")) {
      return false;
    }
    const host = origin.replace(/^https?:\/\//, "").replace(/:\d+$/, "");
    return !LOOPBACK_HOSTS.has(host);
  });
}

async function paneWidths(page) {
  const widths = {};
  for (const testId of PANE_TEST_IDS) {
    const box = await page.getByTestId(testId).boundingBox();
    widths[testId] = box === null ? 0 : Math.round(box.width);
  }
  return widths;
}

async function exportJson(page, target) {
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 30_000 }),
    page.getByTestId("export-actions").getByRole("button", { name: "JSON", exact: true }).click(),
  ]);
  await download.saveAs(target);
  const errorBanner = page.getByTestId("export-error");
  if ((await errorBanner.count()) > 0) {
    throw new Error(`Export reported a failure: ${await errorBanner.first().textContent()}`);
  }
  return JSON.parse(await readFile(target, "utf8"));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  await mkdir(options.outputDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1366, height: 768 } });

  const requestOrigins = new Set();
  const dialogMessages = [];
  const consoleErrors = [];
  const failedResponses = [];
  const steps = [];
  const note = (step, detail) => {
    steps.push({ step, ...detail });
    console.log(`[decision-smoke] ${step} ${JSON.stringify(detail)}`);
  };

  context.on("request", (request) => {
    try {
      const url = new URL(request.url());
      requestOrigins.add(url.host ? `${url.protocol}//${url.host}` : url.protocol);
    } catch {
      requestOrigins.add("<unparsed>");
    }
  });
  context.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push({ status: response.status(), url: response.url() });
    }
  });

  // saveResponseDownload prefers the File System Access picker, a native dialog
  // that headless Chromium cannot present. Hiding it selects the blob fallback,
  // which is the same production path browsers without that API already take.
  await context.addInitScript(() => {
    Object.defineProperty(window, "showSaveFilePicker", {
      value: undefined,
      configurable: true,
    });
  });

  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("dialog", (dialog) => {
    dialogMessages.push(dialog.message());
    void dialog.accept();
  });

  try {
    await page.goto(options.baseUrl, { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.getByRole("button", { name: COPY.projects, exact: true }).click();
    await page.locator(".report-card").first().waitFor({ state: "visible", timeout: 30_000 });
    await page.locator(".report-card").first().click();

    const issueCards = page.locator(".issue-card");
    await issueCards.first().waitFor({ state: "visible", timeout: 30_000 });
    note("findings-list", { issueCards: await issueCards.count() });
    await issueCards.first().click();
    await page.screenshot({ path: path.join(options.outputDir, "01-findings.png"), fullPage: true });

    const evidencePanel = page.locator(".drawing-evidence-panel");
    await evidencePanel.locator(".drawing-evidence-image").waitFor({ state: "visible", timeout: 30_000 });
    await evidencePanel.locator(".drawing-evidence-rect").waitFor({ state: "visible", timeout: 30_000 });
    note("drawing-evidence", {
      ruleId: (await page.locator(".drawing-evidence-caption strong").first().textContent())?.trim(),
    });
    await page.screenshot({ path: path.join(options.outputDir, "02-drawing.png"), fullPage: true });

    const editor = page.locator("#remark-editor");
    await editor.waitFor({ state: "visible", timeout: 30_000 });
    const savedText = await editor.inputValue();
    const draftText = `${savedText}\nРепетиция стенда: правка эксперта до сохранения.`;
    await editor.fill(draftText);
    note("remark-draft", { savedLength: savedText.length, draftLength: draftText.length });
    await page.screenshot({ path: path.join(options.outputDir, "03-card-draft.png"), fullPage: true });

    const draftExport = await exportJson(page, path.join(options.outputDir, "export-draft.json"));
    note("export-while-dirty", { warnings: [...dialogMessages] });

    await page.getByRole("button", { name: COPY.saveRemark, exact: true }).click();
    // A report that already carries a decision refuses further edits, so surface
    // that instead of timing out: the rehearsal needs a freshly seeded report.
    const savedMarker = page.getByText(COPY.remarkSaved, { exact: true }).first();
    const conflictMarker = page.getByTestId("hitl-conflict");
    const failureMarker = page.getByText(COPY.remarkSaveFailed, { exact: true }).first();
    await Promise.race([
      savedMarker.waitFor({ timeout: 30_000 }),
      conflictMarker.waitFor({ timeout: 30_000 }),
      failureMarker.waitFor({ timeout: 30_000 }),
    ]);
    if ((await savedMarker.count()) === 0) {
      const conflict = (await conflictMarker.count()) > 0 ? await conflictMarker.textContent() : null;
      throw new Error(
        `Remark save did not land (${conflict ?? "no conflict text"}). ` +
          "Re-seed the storage dir: an already-decided finding is not editable.",
      );
    }
    await page.getByRole("button", { name: COPY.confirmRemark, exact: true }).click();
    await page.getByText(COPY.confirmed, { exact: true }).first().waitFor({ timeout: 30_000 });

    const historyRows = page.getByTestId("review-history").locator("li");
    await historyRows.first().waitFor({ state: "visible", timeout: 30_000 });
    note("decision", {
      history: (await historyRows.allTextContents()).map((row) => row.trim()),
    });
    await page.screenshot({ path: path.join(options.outputDir, "04-decision.png"), fullPage: true });

    const dialogsBeforeCleanExport = dialogMessages.length;
    const confirmedExport = await exportJson(
      page,
      path.join(options.outputDir, "export-confirmed.json"),
    );
    note("export-after-decision", {
      extraWarnings: dialogMessages.length - dialogsBeforeCleanExport,
    });
    note("export-diff", {
      changedPaths: [...new Set(diffPaths(draftExport, confirmedExport))].sort(),
    });

    const viewportChecks = [];
    for (const viewport of [
      { width: 1366, height: 768 },
      { width: 1280, height: 800 },
    ]) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(400);
      viewportChecks.push({ viewport, panes: await paneWidths(page) });
      await page.screenshot({
        path: path.join(options.outputDir, `05-viewport-${viewport.width}x${viewport.height}.png`),
        fullPage: true,
      });
    }
    note("viewports", { checks: viewportChecks });

    await page.emulateMedia({ media: "print" });
    await page.pdf({
      path: path.join(options.outputDir, "06-expert-print.pdf"),
      format: "A4",
      printBackground: true,
    });
    await page.emulateMedia({ media: "screen" });

    const external = externalOrigins(requestOrigins);
    note("network", { origins: [...requestOrigins].sort(), external });

    await context.tracing.stop({ path: path.join(options.outputDir, "review-decision.trace.zip") });
    const summary = {
      baseUrl: options.baseUrl,
      outputDir: options.outputDir,
      generatedAt: new Date().toISOString(),
      steps,
      consoleErrors,
      failedResponses,
      externalOrigins: external,
    };
    await writeFile(
      path.join(options.outputDir, "review-decision-summary.json"),
      `${JSON.stringify(summary, null, 2)}\n`,
      "utf8",
    );

    if (external.length > 0) {
      throw new Error(`Rehearsal must stay on loopback, saw: ${external.join(", ")}`);
    }
    console.log(
      JSON.stringify({ ok: true, consoleErrors, failedResponses, externalOrigins: external }, null, 2),
    );
  } finally {
    await browser.close();
  }
}

const invokedDirectly = process.argv[1]
  ? import.meta.url === pathToFileURL(process.argv[1]).href
  : false;

if (invokedDirectly) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
