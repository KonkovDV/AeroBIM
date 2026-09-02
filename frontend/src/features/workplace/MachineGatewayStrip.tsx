import { UI_COPY } from "../../lib/ui-copy";
import {
  formatPackageOutcome,
  outcomeClass,
} from "../../components/VerticalSliceKt2";
import type { ValidationReport } from "../../lib/types";

export type HitlDecisionState = "idle" | "saving" | "accepted" | "rejected" | "failed";

export type MachineGatewayStripProps = {
  report: ValidationReport;
  hitlDecisionState: HitlDecisionState;
};

function hitlLabel(state: HitlDecisionState): string {
  if (state === "accepted") {
    return UI_COPY.hitlConfirmed;
  }
  if (state === "rejected") {
    return UI_COPY.hitlRejected;
  }
  if (state === "saving") {
    return UI_COPY.hitlRecording;
  }
  if (state === "failed") {
    return UI_COPY.hitlNotRecorded;
  }
  return UI_COPY.hitlNone;
}

export default function MachineGatewayStrip({
  report,
  hitlDecisionState,
}: MachineGatewayStripProps) {
  const project = report.project_name?.trim();
  return (
    <div className="machine-human-split" data-testid="machine-human-split">
      <article className="machine-gateway">
        <p className="panel-kicker">{UI_COPY.engineGateway}</p>
        <strong className={`outcome-badge ${outcomeClass(report.summary.outcome, report.summary.passed)}`}>
          {formatPackageOutcome(report.summary.outcome, report.summary.passed)}
        </strong>
        <p className="compact-copy">
          {project ? `${project}. ` : ""}
          {UI_COPY.engineFlag}{" "}
          <code>summary.passed</code>.
        </p>
      </article>
      <article className="expert-hitl">
        <p className="panel-kicker">{UI_COPY.hitlVerdict}</p>
        <strong>{hitlLabel(hitlDecisionState)}</strong>
        <p className="compact-copy">{UI_COPY.hitlSeparate}</p>
      </article>
    </div>
  );
}
