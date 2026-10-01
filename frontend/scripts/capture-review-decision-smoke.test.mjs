import { describe, expect, it } from "vitest";

import {
  diffPaths,
  externalOrigins,
  isExpectedHonestyFailure,
  parseArgs,
  unexpectedConsoleErrors,
  unexpectedHttpFailures,
} from "./capture-review-decision-smoke.mjs";

describe("capture-review-decision-smoke helpers", () => {
  it("parses base url and output dir", () => {
    const options = parseArgs([
      "--base-url",
      "http://127.0.0.1:5199",
      "--output-dir",
      "artifacts/review-decision",
    ]);
    expect(options.baseUrl).toBe("http://127.0.0.1:5199");
    expect(options.outputDir.replace(/\\/g, "/")).toContain("artifacts/review-decision");
  });

  it("reports only the paths that actually changed", () => {
    const changed = diffPaths(
      { issues: [{ review: { state: null, actor: null } }] },
      { issues: [{ review: { state: "accepted", actor: "anonymous-dev" } }] },
    );
    expect(changed.sort()).toEqual([
      "<root>.issues.0.review.actor",
      "<root>.issues.0.review.state",
    ]);
  });

  it("treats blob and loopback as on-laptop traffic", () => {
    expect(
      externalOrigins(["blob:", "http://127.0.0.1:5199", "http://127.0.0.1:8099"]),
    ).toEqual([]);
    expect(externalOrigins(["https://fonts.googleapis.com"])).toEqual([
      "https://fonts.googleapis.com",
    ]);
  });

  it("keeps the documented 501 BFF probe out of unexpected failures", () => {
    expect(
      isExpectedHonestyFailure({ status: 501, url: "http://127.0.0.1:8099/v1/auth/bff" }),
    ).toBe(true);
    expect(
      unexpectedHttpFailures([
        { status: 501, url: "http://127.0.0.1:8099/v1/auth/bff" },
        { status: 500, url: "http://127.0.0.1:8099/v1/reports/aa/export/json" },
      ]),
    ).toEqual([{ status: 500, url: "http://127.0.0.1:8099/v1/reports/aa/export/json" }]);
    expect(
      unexpectedConsoleErrors([
        "Failed to load resource: the server responded with a status of 501 (Not Implemented)",
        "The Content Security Policy directive 'frame-ancestors' is ignored when delivered via a <meta> element.",
        "TypeError: exploded",
      ]),
    ).toEqual(["TypeError: exploded"]);
  });
});
