import { Suspense, lazy, startTransition, useDeferredValue, useEffect, useState } from "react";
import { buildExportUrl, fetchReport, fetchReports, getApiBaseUrl } from "./lib/api";
import type { ClashResult, ParsedRequirement, ReportSummaryEntry, ValidationIssue, ValidationReport } from "./lib/types";
import DrawingEvidencePanel from "./components/DrawingEvidencePanel";

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

  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    let cancelled = false;
    setReportsLoading(true);
    fetchReports()
      .then((response) => {
        if (cancelled) {
          return;
        }
        setReports(response.reports);
        setReportsError(null);
        if (response.reports.length > 0) {
          setSelectedReportId((current) => current ?? response.reports[0].report_id);
        }
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
  }, []);

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
            <input
              className="search-input"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by report or request id"
            />
          </div>

          {reportsLoading ? (
            <div className="panel-empty">Loading reports…</div>
          ) : filteredReports.length === 0 ? (
            <div className="panel-empty">No persisted reports match the current query.</div>
          ) : (
            <div className="report-list">
              {filteredReports.map((report) => {
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
                      <span>Request {report.request_id}</span>
                      <span>{report.issue_count} issues</span>
                    </div>
                    <span className="report-card-time">{formatTimestamp(report.created_at)}</span>
                  </button>
                );
              })}
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