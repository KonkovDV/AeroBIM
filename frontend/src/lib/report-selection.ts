import type { ReportSummaryEntry } from "./types";

/**
 * Overlay fixture from backend `seed_smoke_report`.
 * The 15.09 demo seed (`POST /v1/demo/seed-fixture`) must not reuse this id.
 */
export const OVERLAY_FIXTURE_REPORT_ID = "9".repeat(32);

export function isOverlayFixtureReportId(reportId: string): boolean {
  return reportId === OVERLAY_FIXTURE_REPORT_ID;
}

function reportTimestamp(report: ReportSummaryEntry): number {
  const parsed = Date.parse(report.created_at);
  return Number.isNaN(parsed) ? 0 : parsed;
}

/** Новые отчёты сверху; при равной метке — стабильно по report_id. */
export function compareReports(left: ReportSummaryEntry, right: ReportSummaryEntry): number {
  const byTimestamp = reportTimestamp(right) - reportTimestamp(left);
  if (byTimestamp !== 0) {
    return byTimestamp;
  }
  return left.report_id.localeCompare(right.report_id);
}

/** Newest real pack; overlay only if it is the only row (smoke `--skip-demo-seed`). */
export function pickDefaultReportId(reports: ReportSummaryEntry[]): string | null {
  const ranked = [...reports].sort(compareReports);
  const preferred = ranked.find((row) => !isOverlayFixtureReportId(row.report_id));
  return preferred?.report_id ?? ranked[0]?.report_id ?? null;
}

export function pickSelectedReportId(options: {
  current: string | null;
  reports: ReportSummaryEntry[];
  fromUrl: string | null;
  seedInFlight?: boolean;
}): string | null {
  const { current, reports, fromUrl, seedInFlight = false } = options;
  const urlUsable =
    Boolean(fromUrl) &&
    !(seedInFlight && fromUrl !== null && isOverlayFixtureReportId(fromUrl));

  if (fromUrl && urlUsable) {
    if (current === fromUrl) {
      return fromUrl;
    }
    if (!current || reports.some((report) => report.report_id === fromUrl)) {
      return fromUrl;
    }
  }

  if (seedInFlight) {
    if (current && !isOverlayFixtureReportId(current)) {
      return current;
    }
    return null;
  }

  if (current && reports.some((report) => report.report_id === current)) {
    return current;
  }
  // Keep a just-seeded id while GET /reports lags; GET /reports/{id} still loads it.
  if (current) {
    return current;
  }
  return pickDefaultReportId(reports);
}
