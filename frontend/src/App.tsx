import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { getApiBaseUrl } from "./lib/api";
import { readUrlReportId } from "./lib/report-filters";
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
import ErrorBanner from "./features/shell/ErrorBanner";
import UserScreen from "./features/shell/UserScreen";
import ViewerPlaceholder from "./features/shell/ViewerPlaceholder";
import { persistUiRoleAlias, readUiRoleAlias, type UiRoleAlias } from "./lib/ui-role";
import { scrollExpertWorkplaceIntoView } from "./lib/rehearsal-land";
import { UI_COPY } from "./lib/ui-copy";
import { useAuthBff } from "./hooks/useAuthBff";
import { usePackDraft } from "./hooks/usePackDraft";
import { useReportFilters } from "./hooks/useReportFilters";
import { useReports } from "./hooks/useReports";
import { useSelectedReport } from "./hooks/useSelectedReport";
import { useSnapSelectionToFilter } from "./hooks/useSnapSelectionToFilter";
import { useTriageKeyboard } from "./hooks/useTriageKeyboard";
import { useFindingFilters } from "./hooks/useFindingFilters";
import { useTriageView } from "./hooks/useTriageView";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));
export default function App() {
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);
  const authBff = useAuthBff(uiRole);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>(() =>
    readUiRoleAlias() === "user" ? "user" : "review",
  );
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(readUrlReportId);
  const findings = useFindingFilters();

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
    reviewEvents,
    reviewEventsError,
    setSelectedIssueIndex,
    setSelectedClashIndex,
    setRemarkDraft,
    setRemarkSaveState,
    setHitlDecisionState,
    selectIssue,
    saveRemarkEdit,
    decideRemark,
  } = useSelectedReport(selectedReportId, reportsEpoch);
  const pack = usePackDraft();
  const pendingExpertLand = useRef(false);
  const {
    activeIssue,
    filteredIssues,
    hitlRegionCount,
    matchingRequirements,
    viewerFocus,
  } = useTriageView(selectedReport, selectedIssueIndex, selectedClashIndex, {
    severity: findings.issueSeverityFilter,
    hitlOnly: findings.hitlOnlyFilter,
    search: findings.issueSearch,
    clause: findings.clauseFilter,
  });

  const decideActiveRemark = useCallback(
    (eventType: "accepted" | "rejected") => decideRemark(eventType, activeIssue),
    [decideRemark, activeIssue],
  );

  useTriageKeyboard({
    enabled: TRIAGE_KEYBOARD_VIEWS.has(workspaceView),
    filteredIssues,
    selectedIssueIndex,
    hitlEnabled: authBff.hitlEnabled,
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
    if (pendingExpertLand.current && selectedReport && workspaceView === "review") {
      pendingExpertLand.current = false;
      scrollExpertWorkplaceIntoView();
    }
  }, [workspaceView, selectedReport]);

  function handleSeededReport(reportId: string): void {
    pendingExpertLand.current = true;
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
        uiRole={authBff.screenRole}
        bffStatus={authBff.discovery.status}
        roleLocked={authBff.roleLocked}
        onRoleChange={(next) => {
          setUiRole(next);
          persistUiRoleAlias(next);
          setWorkspaceView(next === "user" ? "user" : "review");
        }}
      />

      {reportsError || reportError ? (
        <ErrorBanner
          message={reportsError ?? reportError ?? ""}
          onRetry={() => setReportsEpoch((value) => value + 1)}
        />
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
      <DemoFixturePanel onSeeded={handleSeededReport} hideIntro={selectedReport !== null} />
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
          issueSeverityFilter={findings.issueSeverityFilter}
          hitlOnlyFilter={findings.hitlOnlyFilter}
          hitlRegionCount={hitlRegionCount}
          issueSearch={findings.issueSearch}
          findingGroupBy={findings.findingGroupBy}
          clauseFilter={findings.clauseFilter}
          activeIssue={activeIssue}
          matchingRequirements={matchingRequirements}
          selectedClashIndex={selectedClashIndex}
          remarkDraft={remarkDraft}
          remarkSaveState={remarkSaveState}
          hitlDecisionState={hitlDecisionState}
          hitlEnabled={authBff.hitlEnabled}
          reviewEvents={reviewEvents}
          reviewEventsError={reviewEventsError}
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
          onSeverityChange={findings.setIssueSeverityFilter}
          onHitlOnlyChange={findings.setHitlOnlyFilter}
          onSearchChange={findings.setIssueSearch}
          onGroupByChange={findings.setFindingGroupBy}
          onClauseChange={findings.setClauseFilter}
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
          onOpenScreen={setWorkspaceView}
        />
      ) : null}

      {TRIAGE_KEYBOARD_VIEWS.has(workspaceView) ? (
        <footer className="hotkeys-footer" data-testid="hotkeys-footer">
          <span>{UI_COPY.keyboardFooter}</span>
          <span className="hotkeys-note">{UI_COPY.keyboardFooterNote}</span>
        </footer>
      ) : null}

      {triageHelpOpen ? (
        <aside className="triage-help" role="dialog" aria-label={UI_COPY.keyboardHelpAria}>
          <p>{UI_COPY.keyboardHelp}</p>
        </aside>
      ) : null}
    </div>
  );
}
