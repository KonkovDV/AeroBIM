/**
 * Call-path rehearsal: the 15.09 agenda button «Загрузить демонстрационный
 * комплект» runs POST /v1/demo/seed-fixture (git vertical-slice pack:
 * IFC + IDS + ТЗ + чертёж A-101 via AnalyzeProjectPackage). That report is
 * not the overlay fixture from seed_smoke_report. Overlay absence is
 * recorded, not treated as a defect of this track.
 *
 * Vite-dev only: the button is gated on import.meta.env.DEV. Production
 * builds 404 the route. Not a customer pack. Not product accuracy.
 */
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

import {
  COPY,
  STACK_VITE_DEV,
  assertDemoSeedButton,
  assertDemoSeedPayload,
  assertForcedLight,
  assertHonestyOnExpertScreen,
  assertLoopbackAndQuiet,
  attachNetworkGuards,
  launchChromium,
  waitForViewerReady,
} from "./capture-review-smoke-shared.mjs";

export function parseArgs(argv) {
  const options = {
    baseUrl: "http://127.0.0.1:5173",
    outputDir: path.resolve(process.cwd(), "artifacts", "demo-seed"),
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

async function main() {
  const options = parseArgs(process.argv.slice(2));
  await mkdir(options.outputDir, { recursive: true });

  const browser = await launchChromium();
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    colorScheme: "dark",
  });
  const { requestOrigins, failedResponses, consoleErrors } = attachNetworkGuards(context);
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  try {
    await page.goto(options.baseUrl, { waitUntil: "domcontentloaded", timeout: 30_000 });
    const colorScheme = await assertForcedLight(page);
    await assertDemoSeedButton(page);
    await page.screenshot({ path: path.join(options.outputDir, "01-landing.png"), fullPage: true });

    const seedResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes("/v1/demo/seed-fixture") && response.request().method() === "POST",
      { timeout: 120_000 },
    );
    await page.getByRole("button", { name: COPY.demoSeed }).click();
    const seedResponse = await seedResponsePromise;
    if (!seedResponse.ok()) {
      throw new Error(`demo seed HTTP ${seedResponse.status()}: ${seedResponse.url()}`);
    }
    const seedBody = assertDemoSeedPayload(await seedResponse.json());
    await page.getByText(COPY.demoSeededNeedle).waitFor({ timeout: 30_000 });
    await page.getByText(seedBody.report_id.slice(0, 8)).waitFor({ timeout: 30_000 });
    await page.locator(".issue-card").first().waitFor({ state: "visible", timeout: 30_000 });
    await page.locator(".issue-card").first().click();

    const honesty = await assertHonestyOnExpertScreen(page);
    const overlayPresent = (await page.locator(".drawing-evidence-rect").count()) > 0;
    const viewer = await waitForViewerReady(page, 60_000);
    const issueCount = await page.locator(".issue-card").count();
    await page.screenshot({ path: path.join(options.outputDir, "02-seeded.png"), fullPage: true });

    const network = assertLoopbackAndQuiet({ requestOrigins, failedResponses, consoleErrors });
    await context.tracing.stop({ path: path.join(options.outputDir, "demo-seed.trace.zip") });

    const payload = {
      ok: true,
      demoSeed: true,
      stack: STACK_VITE_DEV,
      overlayRequired: false,
      overlayPresent,
      reportId: seedBody.report_id,
      issueCount,
      seedIssueCount: seedBody.issue_count,
      honesty,
      viewer,
      colorScheme: { emulated: "dark", computed: colorScheme },
      consoleErrors,
      failedResponses,
      externalOrigins: network.externalOrigins,
      note: "Git walls+IDS via POST /v1/demo/seed-fixture. Not the overlay fixture. Not a customer pack.",
    };
    await writeFile(
      path.join(options.outputDir, "demo-seed-summary.json"),
      `${JSON.stringify(payload, null, 2)}\n`,
      "utf8",
    );
    console.log(JSON.stringify(payload, null, 2));
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
