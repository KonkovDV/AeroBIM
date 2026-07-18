import type { CapabilityState, DivergenceRecord, ReportCapabilities } from "../lib/types";

const CAPABILITY_ORDER: Array<keyof ReportCapabilities> = [
  "ifc_schema",
  "ifc_validation",
  "ids",
  "unit_scale",
  "clash",
  "norm_rule_packs",
  "section_pairing",
  "raster",
  "dwg_dxf",
  "cv_human_level",
  "mep_system_clash",
  "calculation_match",
  "calculation_correctness",
];

const BLOCKING_STATES: ReadonlySet<CapabilityState> = new Set(["failed", "missing"]);

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

  const rows = CAPABILITY_ORDER.flatMap((key) => {
    const entry = capabilities[key];
    if (!entry) return [];
    return [{ key, ...entry }];
  });

  const blocking = rows.filter((row) => BLOCKING_STATES.has(row.status));

  return (
    <section className="capability-honesty" data-testid="capability-honesty">
      <div className="capability-honesty-header">
        <h3>Capability honesty</h3>
        <p className="compact-copy">
          FAILED/MISSING capabilities block <code>summary.passed</code>. Advisory disagreements
          never flip the deterministic verdict alone.
        </p>
      </div>

      {blocking.length > 0 && (
        <p className="capability-block-banner" role="status">
          {blocking.length} blocking capability status
          {blocking.length === 1 ? "" : "es"}:{" "}
          {blocking.map((row) => `${formatLabel(row.key)}=${row.status}`).join("; ")}
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
