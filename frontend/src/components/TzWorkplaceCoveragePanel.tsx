import { TZ_UI_SCREENS } from "../lib/tz-ui-screens";
import { TZ_REQUIREMENT_ROWS, tzRequirementView } from "../lib/tz-requirement-map";
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
          <p className="panel-kicker">Покрытие ТЗ</p>
          <h2>Пункт → функция → доказательство</h2>
        </div>
      </div>
      <p className="compact-copy">
        Карта тай-брейка, не поставка. Колонка git — честный статус. Не закрывает RT. Не SLA. Не
        нативный RVT. Машина: <code>ui_expert_workplace_triage_snapshot</code>.
      </p>
      <table className="coverage-table" data-testid="tz-requirement-map">
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Пункт ТЗ</th>
            <th scope="col">Функция</th>
            <th scope="col">Доказательство в git</th>
            <th scope="col">git</th>
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
      <h3>Восемь экранов IA</h3>
      <table className="coverage-table">
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Экран</th>
            <th scope="col">git</th>
            <th scope="col">Заметка</th>
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
