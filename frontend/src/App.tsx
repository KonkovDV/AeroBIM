import { Suspense, lazy, useCallback, useState } from "react";
import { getApiBaseUrl } from "./lib/api";
import { readUrlReportId } from "./lib/report-filters";
import DemoFixturePanel from "./components/DemoFixturePanel";
import DirtyLeaveDialog from "./components/DirtyLeaveDialog";
import KeyboardHelpDialog from "./components/KeyboardHelpDialog";
import { persistTriageShortcuts, readTriageShortcuts } from "./lib/triage-preferences";
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
import { UI_COPY } from "./lib/ui-copy";
import { useAuthBff } from "./hooks/useAuthBff";
import { usePackDraft } from "./hooks/usePackDraft";
import { useReportFilters } from "./hooks/useReportFilters";
import { useReports } from "./hooks/useReports";
import { useRunPolling } from "./hooks/useRunPolling";
import { useSelectedReport } from "./hooks/useSelectedReport";
import { useSnapSelectionToFilter } from "./hooks/useSnapSelectionToFilter";
import { useTriageKeyboard } from "./hooks/useTriageKeyboard";
import { useFindingFilters } from "./hooks/useFindingFilters";
import { useTriageView } from "./hooks/useTriageView";
import { useWorkspaceLanding } from "./hooks/useWorkspaceLanding";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));
export default function App() {
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);
  const authBff = useAuthBff(uiRole);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>(() =>
    uiRole === "user" ? "user" : "review",
  );
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [triageShortcutsEnabled, setTriageShortcutsEnabled] = useState(readTriageShortcuts);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(readUrlReportId);
  const [pendingNav, setPendingNav] = useState<
    | { kind: "report"; reportId: string; thenView?: WorkspaceView }
    | { kind: "view"; view: WorkspaceView }
    | null
  >(null);
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
    historyPending,
    setSelectedClashIndex,
    setRemarkDraft,
    setRemarkSaveState,
    setHitlDecisionState,
    selectIssue,
    pendingSelect,
    conflictMessage,
    confirmPendingSelect,
    dismissPendingSelect,
    saveRemarkEdit,
    decideRemark,
    isDirty,
  } = useSelectedReport(selectedReportId, reportsEpoch);
  const pack = usePackDraft();
  const landing = useWorkspaceLanding({
    workspaceView,
    hasReport: selectedReport !== null,
    setWorkspaceView,
  });
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
    enabled: TRIAGE_KEYBOARD_VIEWS.has(workspaceView) && !triageHelpOpen && triageShortcutsEnabled,
    filteredIssues,
    selectedIssueIndex,
    hitlEnabled: authBff.hitlEnabled,
    setTriageHelpOpen,
    selectIssue,
    decideRemark: decideActiveRemark,
  });
  useSnapSelectionToFilter(filteredIssues, selectedIssueIndex, selectIssue);

  const handleSeededReport = useCallback((reportId: string): void => {
    landing.landOnExpert();
    if (isDirty) {
      if (reportId !== selectedReportId) {
        setPendingNav({ kind: "report", reportId, thenView: "review" });
      }
      return;
    }
    setSelectedReportId(reportId);
    setReportsEpoch((value) => value + 1);
    setWorkspaceView("review");
  }, [isDirty, landing, selectedReportId]);

  const requestWorkspaceView = useCallback(
    (view: WorkspaceView) => {
      if (view === workspaceView) {
        return;
      }
      if (isDirty) {
        setPendingNav({ kind: "view", view });
        return;
      }
      setWorkspaceView(view);
    },
    [isDirty, workspaceView],
  );

  const requestSelectReport = useCallback(
    (reportId: string) => {
      if (reportId === selectedReportId) {
        return;
      }
      if (isDirty) {
        setPendingNav({ kind: "report", reportId });
        return;
      }
      setSelectedReportId(reportId);
    },
    [isDirty, selectedReportId],
  );

  const resolveLeave = useCallback(
    async (mode: "save" | "discard") => {
      if (pendingSelect) {
        await confirmPendingSelect(mode);
        return;
      }
      if (!pendingNav) {
        return;
      }
      if (mode === "save") {
        const saved = await saveRemarkEdit(activeIssue);
        if (!saved) {
          return;
        }
      }
      const nav = pendingNav;
      setPendingNav(null);
      if (nav.kind === "report") {
        setSelectedReportId(nav.reportId);
        setReportsEpoch((value) => value + 1);
        if (nav.thenView) {
          setWorkspaceView(nav.thenView);
        }
      } else {
        setWorkspaceView(nav.view);
      }
    },
    [activeIssue, confirmPendingSelect, pendingNav, pendingSelect, saveRemarkEdit],
  );

  const runPolling = useRunPolling(handleSeededReport, authBff.discovery.status !== "LOADING");

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
        onChange={requestWorkspaceView}
        reviewFindingsCount={selectedReport ? selectedReport.issues.length : null}
      />
      <PackCycleStrip
        workspaceView={workspaceView}
        packDraft={pack.packDraft}
        hasReport={selectedReportId !== null}
        onChange={requestWorkspaceView}
      />
      {import.meta.env.DEV ? (
        <DemoFixturePanel onSeeded={handleSeededReport} hideIntro={selectedReport !== null} />
      ) : null}
      {EXPERT_SHELL_VIEWS.has(workspaceView) && selectedReport ? (
        <CapabilityTopBanner capabilities={selectedReport.capabilities} />
      ) : null}

      {workspaceView === "upload" || workspaceView === "run" ? (
        <PackScreens
          workspaceView={workspaceView}
          pack={pack}
          capabilities={selectedReport?.capabilities ?? null}
          capabilitiesReportId={selectedReport?.report_id ?? selectedReportId}
          onReportReady={handleSeededReport}
          onNavigate={requestWorkspaceView}
          runPolling={runPolling}
        />
      ) : null}

      {workspaceView === "diff" ? <VersionDiffPanel reports={filteredReports} /> : null}

      {workspaceView === "user" ? (
        <UserScreen
          selectedReportId={selectedReportId}
          selectedReport={selectedReport}
          onOpenScreen={requestWorkspaceView}
          onNavigateToFindings={landing.landOnFindings}
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
            if (reportId === selectedReportId) {
              requestWorkspaceView("review");
              return;
            }
            if (isDirty) {
              setPendingNav({ kind: "report", reportId, thenView: "review" });
              return;
            }
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
          historyPending={historyPending}
          conflictMessage={conflictMessage}
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
          onSelectReport={requestSelectReport}
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
          onNavigateToFindings={landing.landOnFindings}
          onOpenScreen={requestWorkspaceView}
        />
      ) : null}

      {TRIAGE_KEYBOARD_VIEWS.has(workspaceView) ? (
        <footer className="hotkeys-footer" data-testid="hotkeys-footer">
          <span>{triageShortcutsEnabled ? UI_COPY.keyboardFooter : UI_COPY.keyboardShortcutsOff}</span>
          <span className="hotkeys-note">{UI_COPY.keyboardFooterNote}</span>
          <button type="button" className="toolbar-button keyboard-help-trigger"
            aria-haspopup="dialog" aria-expanded={triageHelpOpen}
            onClick={() => setTriageHelpOpen(true)}>
            {UI_COPY.keyboardHelpTrigger}
          </button>
        </footer>
      ) : null}

      {pendingSelect || pendingNav ? (
        <DirtyLeaveDialog
          onSave={() => {
            void resolveLeave("save");
          }}
          onDiscard={() => {
            void resolveLeave("discard");
          }}
          onStay={() => {
            dismissPendingSelect();
            setPendingNav(null);
          }}
        />
      ) : null}

      {triageHelpOpen ? (
        <KeyboardHelpDialog
          onClose={() => setTriageHelpOpen(false)}
          shortcutsEnabled={triageShortcutsEnabled}
          onShortcutsChange={(enabled) => {
            setTriageShortcutsEnabled(enabled);
            persistTriageShortcuts(enabled);
          }}
        />
      ) : null}
    </div>
  );
}
