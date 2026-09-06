import {
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { fetchReports } from "../lib/api";
import type { ReportSummaryEntry } from "../lib/types";
import { readUrlReportId } from "../lib/report-filters";
import { UI_COPY } from "../lib/ui-copy";

function reportTimestamp(report: ReportSummaryEntry): number {
  const parsed = Date.parse(report.created_at);
  return Number.isNaN(parsed) ? 0 : parsed;
}

/** Новые отчёты сверху; при равной метке — стабильно по report_id. */
function compareReports(left: ReportSummaryEntry, right: ReportSummaryEntry): number {
  const byTimestamp = reportTimestamp(right) - reportTimestamp(left);
  if (byTimestamp !== 0) {
    return byTimestamp;
  }
  return left.report_id.localeCompare(right.report_id);
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

  /**
   * useMemo обязателен: без него каждый рендер возвращал новый массив, а он
   * уходит пропом в ExpertWorkplace и в зависимости эффектов ниже — фильтрация
   * и группировка пересчитывались на каждый тик таймера прогона.
   */
  const filteredReports = useMemo(() => {
    const normalizedQuery = deferredSearch.trim().toLowerCase();
    const matched = normalizedQuery
      ? reports.filter(
          (report) =>
            report.report_id.toLowerCase().includes(normalizedQuery) ||
            report.request_id.toLowerCase().includes(normalizedQuery),
        )
      : reports.slice();
    return matched.sort(compareReports);
  }, [reports, deferredSearch]);

  const groupedReports = useMemo(
    () =>
      filteredReports.reduce((groups, report) => {
        const key = report.project_name?.trim() || UI_COPY.unspecifiedProject;
        const existing = groups.get(key);
        if (existing) {
          existing.push(report);
        } else {
          groups.set(key, [report]);
        }
        return groups;
      }, new Map<string, ReportSummaryEntry[]>()),
    [filteredReports],
  );

  return { reports, reportsLoading, reportsError, filteredReports, groupedReports };
}
