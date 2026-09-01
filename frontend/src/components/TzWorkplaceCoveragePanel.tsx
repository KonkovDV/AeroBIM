import { TZ_UI_SCREENS } from "../lib/tz-ui-screens";

export default function TzWorkplaceCoveragePanel() {
  return (
    <section className="panel tz-coverage-panel" data-testid="tz-workplace-coverage">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Покрытие ТЗ</p>
          <h2>Восемь экранов</h2>
        </div>
      </div>
      <p className="compact-copy">
        Карта IA, не delivery. Колонка git — честный статус. Не закрывает RT. Не SLA. Не native
        RVT. Машина: <code>ui_expert_workplace_triage_snapshot</code>.
      </p>
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
          {TZ_UI_SCREENS.map((row) => (
            <tr key={row.id}>
              <td>
                <code>{row.id}</code>
              </td>
              <td>{row.titleRu}</td>
              <td>
                <code>{row.git}</code>
              </td>
              <td className="cov-reason">{row.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
