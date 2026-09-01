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
        Матрица capabilities на этом отчёте отсутствует. Тишина ≠ успех. Checkpoint NO_GO. UI не
        пишет <code>summary.passed</code>.
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
        FAILED/MISSING на сервере блокируют <code>summary.passed</code>. UI флаг не пишет
        (ADR-001). Checkpoint NO_GO.
      </p>
    );
  }

  return (
    <p className="capability-top-banner" role="status" data-testid="capability-top-banner">
      {[...blocking, ...skipped].map(humanCapabilityLine).join(". ")}. Не зелёный отчёт из тишины.
    </p>
  );
}
