import { TZ_UI_SCREENS } from "../lib/tz-ui-screens";
import { TZ_REQUIREMENT_ROWS, tzRequirementView } from "../lib/tz-requirement-map";
import { UI_COPY } from "../lib/ui-copy";
import type { WorkspaceView } from "./WorkspaceNav";

export type TzWorkplaceCoveragePanelProps = {
  onOpenScreen?: (view: WorkspaceView) => void;
};

const SCREEN_VIEW: Record<string, WorkspaceView> = {
  "SCR-PROJECTS": "projects",
  "SCR-UPLOAD": "upload",
  "SCR-RUN": "run",
  "SCR-EXPERT": "review",
  "SCR-REMARK": "remark",
  "SCR-EXPORT": "export",
  "SCR-DIFF": "diff",
  "SCR-USER": "user",
};

export default function TzWorkplaceCoveragePanel({ onOpenScreen }: TzWorkplaceCoveragePanelProps) {
  return (
    <section className="panel tz-coverage-panel" data-testid="tz-workplace-coverage">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">{UI_COPY.tzCoverageKicker}</p>
          <h2>{UI_COPY.tzCoverageTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">{UI_COPY.tzCoverageBody}</p>
      <table className="coverage-table" data-testid="tz-requirement-map">
        <thead>
          <tr>
            <th scope="col">{UI_COPY.tzColId}</th>
            <th scope="col">{UI_COPY.tzColPoint}</th>
            <th scope="col">{UI_COPY.tzColFn}</th>
            <th scope="col">{UI_COPY.tzColEvidence}</th>
            <th scope="col">{UI_COPY.tzColGit}</th>
          </tr>
        </thead>
        <tbody>
          {TZ_REQUIREMENT_ROWS.map((row) => {
            const view = tzRequirementView(row.id);
            return (
              <tr key={row.id}>
                <td>
                  {onOpenScreen && view ? (
                    <button type="button" className="linkish" onClick={() => onOpenScreen(view)}>
                      <code>{row.id}</code>
                    </button>
                  ) : (
                    <code>{row.id}</code>
                  )}
                </td>
                <td>{row.tz}</td>
                <td>{row.fn}</td>
                <td className="cov-reason">{row.evidence}</td>
                <td>
                  <code>{row.git}</code>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <h3>{UI_COPY.tzEightScreens}</h3>
      <table className="coverage-table">
        <thead>
          <tr>
            <th scope="col">{UI_COPY.tzColId}</th>
            <th scope="col">{UI_COPY.tzColScreen}</th>
            <th scope="col">{UI_COPY.tzColGit}</th>
            <th scope="col">{UI_COPY.tzColNote}</th>
          </tr>
        </thead>
        <tbody>
          {TZ_UI_SCREENS.map((row) => {
            const view = SCREEN_VIEW[row.id];
            return (
              <tr key={row.id}>
                <td>
                  {onOpenScreen && view ? (
                    <button type="button" className="linkish" onClick={() => onOpenScreen(view)}>
                      <code>{row.id}</code>
                    </button>
                  ) : (
                    <code>{row.id}</code>
                  )}
                </td>
                <td>{row.title}</td>
                <td>
                  <code>{row.git}</code>
                </td>
                <td className="cov-reason">{row.note}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
