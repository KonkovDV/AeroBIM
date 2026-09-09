/**
 * Second half of the expert-workplace rehearsal, after
 * capture-review-shell-smoke.mjs has proved the list -> drawing -> card path:
 * the decision itself, plus the draft-vs-confirmed export pair (OA-21) across
 * HTML / JSON / BCF 2.1 / PDF, and the jury-laptop checks from WP-FE-26
 * (loopback-only traffic, 1366x768 / 1280x800, print stylesheet).
 *
 * Local rehearsal against a throwaway Vite-dev stack. Not a customer SLA, not
 * a measurement of product accuracy, not `python -m aerobim.tools.run_kt3_jury`.
 */
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

import {
  COPY,
  EXPORT_UNSAVED_CONFIRM,
  OA21_NEEDLE,
  STACK_VITE_DEV,
  assertForcedLight,
  assertHonestyOnExpertScreen,
  assertLoopbackAndQuiet,
  assertUnsavedDialogs,
  attachNetworkGuards,
  captureExportBundle,
  exerciseTriageKeys,
  externalOrigins,
  hideSaveFilePicker,
  inspectExportBundle,
  isExpectedHonestyFailure,
  launchChromium,
  unexpectedConsoleErrors,
  unexpectedHttpFailures,
  waitForViewerReady,
} from "./capture-review-smoke-shared.mjs";

const ACTION = {
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

export { externalOrigins, isExpectedHonestyFailure, unexpectedConsoleErrors, unexpectedHttpFailures };

async function paneWidths(page) {
  const widths = {};
  for (const testId of PANE_TEST_IDS) {
    const box = await page.getByTestId(testId).boundingBox();
    widths[testId] = box === null ? 0 : Math.round(box.width);
  }
  return widths;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  await mkdir(options.outputDir, { recursive: true });

  const browser = await launchChromium();
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    colorScheme: "dark",
  });

  const { requestOrigins, failedResponses, consoleErrors } = attachNetworkGuards(context);
  const dialogMessages = [];
  const steps = [];
  const note = (step, detail) => {
    steps.push({ step, ...detail });
    console.log(`[decision-smoke] ${step} ${JSON.stringify(detail)}`);
  };

  await context.addInitScript(hideSaveFilePicker);
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
    const colorScheme = await assertForcedLight(page);
    note("color-scheme", { emulated: "dark", computed: colorScheme });

    await page.getByRole("button", { name: COPY.projects, exact: true }).click();
    await page.locator(".report-card").first().waitFor({ state: "visible", timeout: 30_000 });
    await page.locator(".report-card").first().click();

    const issueCards = page.locator(".issue-card");
    await issueCards.first().waitFor({ state: "visible", timeout: 30_000 });
    note("findings-list", { issueCards: await issueCards.count() });
    await issueCards.first().click();
    await page.screenshot({ path: path.join(options.outputDir, "01-findings.png"), fullPage: true });

    const honesty = await assertHonestyOnExpertScreen(page);
    note("honesty", honesty);

    const viewer = await waitForViewerReady(page);
    note("viewer", viewer);

    const keys = await exerciseTriageKeys(page);
    note("triage-keys", keys);

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
    const draftText = `${savedText}\n${OA21_NEEDLE}: правка эксперта до сохранения.`;
    await editor.fill(draftText);
    note("remark-draft", { savedLength: savedText.length, draftLength: draftText.length });
    await page.screenshot({ path: path.join(options.outputDir, "03-card-draft.png"), fullPage: true });

    const draftBundle = await captureExportBundle(page, options.outputDir, "draft");
    assertUnsavedDialogs(dialogMessages);
    const draftInspect = inspectExportBundle({ ...draftBundle, phase: "draft" });
    note("export-while-dirty", {
      warnings: [...dialogMessages],
      confirmCopy: EXPORT_UNSAVED_CONFIRM,
      formats: draftInspect,
    });

    await page.getByRole("button", { name: ACTION.saveRemark, exact: true }).click();
    const savedMarker = page.getByText(ACTION.remarkSaved, { exact: true }).first();
    const conflictMarker = page.getByTestId("hitl-conflict");
    const failureMarker = page.getByText(ACTION.remarkSaveFailed, { exact: true }).first();
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
    await page.getByRole("button", { name: ACTION.confirmRemark, exact: true }).click();
    await page.getByText(ACTION.confirmed, { exact: true }).first().waitFor({ timeout: 30_000 });
    await page.getByTestId("machine-human-split").getByText(COPY.hitlConfirmed).waitFor({
      timeout: 15_000,
    });

    const historyRows = page.getByTestId("review-history").locator("li");
    await historyRows.first().waitFor({ state: "visible", timeout: 30_000 });
    note("decision", {
      history: (await historyRows.allTextContents()).map((row) => row.trim()),
    });
    await page.screenshot({ path: path.join(options.outputDir, "04-decision.png"), fullPage: true });

    const dialogsBeforeCleanExport = dialogMessages.length;
    const confirmedBundle = await captureExportBundle(page, options.outputDir, "confirmed");
    const extraWarnings = dialogMessages.length - dialogsBeforeCleanExport;
    if (extraWarnings !== 0) {
      throw new Error(`clean export raised ${extraWarnings} unexpected confirm(s)`);
    }
    const confirmedInspect = inspectExportBundle({ ...confirmedBundle, phase: "confirmed" });
    note("export-after-decision", { extraWarnings, formats: confirmedInspect });
    note("export-diff", {
      changedPaths: [...new Set(diffPaths(draftBundle.json, confirmedBundle.json))].sort(),
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

    const network = assertLoopbackAndQuiet({ requestOrigins, failedResponses, consoleErrors });
    note("network", { origins: [...requestOrigins].sort(), external: network.externalOrigins });

    await context.tracing.stop({ path: path.join(options.outputDir, "review-decision.trace.zip") });
    const summary = {
      baseUrl: options.baseUrl,
      outputDir: options.outputDir,
      generatedAt: new Date().toISOString(),
      stack: STACK_VITE_DEV,
      steps,
      consoleErrors,
      failedResponses,
      externalOrigins: network.externalOrigins,
    };
    await writeFile(
      path.join(options.outputDir, "review-decision-summary.json"),
      `${JSON.stringify(summary, null, 2)}\n`,
      "utf8",
    );

    console.log(
      JSON.stringify(
        {
          ok: true,
          stack: STACK_VITE_DEV,
          oa21: { draft: draftInspect, confirmed: confirmedInspect },
          consoleErrors,
          failedResponses,
          externalOrigins: network.externalOrigins,
        },
        null,
        2,
      ),
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
