import path from "node:path";
import process from "node:process";

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
