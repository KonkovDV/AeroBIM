import { useEffect, useRef, useState } from "react";
import {
  cancelAnalyzeJob,
  submitAnalyzeProjectPackage,
  type AnalyzeJobSnapshot,
} from "../lib/api";
import type { ReportCapabilities } from "../lib/types";
import { BLOCKING_STATES, capabilityRows, engineGroupStatus, formatEngineGroupStatus, humanCapabilityLine, RUN_ENGINE_GROUPS } from "../lib/capability-copy";
import { UI_COPY } from "../lib/ui-copy";
import {
  packCompositionLine,
  packDraftFromIfc,
  packDraftHasAny,
  toAnalyzeSubmitBody,
  type PackDraft,
} from "../lib/pack-draft";
import { appendRunJournal, readRunJournal, type RunJournalEntry } from "../lib/run-journal";
import { formatMmss, TERMINAL_JOB_STATUSES, useRunPolling, type RunPolling } from "../hooks/useRunPolling";

export type AnalyzeRunPanelProps = {
  ifcPath: string | null;
  packDraft?: PackDraft;
  onReportReady?: (reportId: string) => void;
  onNeedUpload?: () => void;
  onContinueToExpert?: () => void;
  capabilities?: ReportCapabilities | null;
  /** report_id, которому принадлежат capabilities; иначе матрица прошлого отчёта скрыта. */
  capabilitiesReportId?: string | null;
  /** Поднятый опрос из App: F5 восстанавливает job_id. Без пропа хук живёт в панели. */
  polling?: RunPolling;
};

function capabilitiesForActiveJob(
  capabilities: ReportCapabilities | null | undefined,
  capabilitiesReportId: string | null | undefined,
  job: AnalyzeJobSnapshot | null,
  terminal: boolean,
): ReportCapabilities | null | undefined {
  if (job === null) {
    return capabilities;
  }
  const jobReportId = job.report_id ?? null;
  if (!terminal || !jobReportId) {
    return null;
  }
  if (capabilitiesReportId && jobReportId !== capabilitiesReportId) {
    return null;
  }
  return capabilities;
}

