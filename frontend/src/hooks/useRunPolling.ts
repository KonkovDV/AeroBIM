import { useEffect, useRef, useState } from "react";
import { fetchAnalyzeJob, type AnalyzeJobSnapshot } from "../lib/api";

/** Терминальные статусы jobs/{job_id}: поллинг и таймер останавливаются. */
export const TERMINAL_JOB_STATUSES = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);

export function formatMmss(totalSec: number): string {
  const minutes = String(Math.floor(totalSec / 60)).padStart(2, "0");
  const seconds = String(totalSec % 60).padStart(2, "0");
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
export function useRunPolling(onReportReady?: (reportId: string) => void): RunPolling {
  const [job, setJob] = useState<AnalyzeJobSnapshot | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const startedAt = useRef<number | null>(null);
  const notifiedReportId = useRef<string | null>(null);
  /** job_id, для которого уже заведён отсчёт: иначе таймер продолжает прошлый прогон. */
  const clockJobId = useRef<string | null>(null);

  const jobId = job?.job_id ?? null;
  const jobStatus = job?.status ?? null;
  const terminal = jobStatus !== null && TERMINAL_JOB_STATUSES.has(jobStatus.toLowerCase());

  useEffect(() => {
    if (!jobId || terminal) {
      return;
    }
    if (clockJobId.current !== jobId) {
      clockJobId.current = jobId;
      startedAt.current = Date.now();
      setElapsedSec(0);
      notifiedReportId.current = null;
    }
    if (startedAt.current === null) {
      startedAt.current = Date.now();
    }
    const handle = window.setInterval(() => {
      if (startedAt.current !== null) {
        setElapsedSec(Math.floor((Date.now() - startedAt.current) / 1000));
      }
    }, 1000);
    return () => window.clearInterval(handle);
  }, [jobId, jobStatus, terminal]);

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

    function schedule(): void {
      handle = window.setTimeout(() => {
        void fetchAnalyzeJob(polledJobId)
          .then((snapshot) => {
            if (cancelled) {
              return;
            }
            // Опрос снова живой: снимаем прошлую сетевую ошибку, иначе баннер вечен.
            failures = 0;
            setPollError(null);
            setJob(snapshot);
            delay = delay === 0 ? JOB_POLL_INTERVAL_MS : nextJobPollInterval(delay);
            if (!TERMINAL_JOB_STATUSES.has(snapshot.status.toLowerCase())) {
              schedule();
            }
          })
          .catch((err: unknown) => {
            if (cancelled) {
              return;
            }
            failures += 1;
            setPollError(err instanceof Error ? err.message : "Не удалось опросить задание");
            if (failures >= JOB_POLL_MAX_FAILURES) {
              // Молчание ≠ успех: оставляем последнюю ошибку на экране и прекращаем цикл.
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
      window.clearTimeout(handle);
    };
  }, [jobId, jobStatus, terminal]);

  function trackJob(next: AnalyzeJobSnapshot | null, options?: { restartClock?: boolean }): void {
    setJob(next);
    if (options?.restartClock === true) {
      clockJobId.current = next?.job_id ?? null;
      startedAt.current = Date.now();
      setElapsedSec(0);
      setPollError(null);
      notifiedReportId.current = null;
    }
  }

  return { job, trackJob, pollError, setPollError, elapsedSec, terminal };
}
