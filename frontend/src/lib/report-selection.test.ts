import { describe, expect, it } from "vitest";
import type { ReportSummaryEntry } from "./types";
import {
  OVERLAY_FIXTURE_REPORT_ID,
  pickDefaultReportId,
  pickSelectedReportId,
} from "./report-selection";

function entry(
  reportId: string,
  createdAt: string,
): ReportSummaryEntry {
  return {
    report_id: reportId,
    request_id: `req-${reportId.slice(0, 4)}`,
    created_at: createdAt,
    passed: false,
    issue_count: 1,
  };
}

describe("report selection (demo seed vs overlay fixture)", () => {
  it("auto-selects the newest non-overlay report", () => {
    const older = entry("a".repeat(32), "2026-04-13T09:00:00Z");
    const newer = entry("b".repeat(32), "2026-04-14T09:00:00Z");
    expect(pickDefaultReportId([older, newer])).toBe(newer.report_id);
    expect(
      pickSelectedReportId({
        current: null,
        reports: [older, newer],
        fromUrl: null,
      }),
    ).toBe(newer.report_id);
  });

  it("skips the overlay fixture when another pack exists", () => {
    const overlay = entry(OVERLAY_FIXTURE_REPORT_ID, "2026-09-09T12:00:00Z");
    const pack = entry("c".repeat(32), "2026-04-13T09:00:00Z");
    expect(pickDefaultReportId([overlay, pack])).toBe(pack.report_id);
  });

  it("keeps the overlay when it is the only report", () => {
    const overlay = entry(OVERLAY_FIXTURE_REPORT_ID, "2026-09-09T12:00:00Z");
    expect(pickDefaultReportId([overlay])).toBe(OVERLAY_FIXTURE_REPORT_ID);
  });

  it("does not sit on the overlay while demo seed is in flight", () => {
    const overlay = entry(OVERLAY_FIXTURE_REPORT_ID, "2026-09-09T12:00:00Z");
    expect(
      pickSelectedReportId({
        current: OVERLAY_FIXTURE_REPORT_ID,
        reports: [overlay],
        fromUrl: null,
        seedInFlight: true,
      }),
    ).toBeNull();
  });

  it("keeps a just-seeded id that GET /reports has not listed yet", () => {
    const seeded = "d".repeat(32);
    expect(
      pickSelectedReportId({
        current: seeded,
        reports: [entry(OVERLAY_FIXTURE_REPORT_ID, "2026-09-09T12:00:00Z")],
        fromUrl: null,
      }),
    ).toBe(seeded);
  });

  it("prefers a non-overlay id from the URL", () => {
    const fromUrl = "e".repeat(32);
    const listed = entry(fromUrl, "2026-04-13T09:00:00Z");
    expect(
      pickSelectedReportId({
        current: null,
        reports: [entry(OVERLAY_FIXTURE_REPORT_ID, "2026-09-09T12:00:00Z"), listed],
        fromUrl,
      }),
    ).toBe(fromUrl);
  });
});
