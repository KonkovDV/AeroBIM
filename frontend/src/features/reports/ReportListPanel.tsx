import { startTransition } from "react";
import type { ReportSummaryEntry } from "../../lib/types";
import type {
  PersistedReportFilters,
  PresetScope,
  ReportFilterPreset,
} from "../../lib/report-filters";
import { UI_COPY } from "../../lib/ui-copy";

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
          {report.passed ? UI_COPY.enginePass : UI_COPY.engineFail}
        </span>
      </div>
      <div className="report-card-meta">
        {report.project_name && <span>{report.project_name}</span>}
        {report.discipline && <span>{report.discipline}</span>}
        <span>{UI_COPY.requestLabel(report.request_id)}</span>
        <span>{UI_COPY.issueCount(report.issue_count)}</span>
      </div>
      <span className="report-card-time">{formatTimestamp(report.created_at)}</span>
    </button>
  );
}

function presetTransferLabel(state: PresetTransferState): string {
  if (state === "exported") {
    return UI_COPY.presetCopied;
  }
  if (state === "downloaded") {
    return UI_COPY.presetDownloaded;
  }
  if (state === "imported") {
    return UI_COPY.presetImported;
  }
  return UI_COPY.presetFailed;
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
          <p className="panel-kicker">{UI_COPY.reportListKicker}</p>
          <h2>{UI_COPY.reportListTitle}</h2>
        </div>
      </div>

      <div className="report-toolbar">
        <div className="report-filters" aria-label={UI_COPY.reportFilters}>
          <input
            className="search-input filter-input"
            type="search"
            aria-label={UI_COPY.filterProject}
            value={projectFilter}
            onChange={(event) => onProjectFilterChange(event.target.value)}
            placeholder={UI_COPY.filterProjectPh}
          />
          <input
            className="search-input filter-input"
            type="search"
            aria-label={UI_COPY.filterDiscipline}
            value={disciplineFilter}
            onChange={(event) => onDisciplineFilterChange(event.target.value)}
            placeholder={UI_COPY.filterDisciplinePh}
          />
          <select
            className="search-input filter-select"
            aria-label={UI_COPY.filterStatus}
            value={statusFilter}
            onChange={(event) =>
              onStatusFilterChange(event.target.value as PersistedReportFilters["status"])
            }
          >
            <option value="all">{UI_COPY.statusAll}</option>
            <option value="passed">{UI_COPY.statusPassed}</option>
            <option value="failed">{UI_COPY.statusFailed}</option>
          </select>
        </div>
        <input
          className="search-input report-search-input"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={UI_COPY.searchReports}
        />
        <button
          type="button"
          className={`toolbar-button report-group-toggle ${groupByProject ? "active" : ""}`}
          onClick={onGroupByProjectToggle}
        >
          {groupByProject ? UI_COPY.ungroupReports : UI_COPY.groupByProject}
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label={UI_COPY.copyShareLink}
          onClick={onCopyShareLink}
        >
          {UI_COPY.copyShareLink}
        </button>
        {shareLinkState !== "idle" && (
          <span className={`share-link-status share-link-status-${shareLinkState}`}>
            {shareLinkState === "copied" ? UI_COPY.linkCopied : UI_COPY.copyFailed}
          </span>
        )}
      </div>

      <div className="report-presets" aria-label={UI_COPY.presetsAria}>
        <input
          className="search-input preset-name-input"
          type="text"
          aria-label={UI_COPY.presetName}
          value={presetNameDraft}
          onChange={(event) => onPresetNameChange(event.target.value)}
          placeholder={UI_COPY.presetName}
        />
        <select
          className="search-input preset-scope-select"
          aria-label={UI_COPY.presetScope}
          value={presetScopeDraft}
          onChange={(event) => onPresetScopeChange(event.target.value as PresetScope)}
        >
          <option value="browser">{UI_COPY.presetBrowser}</option>
          <option value="file">{UI_COPY.presetFile}</option>
        </select>
        <button
          type="button"
          className="toolbar-button"
          onClick={onSavePreset}
          disabled={!presetNameDraft.trim()}
        >
          {UI_COPY.savePreset}
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label={UI_COPY.copyPresets}
          onClick={onCopyPresets}
          disabled={filterPresets.length === 0}
        >
          {UI_COPY.copyPresets}
        </button>
        <button
          type="button"
          className="toolbar-button"
          aria-label={UI_COPY.downloadPresets}
          onClick={onDownloadPresets}
          disabled={filterPresets.length === 0}
        >
          {UI_COPY.downloadPresets}
        </button>
        <label className="toolbar-button preset-file-upload">
          {UI_COPY.importPresetsFile}
          <input
            type="file"
            accept=".json,application/json"
            aria-label={UI_COPY.importPresetsFile}
            onChange={(event) => {
              void onImportPresetFile(event);
            }}
          />
        </label>
        <textarea
          className="preset-import-input"
          aria-label={UI_COPY.presetImportPayload}
          value={presetTransferDraft}
          onChange={(event) => onPresetDraftChange(event.target.value)}
          placeholder={UI_COPY.presetImportPh}
        />
        <button
          type="button"
          className="toolbar-button"
          aria-label={UI_COPY.importPresetsJson}
          onClick={onImportPresets}
          disabled={!presetTransferDraft.trim()}
        >
          {UI_COPY.importPresetsJson}
        </button>
        {presetTransferState !== "idle" && (
          <span className={`preset-transfer-status preset-transfer-status-${presetTransferState}`}>
            {presetTransferLabel(presetTransferState)}
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
            <span className={`preset-scope-badge preset-scope-${preset.scope}`}>
              {preset.scope === "file" ? UI_COPY.presetFile : UI_COPY.presetBrowser}
            </span>
            <button
              type="button"
              className="toolbar-button preset-remove"
              aria-label={UI_COPY.removePreset(preset.name)}
              onClick={() => onRemovePreset(preset.id)}
            >
              x
            </button>
          </div>
        ))}
      </div>

      {reportsLoading ? (
        <div className="panel-empty">{UI_COPY.loadingReports}</div>
      ) : filteredReports.length === 0 ? (
        <div className="panel-empty">{UI_COPY.emptyReports}</div>
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
