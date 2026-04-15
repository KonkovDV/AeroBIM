import { Suspense, lazy, startTransition, useDeferredValue, useEffect, useState } from "react";
import { buildExportUrl, fetchReport, fetchReports, getApiBaseUrl } from "./lib/api";
import type { ClashResult, ParsedRequirement, ReportSummaryEntry, ValidationIssue, ValidationReport } from "./lib/types";
import DrawingEvidencePanel from "./components/DrawingEvidencePanel";

const IfcViewerPanel = lazy(() => import("./components/IfcViewerPanel"));
const REPORT_FILTERS_STORAGE_KEY = "aerobim-report-filters-v1";
const REPORT_FILTER_PRESETS_STORAGE_KEY = "aerobim-report-filter-presets-v1";

type PersistedReportFilters = {
  project: string;
  discipline: string;
  status: "all" | "passed" | "failed";
};

type ShareLinkState = "idle" | "copied" | "failed";
type PresetTransferState = "idle" | "exported" | "downloaded" | "imported" | "failed";

type ReportFilterPreset = {
  id: string;
  name: string;
  filters: PersistedReportFilters;
};

function normalizeStatus(value: string | null | undefined): "all" | "passed" | "failed" {
  return value === "passed" || value === "failed" ? value : "all";
}

function readUrlReportFilters(): Partial<PersistedReportFilters> {
  if (typeof window === "undefined") {
    return {};
  }

  const params = new URLSearchParams(window.location.search);
  const project = params.get("project")?.trim();
  const discipline = params.get("discipline")?.trim();
  const status = params.get("status");

  return {
    project: project && project.length > 0 ? project : undefined,
    discipline: discipline && discipline.length > 0 ? discipline : undefined,
    status: status ? normalizeStatus(status) : undefined,
  };
}

function readPersistedReportFilters(): PersistedReportFilters {
  if (typeof window === "undefined") {
    return { project: "", discipline: "", status: "all" };
  }

  try {
    const raw = window.localStorage.getItem(REPORT_FILTERS_STORAGE_KEY);
    if (!raw) {
      return { project: "", discipline: "", status: "all" };
    }
    const parsed = JSON.parse(raw) as Partial<PersistedReportFilters>;
    return {
      project: typeof parsed.project === "string" ? parsed.project : "",
      discipline: typeof parsed.discipline === "string" ? parsed.discipline : "",
      status: normalizeStatus(parsed.status),
    };
  } catch {
    return { project: "", discipline: "", status: "all" };
  }
}

function initialReportFilters(): PersistedReportFilters {
  const persisted = readPersistedReportFilters();
  const fromUrl = readUrlReportFilters();

  return {
    project: fromUrl.project ?? persisted.project,
    discipline: fromUrl.discipline ?? persisted.discipline,
    status: fromUrl.status ?? persisted.status,
  };
}

function persistReportFilters(filters: PersistedReportFilters): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(REPORT_FILTERS_STORAGE_KEY, JSON.stringify(filters));
}

function readPersistedFilterPresets(): ReportFilterPreset[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(REPORT_FILTER_PRESETS_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as Array<Partial<ReportFilterPreset>>;
    return parsed
      .filter((preset) => typeof preset.name === "string" && typeof preset.id === "string" && preset.filters)
      .map((preset) => {
        const filters = preset.filters as Partial<PersistedReportFilters>;
        return {
          id: preset.id as string,
          name: preset.name as string,
          filters: {
            project: typeof filters.project === "string" ? filters.project : "",
            discipline: typeof filters.discipline === "string" ? filters.discipline : "",
            status: normalizeStatus(filters.status),
          },
        };
      });
  } catch {
    return [];
  }
}

function persistFilterPresets(presets: ReportFilterPreset[]): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(REPORT_FILTER_PRESETS_STORAGE_KEY, JSON.stringify(presets));
}

function withReportFilters(url: URL, filters: PersistedReportFilters): URL {
  if (filters.project.trim()) {
    url.searchParams.set("project", filters.project.trim());
  } else {
    url.searchParams.delete("project");
  }

  if (filters.discipline.trim()) {
    url.searchParams.set("discipline", filters.discipline.trim());
  } else {
    url.searchParams.delete("discipline");
  }

  if (filters.status !== "all") {
    url.searchParams.set("status", filters.status);
  } else {
    url.searchParams.delete("status");
  }

  return url;
}

