import { downloadExport } from "../../lib/api";

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
      <button type="button" onClick={() => void downloadExport(reportId, "pdf")}>
        PDF
      </button>
      <button type="button" disabled aria-label="XLSX not on MVP">
        XLSX
      </button>
    </div>
  );
}
