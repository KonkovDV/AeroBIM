import { useEffect, useRef, useState } from "react";
import { ApiHttpError, fetchAnalyzeJob, type AnalyzeJobSnapshot } from "../lib/api";
import { UI_COPY } from "../lib/ui-copy";
import { ACTIVE_JOB_STORAGE_KEY, clearActiveJobId, readActiveJobId, writeActiveJobId } from "../lib/active-job";

/** Терминальные статусы jobs/{job_id}: поллинг и таймер останавливаются. */
export const TERMINAL_JOB_STATUSES = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);

export function formatMmss(totalSec: number): string {
  const minutes = String(Math.floor(totalSec / 60)).padStart(2, "0");
  const seconds = String(Math.floor(totalSec % 60)).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export type RunPolling = {
  job: AnalyzeJobSnapshot | null;
  /** Подмена снимка задания; restartClock — для «Повторного прогона». */
  trackJob: (next: AnalyzeJobSnapshot | null, options?: { restartClock?: boolean }) => void;
  pollError: string | null;
  setPollError: (message: string | null) => void;
  elapsedSec: number;
  terminal: boolean;
  resumePolling: () => void;
};

/**
 * Опрос jobs/{job_id} с backoff 2 с → 15 с. Не SSE: бэкенд не отдаёт /events.
 * Таймер — фактическая длительность прогона. SLA не заявляем.
 */
export const JOB_POLL_INTERVAL_MS = 2000;
export const JOB_POLL_MAX_INTERVAL_MS = 15_000;

/**
 * Предел подряд идущих неудачных опросов. Без него ветка .catch планировала
 * следующий опрос бесконечно: при упавшем бэкенде цикл жил до закрытия вкладки,
 * а на экране висела первая же ошибка.
 */
export const JOB_POLL_MAX_FAILURES = 5;

export function nextJobPollInterval(currentMs: number): number {
  return Math.min(Math.round(currentMs * 1.5), JOB_POLL_MAX_INTERVAL_MS);
}

function sessionStore(): Storage | null {
  return typeof sessionStorage === "undefined" ? null : sessionStorage;
}

function clockStartMs(snapshot: AnalyzeJobSnapshot | null): number {
  if (snapshot?.created_at) {
    const parsed = Date.parse(snapshot.created_at);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return Date.now();
}

function isAbortError(error: unknown): boolean {
  return (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  );
}

export function useRunPolling(
  onReportReady?: (reportId: string) => void,
  restoreWhen = false,
): RunPolling {
  const [job, setJob] = useState<AnalyzeJobSnapshot | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [resumeNonce, setResumeNonce] = useState(0);
  const startedAt = useRef<number | null>(null);
  const notifiedReportId = useRef<string | null>(null);
  /** job_id, для которого уже заведён отсчёт: иначе таймер продолжает прошлый прогон. */
  const clockJobId = useRef<string | null>(null);
  const jobRef = useRef<AnalyzeJobSnapshot | null>(null);
  const restoreAttempted = useRef(false);

  jobRef.current = job;

  const jobId = job?.job_id ?? null;
  const jobStatus = job?.status ?? null;
  const terminal = jobStatus !== null && TERMINAL_JOB_STATUSES.has(jobStatus.toLowerCase());

  useEffect(() => {
    if (!restoreWhen || restoreAttempted.current) {
      return;
    }
    const store = sessionStore();
    const stored = readActiveJobId(store);
    if (!stored) {
      if (store?.getItem(ACTIVE_JOB_STORAGE_KEY)) {
        clearActiveJobId(store);
      }
      restoreAttempted.current = true;
      return;
    }
    restoreAttempted.current = true;
    const controller = new AbortController();
    void fetchAnalyzeJob(stored, { signal: controller.signal })
      .then((snapshot) => {
        if (controller.signal.aborted) {
          return;
        }
        clockJobId.current = snapshot.job_id;
        startedAt.current = clockStartMs(snapshot);
        setElapsedSec(
          Math.max(0, Math.floor((Date.now() - (startedAt.current ?? Date.now())) / 1000)),
        );
        if (snapshot.report_id && TERMINAL_JOB_STATUSES.has(snapshot.status.toLowerCase())) {
          notifiedReportId.current = snapshot.report_id;
        }
        setJob(snapshot);
        writeActiveJobId(snapshot.job_id, sessionStore());
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || isAbortError(error)) {
          return;
        }
        if (
          error instanceof ApiHttpError &&
          (error.status === 400 || error.status === 403 || error.status === 404)
        ) {
          clearActiveJobId(sessionStore());
          return;
        }
        setPollError(error instanceof Error ? error.message : UI_COPY.runPollFailed);
      });
    return () => controller.abort();
  }, [restoreWhen]);

  useEffect(() => {
    if (!jobId || terminal) {
      return;
    }
    if (clockJobId.current !== jobId) {
      clockJobId.current = jobId;
      startedAt.current = clockStartMs(job);
      setElapsedSec(Math.max(0, Math.floor((Date.now() - (startedAt.current ?? Date.now())) / 1000)));
    }
    if (startedAt.current === null) {
      startedAt.current = clockStartMs(job);
    }
    const handle = window.setInterval(() => {
      if (startedAt.current !== null) {
        setElapsedSec(Math.floor((Date.now() - startedAt.current) / 1000));
      }
    }, 1000);
    return () => window.clearInterval(handle);
  }, [job, jobId, terminal]);

  useEffect(() => {
    const reportId = job?.report_id;
    if (!reportId || job?.status.toLowerCase() !== "succeeded") {
      return;
    }
    if (notifiedReportId.current === reportId) {
      return;
    }
    notifiedReportId.current = reportId;
    onReportReady?.(reportId);
  }, [job?.report_id, job?.status, onReportReady]);

  useEffect(() => {
    if (!jobId || terminal) {
      return;
    }
    let cancelled = false;
    let delay = 0;
    let handle = 0;
    let failures = 0;
    const polledJobId = jobId;
    const controller = new AbortController();

    function schedule(): void {
      handle = window.setTimeout(() => {
        void fetchAnalyzeJob(polledJobId, { signal: controller.signal })
          .then((snapshot) => {
            if (cancelled) {
              return;
            }
            failures = 0;
            setPollError(null);
            setJob(snapshot);
            writeActiveJobId(snapshot.job_id, sessionStore());
            delay = delay === 0 ? JOB_POLL_INTERVAL_MS : nextJobPollInterval(delay);
            if (!TERMINAL_JOB_STATUSES.has(snapshot.status.toLowerCase())) {
              schedule();
            }
          })
          .catch((err: unknown) => {
            if (cancelled || isAbortError(err)) {
              return;
            }
            if (
              err instanceof ApiHttpError &&
              (err.status === 400 || err.status === 403 || err.status === 404)
            ) {
              clearActiveJobId(sessionStore());
              setPollError(err.message);
              return;
            }
            failures += 1;
            setPollError(err instanceof Error ? err.message : UI_COPY.runPollFailed);
            if (failures >= JOB_POLL_MAX_FAILURES) {
              return;
            }
            delay = delay === 0 ? JOB_POLL_INTERVAL_MS : nextJobPollInterval(delay);
            schedule();
          });
      }, delay);
    }

    schedule();
    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [jobId, terminal, resumeNonce]);

  function trackJob(next: AnalyzeJobSnapshot | null, options?: { restartClock?: boolean }): void {
    setJob(next);
    if (next?.job_id) {
      writeActiveJobId(next.job_id, sessionStore());
    }
    if (options?.restartClock === true) {
      clockJobId.current = next?.job_id ?? null;
      startedAt.current = clockStartMs(next);
      setElapsedSec(
        next ? Math.max(0, Math.floor((Date.now() - (startedAt.current ?? Date.now())) / 1000)) : 0,
      );
      setPollError(null);
      notifiedReportId.current = null;
    }
  }

  function resumePolling(): void {
    if (!jobId || terminal) {
      return;
    }
    setPollError(null);
    setResumeNonce((n) => n + 1);
  }

  return { job, trackJob, pollError, setPollError, elapsedSec, terminal, resumePolling };
}
