import { Suspense, lazy, useCallback, useDeferredValue, useEffect, useRef, useState } from "react";
import { fetchReport, fetchReports, getApiBaseUrl, postReviewEvent } from "./lib/api";
import type { ParsedRequirement, ReportSummaryEntry, ValidationIssue, ValidationReport } from "./lib/types";
import {
  buildReportFilterShareLink,
  initialReportFilters,
  persistReportFilters,
  readUrlReportId,
  syncReportFiltersToUrl,
  type ReportFilterPreset,
} from "./lib/report-filters";
import { buildViewerFocus, type FindingGroupBy } from "./lib/issue-triage";
import {
  applyUploadedFileResult,
  describePackDraftApplyNote,
  EMPTY_PACK_DRAFT,
} from "./lib/pack-draft";
import CoverageMapPanel from "./components/CoverageMapPanel";
import PackUploadPanel from "./components/PackUploadPanel";
import AnalyzeRunPanel from "./components/AnalyzeRunPanel";
import ReviewKpiPanel from "./components/ReviewKpiPanel";
import TzWorkplaceCoveragePanel from "./components/TzWorkplaceCoveragePanel";
import BlockerHonestyPanel from "./features/honesty/BlockerHonestyPanel";
import DemoFixturePanel from "./components/DemoFixturePanel";
import VersionDiffPanel from "./components/VersionDiffPanel";
import WorkspaceNav, {
  EXPERT_SHELL_VIEWS,
  TRIAGE_KEYBOARD_VIEWS,
  type WorkspaceView,
} from "./components/WorkspaceNav";
import ReportListPanel, { type ShareLinkState } from "./features/reports/ReportListPanel";
import CapabilityTopBanner from "./features/capabilities/CapabilityTopBanner";
import ExpertWorkplace from "./features/workplace/ExpertWorkplace";
import PackCycleStrip from "./features/workplace/PackCycleStrip";
import { persistUiRoleAlias, readUiRoleAlias, type UiRoleAlias } from "./lib/ui-role";
import { useFilterPresets } from "./hooks/useFilterPresets";
import { useTriageKeyboard } from "./hooks/useTriageKeyboard";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));

function ViewerPlaceholder({ message }: { message: string }) {
  return (
    <section className="panel viewer-panel viewer-panel-placeholder">
      <div className="panel-header viewer-header">
        <div>
          <p className="panel-kicker">Spatial Review</p>
          <h2>IFC viewer</h2>
        </div>
      </div>
      <div className="viewer-stage">
        <div className="viewer-overlay">
          <p>{message}</p>
        </div>
      </div>
      <p className="viewer-caption">
        The heavy `web-ifc` viewer runtime is loaded on demand so the report shell remains lightweight until spatial review is actually needed.
      </p>
    </section>
  );
}

function reportSortWeight(report: ReportSummaryEntry): [number, string] {
  const timestamp = Number.isNaN(Date.parse(report.created_at)) ? 0 : Date.parse(report.created_at);
  return [-timestamp, report.report_id];
}

function findMatchingRequirements(report: ValidationReport, issue: ValidationIssue | null): ParsedRequirement[] {
  if (issue === null) {
    return report.requirements;
  }

  return report.requirements.filter((requirement) => requirement.rule_id === issue.rule_id);
}

