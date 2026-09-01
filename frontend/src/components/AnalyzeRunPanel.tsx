import { useEffect, useRef, useState } from "react";
import {
  cancelAnalyzeJob,
  fetchAnalyzeJob,
  submitAnalyzeProjectPackage,
  type AnalyzeJobSnapshot,
} from "../lib/api";
import type { ReportCapabilities } from "../lib/types";
import { capabilityRows, humanCapabilityLine } from "../lib/capability-copy";

export type AnalyzeRunPanelProps = {
  ifcPath: string | null;
  onReportReady?: (reportId: string) => void;
  capabilities?: ReportCapabilities | null;
};

const TERMINAL = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);

const COARSE_STAGES = ["принят", "выполняется", "отчёт"] as const;

function stageIndex(status: string | undefined): number {
  const value = (status ?? "").toLowerCase();
  if (value === "succeeded") {
    return 2;
  }
  if (value === "failed" || value === "cancelled" || value === "dead_letter") {
    return 1;
  }
  if (value === "running" || value === "queued" || value === "pending") {
    return 1;
  }
  return 0;
}

export default function AnalyzeRunPanel({
  ifcPath,
  onReportReady,
  capabilities,
}: AnalyzeRunPanelProps) {
  const [job, setJob] = useState<AnalyzeJobSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);
  const startedAt = useRef<number | null>(null);
  const notifiedReportId = useRef<string | null>(null);

  useEffect(() => {
    if (!job?.job_id || TERMINAL.has(job.status.toLowerCase())) {
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
  }, [job?.job_id, job?.status]);

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
    if (!job?.job_id || TERMINAL.has(job.status.toLowerCase())) {
      return;
    }
    const handle = window.setInterval(() => {
      void fetchAnalyzeJob(job.job_id)
        .then(setJob)
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Job poll failed");
        });
    }, 2000);
    return () => window.clearInterval(handle);
  }, [job?.job_id, job?.status]);

  async function start(): Promise<void> {
    if (!ifcPath) {
      setError("Upload an IFC first. Other natives stay fail-closed.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await submitAnalyzeProjectPackage({ ifc_path: ifcPath });
      setJob(next);
      startedAt.current = Date.now();
      setElapsedSec(0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setBusy(false);
    }
  }

  async function cancel(): Promise<void> {
    if (!job?.job_id) {
      return;
    }
    setBusy(true);
    try {
      setJob(await cancelAnalyzeJob(job.job_id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Cancel failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel run-panel" data-testid="analyze-run-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Прогон</p>
          <h2>Analyze job</h2>
        </div>
      </div>
      <p className="compact-copy">
        Цель ТЗ 30:00 на комплект — не измеренный SLA. Поллинг{" "}
        <code>jobs/{"{job_id}"}</code>, не SSE. Тишина движка ≠ успех.
      </p>
      <p className="compact-copy">IFC path: {ifcPath ?? "—"}</p>
      {job ? (
        <p className="compact-copy" data-testid="analyze-elapsed">
          Таймер прогона: {String(Math.floor(elapsedSec / 60)).padStart(2, "0")}:
          {String(elapsedSec % 60).padStart(2, "0")} / цель ТЗ 30:00 (не измеренный SLA)
        </p>
      ) : null}
      <div className="remark-actions">
        <button type="button" onClick={() => void start()} disabled={busy || !ifcPath}>
          {busy ? "Starting…" : "Start analyze"}
        </button>
        <button type="button" onClick={() => void cancel()} disabled={busy || !job?.job_id}>
          Cancel
        </button>
      </div>
      {job ? (
        <dl className="job-status" data-testid="analyze-job-status">
          <div>
            <dt>job_id</dt>
            <dd>
              <code>{job.job_id}</code>
            </dd>
          </div>
          <div>
            <dt>request_id</dt>
            <dd>
              <code>{job.request_id ?? "—"}</code>
            </dd>
          </div>
          <div>
            <dt>status</dt>
            <dd>
              <code>{job.status}</code>
            </dd>
          </div>
          <div>
            <dt>stage</dt>
            <dd>{job.stage_progress ?? "—"}</dd>
          </div>
          <div>
            <dt>report</dt>
            <dd>{job.report_id ?? "—"}</dd>
          </div>
        </dl>
      ) : null}
      {job ? (
        <ol className="analyze-stages" data-testid="analyze-stages">
          {COARSE_STAGES.map((label, index) => (
            <li
              key={label}
              className={index <= stageIndex(job.status) ? "analyze-stage active" : "analyze-stage"}
            >
              {label}
              {index === 1 && job.stage_progress ? ` · ${job.stage_progress}` : ""}
            </li>
          ))}
        </ol>
      ) : null}
      {job?.status.toLowerCase() === "succeeded" && capabilities ? (
        <ul className="kpi-list" data-testid="analyze-capability-map">
          {capabilityRows(capabilities).map((row) => (
            <li key={row.key}>{humanCapabilityLine(row)}</li>
          ))}
        </ul>
      ) : null}
      <p className="compact-copy">Стадии — грубый статус поллинга, не SSE по движкам.</p>
      {error ? (
        <p className="compact-copy" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
