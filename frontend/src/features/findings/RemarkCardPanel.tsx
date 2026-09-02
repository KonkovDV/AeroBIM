import { useEffect, useState } from "react";
import type { ValidationIssue } from "../../lib/types";
import { fetchReviewEvents, type ReviewEventRow } from "../../lib/api";
import { clauseLine, essenceLine, spatialOrMissing } from "../../lib/issue-triage";
import EvidenceStepper from "./EvidenceStepper";

function dash(value: string | null | undefined): string {
  const text = value?.trim();
  return text ? text : "—";
}

function eventMatchesIssue(event: ReviewEventRow, issue: ValidationIssue): boolean {
  if (event.finding_id && issue.finding_id) {
    return event.finding_id === issue.finding_id;
  }
  if (event.issue_rule_id) {
    return event.issue_rule_id === issue.rule_id;
  }
  return false;
}

export type RemarkCardPanelProps = {
  reportId?: string | null;
  activeIssue: ValidationIssue | null;
  remarkDraft: string;
  remarkSaveState: "idle" | "saving" | "saved" | "failed";
  hitlDecisionState: "idle" | "saving" | "accepted" | "rejected" | "failed";
  hitlEnabled?: boolean;
  onDraftChange: (value: string) => void;
  onSave: () => void;
  onAccept: () => void;
  onReject: () => void;
};

export default function RemarkCardPanel({
  reportId,
  activeIssue,
  remarkDraft,
  remarkSaveState,
  hitlDecisionState,
  hitlEnabled = true,
  onDraftChange,
  onSave,
  onAccept,
  onReject,
}: RemarkCardPanelProps) {
  const [history, setHistory] = useState<ReviewEventRow[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId || !activeIssue) {
      setHistory([]);
      return;
    }
    const controller = new AbortController();
    fetchReviewEvents(reportId, { signal: controller.signal })
      .then((payload) => {
        if (controller.signal.aborted) {
          return;
        }
        const rows = payload.events.filter((event) => eventMatchesIssue(event, activeIssue));
        setHistory(rows);
        setHistoryError(null);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setHistory([]);
          setHistoryError(error instanceof Error ? error.message : "Review history failed");
        }
      });
    return () => controller.abort();
  }, [reportId, activeIssue, remarkSaveState, hitlDecisionState]);

  return (
    <article className="detail-block" data-testid="remark-card">
      <h3>Remark</h3>
      {activeIssue ? (
        <div className="remark-editor">
          <EvidenceStepper issue={activeIssue} />
          {activeIssue.remark?.ai_generated ? (
            <p className="synthetic-content-mark" role="status">
              Synthetic content (AI) · draft, requires expert review · does not affect
              summary.passed
            </p>
          ) : null}
          <dl className="remark-tz-fields">
            <div>
              <dt>Суть</dt>
              <dd>{essenceLine(activeIssue)}</dd>
            </div>
            <div>
              <dt>Норма / СТО / СП</dt>
              <dd>{clauseLine(activeIssue)}</dd>
            </div>
            <div>
              <dt>Этаж</dt>
              <dd>{spatialOrMissing(activeIssue.storey_name ?? activeIssue.remark?.storey_name)}</dd>
            </div>
            <div>
              <dt>Ось</dt>
              <dd>{spatialOrMissing(activeIssue.grid_axis ?? activeIssue.remark?.grid_axis)}</dd>
            </div>
            <div>
              <dt>Элемент / GUID</dt>
              <dd>
                <code>{dash(activeIssue.element_guid)}</code>
              </dd>
            </div>
            <div>
              <dt>finding_id</dt>
              <dd>
                <code>{dash(activeIssue.finding_id)}</code>
              </dd>
            </div>
            <div>
              <dt>source_id</dt>
              <dd>
                <code>{dash(activeIssue.source_id)}</code>
              </dd>
            </div>
            <div>
              <dt>evidence_refs</dt>
              <dd>{activeIssue.evidence_refs?.length ? activeIssue.evidence_refs.join(" · ") : "—"}</dd>
            </div>
          </dl>
          <p className="compact-copy">
            <strong>{activeIssue.remark?.title ?? "Generated remark"}</strong>
          </p>
          <textarea
            id="remark-editor"
            value={remarkDraft}
            rows={5}
            onChange={(event) => onDraftChange(event.target.value)}
            aria-label="Edit remark text"
          />
          <div className="remark-actions">
            <button type="button" onClick={onSave} disabled={remarkSaveState === "saving"}>
              {remarkSaveState === "saving" ? "Saving…" : "Save remark edit"}
            </button>
            <button
              type="button"
              onClick={onAccept}
              disabled={!hitlEnabled || hitlDecisionState === "saving"}
            >
              Confirm remark
            </button>
            <button
              type="button"
              onClick={onReject}
              disabled={!hitlEnabled || hitlDecisionState === "saving"}
            >
              Reject remark
            </button>
            {remarkSaveState === "saved" ? <span className="compact-copy">Saved to review events</span> : null}
            {remarkSaveState === "failed" ? <span className="compact-copy">Save failed</span> : null}
            {hitlDecisionState === "accepted" ? <span className="compact-copy">Confirmed</span> : null}
            {hitlDecisionState === "rejected" ? <span className="compact-copy">Rejected</span> : null}
            {hitlDecisionState === "failed" ? <span className="compact-copy">Decision failed</span> : null}
          </div>
          {!hitlEnabled ? (
            <p className="compact-copy">
              User on this screen is a UI alias, not OIDC. Confirm/Reject are available to Expert.
            </p>
          ) : null}
          <div className="review-history" data-testid="review-history">
            <h4>HITL history</h4>
            {historyError ? <p className="compact-copy">{historyError}</p> : null}
            {history.length === 0 ? (
              <p className="compact-copy">No events for this finding.</p>
            ) : (
              <ol className="kpi-list">
                {history.map((event) => (
                  <li key={event.event_id}>
                    <code>{event.event_type}</code>
                    {event.created_at ? ` · ${event.created_at}` : ""}
                    {event.actor ? ` · ${event.actor}` : ""}
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      ) : (
        <p className="compact-copy">Select an issue to review and edit its remark.</p>
      )}
    </article>
  );
}
