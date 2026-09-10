import { useCallback, useState } from "react";
import { readUrlReportId } from "../lib/report-filters";
import { persistTriageShortcuts, readTriageShortcuts } from "../lib/triage-preferences";
import { persistUiRoleAlias, readUiRoleAlias, type UiRoleAlias } from "../lib/ui-role";
import { TRIAGE_KEYBOARD_VIEWS, type WorkspaceView } from "../components/WorkspaceNav";
import { useAuthBff } from "./useAuthBff";
import { usePackDraft } from "./usePackDraft";
import { useReportFilters } from "./useReportFilters";
import { useReports } from "./useReports";
import { useRunPolling } from "./useRunPolling";
import { useSelectedReport } from "./useSelectedReport";
import { useSnapSelectionToFilter } from "./useSnapSelectionToFilter";
import { useTriageKeyboard } from "./useTriageKeyboard";
import { useFindingFilters } from "./useFindingFilters";
import { useTriageView } from "./useTriageView";
import { useWorkspaceLanding } from "./useWorkspaceLanding";

/** Review-shell orchestration; verdict and HITL persistence remain in their existing owners. */
export function useReviewShell() {
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);
  const authBff = useAuthBff(uiRole);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>(() =>
    uiRole === "user" ? "user" : "review",
  );
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [triageShortcutsEnabled, setTriageShortcutsEnabled] = useState(readTriageShortcuts);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [demoSeedInFlight, setDemoSeedInFlight] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(readUrlReportId);
  const [pendingNav, setPendingNav] = useState<
    | { kind: "report"; reportId: string; thenView?: WorkspaceView }
    | { kind: "view"; view: WorkspaceView }
    | null
  >(null);
  const findings = useFindingFilters();

  const reportFilters = useReportFilters(selectedReportId);
  const reportsState = useReports({
    projectFilter: reportFilters.projectFilter,
    disciplineFilter: reportFilters.disciplineFilter,
    statusFilter: reportFilters.statusFilter,
    search: reportFilters.search,
    epoch: reportsEpoch,
    setSelectedReportId,
    seedInFlight: demoSeedInFlight,
  });
  const review = useSelectedReport(selectedReportId, reportsEpoch);
  const {
    selectedReport, selectedIssueIndex, selectedClashIndex, selectIssue,
    pendingSelect, confirmPendingSelect, saveRemarkEdit, decideRemark, isDirty,
  } = review;
  const pack = usePackDraft();
  const landing = useWorkspaceLanding({
    workspaceView,
    hasReport: selectedReport !== null,
    setWorkspaceView,
  });
  const triage = useTriageView(selectedReport, selectedIssueIndex, selectedClashIndex, {
    severity: findings.issueSeverityFilter,
    hitlOnly: findings.hitlOnlyFilter,
    search: findings.issueSearch,
    clause: findings.clauseFilter,
  });

  const { activeIssue, filteredIssues } = triage;

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

  const beginDemoSeed = useCallback((): void => {
    setDemoSeedInFlight(true);
  }, []);

  const failDemoSeed = useCallback((): void => {
    setDemoSeedInFlight(false);
    setReportsEpoch((value) => value + 1);
  }, []);

  const handleSeededReport = useCallback((reportId: string): void => {
    setDemoSeedInFlight(false);
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


  const changeUiRole = (next: UiRoleAlias) => {
    setUiRole(next);
    persistUiRoleAlias(next);
    setWorkspaceView(next === "user" ? "user" : "review");
  };

  const retryReports = () => setReportsEpoch((value) => value + 1);

  const openProjectReport = (reportId: string) => {
    if (reportId === selectedReportId) {
      requestWorkspaceView("review");
      return;
    }
    if (review.isDirty) {
      setPendingNav({ kind: "report", reportId, thenView: "review" });
      return;
    }
    setSelectedReportId(reportId);
    setWorkspaceView("review");
  };

  const changeDraft = (value: string) => {
    review.setRemarkDraft(value);
    review.setRemarkSaveState("idle");
    review.setHitlDecisionState("idle");
  };

  const stayOnCurrent = () => {
    review.dismissPendingSelect();
    setPendingNav(null);
  };

  const changeShortcuts = (enabled: boolean) => {
    setTriageShortcutsEnabled(enabled);
    persistTriageShortcuts(enabled);
  };

  return {
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
    pendingLeave: Boolean(pendingSelect || pendingNav),
    changeUiRole,
    retryReports,
    openProjectReport,
    changeDraft,
    stayOnCurrent,
    changeShortcuts,
    runPolling,
  };
}