export default function App() {
  const persistedFilters = initialReportFilters();
  const deepLinkReportId = readUrlReportId();
  const [reports, setReports] = useState<ReportSummaryEntry[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(deepLinkReportId);
  const [selectedReport, setSelectedReport] = useState<ValidationReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [selectedIssueIndex, setSelectedIssueIndex] = useState<number>(0);
  const [selectedClashIndex, setSelectedClashIndex] = useState<number | null>(null);
  const [issueSeverityFilter, setIssueSeverityFilter] = useState<"all" | "error" | "warning" | "info">("all");
  const [hitlOnlyFilter, setHitlOnlyFilter] = useState(false);
  const [remarkDraft, setRemarkDraft] = useState("");
  const [remarkSaveState, setRemarkSaveState] = useState<"idle" | "saving" | "saved" | "failed">("idle");
  const [hitlDecisionState, setHitlDecisionState] = useState<"idle" | "saving" | "accepted" | "rejected" | "failed">(
    "idle",
  );
  const [search, setSearch] = useState("");
  const [groupByProject, setGroupByProject] = useState(false);
  const [shareLinkState, setShareLinkState] = useState<ShareLinkState>("idle");
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
  const [projectFilter, setProjectFilter] = useState(persistedFilters.project);
  const [disciplineFilter, setDisciplineFilter] = useState(persistedFilters.discipline);
  const [statusFilter, setStatusFilter] = useState<"all" | "passed" | "failed">(persistedFilters.status);
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>(() =>
    readUiRoleAlias() === "user" ? "user" : "review",
  );
  const [packDraft, setPackDraft] = useState(EMPTY_PACK_DRAFT);
  const packDraftRef = useRef(packDraft);
  packDraftRef.current = packDraft;
  const [draftApplyNote, setDraftApplyNote] = useState<string | null>(null);
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [findingGroupBy, setFindingGroupBy] = useState<FindingGroupBy>("none");

  const deferredSearch = useDeferredValue(search);
  const deferredProjectFilter = useDeferredValue(projectFilter);
  const deferredDisciplineFilter = useDeferredValue(disciplineFilter);
  const deferredStatusFilter = useDeferredValue(statusFilter);

  useEffect(() => {
    const currentFilters = {
      project: projectFilter,
      discipline: disciplineFilter,
      status: statusFilter,
    };
    persistReportFilters(currentFilters);
    syncReportFiltersToUrl(currentFilters, selectedReportId);
    setShareLinkState("idle");
  }, [projectFilter, disciplineFilter, statusFilter, selectedReportId]);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    setReportsLoading(true);
    fetchReports(
      {
        project: deferredProjectFilter.trim() || undefined,
        discipline: deferredDisciplineFilter.trim() || undefined,
        passed:
          deferredStatusFilter === "passed"
            ? true
            : deferredStatusFilter === "failed"
              ? false
              : undefined,
      },
      { signal: controller.signal },
    )
      .then((response) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReports(response.reports);
        setReportsError(null);
        setSelectedReportId((current) => {
          const fromUrl = readUrlReportId();
          if (fromUrl) {
            if (current === fromUrl) {
              return fromUrl;
            }
            if (!current || response.reports.some((report) => report.report_id === fromUrl)) {
              return fromUrl;
            }
          }
          if (current && response.reports.some((report) => report.report_id === current)) {
            return current;
          }
          return response.reports[0]?.report_id ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportsError(error instanceof Error ? error.message : "Failed to load reports.");
      })
      .finally(() => {
        if (!cancelled && !controller.signal.aborted) {
          setReportsLoading(false);
        }
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [deferredProjectFilter, deferredDisciplineFilter, deferredStatusFilter, reportsEpoch]);

  useEffect(() => {
    if (selectedReportId === null) {
      setSelectedReport(null);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setReportLoading(true);
    fetchReport(selectedReportId, { signal: controller.signal })
      .then((report) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setSelectedReport(report);
        setReportError(null);
        setSelectedIssueIndex(0);
        setSelectedClashIndex(null);
        setRemarkDraft(report.issues[0]?.remark?.body ?? "");
        setRemarkSaveState("idle");
        setHitlDecisionState("idle");
      })
      .catch((error: unknown) => {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setReportError(error instanceof Error ? error.message : "Failed to load the report.");
        setSelectedReport(null);
      })
      .finally(() => {
        if (!cancelled && !controller.signal.aborted) {
          setReportLoading(false);
        }
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [selectedReportId]);

  const filteredReports = reports.filter((report) => {
    const normalizedQuery = deferredSearch.trim().toLowerCase();
    if (!normalizedQuery) {
      return true;
    }
    return (
      report.report_id.toLowerCase().includes(normalizedQuery) ||
      report.request_id.toLowerCase().includes(normalizedQuery)
    );
  }).sort((left, right) => {
    const [leftTs, leftId] = reportSortWeight(left);
    const [rightTs, rightId] = reportSortWeight(right);
    if (leftTs !== rightTs) {
      return leftTs - rightTs;
    }
    return leftId.localeCompare(rightId);
  });

  const groupedReports = filteredReports.reduce((groups, report) => {
    const key = report.project_name?.trim() || "Unspecified project";
    const existing = groups.get(key);
    if (existing) {
      existing.push(report);
    } else {
      groups.set(key, [report]);
    }
    return groups;
  }, new Map<string, ReportSummaryEntry[]>());

  const applyPreset = (preset: ReportFilterPreset) => {
    setProjectFilter(preset.filters.project);
    setDisciplineFilter(preset.filters.discipline);
    setStatusFilter(preset.filters.status);
  };

  const copyShareLink = async () => {
    if (typeof window === "undefined" || !window.navigator.clipboard) {
      setShareLinkState("failed");
      return;
    }

    const link = buildReportFilterShareLink({
      project: projectFilter,
      discipline: disciplineFilter,
      status: statusFilter,
    });

    try {
      await window.navigator.clipboard.writeText(link);
      setShareLinkState("copied");
    } catch {
      setShareLinkState("failed");
    }
  };

  const activeIssue =
    selectedReport && selectedReport.issues.length > 0
      ? selectedReport.issues[Math.min(selectedIssueIndex, selectedReport.issues.length - 1)]
      : null;
  const filteredIssues =
    selectedReport === null
      ? []
      : selectedReport.issues
          .map((issue, index) => ({ issue, index }))
          .filter(({ issue }) => {
            if (issueSeverityFilter !== "all" && issue.severity !== issueSeverityFilter) {
              return false;
            }
            if (hitlOnlyFilter) {
              const isHitlIssue = issue.rule_id === "AEROBIM-DRAWING-REGION-HITL";
              const hasHitlRegion =
                (selectedReport.drawing_regions ?? []).some((region) => region.hitl_required === true) &&
                isHitlIssue;
              return isHitlIssue || hasHitlRegion;
            }
            return true;
          })
          // Reviewer triage order: priority desc (stable — ties keep report order).
          .sort((a, b) => (b.issue.priority ?? 0) - (a.issue.priority ?? 0));
  const hitlRegionCount = selectedReport
    ? (selectedReport.drawing_regions ?? []).filter((region) => region.hitl_required === true).length
    : 0;
  const activeClash =
    selectedReport && selectedClashIndex !== null && selectedReport.clash_results.length > 0
      ? selectedReport.clash_results[Math.min(selectedClashIndex, selectedReport.clash_results.length - 1)]
      : null;
  const matchingRequirements = selectedReport ? findMatchingRequirements(selectedReport, activeIssue) : [];
  const viewerFocus = buildViewerFocus(activeIssue, activeClash);

  async function saveRemarkEdit(): Promise<void> {
    if (!selectedReport || !activeIssue) {
      return;
    }
    setRemarkSaveState("saving");
    try {
      await postReviewEvent(selectedReport.report_id, {
        event_type: "edited_remark",
        issue_rule_id: activeIssue.rule_id,
        finding_id: activeIssue.finding_id ?? undefined,
        note: remarkDraft,
      });
      setRemarkSaveState("saved");
    } catch {
      setRemarkSaveState("failed");
    }
  }

  const decideRemark = useCallback(
    async (eventType: "accepted" | "rejected"): Promise<void> => {
      if (!selectedReport || !activeIssue) {
        return;
      }
      setHitlDecisionState("saving");
      try {
        await postReviewEvent(selectedReport.report_id, {
          event_type: eventType,
          issue_rule_id: activeIssue.rule_id,
          finding_id: activeIssue.finding_id ?? undefined,
          note: remarkDraft,
        });
        setHitlDecisionState(eventType);
      } catch {
        setHitlDecisionState("failed");
      }
    },
    [selectedReport, activeIssue, remarkDraft],
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
    decideRemark,
  });

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

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">AeroBIM review shell · checkpoint NO_GO</p>
          <h1>Reports, issues, provenance.</h1>
          <p className="lede">
            Pack seam: model ↔ sheets ↔ TZ ↔ calculations. Not a 10D/Tangl replacement. UI does not
            write <code>summary.passed</code>. Native RVT/NWD/DWG fail-closed. Not a measured 30:00
            SLA.
          </p>
        </div>
        <div className="header-card">
          <span>API</span>
          <strong>{getApiBaseUrl() || "same-origin /v1 (Vite proxy)"}</strong>
          <span>{reports.length} report(s) loaded</span>
          <label className="role-alias">
            UI role (not OIDC)
            <select
              aria-label="UI role alias"
              value={uiRole}
              onChange={(event) => {
                const next = event.target.value === "user" ? "user" : "expert";
                setUiRole(next);
                persistUiRoleAlias(next);
                setWorkspaceView(next === "user" ? "user" : "review");
              }}
            >
              <option value="expert">Expert</option>
              <option value="user">User</option>
            </select>
          </label>
        </div>
      </header>

      {(reportsError || reportError) && (
        <section className="error-banner">
          {reportsError ?? reportError}
        </section>
      )}

      <WorkspaceNav workspaceView={workspaceView} onChange={setWorkspaceView} />
      <PackCycleStrip
        workspaceView={workspaceView}
        packDraft={packDraft}
        hasReport={selectedReportId !== null}
        onChange={setWorkspaceView}
      />
      <DemoFixturePanel onSeeded={handleSeededReport} />
      {EXPERT_SHELL_VIEWS.has(workspaceView) && selectedReport ? (
        <CapabilityTopBanner capabilities={selectedReport.capabilities} />
      ) : null}

      {workspaceView === "upload" ? (
        <div className="workspace-alt">
          <PackUploadPanel
            draftApplyNote={draftApplyNote}
            onUploadedPath={(path, filename) => {
              const { draft, note } = applyUploadedFileResult(packDraftRef.current, path, filename);
              packDraftRef.current = draft;
              setPackDraft(draft);
              if (note.kind === "replaced" || note.kind === "not_in_draft") {
                setDraftApplyNote(describePackDraftApplyNote(note));
              } else {
                setDraftApplyNote(null);
              }
              if (note.kind === "filled" && note.slot === "ifc") {
                setWorkspaceView("run");
              }
            }}
            onContinueToRun={() => setWorkspaceView("run")}
          />
        </div>
      ) : null}

      {workspaceView === "run" ? (
        <div className="workspace-alt">
          <AnalyzeRunPanel
            ifcPath={packDraft.ifcPath}
            packDraft={packDraft}
            onReportReady={handleSeededReport}
            onNeedUpload={() => setWorkspaceView("upload")}
            capabilities={selectedReport?.capabilities ?? null}
          />
        </div>
      ) : null}

      {workspaceView === "diff" ? <VersionDiffPanel reports={filteredReports} /> : null}

      {workspaceView === "user" ? (
        <div className="workspace-alt">
          <TzWorkplaceCoveragePanel onOpenScreen={setWorkspaceView} />
          <BlockerHonestyPanel />
          <ReviewKpiPanel reportId={selectedReportId} />
          {selectedReport ? (
            <CoverageMapPanel
              reportId={selectedReport.report_id}
              onNavigateToFindings={() => {
                setWorkspaceView("review");
                document.querySelector(".issue-list")?.scrollIntoView({ behavior: "smooth" });
              }}
            />
          ) : (
            <p className="panel-empty">Select a report on Projects or Expert.</p>
          )}
        </div>
      ) : null}

      {workspaceView === "projects" ? (
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
            onSelectReport={(reportId) => {
              setSelectedReportId(reportId);
              setWorkspaceView("review");
            }}
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
          findingGroupBy={findingGroupBy}
          activeIssue={activeIssue}
          matchingRequirements={matchingRequirements}
          selectedClashIndex={selectedClashIndex}
          remarkDraft={remarkDraft}
          remarkSaveState={remarkSaveState}
          hitlDecisionState={hitlDecisionState}
          hitlEnabled={uiRole === "expert"}
          spatialViewer={
            <Suspense fallback={<ViewerPlaceholder message="Loading the spatial review runtime…" />}>
              {selectedReport ? (
                <IfcViewerPanel
                  report={selectedReport}
                  selectedGuids={viewerFocus.guids}
                  selectionMode={viewerFocus.mode}
                  selectionHeading={viewerFocus.heading}
                  selectionDetail={viewerFocus.detail}
                />
              ) : (
                <ViewerPlaceholder message="Select a persisted report to load its IFC source into the browser viewer." />
              )}
            </Suspense>
          }
          onSelectReport={setSelectedReportId}
          onSeverityChange={setIssueSeverityFilter}
          onHitlOnlyChange={setHitlOnlyFilter}
          onGroupByChange={setFindingGroupBy}
          onSelectIssue={(index, issue) => {
            setSelectedIssueIndex(index);
            setSelectedClashIndex(null);
            setRemarkDraft(issue.remark?.body ?? "");
            setRemarkSaveState("idle");
            setHitlDecisionState("idle");
          }}
          onSelectClash={setSelectedClashIndex}
          onDraftChange={(value) => {
            setRemarkDraft(value);
            setRemarkSaveState("idle");
            setHitlDecisionState("idle");
          }}
          onSave={() => {
            void saveRemarkEdit();
          }}
          onAccept={() => {
            void decideRemark("accepted");
          }}
          onReject={() => {
            void decideRemark("rejected");
          }}
          onNavigateToFindings={() => {
            setWorkspaceView("review");
            document.querySelector(".issue-list")?.scrollIntoView({ behavior: "smooth" });
          }}
        />
      ) : null}

      {triageHelpOpen ? (
        <aside className="triage-help" role="dialog" aria-label="Triage keyboard help">
          <p>
            J/K or arrows — next/previous finding. A — confirm. R — reject. E — focus remark. ? —
            this help. Esc — close. Mouse-only triage fails the cognitive-load criterion.
          </p>
        </aside>
      ) : null}
    </div>
  );
}