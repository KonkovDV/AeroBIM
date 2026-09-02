import { startTransition } from "react";
import type { ReportSummaryEntry } from "../../lib/types";
import type {
  PersistedReportFilters,
  PresetScope,
  ReportFilterPreset,
} from "../../lib/report-filters";

export type ShareLinkState = "idle" | "copied" | "failed";
export type PresetTransferState = "idle" | "exported" | "downloaded" | "imported" | "failed";

export type ReportListPanelProps = {
  reportsLoading: boolean;
  filteredReports: ReportSummaryEntry[];
  groupedReports: Map<string, ReportSummaryEntry[]>;
  selectedReportId: string | null;
  search: string;
  groupByProject: boolean;
  projectFilter: string;
  disciplineFilter: string;
  statusFilter: "all" | "passed" | "failed";
  shareLinkState: ShareLinkState;
  presetTransferState: PresetTransferState;
  presetTransferDraft: string;
  presetNameDraft: string;
  presetScopeDraft: PresetScope;
  filterPresets: ReportFilterPreset[];
  onSearchChange: (value: string) => void;
  onGroupByProjectToggle: () => void;
  onProjectFilterChange: (value: string) => void;
  onDisciplineFilterChange: (value: string) => void;
  onStatusFilterChange: (value: "all" | "passed" | "failed") => void;
  onSelectReport: (reportId: string) => void;
  onCopyShareLink: () => void;
  onPresetNameChange: (value: string) => void;
  onPresetScopeChange: (value: PresetScope) => void;
  onSavePreset: () => void;
  onCopyPresets: () => void;
  onDownloadPresets: () => void;
  onImportPresets: () => void;
  onImportPresetFile: (event: { target: HTMLInputElement }) => void;
  onPresetDraftChange: (value: string) => void;
  onApplyPreset: (preset: ReportFilterPreset) => void;
  onRemovePreset: (presetId: string) => void;
};

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function ReportCard({
  report,
  selected,
  onSelect,
}: {
  report: ReportSummaryEntry;
  selected: boolean;
  onSelect: (reportId: string) => void;
}) {
  return (
    <button
      type="button"
      className={`report-card ${selected ? "active" : ""}`}
      onClick={() => {
        startTransition(() => {
          onSelect(report.report_id);
        });
      }}
    >
      <div className="report-card-row">
        <strong>{report.report_id.slice(0, 8)}</strong>
        <span className={`status-pill ${report.passed ? "pass" : "fail"}`}>
          {report.passed ? "Engine Pass" : "Engine Fail"}
        </span>
      </div>
      <div className="report-card-meta">
        {report.project_name && <span>{report.project_name}</span>}
        {report.discipline && <span>{report.discipline}</span>}
        <span>Request {report.request_id}</span>
        <span>{report.issue_count} issues</span>
      </div>
      <span className="report-card-time">{formatTimestamp(report.created_at)}</span>
    </button>
  );
}

