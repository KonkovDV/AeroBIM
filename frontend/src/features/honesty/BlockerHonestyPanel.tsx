import { useEffect, useState } from "react";
import { fetchSystemCapabilities, type SystemCapabilitiesPayload } from "../../lib/api";
import { INTAKE_GATE_KEYS, intakeGateLabel, isIntakeGateTrue } from "../../lib/intake-gates";

function intakeStatusLabel(status: string): string {
  if (status === "BLOCKED_NO_CUSTOMER_DATA") {
    return "gates closed (channel received, pack not in git)";
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
          setError(err instanceof Error ? err.message : "capabilities unavailable");
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
          <p className="panel-kicker">Acceptance blockers</p>
          <h2>RT-001 / RT-002 / RT-003</h2>
        </div>
      </div>
      <p className="compact-copy">
        This screen helps the pilot; it does not hide the checkpoint. The UI does not flip gates.
        Two adjudicators and a signed profile sit outside this shell. κ/α is computed on the backend
        once a corpus exists. Checkpoint NO_GO.
      </p>
      <ul className="kpi-list" data-testid="rt-blocker-list">
        <li>
          RT-001 {rt001 ? "cannot be treated as CLOSED from this screen" : "OPEN"}: no labeled
          Russian PD pack and two independent adjudicators.
        </li>
        <li>
          RT-002 {rt002 ? "cannot be treated as CLOSED from this screen" : "OPEN"}: no Samolet-signed
          acceptance profile.
        </li>
        <li>
          RT-003 {rt003 ? "cannot be treated as CLOSED from this screen" : "OPEN"}: federated MEP
          clashes remain NOT_VERIFIED.
        </li>
      </ul>
      {loading ? <p className="compact-copy">Loading GET /v1/system/capabilities…</p> : null}
      {error ? (
        <p className="compact-copy" role="status">
          Live gate snapshot unavailable ({error}). The static list below stays OPEN.
        </p>
      ) : null}
      {payload ? (
        <p className="compact-copy">
          Intake: <code>{intakeStatusLabel(payload.customer_intake_gate.status)}</code> · claim_level{" "}
          <code>{payload.customer_intake_gate.claim_level}</code> · checkpoint{" "}
          <code>{payload.customer_intake_gate.checkpoint}</code>
          {payload.auth_bff?.status ? ` · auth_bff ${payload.auth_bff.status}` : ""}
          {payload.bcf_t2
            ? ` · BCF T2 ${payload.bcf_t2.status}${payload.bcf_t2.claim_allowed ? "" : " (not VERIFIED)"}`
            : ""}
        </p>
      ) : null}
      <table className="coverage-table" data-testid="intake-gate-table">
        <thead>
          <tr>
            <th scope="col">Gate</th>
            <th scope="col">In file</th>
            <th scope="col">Meaning</th>
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
      <p className="compact-copy">
        true in the gate JSON ≠ RT CLOSED and ≠ product accuracy. PrecisionClaim.publishable stays
        the gateway. BCF import into a CDE and OIDC are not evidenced.
      </p>
    </section>
  );
}
