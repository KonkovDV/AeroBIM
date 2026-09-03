import ReportListPanel from "./ReportListPanel";
import { useFilterPresets } from "../../hooks/useFilterPresets";
import type { useReportFilters } from "../../hooks/useReportFilters";
import type { ReportSummaryEntry } from "../../lib/types";

type ProjectsScreenProps = {
  filters: ReturnType<typeof useReportFilters>;
  reportsLoading: boolean;
  filteredReports: ReportSummaryEntry[];
  groupedReports: Map<string, ReportSummaryEntry[]>;
  selectedReportId: string | null;
  onSelectReport: (reportId: string) => void;
};

/** Экран «Проекты»: индекс отчётов + пресеты фильтров (обмен через JSON). */
export default function ProjectsScreen({
  filters,
  reportsLoading,
  filteredReports,
  groupedReports,
  selectedReportId,
  onSelectReport,
}: ProjectsScreenProps) {
  const {
    filterPresets,
    presetTransferState,
    presetTransferDraft,
    presetNameDraft,
    presetScopeDraft,
    setPresetNameDraft,
    setPresetScopeDraft,
    setPresetTransferDraft,
    setPresetTransferState,
    saveCurrentPreset,
    removePreset,
    copyPresetPayload,
    downloadPresetPayload,
    importPresetPayload,
    importPresetFile,
  } = useFilterPresets();
  const {
    search,
    setSearch,
    groupByProject,
    setGroupByProject,
    shareLinkState,
    projectFilter,
    setProjectFilter,
    disciplineFilter,
    setDisciplineFilter,
    statusFilter,
    setStatusFilter,
    applyPreset,
    copyShareLink,
  } = filters;

  return (
    <main className="workspace-alt" data-testid="projects-index">
      <ReportListPanel
        reportsLoading={reportsLoading}
        filteredReports={filteredReports}
        groupedReports={groupedReports}
        selectedReportId={selectedReportId}
        search={search}
        groupByProject={groupByProject}
        projectFilter={projectFilter}
        disciplineFilter={disciplineFilter}
        statusFilter={statusFilter}
        shareLinkState={shareLinkState}
        presetTransferState={presetTransferState}
        presetTransferDraft={presetTransferDraft}
        presetNameDraft={presetNameDraft}
        presetScopeDraft={presetScopeDraft}
        filterPresets={filterPresets}
        onSearchChange={setSearch}
        onGroupByProjectToggle={() => setGroupByProject((current) => !current)}
        onProjectFilterChange={setProjectFilter}
        onDisciplineFilterChange={setDisciplineFilter}
        onStatusFilterChange={setStatusFilter}
        onSelectReport={onSelectReport}
        onCopyShareLink={() => {
          void copyShareLink();
        }}
        onPresetNameChange={setPresetNameDraft}
        onPresetScopeChange={setPresetScopeDraft}
        onSavePreset={() =>
          saveCurrentPreset({
            project: projectFilter,
            discipline: disciplineFilter,
            status: statusFilter,
          })
        }
        onCopyPresets={() => {
          void copyPresetPayload();
        }}
        onDownloadPresets={downloadPresetPayload}
        onImportPresets={importPresetPayload}
        onImportPresetFile={(event) => {
          void importPresetFile(event);
        }}
        onPresetDraftChange={(value) => {
          setPresetTransferDraft(value);
          setPresetTransferState("idle");
        }}
        onApplyPreset={applyPreset}
        onRemovePreset={removePreset}
      />
    </main>
  );
}
