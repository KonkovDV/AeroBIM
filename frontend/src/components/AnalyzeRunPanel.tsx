import { useState } from "react";
import {
  cancelAnalyzeJob,
  submitAnalyzeProjectPackage,
} from "../lib/api";
import type { ReportCapabilities } from "../lib/types";
import { BLOCKING_STATES, capabilityRows, engineGroupStatus, humanCapabilityLine, RUN_ENGINE_GROUPS } from "../lib/capability-copy";
import { UI_COPY } from "../lib/ui-copy";
import {
  packDraftFromIfc,
  packDraftHasAny,
  toAnalyzeSubmitBody,
  type PackDraft,
} from "../lib/pack-draft";
import { formatMmss, useRunPolling } from "../hooks/useRunPolling";

export type AnalyzeRunPanelProps = {
  ifcPath: string | null;
  packDraft?: PackDraft;
  onReportReady?: (reportId: string) => void;
  onNeedUpload?: () => void;
  onContinueToExpert?: () => void;
  capabilities?: ReportCapabilities | null;
};

const COARSE_STAGES = ["принято", "идёт", "отчёт"] as const;

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

function packCompositionLine(draft: PackDraft): string {
  const parts = [
    `IFC ${draft.ifcPath ? "✓" : "—"}`,
    `IDS ${draft.idsPath ? "✓" : "—"}`,
    `листы ${draft.drawings.length}`,
    `ТЗ ${draft.requirementPath ? "✓" : "—"}`,
    `расчёт ${draft.calculationPath ? "✓" : "—"}`,
  ];
  return parts.join(" · ");
}

/** Полоса состояния прогона: время, гейт, состав пакета, доказательность. */
function RunStatusStrip({
  jobStatus,
  elapsedSec,
  terminal,
  draft,
  capabilities,
}: {
  jobStatus: string | null;
  elapsedSec: number;
  terminal: boolean;
  draft: PackDraft;
  capabilities: ReportCapabilities | null | undefined;
}) {
  const timerCell = jobStatus
    ? terminal
      ? UI_COPY.runFinalTime(formatMmss(elapsedSec))
      : UI_COPY.runTimer(formatMmss(elapsedSec))
    : UI_COPY.runTimerIdle;
  const rows = capabilities ? capabilityRows(capabilities) : [];
  const blocking = rows.filter((row) => BLOCKING_STATES.has(row.status)).length;
  const skipped = rows.filter(
    (row) =>
      row.status === "skipped" || row.status === "not_verified" || row.status === "not_implemented",
  ).length;
  return (
    <div className="run-status-strip" data-testid="run-status-strip">
      <div className="run-status-cell">
        <span className="run-status-kicker">{UI_COPY.runCellCurrent}</span>
        <strong className="run-status-value" data-testid="analyze-elapsed">
          {timerCell}
        </strong>
      </div>
      <div className="run-status-cell">
        <span className="run-status-kicker">{UI_COPY.runCellGate}</span>
        <strong className="run-status-value">
          {jobStatus ? <code>{jobStatus}</code> : UI_COPY.runGateNone}
        </strong>
      </div>
      <div className="run-status-cell">
        <span className="run-status-kicker">{UI_COPY.runCellPack}</span>
        <strong className="run-status-value">
          {packDraftHasAny(draft) ? packCompositionLine(draft) : UI_COPY.runPackEmpty}
        </strong>
      </div>
      <div className="run-status-cell">
        <span className="run-status-kicker">{UI_COPY.runCellEvidence}</span>
        <strong className="run-status-value">
          {capabilities ? UI_COPY.runEvidenceSummary(blocking, skipped) : UI_COPY.runEvidenceNone}
        </strong>
      </div>
    </div>
  );
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
  const { job, trackJob, pollError, setPollError, elapsedSec, terminal } = useRunPolling(onReportReady);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function start(): Promise<void> {
    if (!packDraftHasAny(draft)) {
      setError("Сначала загрузите IFC или документы. Нативные RVT/NWD/DWG — жёсткий отказ.");
      return;
    }
    setBusy(true);
    setError(null);
    setPollError(null);
    try {
      const next = await submitAnalyzeProjectPackage(toAnalyzeSubmitBody(draft));
      trackJob(next, { restartClock: true });
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
      trackJob(await cancelAnalyzeJob(job.job_id));
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
      <p className="compact-copy">{UI_COPY.runHonesty}</p>
      <RunStatusStrip
        jobStatus={job?.status ?? null}
        elapsedSec={elapsedSec}
        terminal={terminal}
        draft={draft}
        capabilities={capabilities}
      />
      <div className="remark-actions">
        <button type="button" onClick={() => void start()} disabled={busy || !packDraftHasAny(draft)}>
          {busy ? "Запускаем…" : "Запустить анализ"}
        </button>
        <button type="button" onClick={() => void cancel()} disabled={busy || !job?.job_id || terminal}>
          Отменить
        </button>
        {terminal ? (
          <button type="button" onClick={() => void start()} disabled={busy || !packDraftHasAny(draft)}>
            {UI_COPY.repeatRun}
          </button>
        ) : null}
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
            <dt>{UI_COPY.runStatusLabel}</dt>
            <dd>
              <code>{job.status}</code>
            </dd>
          </div>
          <div>
            <dt>{UI_COPY.runStageLabel}</dt>
            <dd>{job.stage_progress ?? "—"}</dd>
          </div>
          <div>
            <dt>{UI_COPY.runReportLabel}</dt>
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
      <p className="compact-copy">Стадии — грубый статус опроса, не SSE по движкам.</p>
      {error || pollError ? (
        <p className="compact-copy" role="alert">
          {error ?? pollError}
        </p>
      ) : null}
    </section>
  );
}
