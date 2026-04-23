import { mkdir } from "node:fs/promises";
import { readFile, stat } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

const defaultBaseUrl = "http://127.0.0.1:5173";
const defaultReportPrefix = "99999999";
const defaultOutputDir = path.resolve(process.cwd(), "artifacts", "browser-smoke");

export function parseArgs(argv) {
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

export function validateExportLinks(exportLinks) {
  const suffixes = {
    html: "html",
    json: "json",
    bcf: "bcf",
  };

  const reportIds = new Set();
  for (const [format, expectedSuffix] of Object.entries(suffixes)) {
    const href = exportLinks[format];
    if (typeof href !== "string" || href.length === 0) {
      throw new Error(`Missing export link for ${format}`);
    }
    const match = href.match(/\/v1\/reports\/([a-f0-9]{32})\/export\/(html|json|bcf)$/i);
    if (!match) {
      throw new Error(`Unexpected export href for ${format}: ${href}`);
    }
    if (match[2].toLowerCase() !== expectedSuffix) {
      throw new Error(`Export href for ${format} ended with ${match[2]} instead of ${expectedSuffix}`);
    }
    reportIds.add(match[1].toLowerCase());
  }

  if (reportIds.size !== 1) {
    throw new Error(`Expected export links to target one report, got ${reportIds.size}`);
  }

  return {
    reportId: [...reportIds][0],
    links: exportLinks,
  };
}

async function artifactMetadata(filePath) {
  const fileBuffer = await readFile(filePath);
  const fileStats = await stat(filePath);
  return {
    path: filePath,
    size_bytes: fileStats.size,
    sha256: createHash("sha256").update(fileBuffer).digest("hex"),
  };
}

async function buildSmokePayload(options, artifactPaths, checks) {
  const integrity = {
    trace: await artifactMetadata(artifactPaths.tracePath),
    issue: await artifactMetadata(artifactPaths.issueScreenshotPath),
    clash:
      artifactPaths.clashScreenshotPath !== null
        ? await artifactMetadata(artifactPaths.clashScreenshotPath)
        : null,
  };

  return {
    baseUrl: options.baseUrl,
    reportPrefix: options.reportPrefix,
    generatedAt: new Date().toISOString(),
    screenshots: {
      issue: artifactPaths.issueScreenshotPath,
      clash: artifactPaths.clashScreenshotPath,
    },
    trace: artifactPaths.tracePath,
    artifact_integrity: integrity,
    checks,
  };
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

async function getLocatorText(locator, description) {
  const text = await locator.textContent();
  if (!text) {
    throw new Error(`Expected text content for ${description}`);
  }
  return text.trim();
}

async function assertIssueReviewState(page) {
  const exportLinks = {
    html: await page.getByRole("link", { name: "HTML" }).getAttribute("href"),
    json: await page.getByRole("link", { name: "JSON" }).getAttribute("href"),
    bcf: await page.getByRole("link", { name: "BCF" }).getAttribute("href"),
  };
  const validatedExports = validateExportLinks(exportLinks);

  await page.locator(".drawing-evidence-panel .drawing-evidence-rect").waitFor({
    state: "visible",
    timeout: 30_000,
  });

  const activeIssueBlock = page
    .locator(".provenance-panel .detail-block")
    .filter({ has: page.getByRole("heading", { name: "Active issue" }) })
    .first();
  await activeIssueBlock.waitFor({ state: "visible", timeout: 30_000 });

  return {
    exportReportId: validatedExports.reportId,
    overlayVisible: true,
    activeIssueRuleId: await getLocatorText(page.locator(".drawing-evidence-caption strong").first(), "active issue rule id"),
  };
}

async function assertPresetScopeState(page) {
  const presetName = "Smoke Team Preset";

  await page.getByLabel("Preset name").fill(presetName);
  await page.getByLabel("Preset scope").selectOption("team");
  await page.getByRole("button", { name: "Save preset" }).click();

  const presetChip = page
    .locator(".preset-chip")
    .filter({ has: page.getByRole("button", { name: presetName }) })
    .first();
  await presetChip.waitFor({ state: "visible", timeout: 30_000 });

  const scopeBadge = presetChip.locator(".preset-scope-badge").first();
  const scopeText = (await scopeBadge.textContent())?.trim().toLowerCase();
  if (scopeText !== "team") {
    throw new Error(`Expected preset scope badge to be team, got: ${scopeText ?? "<empty>"}`);
  }

  return {
    presetName,
    scope: scopeText,
  };
}

async function assertClashReviewState(page, clashCard) {
  if (!(await clashCard.count())) {
    return {
      clashCardPresent: false,
      clashFocusVisible: false,
    };
  }

  await page.locator(".collection-card-button.active").first().waitFor({
    state: "visible",
    timeout: 30_000,
  });
  await page.locator(".viewer-meta").getByText("clash pair").waitFor({
    state: "visible",
    timeout: 30_000,
  });

  return {
    clashCardPresent: true,
    clashFocusVisible: true,
    clashHeading: await getLocatorText(page.locator(".viewer-selection-card strong").first(), "clash selection heading"),
  };
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
    const issueChecks = await assertIssueReviewState(page);
    const presetChecks = await assertPresetScopeState(page);
    await page.screenshot({ path: issueScreenshotPath, fullPage: true });

    const clashCard = page.locator(".collection-card-button").first();
    await clickIfVisible(clashCard);
    const clashChecks = await assertClashReviewState(page, clashCard);
    let capturedClashScreenshotPath = null;
    if (await clashCard.count()) {
      await page.screenshot({ path: clashScreenshotPath, fullPage: true });
      capturedClashScreenshotPath = clashScreenshotPath;
    }

    await context.tracing.stop({ path: tracePath });
    console.log(
      JSON.stringify(
        buildSmokePayload(
          options,
          {
            issueScreenshotPath,
            clashScreenshotPath: capturedClashScreenshotPath,
            tracePath,
          },
          {
            issue: issueChecks,
            clash: clashChecks,
            presets: presetChecks,
          },
        ),
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
}

const isDirectExecution = process.argv[1]
  ? import.meta.url === pathToFileURL(process.argv[1]).href
  : false;

if (isDirectExecution) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}