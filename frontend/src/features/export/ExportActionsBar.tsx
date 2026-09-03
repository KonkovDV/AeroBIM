import { useState } from "react";
import { downloadExport, type ExportFormat } from "../../lib/api";
import { UI_COPY } from "../../lib/ui-copy";

export type ExportActionsBarProps = {
  reportId: string;
};

type ExportRequest = { format: ExportFormat; bcfVersion?: "2.1" | "3.0" };

const EXPORT_ACTIONS: readonly (ExportRequest & { label: string })[] = [
  { format: "html", label: "HTML" },
  { format: "json", label: "JSON" },
  { format: "bcf", label: "BCF" },
  { format: "bcf", bcfVersion: "3.0", label: "BCF 3.0" },
];

function actionKey(action: ExportRequest): string {
  return action.bcfVersion ? `${action.format}-${action.bcfVersion}` : action.format;
}

export default function ExportActionsBar({ reportId }: ExportActionsBarProps) {
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: ExportRequest): Promise<void> {
    setPendingKey(actionKey(action));
    setError(null);
    try {
      await downloadExport(reportId, action.format, { bcfVersion: action.bcfVersion });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : UI_COPY.exportFailedGeneric);
    } finally {
      setPendingKey(null);
    }
  }

  const busy = pendingKey !== null;

  return (
    <div className="export-actions" id="export-actions" data-testid="export-actions">
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
        title={UI_COPY.exportPdfHint}
        disabled={busy}
        onClick={() => void run({ format: "pdf" })}
      >
        {pendingKey === "pdf" ? UI_COPY.exportInProgress : UI_COPY.exportPdf}
      </button>
      <p className="compact-copy">{UI_COPY.exportPdfHint}</p>
      {error ? (
        <p className="compact-copy export-error" role="alert" data-testid="export-error">
          {UI_COPY.exportFailed(error)}
        </p>
      ) : null}
    </div>
  );
}
