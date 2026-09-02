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
  if (!capabilities) {
    return (
      <p className="capability-top-banner" role="status" data-testid="capability-top-banner">
        {UI_COPY.capabilityMissing}
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
        {UI_COPY.capabilityOkBanner}
      </p>
    );
  }

  return (
    <p className="capability-top-banner" role="status" data-testid="capability-top-banner">
      {[...blocking, ...skipped].map(humanCapabilityLine).join(". ")}. Тишина ≠ успех.
    </p>
  );
}
