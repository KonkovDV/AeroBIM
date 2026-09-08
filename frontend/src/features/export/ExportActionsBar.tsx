import { useState } from "react";
import { downloadExport, type ExportFormat } from "../../lib/api";
import { classifyRequestFailure, type RequestFailureKind } from "../../lib/request-failure";
import { requestFailureBody } from "../../lib/request-failure-copy";
import { UI_COPY } from "../../lib/ui-copy";

export type ExportActionsBarProps = {
  reportId: string;
  unsavedRemark?: boolean;
  showLimits?: boolean;
};

type ExportRequest = { format: ExportFormat; bcfVersion?: "2.1" | "3.0" };

const EXPORT_ACTIONS: readonly (ExportRequest & { label: string })[] = [
  { format: "html", label: "HTML" },
  { format: "json", label: "JSON" },
  { format: "bcf", label: "BCF" },
  { format: "bcf", bcfVersion: "3.0", label: "BCF 3.0" },
];

/**
 * Подсказка про PDF живёт ровно в одном месте — в видимом абзаце. Раньше тот же
 * текст дублировался в title кнопки, и скринридер произносил его дважды.
 */
const PDF_HINT_ID = "export-pdf-hint";

function actionKey(action: ExportRequest): string {
  return action.bcfVersion ? `${action.format}-${action.bcfVersion}` : action.format;
}

export default function ExportActionsBar({
  reportId,
  unsavedRemark = false,
  showLimits = false,
}: ExportActionsBarProps) {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<RequestFailureKind | null>(null);

  async function run(action: ExportRequest): Promise<void> {
    if (unsavedRemark && !window.confirm(UI_COPY.exportUnsavedConfirm)) {
      return;
    }
    setPendingKey(actionKey(action));
    setErrorKind(null);
    try {
      await downloadExport(reportId, action.format, { bcfVersion: action.bcfVersion });
    } catch (err: unknown) {
      setErrorKind(classifyRequestFailure(err));
    } finally {
      setPendingKey(null);
    }
  }

  const busy = pendingKey !== null;

  return (
    <div
      className="export-actions"
      id="export-actions"
      data-testid="export-actions"
      aria-busy={busy}
    >
      <div className="export-actions-row">
        {EXPORT_ACTIONS.map((action) => (
          <button
            key={actionKey(action)}
            type="button"
            disabled={busy}
            onClick={() => void run(action)}
          >
            {pendingKey === actionKey(action) ? UI_COPY.exportInProgress : action.label}
          </button>
        ))}
        <button
          type="button"
          aria-label={UI_COPY.exportPdf}
          aria-describedby={PDF_HINT_ID}
          disabled={busy}
          onClick={() => void run({ format: "pdf" })}
        >
          {pendingKey === "pdf" ? UI_COPY.exportInProgress : UI_COPY.exportPdf}
        </button>
      </div>
      <aside className="export-honesty">
        <p className="compact-copy" id={PDF_HINT_ID}>
          {UI_COPY.exportPdfHint}
        </p>
        <p className="compact-copy">{UI_COPY.exportSavedOnlyHint}</p>
        {showLimits ? <p className="compact-copy">{UI_COPY.xlsxNotMvp}</p> : null}
      </aside>
      {errorKind ? (
        <p className="compact-copy export-error" role="alert" data-testid="export-error" data-kind={errorKind}>
          {requestFailureBody(errorKind)}
        </p>
      ) : null}
    </div>
  );
}
