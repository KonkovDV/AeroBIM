import { mkdir } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const defaultBaseUrl = "http://127.0.0.1:5173";
const defaultReportPrefix = "99999999";
const defaultOutputDir = path.resolve(process.cwd(), "artifacts", "browser-smoke");

function parseArgs(argv) {
  const options = {
    baseUrl: defaultBaseUrl,
    reportPrefix: defaultReportPrefix,
    outputDir: defaultOutputDir,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const next = argv[index + 1];
    if ((token === "--base-url" || token === "-u") && next) {
      options.baseUrl = next;
      index += 1;
      continue;
    }
    if ((token === "--report-prefix" || token === "-r") && next) {
      options.reportPrefix = next;
      index += 1;
      continue;
    }
    if ((token === "--output-dir" || token === "-o") && next) {
      options.outputDir = path.resolve(next);
      index += 1;
      continue;
    }
  }

  return options;
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    throw new Error(
      "Playwright is required for browser smoke capture. Install it in the workspace root or frontend environment before running npm run smoke:browser.",
    );
  }
}

async function launchBrowser(playwright) {
  const launchOptions = { headless: true };
  try {
    return await playwright.chromium.launch(launchOptions);
  } catch (error) {
    if (process.platform === "win32") {
      return playwright.chromium.launch({ ...launchOptions, channel: "msedge" });
    }
    throw error;
  }
}

async function clickIfVisible(locator) {
  if (await locator.count()) {
    await locator.first().click();
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const playwright = await loadPlaywright();
  const browser = await launchBrowser(playwright);
  const context = await browser.newContext({ viewport: { width: 1600, height: 1600 } });

  await mkdir(options.outputDir, { recursive: true });

  const tracePath = path.join(options.outputDir, "review-shell-smoke.trace.zip");
  const issueScreenshotPath = path.join(options.outputDir, "review-shell-issue.png");
  const clashScreenshotPath = path.join(options.outputDir, "review-shell-clash.png");

  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();

  try {
    await page.goto(options.baseUrl, { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.locator(".report-card").first().waitFor({ state: "visible", timeout: 30_000 });

    const seededReport = page.locator(".report-card").filter({ hasText: options.reportPrefix });
    if (await seededReport.count()) {
      await seededReport.first().click();
    } else {
      await page.locator(".report-card").first().click();
    }

    await page.locator(".issue-card").first().waitFor({ state: "visible", timeout: 30_000 });
    await page.locator(".issue-card").first().click();
    await page.locator(".drawing-evidence-panel .drawing-evidence-image").waitFor({
      state: "visible",
      timeout: 30_000,
    });
    await page.screenshot({ path: issueScreenshotPath, fullPage: true });

    const clashCard = page.locator(".collection-card-button").first();
    await clickIfVisible(clashCard);
    if (await clashCard.count()) {
      await page.locator(".collection-card-button.active").first().waitFor({
        state: "visible",
        timeout: 30_000,
      });
      await page.screenshot({ path: clashScreenshotPath, fullPage: true });
    }

    await context.tracing.stop({ path: tracePath });
    console.log(
      JSON.stringify(
        {
          baseUrl: options.baseUrl,
          reportPrefix: options.reportPrefix,
          screenshots: {
            issue: issueScreenshotPath,
            clash: clashScreenshotPath,
          },
          trace: tracePath,
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});