function syncReportFiltersToUrl(filters: PersistedReportFilters): void {
  if (typeof window === "undefined") {
    return;
  }

  const url = withReportFilters(new URL(window.location.href), filters);

  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

function buildReportFilterShareLink(filters: PersistedReportFilters): string {
  if (typeof window === "undefined") {
    return "";
  }

  return withReportFilters(new URL(window.location.href), filters).toString();
}

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

function findMatchingRequirements(report: ValidationReport, issue: ValidationIssue | null): ParsedRequirement[] {
  if (issue === null) {
    return report.requirements;
  }

  return report.requirements.filter((requirement) => requirement.rule_id === issue.rule_id);
}

type ViewerFocus = {
  mode: "none" | "issue" | "clash";
  guids: string[];
  heading: string;
  detail: string;
};

function buildViewerFocus(activeIssue: ValidationIssue | null, activeClash: ClashResult | null): ViewerFocus {
  if (activeClash !== null) {
    const guids = [...new Set([activeClash.element_a_guid, activeClash.element_b_guid].filter((guid) => guid.length > 0))];
    return {
      mode: "clash",
      guids,
      heading: `${activeClash.clash_type} clash pair`,
      detail: `${guids.length} selected IFC elements from the active clash review pair.`,
    };
  }

  if (activeIssue?.element_guid) {
    return {
      mode: "issue",
      guids: [activeIssue.element_guid],
      heading: activeIssue.rule_id,
      detail: `Single-element focus from the active issue GUID ${activeIssue.element_guid}.`,
    };
  }

  return {
    mode: "none",
    guids: [],
    heading: "No spatial selection",
    detail: "Select an issue with IFC GUID evidence or a clash pair to drive the viewer selection.",
  };
}

export default function App() {
  const persistedFilters = initialReportFilters();
  const [reports, setReports] = useState<ReportSummaryEntry[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<ValidationReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [selectedIssueIndex, setSelectedIssueIndex] = useState<number>(0);
  const [selectedClashIndex, setSelectedClashIndex] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [groupByProject, setGroupByProject] = useState(false);
  const [shareLinkState, setShareLinkState] = useState<ShareLinkState>("idle");
  const [presetTransferState, setPresetTransferState] = useState<PresetTransferState>("idle");
  const [presetTransferDraft, setPresetTransferDraft] = useState("");
  const [presetNameDraft, setPresetNameDraft] = useState("");
  const [filterPresets, setFilterPresets] = useState<ReportFilterPreset[]>(readPersistedFilterPresets());
  const [projectFilter, setProjectFilter] = useState(persistedFilters.project);
  const [disciplineFilter, setDisciplineFilter] = useState(persistedFilters.discipline);
  const [statusFilter, setStatusFilter] = useState<"all" | "passed" | "failed">(persistedFilters.status);

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
    syncReportFiltersToUrl(currentFilters);
    setShareLinkState("idle");
  }, [projectFilter, disciplineFilter, statusFilter]);

  useEffect(() => {
    persistFilterPresets(filterPresets);
  }, [filterPresets]);

  useEffect(() => {
    let cancelled = false;
    setReportsLoading(true);
    fetchReports({
      project: deferredProjectFilter.trim() || undefined,
      discipline: deferredDisciplineFilter.trim() || undefined,
      passed:
        deferredStatusFilter === "passed"
          ? true
          : deferredStatusFilter === "failed"
            ? false
            : undefined,
    })
      .then((response) => {
        if (cancelled) {
          return;
        }
        setReports(response.reports);
        setReportsError(null);
        setSelectedReportId((current) => {
          if (current && response.reports.some((report) => report.report_id === current)) {
            return current;
          }
          return response.reports[0]?.report_id ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setReportsError(error instanceof Error ? error.message : "Failed to load reports.");
      })
      .finally(() => {
        if (!cancelled) {
          setReportsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [deferredProjectFilter, deferredDisciplineFilter, deferredStatusFilter]);

  useEffect(() => {
    if (selectedReportId === null) {
      setSelectedReport(null);
      return;
    }

    let cancelled = false;
    setReportLoading(true);
    fetchReport(selectedReportId)
      .then((report) => {
        if (cancelled) {
          return;
        }
        setSelectedReport(report);
        setReportError(null);
        setSelectedIssueIndex(0);
        setSelectedClashIndex(null);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setReportError(error instanceof Error ? error.message : "Failed to load the report.");
        setSelectedReport(null);
      })
      .finally(() => {
        if (!cancelled) {
          setReportLoading(false);
        }
      });

    return () => {
      cancelled = true;
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

  const renderReportCard = (report: ReportSummaryEntry) => {
    const isActive = report.report_id === selectedReportId;
    return (
      <button
        key={report.report_id}
        type="button"
        className={`report-card ${isActive ? "active" : ""}`}
        onClick={() => {
          startTransition(() => {
            setSelectedReportId(report.report_id);
          });
        }}
      >
        <div className="report-card-row">
          <strong>{report.report_id.slice(0, 8)}</strong>
          <span className={`status-pill ${report.passed ? "pass" : "fail"}`}>
            {report.passed ? "Pass" : "Fail"}
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
  };

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
          filters: currentFilters,
        };
        return updated;
      }

      return [
        ...current,
        {
          id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          name,
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
              filters: incoming.filters,
            };
            return;
          }

          merged.push({
            id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            name: incoming.name,
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
  const activeClash =
    selectedReport && selectedClashIndex !== null && selectedReport.clash_results.length > 0
      ? selectedReport.clash_results[Math.min(selectedClashIndex, selectedReport.clash_results.length - 1)]
      : null;
  const matchingRequirements = selectedReport ? findMatchingRequirements(selectedReport, activeIssue) : [];
  const viewerFocus = buildViewerFocus(activeIssue, activeClash);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">AeroBIM review shell</p>
          <h1>Reports, issues, provenance.</h1>
          <p className="lede">
            Minimal browser triage surface for persisted validation reports. The validation truth remains in the backend; the shell exists to inspect, filter, and export it.
          </p>
        </div>
        <div className="header-card">
          <span>API</span>
          <strong>{getApiBaseUrl()}</strong>
          <span>{reports.length} report(s) loaded</span>
        </div>
      </header>

      {(reportsError || reportError) && (
        <section className="error-banner">
          {reportsError ?? reportError}
        </section>
      )}

      <main className="workspace-grid">
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
                onChange={(event) => setProjectFilter(event.target.value)}
                placeholder="Filter by project"
              />
              <input
                className="search-input filter-input"
                type="search"
                aria-label="Discipline filter"
                value={disciplineFilter}
                onChange={(event) => setDisciplineFilter(event.target.value)}
                placeholder="Filter by discipline"
              />
              <select
                className="search-input filter-select"
                aria-label="Status filter"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as "all" | "passed" | "failed")}
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
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search loaded reports"
            />
            <button
              type="button"
              className={`toolbar-button report-group-toggle ${groupByProject ? "active" : ""}`}
              onClick={() => setGroupByProject((current) => !current)}
            >
              {groupByProject ? "Ungroup reports" : "Group by project"}
            </button>
            <button
              type="button"
              className="toolbar-button"
              aria-label="Copy share link"
              onClick={() => {
                void copyShareLink();
              }}
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
              onChange={(event) => setPresetNameDraft(event.target.value)}
              placeholder="Preset name"
            />
            <button
              type="button"
              className="toolbar-button"
              onClick={saveCurrentPreset}
              disabled={!presetNameDraft.trim()}
            >
              Save preset
            </button>
            <button
              type="button"
              className="toolbar-button"
              aria-label="Copy presets JSON"
              onClick={() => {
                void copyPresetPayload();
              }}
              disabled={filterPresets.length === 0}
            >
              Copy presets JSON
            </button>
            <button
              type="button"
              className="toolbar-button"
              aria-label="Download presets JSON"
              onClick={downloadPresetPayload}
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
                  void importPresetFile(event);
                }}
              />
            </label>
            <textarea
              className="preset-import-input"
              aria-label="Preset import payload"
              value={presetTransferDraft}
              onChange={(event) => {
                setPresetTransferDraft(event.target.value);
                setPresetTransferState("idle");
              }}
              placeholder='Paste preset JSON (e.g. [{"name":"Hospital","filters":{...}}])'
            />
            <button
              type="button"
              className="toolbar-button"
              aria-label="Import presets JSON"
              onClick={importPresetPayload}
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
                  onClick={() => applyPreset(preset)}
                >
                  {preset.name}
                </button>
                <button
                  type="button"
                  className="toolbar-button preset-remove"
                  aria-label={`Remove preset ${preset.name}`}
                  onClick={() => removePreset(preset.id)}
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
                  <div className="report-list">
                    {projectReports.map((report) => renderReportCard(report))}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <div className="report-list">
              {filteredReports.map((report) => renderReportCard(report))}
            </div>
          )}
        </section>

        <section className="panel issue-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Inspection</p>
              <h2>Issue detail</h2>
            </div>
            {selectedReport && (
              <div className="export-actions">
                <a href={buildExportUrl(selectedReport.report_id, "html")} target="_blank" rel="noreferrer">HTML</a>
                <a href={buildExportUrl(selectedReport.report_id, "json")} target="_blank" rel="noreferrer">JSON</a>
                <a href={buildExportUrl(selectedReport.report_id, "bcf")} target="_blank" rel="noreferrer">BCF</a>
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
                  <strong>{selectedReport.summary.passed ? "Passed" : "Failed"}</strong>
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

              <div className="report-context">
                <span>IFC: {selectedReport.ifc_path}</span>
                <span>Created: {formatTimestamp(selectedReport.created_at)}</span>
                <span>Request: {selectedReport.request_id}</span>
              </div>

              <div className="issue-list">
                {selectedReport.issues.length === 0 ? (
                  <div className="panel-empty compact">No issues. This report passed all current checks.</div>
                ) : (
                  selectedReport.issues.map((issue, index) => (
                    <button
                      key={`${issue.rule_id}-${index}`}
                      type="button"
                      className={`issue-card ${index === selectedIssueIndex ? "active" : ""}`}
                      onClick={() => {
                        startTransition(() => {
                          setSelectedIssueIndex(index);
                          setSelectedClashIndex(null);
                        });
                      }}
                    >
                      <div className="issue-card-row">
                        <span className={`severity-pill severity-${issue.severity}`}>{issue.severity}</span>
                        <strong>{issue.rule_id}</strong>
                      </div>
                      <p>{issue.message}</p>
                      <div className="issue-card-meta">
                        <span>{issue.category}</span>
                        <span>{issue.target_ref ?? issue.element_guid ?? "no target"}</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </>
          )}
        </section>

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
                <article className="detail-block">
                  <h3>Active issue</h3>
                  {activeIssue ? (
                    <dl className="detail-grid">
                      <div><dt>Rule</dt><dd>{activeIssue.rule_id}</dd></div>
                      <div><dt>Category</dt><dd>{activeIssue.category}</dd></div>
                      <div><dt>Entity</dt><dd>{activeIssue.ifc_entity ?? "—"}</dd></div>
                      <div><dt>Target</dt><dd>{activeIssue.target_ref ?? activeIssue.element_guid ?? "—"}</dd></div>
                      <div><dt>Expected</dt><dd>{activeIssue.expected_value ?? "—"}</dd></div>
                      <div><dt>Observed</dt><dd>{activeIssue.observed_value ?? "—"}</dd></div>
                      <div><dt>Unit</dt><dd>{activeIssue.unit ?? "—"}</dd></div>
                      <div><dt>Problem zone</dt><dd>{activeIssue.problem_zone ? `${activeIssue.problem_zone.sheet_id ?? "sheet?"} · page ${activeIssue.problem_zone.page_number ?? "?"}` : "—"}</dd></div>
                    </dl>
                  ) : (
                    <p className="compact-copy">No active issue. Use the report detail panel to choose one.</p>
                  )}
                </article>

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
      </main>
    </div>
  );
}