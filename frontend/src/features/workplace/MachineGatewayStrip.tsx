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
    return "Confirmed by expert";
  }
  if (state === "rejected") {
    return "Rejected by expert";
  }
  if (state === "saving") {
    return "Recording HITL…";
  }
  if (state === "failed") {
    return "HITL not recorded";
  }
  return "No expert decision";
}

export default function MachineGatewayStrip({
  report,
  hitlDecisionState,
}: MachineGatewayStripProps) {
  const project = report.project_name?.trim();
  return (
    <div className="machine-human-split" data-testid="machine-human-split">
      <article className="machine-gateway">
        <p className="panel-kicker">Engine gateway</p>
        <strong className={`outcome-badge ${outcomeClass(report.summary.outcome, report.summary.passed)}`}>
          {formatPackageOutcome(report.summary.outcome, report.summary.passed)}
        </strong>
        <p className="compact-copy">
          {project ? `${project}. ` : ""}
          Technical flag from the server. Not an expert signature. UI does not write{" "}
          <code>summary.passed</code>.
        </p>
      </article>
      <article className="expert-hitl">
        <p className="panel-kicker">HITL verdict</p>
        <strong>{hitlLabel(hitlDecisionState)}</strong>
        <p className="compact-copy">Separate entity. ADR-001. UI role is not OIDC.</p>
      </article>
    </div>
  );
}
