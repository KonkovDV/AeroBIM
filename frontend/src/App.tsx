import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import { getApiBaseUrl } from "./lib/api";
import type { ParsedRequirement, ValidationIssue, ValidationReport } from "./lib/types";
import { readUrlReportId } from "./lib/report-filters";
import { buildViewerFocus, filterTriageIssues, type FindingGroupBy } from "./lib/issue-triage";
import DemoFixturePanel from "./components/DemoFixturePanel";
import VersionDiffPanel from "./components/VersionDiffPanel";
import WorkspaceNav, {
  EXPERT_SHELL_VIEWS,
  TRIAGE_KEYBOARD_VIEWS,
  type WorkspaceView,
} from "./components/WorkspaceNav";
import CapabilityTopBanner from "./features/capabilities/CapabilityTopBanner";
import ExpertWorkplace from "./features/workplace/ExpertWorkplace";
import PackCycleStrip from "./features/workplace/PackCycleStrip";
import ProjectsScreen from "./features/reports/ProjectsScreen";
import PackScreens from "./features/shell/PackScreens";
import ShellHeader from "./features/shell/ShellHeader";
import UserScreen from "./features/shell/UserScreen";
import ViewerPlaceholder from "./features/shell/ViewerPlaceholder";
import { persistUiRoleAlias, readUiRoleAlias, type UiRoleAlias } from "./lib/ui-role";
import { UI_COPY } from "./lib/ui-copy";
import { usePackDraft } from "./hooks/usePackDraft";
import { useReportFilters } from "./hooks/useReportFilters";
import { useReports } from "./hooks/useReports";
import { useSelectedReport } from "./hooks/useSelectedReport";
import { useTriageKeyboard } from "./hooks/useTriageKeyboard";
import { useSnapSelectionToFilter } from "./hooks/useSnapSelectionToFilter";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));

function findMatchingRequirements(
  report: ValidationReport,
  issue: ValidationIssue | null,
): ParsedRequirement[] {
  if (issue === null) {
    return report.requirements;
  }
  return report.requirements.filter((requirement) => requirement.rule_id === issue.rule_id);
}

