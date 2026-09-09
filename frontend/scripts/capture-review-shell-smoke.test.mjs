import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { parseArgs, validateExportLinks } from "./capture-review-shell-smoke-helpers.mjs";
import { buildSmokePayload } from "./capture-review-shell-smoke.mjs";

describe("capture-review-shell-smoke helpers", () => {
  it("parses explicit base url, report prefix, and output dir", () => {
    const options = parseArgs([
      "--base-url",
      "http://127.0.0.1:3001",
      "--report-prefix",
      "abcdef12",
      "--output-dir",
      "artifacts/tmp-smoke",
    ]);

    expect(options.baseUrl).toBe("http://127.0.0.1:3001");
    expect(options.reportPrefix).toBe("abcdef12");
    expect(options.outputDir.replace(/\\/g, "/")).toContain("artifacts/tmp-smoke");
  });

  it("accepts consistent export links for one report", () => {
    const result = validateExportLinks({
      html: "http://127.0.0.1:8080/v1/reports/99999999999999999999999999999999/export/html",
      json: "http://127.0.0.1:8080/v1/reports/99999999999999999999999999999999/export/json",
      bcf: "http://127.0.0.1:8080/v1/reports/99999999999999999999999999999999/export/bcf",
      pdf: "http://127.0.0.1:8080/v1/reports/99999999999999999999999999999999/export/pdf",
    });

    expect(result.reportId).toBe("99999999999999999999999999999999");
  });

  it("rejects export links when they point to different reports", () => {
    expect(() =>
      validateExportLinks({
        html: "http://127.0.0.1:8080/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/html",
        json: "http://127.0.0.1:8080/v1/reports/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/export/json",
        bcf: "http://127.0.0.1:8080/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/bcf",
        pdf: "http://127.0.0.1:8080/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/pdf",
      }),
    ).toThrow(/one report/i);
  });
});

describe("buildSmokePayload", () => {
  it("JSON.stringify of the promise is empty, awaited payload keeps checks and trace hash", async () => {
    const dir = await mkdtemp(path.join(tmpdir(), "aerobim-smoke-"));
    const tracePath = path.join(dir, "trace.zip");
    const issueScreenshotPath = path.join(dir, "issue.png");
    await writeFile(tracePath, "trace-bytes");
    await writeFile(issueScreenshotPath, "png-bytes");
    const pending = buildSmokePayload(
      { baseUrl: "http://127.0.0.1:3001", reportPrefix: "ab" },
      { issueScreenshotPath, clashScreenshotPath: null, tracePath },
      { issue: { ok: true }, clash: { ok: true }, presets: { ok: true } },
    );
    expect(JSON.stringify(pending)).toBe("{}");
    const payload = await pending;
    expect(payload.checks.issue.ok).toBe(true);
    expect(payload.stack).toBe("vite-dev");
    expect(payload.artifact_integrity.trace.sha256).toMatch(/^[a-f0-9]{64}$/);
  });

  it("fails when the trace file is missing instead of printing empty evidence", async () => {
    await expect(
      buildSmokePayload(
        { baseUrl: "http://127.0.0.1:3001", reportPrefix: "ab" },
        {
          issueScreenshotPath: path.join(tmpdir(), "missing-issue.png"),
          clashScreenshotPath: null,
          tracePath: path.join(tmpdir(), "missing-trace.zip"),
        },
        { issue: { ok: true } },
      ),
    ).rejects.toThrow();
  });
});