import { useState } from "react";
import type { ValidationIssue } from "../../lib/types";
import type { ReviewEventRow } from "../../lib/api";
import { hitlEventTypeLabel } from "../../lib/hitl-event-copy";
import { eventMatchesIssue } from "../../lib/hitl-state";
import { clauseLine, essenceLine, spatialOrMissing } from "../../lib/issue-triage";
import { UI_COPY } from "../../lib/ui-copy";
import EvidenceStepper from "./EvidenceStepper";

function dash(value: string | null | undefined): string {
  const text = value?.trim();
  return text ? text : "—";
}

function GuidCopyRow({ guid }: { guid: string | null | undefined }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const text = guid?.trim() ?? "";
  if (!text) {
    return <code>—</code>;
  }

  async function copyGuid(): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <span className="guid-copy-row">
      <code>{text}</code>
      <button type="button" className="toolbar-button" onClick={() => void copyGuid()}>
        {UI_COPY.copyGuid}
      </button>
      {copyState === "copied" ? <span className="compact-copy">{UI_COPY.guidCopied}</span> : null}
      {copyState === "failed" ? <span className="compact-copy">{UI_COPY.guidCopyFailed}</span> : null}
    </span>
  );
}

export type RemarkCardPanelProps = {
  reportId?: string | null;
  activeIssue: ValidationIssue | null;
  remarkDraft: string;
  remarkSaveState: "idle" | "saving" | "saved" | "failed";
  hitlDecisionState: "idle" | "saving" | "accepted" | "rejected" | "failed";
  hitlEnabled?: boolean;
  reviewEvents?: ReviewEventRow[];
  reviewEventsError?: string | null;
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
  reviewEvents = [],
  reviewEventsError = null,
  onDraftChange,
  onSave,
  onAccept,
  onReject,
}: RemarkCardPanelProps) {
  const history = activeIssue
    ? reviewEvents.filter((event) => eventMatchesIssue(event, activeIssue))
    : [];
  const historyError = reportId ? reviewEventsError : null;

  return (
    <article className="detail-block" data-testid="remark-card">
      <h3>{UI_COPY.remarkHeading}</h3>
      {activeIssue ? (
        <div className="remark-editor">
          <EvidenceStepper issue={activeIssue} />
          {activeIssue.remark?.ai_generated ? (
            <p className="synthetic-content-mark" role="status">
              {UI_COPY.syntheticMark}
            </p>
          ) : null}
          <dl className="remark-tz-fields">
            <div>
              <dt>{UI_COPY.remarkEssence}</dt>
              <dd>{essenceLine(activeIssue)}</dd>
            </div>
            <div>
              <dt>{UI_COPY.remarkClause}</dt>
              <dd>{clauseLine(activeIssue)}</dd>
            </div>
            <div>
              <dt>{UI_COPY.remarkLocation}</dt>
              <dd>{spatialOrMissing(activeIssue.remark?.location_line)}</dd>
            </div>
            <div>
              <dt>{UI_COPY.remarkStorey}</dt>
              <dd>{spatialOrMissing(activeIssue.storey_name ?? activeIssue.remark?.storey_name)}</dd>
            </div>
            <div>
              <dt>{UI_COPY.remarkAxis}</dt>
              <dd>{spatialOrMissing(activeIssue.grid_axis ?? activeIssue.remark?.grid_axis)}</dd>
            </div>
            <div>
              <dt>{UI_COPY.remarkElement}</dt>
              <dd>
                <GuidCopyRow guid={activeIssue.element_guid} />
              </dd>
            </div>
            <div>
              <dt>{UI_COPY.provFindingId}</dt>
              <dd>
                <code>{dash(activeIssue.finding_id)}</code>
              </dd>
            </div>
            <div>
              <dt>{UI_COPY.provSourceId}</dt>
              <dd>
                <code>{dash(activeIssue.source_id)}</code>
              </dd>
            </div>
            <div>
              <dt>{UI_COPY.provEvidenceRefs}</dt>
              <dd>{activeIssue.evidence_refs?.length ? activeIssue.evidence_refs.join(" · ") : "—"}</dd>
            </div>
          </dl>
          <p className="compact-copy">
            <strong>{activeIssue.remark?.title ?? UI_COPY.generatedRemark}</strong>
          </p>
          {hitlEnabled ? (
            <>
              <textarea
                id="remark-editor"
                value={remarkDraft}
                rows={5}
                onChange={(event) => onDraftChange(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    onSave();
                  }
                }}
                aria-label={UI_COPY.editRemark}
              />
              <div className="remark-actions">
                <button
                  type="button"
                  onClick={onSave}
                  disabled={remarkSaveState === "saving"}
                  title={UI_COPY.remarkSaveHotkey}
                >
                  {remarkSaveState === "saving" ? UI_COPY.savingRemark : UI_COPY.saveRemark}
                </button>
                <button
                  type="button"
                  onClick={onAccept}
                  disabled={hitlDecisionState === "saving"}
                >
                  {UI_COPY.confirmRemark}
                </button>
                <button
                  type="button"
                  onClick={onReject}
                  disabled={hitlDecisionState === "saving"}
                >
                  {UI_COPY.rejectRemark}
                </button>
                {remarkSaveState === "saved" ? <span className="compact-copy">{UI_COPY.remarkSaved}</span> : null}
                {remarkSaveState === "failed" ? <span className="compact-copy">{UI_COPY.remarkSaveFailed}</span> : null}
                {hitlDecisionState === "accepted" ? <span className="compact-copy">{UI_COPY.confirmed}</span> : null}
                {hitlDecisionState === "rejected" ? <span className="compact-copy">{UI_COPY.rejected}</span> : null}
                {hitlDecisionState === "failed" ? <span className="compact-copy">{UI_COPY.remarkDecisionFailed}</span> : null}
              </div>
            </>
          ) : (
            <p className="compact-copy" data-testid="hitl-readonly-note">
              {UI_COPY.hitlUserAlias}
            </p>
          )}
          <div className="review-history" data-testid="review-history">
            <h4>{UI_COPY.hitlHistory}</h4>
            {historyError ? <p className="compact-copy">{historyError}</p> : null}
            {history.length === 0 ? (
              <p className="compact-copy">{UI_COPY.noEvents}</p>
            ) : (
              <ol className="kpi-list">
                {history.map((event) => (
                  <li key={event.event_id}>
                    <code>{hitlEventTypeLabel(event.event_type)}</code>
                    {event.created_at ? ` · ${event.created_at}` : ""}
                    {event.actor ? ` · ${event.actor}` : ""}
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      ) : (
        <p className="compact-copy">{UI_COPY.selectIssue}</p>
      )}
    </article>
  );
}