const COARSE_STAGES = [
  UI_COPY.runStageAccepted,
  UI_COPY.runStageRunning,
  UI_COPY.runStageReport,
] as const;

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
  capabilitiesReportId,
  polling,
}: AnalyzeRunPanelProps) {
  const draft = packDraft ?? packDraftFromIfc(ifcPath);
  const owned = useRunPolling(polling ? undefined : onReportReady);
  const { job, trackJob, pollError, setPollError, elapsedSec, terminal, resumePolling } =
    polling ?? owned;
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [journal, setJournal] = useState<RunJournalEntry[]>(() =>
    typeof sessionStorage === "undefined" ? [] : readRunJournal(sessionStorage),
  );

  const [confirmingCancel, setConfirmingCancel] = useState(false);

  /** Терминальный прогон попадает в журнал ровно один раз. */
  const recordedJobRef = useRef<string | null>(null);
  /*
   * Секунды читаются через ref, а не через зависимость: таймер тикает каждую
   * секунду, и эффект с elapsedSec в deps перезапускался столько же раз после
   * завершения прогона.
   */
  const elapsedRef = useRef(elapsedSec);

  useEffect(() => {
    elapsedRef.current = elapsedSec;
  }, [elapsedSec]);

  function recordJournal(snapshot: { job_id: string; status: string }, elapsed: number): void {
    if (!TERMINAL_JOB_STATUSES.has(snapshot.status.toLowerCase())) {
      return;
    }
    /*
     * Сторож по job_id закрывает и вторую дорогу: если отправка сразу вернула
     * терминальный статус, запись шла и из start(), и из эффекта.
     */
    if (recordedJobRef.current === snapshot.job_id) {
      return;
    }
    recordedJobRef.current = snapshot.job_id;
    const storage = typeof sessionStorage === "undefined" ? null : sessionStorage;
    setJournal(
      appendRunJournal(
        {
          job_id: snapshot.job_id,
          status: snapshot.status,
          elapsed_sec: elapsed,
          recorded_at: new Date().toISOString(),
        },
        storage,
      ),
    );
  }

  useEffect(() => {
    if (!job || !terminal) {
      return;
    }
    recordJournal(job, elapsedRef.current);
    setConfirmingCancel(false);
  }, [job, terminal]);

  const jobInFlight = job !== null && !terminal;
  const startLocked = busy || jobInFlight;
  const scopedCapabilities = capabilitiesForActiveJob(
    capabilities,
    capabilitiesReportId,
    job,
    terminal,
  );

  async function start(): Promise<void> {
    if (startLocked) {
      return;
    }
    if (!packDraftHasAny(draft)) {
      setError(UI_COPY.runNeedUpload);
      return;
    }
    setBusy(true);
    setError(null);
    setPollError(null);
    try {
      const next = await submitAnalyzeProjectPackage(toAnalyzeSubmitBody(draft));
      trackJob(next, { restartClock: true });
      recordJournal(next, 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : UI_COPY.runSubmitFailed);
    } finally {
      setBusy(false);
    }
  }

  async function cancel(): Promise<void> {
    if (!job?.job_id) {
      return;
    }
    setBusy(true);
    setConfirmingCancel(false);
    try {
      trackJob(await cancelAnalyzeJob(job.job_id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : UI_COPY.runCancelFailed);
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
      <p className="compact-copy" data-testid="analyze-size-honesty">
        {UI_COPY.runSizeHonesty}
      </p>
      <RunStatusStrip
        jobStatus={job?.status ?? null}
        elapsedSec={elapsedSec}
        terminal={terminal}
        draft={draft}
        capabilities={scopedCapabilities}
      />
      <div className="remark-actions">
        <button
          type="button"
          onClick={() => void start()}
          disabled={startLocked || !packDraftHasAny(draft)}
          aria-busy={busy}
        >
          {busy ? UI_COPY.runStarting : UI_COPY.runStart}
        </button>
        {confirmingCancel ? (
          <span className="run-cancel-confirm" data-testid="run-cancel-confirm">
            <span className="compact-copy">{UI_COPY.runCancelConfirm}</span>
            <button type="button" onClick={() => void cancel()} disabled={busy || !job?.job_id || terminal}>
              {UI_COPY.runCancelYes}
            </button>
            <button type="button" onClick={() => setConfirmingCancel(false)} disabled={busy}>
              {UI_COPY.runCancelKeep}
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmingCancel(true)}
            disabled={busy || !job?.job_id || terminal}
          >
            {UI_COPY.runCancel}
          </button>
        )}
        {terminal ? (
          <button type="button" onClick={() => void start()} disabled={busy || !packDraftHasAny(draft)}>
            {UI_COPY.repeatRun}
          </button>
        ) : null}
        {onNeedUpload ? (
          <button type="button" onClick={onNeedUpload}>
            {UI_COPY.runToUpload}
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
          const status = engineGroupStatus(scopedCapabilities, group.keys);
          return (
            <li key={group.id} className={`analyze-engine analyze-engine-${status}`}>
              {group.title}: {formatEngineGroupStatus(status)}
            </li>
          );
        })}
      </ol>
      {job?.status.toLowerCase() === "succeeded" && scopedCapabilities ? (
        <ul className="kpi-list" data-testid="analyze-capability-map">
          {capabilityRows(scopedCapabilities).map((row) => (
            <li key={row.key}>{humanCapabilityLine(row)}</li>
          ))}
        </ul>
      ) : null}
      <p className="compact-copy">{UI_COPY.runStagesHonesty}</p>
      {/*
        Два независимых канала. Раньше стояло {error ?? pollError}: упавшая отправка
        навсегда прятала ошибку опроса, и потеря связи выглядела как тишина.
      */}
      {error ? (
        <p className="compact-copy" role="alert" data-testid="analyze-error">
          {error}
        </p>
      ) : null}
      {pollError ? (
        <p className="compact-copy" role="alert" data-testid="analyze-poll-error">
          {pollError}
        </p>
      ) : null}
      {pollError && jobInFlight ? (
        <button type="button" onClick={resumePolling} data-testid="analyze-resume-poll">
          {UI_COPY.runResumePoll}
        </button>
      ) : null}
      <section className="run-journal" data-testid="run-journal">
        <h3>{UI_COPY.runJournalTitle}</h3>
        <p className="compact-copy">{UI_COPY.runJournalHonesty}</p>
        {journal.length === 0 ? (
          <p className="compact-copy">{UI_COPY.runJournalEmpty}</p>
        ) : (
          <ol className="kpi-list">
            {journal.map((row) => (
              <li key={row.job_id}>
                <code>{row.job_id}</code>
                {` · ${row.status} · ${formatMmss(row.elapsed_sec)}`}
              </li>
            ))}
          </ol>
        )}
      </section>
    </section>
  );
}