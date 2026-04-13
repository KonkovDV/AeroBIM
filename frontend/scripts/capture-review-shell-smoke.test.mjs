import { describe, expect, it } from "vitest";

import { parseArgs, validateExportLinks } from "./capture-review-shell-smoke.mjs";

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
    });

    expect(result.reportId).toBe("99999999999999999999999999999999");
  });

  it("rejects export links when they point to different reports", () => {
    expect(() =>
      validateExportLinks({
        html: "http://127.0.0.1:8080/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/html",
        json: "http://127.0.0.1:8080/v1/reports/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/export/json",
        bcf: "http://127.0.0.1:8080/v1/reports/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/export/bcf",
      }),
    ).toThrow(/one report/i);
  });
});