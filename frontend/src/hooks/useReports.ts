import { useDeferredValue, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { fetchReports } from "../lib/api";
import type { ReportSummaryEntry } from "../lib/types";
import { readUrlReportId } from "../lib/report-filters";
import { UI_COPY } from "../lib/ui-copy";

function reportSortWeight(report: ReportSummaryEntry): [number, string] {
  const timestamp = Number.isNaN(Date.parse(report.created_at)) ? 0 : Date.parse(report.created_at);
  return [-timestamp, report.report_id];
}

export type UseReportsOptions = {
  projectFilter: string;
  disciplineFilter: string;
  statusFilter: "all" | "passed" | "failed";
  search: string;
  epoch: number;
  setSelectedReportId: Dispatch<SetStateAction<string | null>>;
};

export type ReportsState = {
  reports: ReportSummaryEntry[];
  reportsLoading: boolean;
  reportsError: string | null;
  filteredReports: ReportSummaryEntry[];
  groupedReports: Map<string, ReportSummaryEntry[]>;
};

/** Список отчётов: загрузка с фильтрами, сверка выбора, поиск, сортировка, группировка. */
export function useReports(options: UseReportsOptions): ReportsState {
  const {
    projectFilter,
    disciplineFilter,
    statusFilter,
    search,
    epoch,
    setSelectedReportId,
  } = options;
  const [reports, setReports] = useState<ReportSummaryEntry[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);

  const deferredSearch = useDeferredValue(search);
  const deferredProjectFilter = useDeferredValue(projectFilter);
  const deferredDisciplineFilter = useDeferredValue(disciplineFilter);
  const deferredStatusFilter = useDeferredValue(statusFilter);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    setReportsLoading(true);
    fetchReports(
      {
        project: deferredProjectFilter.trim() || undefined,
        discipline: deferredDisciplineFilter.trim() || undefined,
        passed:
          deferredStatusFilter === "passed"
            ? true
            : deferredStatusFilter === "failed"
              ? false
              : undefined,
      },
      { signal: controller.signal },
    )
      .then((response) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReports(response.reports);
        setReportsError(null);
        setSelectedReportId((current) => {
          const fromUrl = readUrlReportId();
          if (fromUrl) {
            if (current === fromUrl) {
              return fromUrl;
            }
            if (!current || response.reports.some((report) => report.report_id === fromUrl)) {
              return fromUrl;
            }
          }
          if (current && response.reports.some((report) => report.report_id === current)) {
            return current;
          }
          // Keep a just-seeded id while GET /reports lags; GET /reports/{id} still loads it.
          if (current) {
            return current;
          }
          return response.reports[0]?.report_id ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportsError(error instanceof Error ? error.message : UI_COPY.loadReportsFailed);
      })
      .finally(() => {
        if (!cancelled && !controller.signal.aborted) {
          setReportsLoading(false);
        }
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [deferredProjectFilter, deferredDisciplineFilter, deferredStatusFilter, epoch, setSelectedReportId]);

  const filteredReports = reports
    .filter((report) => {
      const normalizedQuery = deferredSearch.trim().toLowerCase();
      if (!normalizedQuery) {
        return true;
      }
      return (
        report.report_id.toLowerCase().includes(normalizedQuery) ||
        report.request_id.toLowerCase().includes(normalizedQuery)
      );
    })
    .sort((left, right) => {
      const [leftTs, leftId] = reportSortWeight(left);
      const [rightTs, rightId] = reportSortWeight(right);
      if (leftTs !== rightTs) {
        return leftTs - rightTs;
      }
      return leftId.localeCompare(rightId);
    });

  const groupedReports = filteredReports.reduce((groups, report) => {
    const key = report.project_name?.trim() || UI_COPY.unspecifiedProject;
    const existing = groups.get(key);
    if (existing) {
      existing.push(report);
    } else {
      groups.set(key, [report]);
    }
    return groups;
  }, new Map<string, ReportSummaryEntry[]>());

  return { reports, reportsLoading, reportsError, filteredReports, groupedReports };
}
