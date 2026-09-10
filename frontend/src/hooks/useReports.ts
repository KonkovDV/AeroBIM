import {
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { fetchReports } from "../lib/api";
import type { ReportSummaryEntry } from "../lib/types";
import { readUrlReportId } from "../lib/report-filters";
import {
  compareReports,
  OVERLAY_FIXTURE_REPORT_ID,
  pickSelectedReportId,
} from "../lib/report-selection";
import { classifyRequestFailure, type RequestFailureKind } from "../lib/request-failure";
import { UI_COPY } from "../lib/ui-copy";

export type UseReportsOptions = {
  projectFilter: string;
  disciplineFilter: string;
  statusFilter: "all" | "passed" | "failed";
  search: string;
  epoch: number;
  setSelectedReportId: Dispatch<SetStateAction<string | null>>;
  /** Demo seed POST in flight: do not auto-select the overlay fixture. */
  seedInFlight?: boolean;
};

export type ReportsState = {
  reports: ReportSummaryEntry[];
  reportsLoading: boolean;
  reportsError: RequestFailureKind | null;
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
    seedInFlight = false,
  } = options;
  const [reports, setReports] = useState<ReportSummaryEntry[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<RequestFailureKind | null>(null);
  const seedInFlightRef = useRef(seedInFlight);
  seedInFlightRef.current = seedInFlight;

  const deferredSearch = useDeferredValue(search);
  const deferredProjectFilter = useDeferredValue(projectFilter);
  const deferredDisciplineFilter = useDeferredValue(disciplineFilter);
  const deferredStatusFilter = useDeferredValue(statusFilter);

  useEffect(() => {
    if (!seedInFlight) {
      return;
    }
    setSelectedReportId((current) =>
      current === OVERLAY_FIXTURE_REPORT_ID ? null : current,
    );
  }, [seedInFlight, setSelectedReportId]);

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
        setSelectedReportId((current) =>
          pickSelectedReportId({
            current,
            reports: response.reports,
            fromUrl: readUrlReportId(),
            seedInFlight: seedInFlightRef.current,
          }),
        );
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportsError(classifyRequestFailure(error));
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
