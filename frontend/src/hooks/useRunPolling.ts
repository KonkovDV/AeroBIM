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
 * Опрос jobs/{job_id} раз в 2 с + живой счётчик от старта. Не SSE.
 * Таймер — фактическая длительность прогона. SLA не заявляем.
 */
export function useRunPolling(onReportReady?: (reportId: string) => void): RunPolling {
  const [job, setJob] = useState<AnalyzeJobSnapshot | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const startedAt = useRef<number | null>(null);
  const notifiedReportId = useRef<string | null>(null);

  const jobId = job?.job_id ?? null;
  const jobStatus = job?.status ?? null;
  const terminal = jobStatus !== null && TERMINAL_JOB_STATUSES.has(jobStatus.toLowerCase());

  useEffect(() => {
    if (!jobId || terminal) {
      return;
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
    const handle = window.setInterval(() => {
      void fetchAnalyzeJob(jobId)
        .then(setJob)
        .catch((err: unknown) => {
          setPollError(err instanceof Error ? err.message : "Не удалось опросить задание");
        });
    }, 2000);
    return () => window.clearInterval(handle);
  }, [jobId, jobStatus, terminal]);

  function trackJob(next: AnalyzeJobSnapshot | null, options?: { restartClock?: boolean }): void {
    setJob(next);
    if (options?.restartClock === true) {
      startedAt.current = Date.now();
      setElapsedSec(0);
      notifiedReportId.current = null;
    }
  }

  return { job, trackJob, pollError, setPollError, elapsedSec, terminal };
}
