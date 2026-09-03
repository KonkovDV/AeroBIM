import { useEffect, useState } from "react";
import { fetchSystemCapabilities, type SystemCapabilitiesPayload } from "../../lib/api";
import { INTAKE_GATE_KEYS, intakeGateLabel, isIntakeGateTrue } from "../../lib/intake-gates";
import { UI_COPY } from "../../lib/ui-copy";

function intakeStatusLabel(status: string): string {
  if (status === "BLOCKED_NO_CUSTOMER_DATA") {
    return UI_COPY.blockersGateClosed;
  }
  return status;
}

export default function BlockerHonestyPanel() {
  const [payload, setPayload] = useState<SystemCapabilitiesPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    void fetchSystemCapabilities({ signal: controller.signal })
      .then((next) => {
        setPayload(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setPayload(null);
          setError(err instanceof Error ? err.message : UI_COPY.kpiUnavailable);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, []);

  const trueGates = payload?.customer_intake_gate.true_gates ?? [];
  const answers = payload?.samolet_mvp_answers;
  const rt001 = answers?.closes_rt001 === true;
  const rt002 = answers?.closes_rt002 === true;
  const rt003 = answers?.closes_rt003 === true;

  return (
    <section className="panel blocker-honesty-panel" data-testid="blocker-honesty-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">{UI_COPY.blockersKicker}</p>
          <h2>{UI_COPY.blockersTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">{UI_COPY.blockersBody}</p>
      <ul className="kpi-list" data-testid="rt-blocker-list">
        <li>
          RT-001 {rt001 ? UI_COPY.blockerNotClosable : UI_COPY.blockerRt001Open}.
        </li>
        <li>
          RT-002 {rt002 ? UI_COPY.blockerNotClosable : UI_COPY.blockerRt002Open}.
        </li>
        <li>
          RT-003 {rt003 ? UI_COPY.blockerNotClosable : UI_COPY.blockerRt003Open}.
        </li>
      </ul>
      {loading ? <p className="compact-copy">{UI_COPY.blockersLoading}</p> : null}
      {error ? (
        <p className="compact-copy" role="status">
          {UI_COPY.blockersSnapshotFailed(error)}
        </p>
      ) : null}
      {payload ? (
        <p className="compact-copy">
          {UI_COPY.blockersIntake}: <code>{intakeStatusLabel(payload.customer_intake_gate.status)}</code> ·{" "}
          {UI_COPY.blockersClaimLevel} <code>{payload.customer_intake_gate.claim_level}</code> ·{" "}
          {UI_COPY.blockersCheckpoint} <code>{payload.customer_intake_gate.checkpoint}</code>
          {payload.auth_bff?.status ? ` · auth_bff ${payload.auth_bff.status}` : ""}
          {payload.bcf_t2
            ? ` · BCF T2 ${payload.bcf_t2.status}${payload.bcf_t2.claim_allowed ? "" : ` (${UI_COPY.blockersNotVerified})`}`
            : ""}
        </p>
      ) : null}
      <table className="coverage-table" data-testid="intake-gate-table">
        <thead>
          <tr>
            <th scope="col">{UI_COPY.blockersGateCol}</th>
            <th scope="col">{UI_COPY.blockersInFileCol}</th>
            <th scope="col">{UI_COPY.blockersMeaningCol}</th>
          </tr>
        </thead>
        <tbody>
          {INTAKE_GATE_KEYS.map((key) => (
            <tr key={key}>
              <td>
                <code>{key}</code>
              </td>
              <td>
                <code>{isIntakeGateTrue(trueGates, key) ? "true" : "false"}</code>
              </td>
              <td className="cov-reason">{intakeGateLabel(key)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="compact-copy">{UI_COPY.blockersFooter}</p>
    </section>
  );
}
