import type { ReportCapabilities } from "../../lib/types";
import {
  BLOCKING_STATES,
  capabilityRows,
  humanCapabilityLine,
} from "../../lib/capability-copy";

export default function CapabilityTopBanner({
  capabilities,
}: {
  capabilities?: ReportCapabilities | null;
}) {
  if (!capabilities) {
    return (
      <p className="capability-top-banner" role="status" data-testid="capability-top-banner">
        Capabilities matrix is missing on this report. Silence is never success. Checkpoint NO_GO. UI
        does not write <code>summary.passed</code>.
      </p>
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

  if (blocking.length === 0 && skipped.length === 0) {
    return (
      <p className="capability-top-banner capability-top-banner-ok" role="status" data-testid="capability-top-banner">
        FAILED/MISSING on the server block <code>summary.passed</code>. The UI does not write the
        flag (ADR-001). Checkpoint NO_GO.
      </p>
    );
  }

  return (
    <p className="capability-top-banner" role="status" data-testid="capability-top-banner">
      {[...blocking, ...skipped].map(humanCapabilityLine).join(". ")}. Тишина ≠ успех.
    </p>
  );
}
