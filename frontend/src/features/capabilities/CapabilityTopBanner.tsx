import type { ReportCapabilities } from "../../lib/types";
import {
  BLOCKING_STATES,
  capabilityRows,
  humanCapabilityLine,
} from "../../lib/capability-copy";
import { UI_COPY } from "../../lib/ui-copy";

export default function CapabilityTopBanner({
  capabilities,
}: {
  capabilities?: ReportCapabilities | null;
}) {
  const rows = capabilities ? capabilityRows(capabilities) : [];
  if (rows.length === 0) {
    return (
      <p className="capability-top-banner" role="note" data-testid="capability-top-banner">
        {UI_COPY.capabilityMissing}
      </p>
    );
  }

  const blocking = rows.filter((row) => BLOCKING_STATES.has(row.status));
  const skipped = rows.filter(
    (row) =>
      row.status === "skipped" ||
      row.status === "not_verified" ||
      row.status === "not_implemented",
  );

  if (blocking.length === 0 && skipped.length === 0) {
    return (
      <p className="capability-top-banner capability-top-banner-ok" role="note" data-testid="capability-top-banner">
        {UI_COPY.capabilityOkBanner}
      </p>
    );
  }

  const incomplete = [...blocking, ...skipped];
  return (
    <div className="capability-top-banner" role="note" data-testid="capability-top-banner">
      <details>
        <summary>
          {UI_COPY.capabilityIncompleteSummary(incomplete.length, rows.length)}. {UI_COPY.silenceIsNotSuccess}
        </summary>
        <p className="capability-top-banner-lines">{incomplete.map(humanCapabilityLine).join(". ")}</p>
      </details>
    </div>
  );
}
