import { Suspense, lazy, startTransition, useDeferredValue, useEffect, useState } from "react";
import { downloadExport, fetchReport, fetchReports, getApiBaseUrl, postReviewEvent } from "./lib/api";
import type { ParsedRequirement, ReportSummaryEntry, ValidationIssue, ValidationReport } from "./lib/types";
import {
  buildReportFilterShareLink,
  initialReportFilters,
  normalizePresetScope,
  normalizeStatus,
  persistFilterPresets,
  persistReportFilters,
  readPersistedFilterPresets,
  readUrlReportId,
  syncReportFiltersToUrl,
  type PersistedReportFilters,
  type PresetScope,
  type ReportFilterPreset,
} from "./lib/report-filters";
import { buildViewerFocus, type FindingGroupBy } from "./lib/issue-triage";
import DrawingEvidencePanel from "./components/DrawingEvidencePanel";
import CapabilityHonestyPanel from "./components/CapabilityHonestyPanel";
import CoverageMapPanel from "./components/CoverageMapPanel";
import ProvenancePanel from "./components/ProvenancePanel";
import PackUploadPanel from "./components/PackUploadPanel";
import AnalyzeRunPanel from "./components/AnalyzeRunPanel";
import ReviewKpiPanel from "./components/ReviewKpiPanel";
import TzWorkplaceCoveragePanel from "./components/TzWorkplaceCoveragePanel";
import DemoFixturePanel from "./components/DemoFixturePanel";
import VersionDiffPanel from "./components/VersionDiffPanel";
import WorkspaceNav, {
  EXPERT_SHELL_VIEWS,
  TRIAGE_KEYBOARD_VIEWS,
  type WorkspaceView,
} from "./components/WorkspaceNav";
import VerticalSliceKt2, {
  formatPackageOutcome,
  outcomeClass,
} from "./components/VerticalSliceKt2";
import ReportListPanel, {
  type PresetTransferState,
  type ShareLinkState,
} from "./features/reports/ReportListPanel";
import FindingListPanel from "./features/findings/FindingListPanel";
import RemarkCardPanel from "./features/findings/RemarkCardPanel";
import CapabilityTopBanner from "./features/capabilities/CapabilityTopBanner";
import { persistUiRoleAlias, readUiRoleAlias, type UiRoleAlias } from "./lib/ui-role";
import ResizableWorkplace from "./features/workplace/ResizableWorkplace";

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

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
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
  const [presetTransferState, setPresetTransferState] = useState<PresetTransferState>("idle");
  const [presetTransferDraft, setPresetTransferDraft] = useState("");
  const [presetNameDraft, setPresetNameDraft] = useState("");
  const [presetScopeDraft, setPresetScopeDraft] = useState<PresetScope>("local");
  const [filterPresets, setFilterPresets] = useState<ReportFilterPreset[]>(readPersistedFilterPresets());
  const [projectFilter, setProjectFilter] = useState(persistedFilters.project);
  const [disciplineFilter, setDisciplineFilter] = useState(persistedFilters.discipline);
  const [statusFilter, setStatusFilter] = useState<"all" | "passed" | "failed">(persistedFilters.status);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>("review");
  const [uploadedIfcPath, setUploadedIfcPath] = useState<string | null>(null);
  const [triageHelpOpen, setTriageHelpOpen] = useState(false);
  const [reportsEpoch, setReportsEpoch] = useState(0);
  const [findingGroupBy, setFindingGroupBy] = useState<FindingGroupBy>("none");
  const [uiRole, setUiRole] = useState<UiRoleAlias>(readUiRoleAlias);

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
    persistFilterPresets(filterPresets);
  }, [filterPresets]);

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

  const saveCurrentPreset = () => {
    const name = presetNameDraft.trim();
    if (!name) {
      return;
    }

    const currentFilters: PersistedReportFilters = {
      project: projectFilter,
      discipline: disciplineFilter,
      status: statusFilter,
    };

    setFilterPresets((current) => {
      const existingIndex = current.findIndex((preset) => preset.name.toLowerCase() === name.toLowerCase());
      if (existingIndex >= 0) {
        const updated = [...current];
        updated[existingIndex] = {
          ...updated[existingIndex],
          name,
          scope: presetScopeDraft,
          filters: currentFilters,
        };
        return updated;
      }

      return [
        ...current,
        {
          id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          name,
          scope: presetScopeDraft,
          filters: currentFilters,
        },
      ];
    });
    setPresetNameDraft("");
  };

  const applyPreset = (preset: ReportFilterPreset) => {
    setProjectFilter(preset.filters.project);
    setDisciplineFilter(preset.filters.discipline);
    setStatusFilter(preset.filters.status);
  };

  const removePreset = (presetId: string) => {
    setFilterPresets((current) => current.filter((preset) => preset.id !== presetId));
  };

  const mergePresetPayload = (rawPayload: string): boolean => {
    const raw = rawPayload.trim();
    if (!raw) {
      return false;
    }

    try {
      const parsed = JSON.parse(raw) as Array<{
        name?: unknown;
        scope?: unknown;
        filters?: Partial<PersistedReportFilters>;
      }>;

      if (!Array.isArray(parsed)) {
        throw new Error("Preset payload must be an array");
      }

      const normalized = parsed
        .filter((entry) => typeof entry.name === "string" && entry.filters)
        .map((entry) => {
          const filters = entry.filters as Partial<PersistedReportFilters>;
          return {
            name: (entry.name as string).trim(),
            scope: normalizePresetScope(entry.scope, "team"),
            filters: {
              project: typeof filters.project === "string" ? filters.project : "",
              discipline: typeof filters.discipline === "string" ? filters.discipline : "",
              status: normalizeStatus(filters.status),
            },
          };
        })
        .filter((entry) => entry.name.length > 0);

      if (normalized.length === 0) {
        throw new Error("Preset payload has no valid entries");
      }

      setFilterPresets((current) => {
        const merged = [...current];

        normalized.forEach((incoming) => {
          const existingIndex = merged.findIndex((preset) => preset.name.toLowerCase() === incoming.name.toLowerCase());
          if (existingIndex >= 0) {
            merged[existingIndex] = {
              ...merged[existingIndex],
              name: incoming.name,
              scope: incoming.scope,
              filters: incoming.filters,
            };
            return;
          }

          merged.push({
            id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            name: incoming.name,
            scope: incoming.scope,
            filters: incoming.filters,
          });
        });

        return merged;
      });

      return true;
    } catch {
      return false;
    }
  };

  const copyPresetPayload = async () => {
    if (typeof window === "undefined" || !window.navigator.clipboard) {
      setPresetTransferState("failed");
      return;
    }

    const payload = filterPresets.map((preset) => ({
      name: preset.name,
      scope: preset.scope,
      filters: preset.filters,
    }));

    try {
      await window.navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setPresetTransferState("exported");
    } catch {
      setPresetTransferState("failed");
    }
  };

  const downloadPresetPayload = () => {
    if (typeof window === "undefined" || filterPresets.length === 0) {
      setPresetTransferState("failed");
      return;
    }

    try {
      const payload = filterPresets.map((preset) => ({
        name: preset.name,
        scope: preset.scope,
        filters: preset.filters,
      }));
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json",
      });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = "aerobim-report-filter-presets.json";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(objectUrl);
      setPresetTransferState("downloaded");
    } catch {
      setPresetTransferState("failed");
    }
  };

  const importPresetPayload = () => {
    if (!presetTransferDraft.trim()) {
      return;
    }

    const imported = mergePresetPayload(presetTransferDraft);
    if (imported) {
      setPresetTransferDraft("");
      setPresetTransferState("imported");
      return;
    }

    setPresetTransferState("failed");
  };

  const importPresetFile = async (event: { target: HTMLInputElement }) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const raw = await file.text();
      setPresetTransferDraft(raw);
      const imported = mergePresetPayload(raw);
      if (imported) {
        setPresetTransferState("imported");
      } else {
        setPresetTransferState("failed");
      }
    } catch {
      setPresetTransferState("failed");
    } finally {
      event.target.value = "";
    }
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

  async function decideRemark(eventType: "accepted" | "rejected"): Promise<void> {
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
  }

  useEffect(() => {
    if (!TRIAGE_KEYBOARD_VIEWS.has(workspaceView)) {
      return;
    }

    function onKeyDown(event: KeyboardEvent): void {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target?.isContentEditable) {
        if (event.key === "Escape") {
          setTriageHelpOpen(false);
        }
        return;
      }
      if (event.key === "?" || (event.shiftKey && event.key === "/")) {
        event.preventDefault();
        setTriageHelpOpen((open) => !open);
        return;
      }
      if (event.key === "Escape") {
        setTriageHelpOpen(false);
        return;
      }
      if (filteredIssues.length === 0) {
        return;
      }
      const currentPos = filteredIssues.findIndex(({ index }) => index === selectedIssueIndex);
      const pos = currentPos >= 0 ? currentPos : 0;
      if (event.key === "j" || event.key === "J" || event.key === "ArrowDown") {
        event.preventDefault();
        const next = filteredIssues[Math.min(pos + 1, filteredIssues.length - 1)];
        if (next) {
          setSelectedIssueIndex(next.index);
          setSelectedClashIndex(null);
          setRemarkDraft(next.issue.remark?.body ?? "");
        }
        return;
      }
      if (event.key === "k" || event.key === "K" || event.key === "ArrowUp") {
        event.preventDefault();
        const prev = filteredIssues[Math.max(pos - 1, 0)];
        if (prev) {
          setSelectedIssueIndex(prev.index);
          setSelectedClashIndex(null);
          setRemarkDraft(prev.issue.remark?.body ?? "");
        }
        return;
      }
      if (event.key === "a" || event.key === "A") {
        if (uiRole !== "expert") {
          return;
        }
        event.preventDefault();
        void decideRemark("accepted");
        return;
      }
      if (event.key === "r" || event.key === "R") {
        if (uiRole !== "expert") {
          return;
        }
        event.preventDefault();
        void decideRemark("rejected");
        return;
      }
      if (event.key === "e" || event.key === "E") {
        event.preventDefault();
        document.getElementById("remark-editor")?.focus();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [workspaceView, filteredIssues, selectedIssueIndex, remarkDraft, uiRole]);

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
            Шов комплекта: модель ↔ чертежи ↔ ТЗ ↔ расчёты. Не замена 10D/Tangl. UI не пишет{" "}
            <code>summary.passed</code>. Native RVT/NWD/DWG fail-closed. Не SLA 30 минут.
          </p>
        </div>
        <div className="header-card">
          <span>API</span>
          <strong>{getApiBaseUrl() || "same-origin /v1 (Vite proxy)"}</strong>
          <span>{reports.length} report(s) loaded</span>
          <label className="role-alias">
            Роль UI (не OIDC)
            <select
              aria-label="UI role alias"
              value={uiRole}
              onChange={(event) => {
                const next = event.target.value === "user" ? "user" : "expert";
                setUiRole(next);
                persistUiRoleAlias(next);
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
      <DemoFixturePanel onSeeded={handleSeededReport} />
      {EXPERT_SHELL_VIEWS.has(workspaceView) && selectedReport ? (
        <CapabilityTopBanner capabilities={selectedReport.capabilities} />
      ) : null}

      {workspaceView === "upload" ? (
        <div className="workspace-alt">
          <PackUploadPanel
            onUploadedPath={(path, filename) => {
              if (filename.toLowerCase().endsWith(".ifc") || filename.toLowerCase().endsWith(".ifczip")) {
                setUploadedIfcPath(path);
              }
            }}
          />
        </div>
      ) : null}

      {workspaceView === "run" ? (
        <div className="workspace-alt">
          <AnalyzeRunPanel
            ifcPath={uploadedIfcPath}
            onReportReady={handleSeededReport}
            capabilities={selectedReport?.capabilities ?? null}
          />
        </div>
      ) : null}

      {workspaceView === "diff" ? <VersionDiffPanel reports={filteredReports} /> : null}

      {workspaceView === "user" ? (
        <div className="workspace-alt">
          <ReviewKpiPanel reportId={selectedReportId} />
          <TzWorkplaceCoveragePanel />
          {selectedReport ? (
            <CoverageMapPanel
              reportId={selectedReport.report_id}
              onNavigateToFindings={() => {
                setWorkspaceView("review");
                document.querySelector(".issue-list")?.scrollIntoView({ behavior: "smooth" });
              }}
            />
          ) : (
            <p className="panel-empty">Выберите отчёт на экране «Проекты» или «Эксперт».</p>
          )}
        </div>
      ) : null}

      {EXPERT_SHELL_VIEWS.has(workspaceView) ? (
        workspaceView === "projects" ? (
        <main className="workspace-alt">
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
          onSelectReport={setSelectedReportId}
          onCopyShareLink={() => {
            void copyShareLink();
          }}
          onPresetNameChange={setPresetNameDraft}
          onPresetScopeChange={setPresetScopeDraft}
          onSavePreset={saveCurrentPreset}
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
        ) : (
        <ResizableWorkplace
          left={
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
          onSelectReport={setSelectedReportId}
          onCopyShareLink={() => {
            void copyShareLink();
          }}
          onPresetNameChange={setPresetNameDraft}
          onPresetScopeChange={setPresetScopeDraft}
          onSavePreset={saveCurrentPreset}
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
          }
          center={
        <section className="panel issue-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Inspection</p>
              <h2>Issue detail</h2>
            </div>
            {selectedReport && (
              <div className="export-actions" id="export-actions">
                <button type="button" onClick={() => void downloadExport(selectedReport.report_id, "html")}>HTML</button>
                <button type="button" onClick={() => void downloadExport(selectedReport.report_id, "json")}>JSON</button>
                <button type="button" onClick={() => void downloadExport(selectedReport.report_id, "bcf")}>BCF</button>
                <button
                  type="button"
                  onClick={() => void downloadExport(selectedReport.report_id, "bcf", { bcfVersion: "3.0" })}
                >
                  BCF 3.0
                </button>
                <button type="button" onClick={() => void downloadExport(selectedReport.report_id, "pdf")}>PDF</button>
                <button type="button" disabled aria-label="XLSX not on MVP">
                  XLSX
                </button>
              </div>
            )}
          </div>

          {reportLoading ? (
            <div className="panel-empty">Loading report detail…</div>
          ) : selectedReport === null ? (
            <div className="panel-empty">Choose a report to inspect its issues and provenance.</div>
          ) : (
            <>
              <div className="summary-grid">
                <article className="summary-tile">
                  <span>Status</span>
                  <strong
                    className={`outcome-badge ${outcomeClass(
                      selectedReport.summary.outcome,
                      selectedReport.summary.passed,
                    )}`}
                  >
                    {formatPackageOutcome(
                      selectedReport.summary.outcome,
                      selectedReport.summary.passed,
                    )}
                  </strong>
                </article>
                <article className="summary-tile">
                  <span>Requirements</span>
                  <strong>{selectedReport.summary.requirement_count}</strong>
                </article>
                <article className="summary-tile">
                  <span>Issues</span>
                  <strong>{selectedReport.summary.issue_count}</strong>
                </article>
                <article className="summary-tile">
                  <span>Drawing annotations</span>
                  <strong>{selectedReport.summary.drawing_annotation_count}</strong>
                </article>
              </div>

              <VerticalSliceKt2 report={selectedReport} issue={activeIssue} />

              <div className="report-context">
                <span>IFC: available via report source download</span>
                <span>Created: {formatTimestamp(selectedReport.created_at)}</span>
                <span>Request: {selectedReport.request_id}</span>
                {selectedReport.stage && <span>Stage: {selectedReport.stage}</span>}
                {selectedReport.revision && <span>Revision: {selectedReport.revision}</span>}
                {selectedReport.doc_status && <span>Status: {selectedReport.doc_status}</span>}
                {selectedReport.information_container_id && (
                  <span>CDE: {selectedReport.information_container_id}</span>
                )}
              </div>

              <CapabilityHonestyPanel
                capabilities={selectedReport.capabilities}
                divergences={selectedReport.divergences}
              />

              <CoverageMapPanel
                reportId={selectedReport.report_id}
                onNavigateToFindings={() => {
                  document.querySelector(".issue-list")?.scrollIntoView({ behavior: "smooth" });
                }}
              />

              <FindingListPanel
                issues={filteredIssues}
                totalIssueCount={selectedReport.issues.length}
                selectedIssueIndex={selectedIssueIndex}
                issueSeverityFilter={issueSeverityFilter}
                hitlOnlyFilter={hitlOnlyFilter}
                hitlRegionCount={hitlRegionCount}
                groupBy={findingGroupBy}
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
              />
            </>
          )}
        </section>
          }
          right={
        <div className="side-stack">
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

          <DrawingEvidencePanel report={selectedReport} activeIssue={activeIssue} />

          <section className="panel provenance-panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Evidence</p>
                <h2>Provenance</h2>
              </div>
            </div>

            {selectedReport === null ? (
              <div className="panel-empty">Select a report first.</div>
            ) : (
              <div className="provenance-stack">
                <RemarkCardPanel
                  reportId={selectedReport.report_id}
                  activeIssue={activeIssue}
                  remarkDraft={remarkDraft}
                  remarkSaveState={remarkSaveState}
                  hitlDecisionState={hitlDecisionState}
                  hitlEnabled={uiRole === "expert"}
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
                />
                <ProvenancePanel activeIssue={activeIssue} />

                <article className="detail-block">
                  <h3>Matching requirements</h3>
                  {matchingRequirements.length === 0 ? (
                    <p className="compact-copy">No exact requirement match by rule id. The report may be driven by synthesized or aggregate logic.</p>
                  ) : (
                    <div className="collection-stack">
                      {matchingRequirements.map((requirement) => (
                        <div key={`${requirement.rule_id}-${requirement.source_kind}`} className="collection-card">
                          <strong>{requirement.rule_id}</strong>
                          <span>{requirement.source_kind}</span>
                          <p>{requirement.property_set ?? requirement.ifc_entity ?? "Requirement without entity scope"}</p>
                          <div className="collection-meta">
                            <span>{requirement.property_name ?? "no property"}</span>
                            <span>{requirement.expected_value ?? "no expected value"}</span>
                            <span>{requirement.unit ?? "no unit"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>

                <article className="detail-block">
                  <h3>Drawing annotations</h3>
                  {selectedReport.drawing_annotations.length === 0 ? (
                    <p className="compact-copy">No drawing annotations were materialized for this report.</p>
                  ) : (
                    <div className="collection-stack">
                      {selectedReport.drawing_annotations.map((annotation) => (
                        <div key={annotation.annotation_id} className="collection-card">
                          <strong>{annotation.annotation_id}</strong>
                          <span>{annotation.source}</span>
                          <p>{annotation.target_ref} · {annotation.measure_name} = {annotation.observed_value} {annotation.unit ?? ""}</p>
                          <div className="collection-meta">
                            <span>{annotation.sheet_id}</span>
                            <span>{annotation.problem_zone?.page_number ? `page ${annotation.problem_zone.page_number}` : "no page"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>

                <article className="detail-block">
                  <h3>Clashes</h3>
                  {selectedReport.clash_results.length === 0 ? (
                    <p className="compact-copy">No clash payloads were attached to this report.</p>
                  ) : (
                    <div className="collection-stack">
                      {selectedReport.clash_results.map((clash, index) => (
                        <button
                          key={`${clash.element_a_guid}-${clash.element_b_guid}-${index}`}
                          type="button"
                          className={`collection-card collection-card-button ${index === selectedClashIndex ? "active" : ""}`}
                          onClick={() => {
                            startTransition(() => {
                              setSelectedClashIndex((current) => (current === index ? null : index));
                            });
                          }}
                        >
                          <div className="collection-card-row">
                            <strong>{clash.clash_type}</strong>
                            <span className="selection-badge">{index === selectedClashIndex ? "viewer focus" : "focus clash"}</span>
                          </div>
                          <p>{clash.description}</p>
                          <div className="collection-meta">
                            <span>{clash.element_a_guid}</span>
                            <span>{clash.element_b_guid}</span>
                            <span>{clash.distance.toFixed(3)} m</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </article>
              </div>
            )}
          </section>
        </div>
          }
        />
        )
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