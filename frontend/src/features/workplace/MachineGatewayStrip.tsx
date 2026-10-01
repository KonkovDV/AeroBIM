import { UI_COPY } from "../../lib/ui-copy";
import { formatPackageOutcome, outcomeClass } from "../../components/VerticalSliceKt2";
import type { ValidationReport } from "../../lib/types";

export type HitlDecisionState = "idle" | "saving" | "accepted" | "rejected" | "failed";
export type MachineGatewayStripProps = {
  report: ValidationReport;
  hitlDecisionState: HitlDecisionState;
  persistedHitlState?: string | null;
};

function persistedLabel(persisted: string | null): string {
  if (persisted === "accepted") return UI_COPY.hitlConfirmed;
  if (persisted === "rejected") return UI_COPY.hitlRejected;
  if (persisted === "edited") return UI_COPY.hitlEdited;
  if (persisted === "opened") return UI_COPY.hitlOpened;
  return UI_COPY.hitlNone;
}

function hitlLabel(persisted: string | null, request: HitlDecisionState): string {
  const known = persistedLabel(persisted);
  if (request === "saving") {
    return persisted ? `${known} · ${UI_COPY.hitlRecording}` : UI_COPY.hitlRecording;
  }
  if (request === "failed") {
    return persisted ? `${known} · ${UI_COPY.hitlNotRecorded}` : UI_COPY.hitlNotRecorded;
  }
  return known;
}

export default function MachineGatewayStrip({ report, hitlDecisionState, persistedHitlState = null }: MachineGatewayStripProps) {
  const project = report.project_name?.trim();
  return (
    <div className="machine-human-split" data-testid="machine-human-split">
      <article className="machine-gateway">
        <p className="panel-kicker">{UI_COPY.engineGateway}</p>
        <strong className={`outcome-badge ${outcomeClass(report.summary.outcome, report.summary.passed)}`}>
          {formatPackageOutcome(report.summary.outcome, report.summary.passed)}
        </strong>
        <p className="compact-copy">{project ? `${project}. ` : ""}{UI_COPY.engineFlag}</p>
      </article>
      <article className="expert-hitl">
        <p className="panel-kicker">{UI_COPY.hitlVerdict}</p>
        <strong aria-live="polite" aria-atomic="true">{hitlLabel(persistedHitlState, hitlDecisionState)}</strong>
        <p className="compact-copy">{UI_COPY.hitlSeparate}</p>
      </article>
    </div>
  );
}