export default function App() {
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>(() =>
    readUiRoleAlias() === "user" ? "user" : "review",
  );
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [findingGroupBy, setFindingGroupBy] = useState<FindingGroupBy>("none");
  const [issueSeverityFilter, setIssueSeverityFilter] = useState<
    "all" | "error" | "warning" | "info"
  >("all");
  const [hitlOnlyFilter, setHitlOnlyFilter] = useState(false);
  const [issueSearch, setIssueSearch] = useState("");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(readUrlReportId);

  const reportFilters = useReportFilters(selectedReportId);
  const { reports, reportsLoading, reportsError, filteredReports, groupedReports } = useReports({
    projectFilter: reportFilters.projectFilter,
    disciplineFilter: reportFilters.disciplineFilter,
    statusFilter: reportFilters.statusFilter,
    search: reportFilters.search,
    epoch: reportsEpoch,
    setSelectedReportId,
  });
  const {
    selectedReport,
    reportLoading,
    reportError,
    selectedIssueIndex,
    selectedClashIndex,
    remarkDraft,
    remarkSaveState,
    hitlDecisionState,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    setRemarkSaveState,
    setHitlDecisionState,
    selectIssue,
    saveRemarkEdit,
    decideRemark,
  } = useSelectedReport(selectedReportId);
  const pack = usePackDraft();

  const activeIssue =
    selectedReport && selectedReport.issues.length > 0
      ? selectedReport.issues[Math.min(selectedIssueIndex, selectedReport.issues.length - 1)]
      : null;
  const filteredIssues =
    selectedReport === null
      ? []
      : filterTriageIssues(selectedReport, {
          severity: issueSeverityFilter,
          hitlOnly: hitlOnlyFilter,
          search: issueSearch,
        });
  const hitlRegionCount = selectedReport
    ? (selectedReport.drawing_regions ?? []).filter((region) => region.hitl_required === true)
        .length
    : 0;
  const activeClash =
    selectedReport && selectedClashIndex !== null && selectedReport.clash_results.length > 0
      ? selectedReport.clash_results[
          Math.min(selectedClashIndex, selectedReport.clash_results.length - 1)
        ]
      : null;
  const matchingRequirements = selectedReport
    ? findMatchingRequirements(selectedReport, activeIssue)
    : [];
  const viewerFocus = buildViewerFocus(activeIssue, activeClash);

  const decideActiveRemark = useCallback(
    (eventType: "accepted" | "rejected") => decideRemark(eventType, activeIssue),
    [decideRemark, activeIssue],
  );

  useTriageKeyboard({
    enabled: TRIAGE_KEYBOARD_VIEWS.has(workspaceView),
    filteredIssues,
    selectedIssueIndex,
    uiRole,
    setTriageHelpOpen,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    decideRemark: decideActiveRemark,
  });
  useSnapSelectionToFilter(filteredIssues, selectedIssueIndex, selectIssue);

  useEffect(() => {
    if (workspaceView === "remark") {
      document.getElementById("remark-editor")?.focus();
    }
    if (workspaceView === "export") {
      document.getElementById("export-actions")?.scrollIntoView({ block: "nearest" });
    }
  }, [workspaceView, selectedReport]);

  function handleSeededReport(reportId: string): void {
    setSelectedReportId(reportId);
    setReportsEpoch((value) => value + 1);
    setWorkspaceView("review");
  }

  function navigateToFindings(): void {
    setWorkspaceView("review");
    document.querySelector(".issue-list")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="app-shell">
      <ShellHeader
        apiBase={getApiBaseUrl()}
        reportCount={reports.length}
        uiRole={uiRole}
        onRoleChange={(next) => {
          setUiRole(next);
          persistUiRoleAlias(next);
          setWorkspaceView(next === "user" ? "user" : "review");
        }}
      />

      {reportsError || reportError ? (
        <section className="error-banner">{reportsError ?? reportError}</section>
      ) : null}

      <WorkspaceNav
        workspaceView={workspaceView}
        onChange={setWorkspaceView}
        reviewFindingsCount={selectedReport ? selectedReport.issues.length : null}
      />
      <PackCycleStrip
        workspaceView={workspaceView}
        packDraft={pack.packDraft}
        hasReport={selectedReportId !== null}
        onChange={setWorkspaceView}
      />
      <DemoFixturePanel onSeeded={handleSeededReport} />
      {EXPERT_SHELL_VIEWS.has(workspaceView) && selectedReport ? (
        <CapabilityTopBanner capabilities={selectedReport.capabilities} />
      ) : null}

      {workspaceView === "upload" || workspaceView === "run" ? (
        <PackScreens
          workspaceView={workspaceView}
          pack={pack}
          capabilities={selectedReport?.capabilities ?? null}
          onReportReady={handleSeededReport}
          onNavigate={setWorkspaceView}
        />
      ) : null}

      {workspaceView === "diff" ? <VersionDiffPanel reports={filteredReports} /> : null}

      {workspaceView === "user" ? (
        <UserScreen
          selectedReportId={selectedReportId}
          selectedReport={selectedReport}
          onOpenScreen={setWorkspaceView}
          onNavigateToFindings={navigateToFindings}
        />
      ) : null}

      {workspaceView === "projects" ? (
        <ProjectsScreen
          filters={reportFilters}
          reportsLoading={reportsLoading}
          filteredReports={filteredReports}
          groupedReports={groupedReports}
          selectedReportId={selectedReportId}
          onSelectReport={(reportId) => {
            setSelectedReportId(reportId);
            setWorkspaceView("review");
          }}
        />
      ) : null}

      {EXPERT_SHELL_VIEWS.has(workspaceView) ? (
        <ExpertWorkplace
          workspaceView={workspaceView}
          reports={filteredReports}
          selectedReportId={selectedReportId}
          selectedReport={selectedReport}
          reportLoading={reportLoading}
          filteredIssues={filteredIssues}
          selectedIssueIndex={selectedIssueIndex}
          issueSeverityFilter={issueSeverityFilter}
          hitlOnlyFilter={hitlOnlyFilter}
          hitlRegionCount={hitlRegionCount}
          issueSearch={issueSearch}
          findingGroupBy={findingGroupBy}
          activeIssue={activeIssue}
          matchingRequirements={matchingRequirements}
          selectedClashIndex={selectedClashIndex}
          remarkDraft={remarkDraft}
          remarkSaveState={remarkSaveState}
          hitlDecisionState={hitlDecisionState}
          hitlEnabled={uiRole === "expert"}
          spatialViewer={
            <Suspense fallback={<ViewerPlaceholder message={UI_COPY.viewerLoading} />}>
              {selectedReport ? (
                <IfcViewerPanel
                  report={selectedReport}
                  selectedGuids={viewerFocus.guids}
                  selectionMode={viewerFocus.mode}
                  selectionHeading={viewerFocus.heading}
                  selectionDetail={viewerFocus.detail}
                />
              ) : (
                <ViewerPlaceholder message={UI_COPY.viewerNeedReport} />
              )}
            </Suspense>
          }
          onSelectReport={setSelectedReportId}
          onSeverityChange={setIssueSeverityFilter}
          onHitlOnlyChange={setHitlOnlyFilter}
          onSearchChange={setIssueSearch}
          onGroupByChange={setFindingGroupBy}
          onSelectIssue={selectIssue}
          onSelectClash={setSelectedClashIndex}
          onDraftChange={(value) => {
            setRemarkDraft(value);
            setRemarkSaveState("idle");
            setHitlDecisionState("idle");
          }}
          onSave={() => {
            void saveRemarkEdit(activeIssue);
          }}
          onAccept={() => {
            void decideActiveRemark("accepted");
          }}
          onReject={() => {
            void decideActiveRemark("rejected");
          }}
          onNavigateToFindings={navigateToFindings}
        />
      ) : null}

      {TRIAGE_KEYBOARD_VIEWS.has(workspaceView) ? (
        <footer className="hotkeys-footer" data-testid="hotkeys-footer">
          <span>{UI_COPY.keyboardFooter}</span>
          <span className="hotkeys-note">{UI_COPY.keyboardFooterNote}</span>
        </footer>
      ) : null}

      {triageHelpOpen ? (
        <aside className="triage-help" role="dialog" aria-label="Справка клавиатуры триажа">
          <p>{UI_COPY.keyboardHelp}</p>
        </aside>
      ) : null}
    </div>
  );
}
