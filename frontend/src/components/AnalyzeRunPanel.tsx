import { useEffect, useRef, useState } from "react";
import {
  cancelAnalyzeJob,
  fetchAnalyzeJob,
  submitAnalyzeProjectPackage,
  type AnalyzeJobSnapshot,
} from "../lib/api";
import type { ReportCapabilities } from "../lib/types";
import { capabilityRows, engineGroupStatus, humanCapabilityLine, RUN_ENGINE_GROUPS } from "../lib/capability-copy";
import { UI_COPY } from "../lib/ui-copy";
import {
  packDraftFromIfc,
  packDraftHasAny,
  toAnalyzeSubmitBody,
  type PackDraft,
} from "../lib/pack-draft";

export type AnalyzeRunPanelProps = {
  ifcPath: string | null;
  packDraft?: PackDraft;
  onReportReady?: (reportId: string) => void;
  onNeedUpload?: () => void;
  onContinueToExpert?: () => void;
  capabilities?: ReportCapabilities | null;
};

const TERMINAL = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);

const COARSE_STAGES = ["принято", "идёт", "отчёт"] as const;

function formatMmss(totalSec: number): string {
  const minutes = String(Math.floor(totalSec / 60)).padStart(2, "0");
  const seconds = String(totalSec % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

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
  packDraft,
  onReportReady,
  onNeedUpload,
  onContinueToExpert,
  capabilities,
}: AnalyzeRunPanelProps) {
  const draft = packDraft ?? packDraftFromIfc(ifcPath);
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
          setError(err instanceof Error ? err.message : "Не удалось опросить задание");
        });
    }, 2000);
    return () => window.clearInterval(handle);
  }, [job?.job_id, job?.status]);

  async function start(): Promise<void> {
    if (!packDraftHasAny(draft)) {
      setError("Сначала загрузите IFC или документы. Нативные RVT/NWD/DWG — fail-closed.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await submitAnalyzeProjectPackage(toAnalyzeSubmitBody(draft));
      setJob(next);
      startedAt.current = Date.now();
      setElapsedSec(0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Не удалось отправить задание");
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
      setError(err instanceof Error ? err.message : "Не удалось отменить задание");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel run-panel" data-testid="analyze-run-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">{UI_COPY.runKicker}</p>
          <h2>{UI_COPY.runTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">
        Цель ТЗ 30:00 на комплект — не измеренный SLA. Поллинг{" "}
        <code>jobs/{"{job_id}"}</code>, не SSE. Тишина ≠ успех.
      </p>
      <p className="compact-copy">
        IFC: {draft.ifcPath ?? "—"}. IDS: {draft.idsPath ?? "—"}. Листы: {draft.drawings.length}. ТЗ:{" "}
        {draft.requirementPath ?? "—"}. Расчёт: {draft.calculationPath ?? "—"}.
      </p>
      <p className="run-timer compact-copy" data-testid="analyze-elapsed">
        {job ? UI_COPY.runTimer(formatMmss(elapsedSec)) : UI_COPY.runTimerIdle}
      </p>
      <div className="remark-actions">
        <button type="button" onClick={() => void start()} disabled={busy || !packDraftHasAny(draft)}>
          {busy ? "Запускаем…" : "Запустить анализ"}
        </button>
        <button type="button" onClick={() => void cancel()} disabled={busy || !job?.job_id}>
          Отменить
        </button>
        {onNeedUpload ? (
          <button type="button" onClick={onNeedUpload}>
            К загрузке
          </button>
        ) : null}
        {onContinueToExpert && job?.status.toLowerCase() === "succeeded" ? (
          <button type="button" onClick={onContinueToExpert}>
            {UI_COPY.toExpert}
          </button>
        ) : null}
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
      <ol className="analyze-engines" data-testid="analyze-engine-groups">
        {RUN_ENGINE_GROUPS.map((group) => {
          const status = engineGroupStatus(capabilities, group.keys);
          return (
            <li key={group.id} className={`analyze-engine analyze-engine-${status}`}>
              {group.title}: {status === "pending" ? "ожидание" : status}
            </li>
          );
        })}
      </ol>
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
