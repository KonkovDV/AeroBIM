import { Suspense, lazy } from "react";
import { getApiBaseUrl } from "./lib/api";
import DemoFixturePanel from "./components/DemoFixturePanel";
import DirtyLeaveDialog from "./components/DirtyLeaveDialog";
import KeyboardHelpDialog from "./components/KeyboardHelpDialog";
import VersionDiffPanel from "./components/VersionDiffPanel";
import WorkspaceNav, {
  EXPERT_SHELL_VIEWS,
  TRIAGE_KEYBOARD_VIEWS,
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
import { UI_COPY } from "./lib/ui-copy";

import { useReviewShell } from "./hooks/useReviewShell";
import IfcViewerErrorBoundary from "./features/shell/IfcViewerErrorBoundary";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));
export default function App() {
  const {
    authBff,
    workspaceView,
    triageHelpOpen,
    setTriageHelpOpen,
    triageShortcutsEnabled,
    selectedReportId,
    findings,
    reportFilters,
    reportsState,
    review,
    pack,
    landing,
    triage,
    handleSeededReport,
    beginDemoSeed,
    failDemoSeed,
    requestWorkspaceView,
    requestSelectReport,
    resolveLeave,
    decideActiveRemark,
    pendingLeave,
    changeUiRole,
    retryReports,
    openProjectReport,
    changeDraft,
    stayOnCurrent,
    changeShortcuts,
    runPolling,
  } = useReviewShell();

  return (
    <div className="app-shell">
      <ShellHeader
        apiBase={getApiBaseUrl()}
        reportCount={reportsState.reports.length}
        uiRole={authBff.screenRole}
        bffStatus={authBff.discovery.status}
        roleLocked={authBff.roleLocked}
        onRoleChange={changeUiRole}
      />

      {reportsState.reportsError || review.reportError ? (
        <ErrorBanner
          kind={reportsState.reportsError ?? review.reportError ?? "unknown"}
          onRetry={retryReports}
        />
      ) : null}

      <WorkspaceNav
        workspaceView={workspaceView}
        onChange={requestWorkspaceView}
        reviewFindingsCount={review.selectedReport ? review.selectedReport.issues.length : null}
      />
      <PackCycleStrip
        workspaceView={workspaceView}
        packDraft={pack.packDraft}
        hasReport={selectedReportId !== null}
        onChange={requestWorkspaceView}
      />
      <div id="work-area" tabIndex={-1} className="skip-to-work-target" />
      {import.meta.env.DEV ? (
        <DemoFixturePanel
          onSeeded={handleSeededReport}
          onSeedStarted={beginDemoSeed}
          onSeedFailed={failDemoSeed}
          hideIntro={review.selectedReport !== null}
        />
      ) : null}
      {EXPERT_SHELL_VIEWS.has(workspaceView) && review.selectedReport ? (
        <CapabilityTopBanner capabilities={review.selectedReport.capabilities} />
      ) : null}

      {workspaceView === "upload" || workspaceView === "run" ? (
        <PackScreens
          workspaceView={workspaceView}
          pack={pack}
          capabilities={review.selectedReport?.capabilities ?? null}
          capabilitiesReportId={review.selectedReport?.report_id ?? selectedReportId}
          onReportReady={handleSeededReport}
          onNavigate={requestWorkspaceView}
          runPolling={runPolling}
        />
      ) : null}

      {workspaceView === "diff" ? <VersionDiffPanel reports={reportsState.filteredReports} /> : null}

      {workspaceView === "user" ? (
        <UserScreen
          selectedReportId={selectedReportId}
          selectedReport={review.selectedReport}
          onOpenScreen={requestWorkspaceView}
          onNavigateToFindings={landing.landOnFindings}
        />
      ) : null}

      {workspaceView === "projects" ? (
        <ProjectsScreen
          filters={reportFilters}
          reportsLoading={reportsState.reportsLoading}
          filteredReports={reportsState.filteredReports}
          groupedReports={reportsState.groupedReports}
          selectedReportId={selectedReportId}
          onSelectReport={openProjectReport}
        />
      ) : null}

      {EXPERT_SHELL_VIEWS.has(workspaceView) ? (
        <ExpertWorkplace
          workspaceView={workspaceView}
          reports={reportsState.filteredReports}
          selectedReportId={selectedReportId}
          selectedReport={review.selectedReport}
          reportLoading={review.reportLoading}
          filteredIssues={triage.filteredIssues}
          advisoryIssues={triage.advisoryIssues}
          selectedIssueIndex={review.selectedIssueIndex}
          issueSeverityFilter={findings.issueSeverityFilter}
          hitlOnlyFilter={findings.hitlOnlyFilter}
          hitlRegionCount={triage.hitlRegionCount}
          issueSearch={findings.issueSearch}
          findingGroupBy={findings.findingGroupBy}
          clauseFilter={findings.clauseFilter}
          activeIssue={triage.activeIssue}
          matchingRequirements={triage.matchingRequirements}
          selectedClashIndex={review.selectedClashIndex}
          remarkDraft={review.remarkDraft}
          remarkSaveState={review.remarkSaveState}
          hitlDecisionState={review.hitlDecisionState}
          hitlEnabled={authBff.hitlEnabled}
          reviewEvents={review.reviewEvents}
          reviewEventsError={review.reviewEventsError}
          historyPending={review.historyPending}
          conflictMessage={review.conflictMessage}
          spatialViewer={
            <IfcViewerErrorBoundary>
              <Suspense fallback={<ViewerPlaceholder message={UI_COPY.viewerLoading} />}>
                {review.selectedReport ? (
                  <IfcViewerPanel
                    report={review.selectedReport}
                    selectedGuids={triage.viewerFocus.guids}
                    selectionMode={triage.viewerFocus.mode}
                    selectionHeading={triage.viewerFocus.heading}
                    selectionDetail={triage.viewerFocus.detail}
                  />
                ) : (
                  <ViewerPlaceholder message={UI_COPY.viewerNeedReport} />
                )}
              </Suspense>
            </IfcViewerErrorBoundary>
          }
          onSelectReport={requestSelectReport}
          onSeverityChange={findings.setIssueSeverityFilter}
          onHitlOnlyChange={findings.setHitlOnlyFilter}
          onSearchChange={findings.setIssueSearch}
          onGroupByChange={findings.setFindingGroupBy}
          onClauseChange={findings.setClauseFilter}
          onSelectIssue={review.selectIssue}
          onSelectClash={review.setSelectedClashIndex}
          onDraftChange={changeDraft}
          onSave={() => {
            void review.saveRemarkEdit(triage.activeIssue);
          }}
          onAccept={() => {
            void decideActiveRemark("accepted");
          }}
          onReject={() => {
            void decideActiveRemark("rejected");
          }}
          onNavigateToFindings={landing.landOnFindings}
          onOpenScreen={requestWorkspaceView}
          unsavedRemark={review.isDirty}
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

      {pendingLeave ? (
        <DirtyLeaveDialog
          busy={review.remarkSaveState === "saving"}
          saveDisabled={review.historyPending || !review.remarkDraft.trim()}
          errorMessage={
            review.remarkSaveState === "failed" ? review.conflictMessage ?? UI_COPY.remarkSaveFailed : null
          }
          onSave={() => {
            void resolveLeave("save");
          }}
          onDiscard={() => {
            void resolveLeave("discard");
          }}
          onStay={stayOnCurrent}
        />
      ) : null}

      {triageHelpOpen ? (
        <KeyboardHelpDialog
          onClose={() => setTriageHelpOpen(false)}
          shortcutsEnabled={triageShortcutsEnabled}
          onShortcutsChange={changeShortcuts}
        />
      ) : null}
    </div>
  );
}
