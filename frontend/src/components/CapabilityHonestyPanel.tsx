import type { CapabilityState, DivergenceRecord, ReportCapabilities } from "../lib/types";
import { BLOCKING_STATES, capabilityRows } from "../lib/capability-copy";

function formatLabel(key: string): string {
  return key.replaceAll("_", " ");
}

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
        <h3>Capability honesty</h3>
        <p className="compact-copy">
          No capability matrix on this report. Sign-off operators should treat missing matrix as
          incomplete evidence — not as OK.
        </p>
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
        <h3>Capability honesty</h3>
        <p className="compact-copy">
          FAILED/MISSING capabilities block <code>summary.passed</code>. Advisory disagreements
          never flip the deterministic verdict alone. UI never writes that flag (ADR-001).
        </p>
      </div>

      {blocking.length > 0 && (
        <p className="capability-block-banner" role="status">
          {blocking.length} blocking capability status
          {blocking.length === 1 ? "" : "es"}:{" "}
          {blocking.map((row) => `${formatLabel(row.key)}=${row.status}`).join("; ")}
        </p>
      )}

      {skipped.length > 0 && (
        <p className="capability-skip-banner" role="status" data-testid="capability-skip-banner">
          Silence is never success. Skipped / not_verified / not_implemented:{" "}
          {skipped.map((row) => `${formatLabel(row.key)}=${row.status}`).join("; ")}. A green
          report from silence is forbidden.
        </p>
      )}

      <table className="capability-table">
        <thead>
          <tr>
            <th scope="col">Capability</th>
            <th scope="col">Status</th>
            <th scope="col">Reason</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className={statusClass(row.status)}>
              <td>{formatLabel(row.key)}</td>
              <td>
                <code>{row.status}</code>
              </td>
              <td>{row.reason?.trim() ? row.reason : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="divergence-block" data-testid="divergence-list">
        <h4>AI ↔ engine divergences</h4>
        {divergences.length === 0 ? (
          <p className="compact-copy">No recorded divergences for this report.</p>
        ) : (
          <ul>
            {divergences.map((item) => (
              <li key={`${item.finding_key}-${item.engine_verdict}-${item.advisory_verdict}`}>
                <strong>{item.finding_key}</strong>: engine <code>{item.engine_verdict}</code> vs
                advisory <code>{item.advisory_verdict}</code>
                {item.resolution ? ` → ${item.resolution}` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