export default function ReportListPanel({
  reportsLoading,
  filteredReports,
  groupedReports,
  selectedReportId,
  search,
  groupByProject,
  projectFilter,
  disciplineFilter,
  statusFilter,
  shareLinkState,
  presetTransferState,
  presetTransferDraft,
  presetNameDraft,
  presetScopeDraft,
  filterPresets,
  onSearchChange,
  onGroupByProjectToggle,
  onProjectFilterChange,
  onDisciplineFilterChange,
  onStatusFilterChange,
  onSelectReport,
  onCopyShareLink,
  onPresetNameChange,
  onPresetScopeChange,
  onSavePreset,
  onCopyPresets,
  onDownloadPresets,
  onImportPresets,
  onImportPresetFile,
  onPresetDraftChange,
  onApplyPreset,
  onRemovePreset,
}: ReportListPanelProps) {
  const renderCard = (report: ReportSummaryEntry) => (
    <ReportCard
      key={report.report_id}
      report={report}
      selected={report.report_id === selectedReportId}
      onSelect={onSelectReport}
    />
  );

  return (
    <section className="panel report-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Index</p>
          <h2>Report list</h2>
        </div>
      </div>

      <div className="report-toolbar">
        <div className="report-filters" aria-label="Report list filters">
          <input
            className="search-input filter-input"
            type="search"
            aria-label="Project filter"
            value={projectFilter}
            onChange={(event) => onProjectFilterChange(event.target.value)}
            placeholder="Filter by project"
          />
          <input
            className="search-input filter-input"
            type="search"
            aria-label="Discipline filter"
            value={disciplineFilter}
            onChange={(event) => onDisciplineFilterChange(event.target.value)}
            placeholder="Filter by discipline"
          />
          <select
            className="search-input filter-select"
            aria-label="Status filter"
            value={statusFilter}
            onChange={(event) =>
              onStatusFilterChange(event.target.value as PersistedReportFilters["status"])
            }
          >
            <option value="all">All statuses</option>
            <option value="passed">Passed only</option>
            <option value="failed">Failed only</option>
          </select>
        </div>
        <input
          className="search-input report-search-input"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search loaded reports"
        />
        <button
          type="button"
          className={`toolbar-button report-group-toggle ${groupByProject ? "active" : ""}`}
          onClick={onGroupByProjectToggle}
        >
          {groupByProject ? "Ungroup reports" : "Group by project"}
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label="Copy share link"
          onClick={onCopyShareLink}
        >
          Copy share link
        </button>
        {shareLinkState !== "idle" && (
          <span className={`share-link-status share-link-status-${shareLinkState}`}>
            {shareLinkState === "copied" ? "Link copied" : "Copy failed"}
          </span>
        )}
      </div>

      <div className="report-presets" aria-label="Report filter presets">
        <input
          className="search-input preset-name-input"
          type="text"
          aria-label="Preset name"
          value={presetNameDraft}
          onChange={(event) => onPresetNameChange(event.target.value)}
          placeholder="Preset name"
        />
        <select
          className="search-input preset-scope-select"
          aria-label="Preset scope"
          value={presetScopeDraft}
          onChange={(event) => onPresetScopeChange(event.target.value as PresetScope)}
        >
          <option value="local">Local scope</option>
          <option value="team">Team scope</option>
        </select>
        <button
          type="button"
          className="toolbar-button"
          onClick={onSavePreset}
          disabled={!presetNameDraft.trim()}
        >
          Save preset
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label="Copy presets JSON"
          onClick={onCopyPresets}
          disabled={filterPresets.length === 0}
        >
          Copy presets JSON
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label="Download presets JSON"
          onClick={onDownloadPresets}
          disabled={filterPresets.length === 0}
        >
          Download presets JSON
        </button>
        <label className="toolbar-button preset-file-upload" aria-label="Import presets file label">
          Import presets file
          <input
            type="file"
            accept=".json,application/json"
            aria-label="Import presets file"
            onChange={(event) => {
              void onImportPresetFile(event);
            }}
          />
        </label>
        <textarea
          className="preset-import-input"
          aria-label="Preset import payload"
          value={presetTransferDraft}
          onChange={(event) => onPresetDraftChange(event.target.value)}
          placeholder='Paste preset JSON (e.g. [{"name":"Hospital","filters":{...}}])'
        />
        <button
          type="button"
          className="toolbar-button"
          aria-label="Import presets JSON"
          onClick={onImportPresets}
          disabled={!presetTransferDraft.trim()}
        >
          Import presets JSON
        </button>
        {presetTransferState !== "idle" && (
          <span className={`preset-transfer-status preset-transfer-status-${presetTransferState}`}>
            {presetTransferState === "exported"
              ? "Preset JSON copied"
              : presetTransferState === "downloaded"
                ? "Preset JSON downloaded"
                : presetTransferState === "imported"
                  ? "Preset JSON imported"
                  : "Preset transfer failed"}
          </span>
        )}
        {filterPresets.map((preset) => (
          <div key={preset.id} className="preset-chip">
            <button
              type="button"
              className="toolbar-button preset-apply"
              onClick={() => onApplyPreset(preset)}
            >
              {preset.name}
            </button>
            <span className={`preset-scope-badge preset-scope-${preset.scope}`}>{preset.scope}</span>
            <button
              type="button"
              className="toolbar-button preset-remove"
              aria-label={`Remove preset ${preset.name}`}
              onClick={() => onRemovePreset(preset.id)}
            >
              x
            </button>
          </div>
        ))}
      </div>

      {reportsLoading ? (
        <div className="panel-empty">Loading reports…</div>
      ) : filteredReports.length === 0 ? (
        <div className="panel-empty">No persisted reports match the current query.</div>
      ) : groupByProject ? (
        <div className="report-groups">
          {Array.from(groupedReports.entries()).map(([projectName, projectReports]) => (
            <section key={projectName} className="report-group">
              <h3 className="report-group-title">
                {projectName} ({projectReports.length})
              </h3>
              <div className="report-list">{projectReports.map((report) => renderCard(report))}</div>
            </section>
          ))}
        </div>
      ) : (
        <div className="report-list">{filteredReports.map((report) => renderCard(report))}</div>
      )}
    </section>
  );
}
