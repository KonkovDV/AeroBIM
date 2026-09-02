import { downloadExport } from "../../lib/api";
import { UI_COPY } from "../../lib/ui-copy";

export type ExportActionsBarProps = {
  reportId: string;
};

export default function ExportActionsBar({ reportId }: ExportActionsBarProps) {
  return (
    <div className="export-actions" id="export-actions" data-testid="export-actions">
      <button type="button" onClick={() => void downloadExport(reportId, "html")}>
        HTML
      </button>
      <button type="button" onClick={() => void downloadExport(reportId, "json")}>
        JSON
      </button>
      <button type="button" onClick={() => void downloadExport(reportId, "bcf")}>
        BCF
      </button>
      <button
        type="button"
        onClick={() => void downloadExport(reportId, "bcf", { bcfVersion: "3.0" })}
      >
        BCF 3.0
      </button>
      <button
        type="button"
        aria-label={UI_COPY.exportPdf}
        title={UI_COPY.exportPdfHint}
        onClick={() => void downloadExport(reportId, "pdf")}
      >
        {UI_COPY.exportPdf}
      </button>
      <button type="button" disabled aria-label={UI_COPY.xlsxNotMvp}>
        XLSX
      </button>
      <p className="compact-copy">{UI_COPY.exportPdfHint}</p>
    </div>
  );
}
