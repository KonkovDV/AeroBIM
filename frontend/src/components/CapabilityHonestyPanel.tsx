import type { CapabilityState, DivergenceRecord, ReportCapabilities } from "../lib/types";
import { BLOCKING_STATES, capabilityRows, capabilityStatusPhrase, formatCapabilityLabel, formatCapabilityState } from "../lib/capability-copy";
import { UI_COPY } from "../lib/ui-copy";

function statusClass(status: CapabilityState): string {
  if (status === "ok") return "cap-ok";
  if (BLOCKING_STATES.has(status)) return "cap-block";
  if (status === "skipped" || status === "not_verified" || status === "not_implemented") {
    return "cap-warn";
  }
  return "cap-neutral";
}

export interface CapabilityHonestyPanelProps {
  capabilities?: ReportCapabilities | null;
  divergences?: DivergenceRecord[];
}

export default function CapabilityHonestyPanel({
  capabilities,
  divergences = [],
}: CapabilityHonestyPanelProps) {
  if (!capabilities) {
    return (
      <section className="capability-honesty" data-testid="capability-honesty">
        <h3>{UI_COPY.capHonestyTitle}</h3>
        <p className="compact-copy">{UI_COPY.capHonestyMissing}</p>
      </section>
    );
  }

  const rows = capabilityRows(capabilities);

  const blocking = rows.filter((row) => BLOCKING_STATES.has(row.status));
  const skipped = rows.filter(
    (row) =>
      row.status === "skipped" ||
      row.status === "not_verified" ||
      row.status === "not_implemented",
  );

  return (
    <section className="capability-honesty" data-testid="capability-honesty">
      <div className="capability-honesty-header">
        <h3>{UI_COPY.capHonestyTitle}</h3>
        <p className="compact-copy">{UI_COPY.capHonestyBody}</p>
      </div>

      {blocking.length > 0 && (
        <p className="capability-block-banner" role="status">
          {UI_COPY.capBlocking(
            blocking.length,
            blocking.map(capabilityStatusPhrase).join("; "),
          )}
        </p>
      )}

      {skipped.length > 0 && (
        <p className="capability-skip-banner" role="status" data-testid="capability-skip-banner">
          {UI_COPY.capSkipped(
            skipped.map(capabilityStatusPhrase).join("; "),
          )}
        </p>
      )}

      <table className="capability-table">
        <thead>
          <tr>
            <th scope="col">{UI_COPY.capColCapability}</th>
            <th scope="col">{UI_COPY.capColStatus}</th>
            <th scope="col">{UI_COPY.capColReason}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className={statusClass(row.status)}>
              <td>{formatCapabilityLabel(row.key)}</td>
              <td>
                {formatCapabilityState(row.status)}
              </td>
              <td>{row.reason?.trim() ? row.reason : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="divergence-block" data-testid="divergence-list">
        <h4>{UI_COPY.capDivergencesTitle}</h4>
        {divergences.length === 0 ? (
          <p className="compact-copy">{UI_COPY.capNoDivergences}</p>
        ) : (
          <ul>
            {divergences.map((item) => (
              <li key={`${item.finding_key}-${item.engine_verdict}-${item.advisory_verdict}`}>
                <strong>{item.finding_key}</strong>:{" "}
                {UI_COPY.capEngineVs(item.engine_verdict, item.advisory_verdict)}
                {item.resolution ? ` → ${item.resolution}` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
