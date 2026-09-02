import { startTransition, type ReactNode } from "react";
import type { ParsedRequirement, ReportSummaryEntry, ValidationIssue, ValidationReport } from "../../lib/types";
import type { FindingGroupBy, IndexedIssue } from "../../lib/issue-triage";
import type { WorkspaceView } from "../../components/WorkspaceNav";
import { UI_COPY } from "../../lib/ui-copy";
import CoverageMapPanel from "../../components/CoverageMapPanel";
import CapabilityHonestyPanel from "../../components/CapabilityHonestyPanel";
import ProvenancePanel from "../../components/ProvenancePanel";
import DrawingEvidencePanel from "../../components/DrawingEvidencePanel";
import VerticalSliceKt2 from "../../components/VerticalSliceKt2";
import FindingListPanel from "../findings/FindingListPanel";
import RemarkCardPanel from "../findings/RemarkCardPanel";
import ExportActionsBar from "../export/ExportActionsBar";
import MachineGatewayStrip, { type HitlDecisionState } from "./MachineGatewayStrip";
import ResizableWorkplace from "./ResizableWorkplace";

export type ExpertWorkplaceProps = {
  workspaceView: WorkspaceView;
  reports: ReportSummaryEntry[];
  selectedReportId: string | null;
  selectedReport: ValidationReport | null;
  reportLoading: boolean;
  filteredIssues: IndexedIssue[];
  selectedIssueIndex: number;
  issueSeverityFilter: "all" | "error" | "warning" | "info";
  hitlOnlyFilter: boolean;
  hitlRegionCount: number;
  findingGroupBy: FindingGroupBy;
  activeIssue: ValidationIssue | null;
  matchingRequirements: ParsedRequirement[];
  selectedClashIndex: number | null;
  remarkDraft: string;
  remarkSaveState: "idle" | "saving" | "saved" | "failed";
  hitlDecisionState: HitlDecisionState;
  hitlEnabled: boolean;
  spatialViewer: ReactNode;
  onSelectReport: (reportId: string) => void;
  onSeverityChange: (value: "all" | "error" | "warning" | "info") => void;
  onHitlOnlyChange: (value: boolean) => void;
  onGroupByChange: (value: FindingGroupBy) => void;
  onSelectIssue: (index: number, issue: ValidationIssue) => void;
  onSelectClash: (index: number | null) => void;
  onDraftChange: (value: string) => void;
  onSave: () => void;
  onAccept: () => void;
  onReject: () => void;
  onNavigateToFindings: () => void;
};

export default function ExpertWorkplace({
  workspaceView,
  reports,
  selectedReportId,
  selectedReport,
  reportLoading,
  filteredIssues,
  selectedIssueIndex,
  issueSeverityFilter,
  hitlOnlyFilter,
  hitlRegionCount,
  findingGroupBy,
  activeIssue,
  matchingRequirements,
  selectedClashIndex,
  remarkDraft,
  remarkSaveState,
  hitlDecisionState,
  hitlEnabled,
  spatialViewer,
  onSelectReport,
  onSeverityChange,
  onHitlOnlyChange,
  onGroupByChange,
  onSelectIssue,
  onSelectClash,
  onDraftChange,
  onSave,
  onAccept,
  onReject,
  onNavigateToFindings,
}: ExpertWorkplaceProps) {
  const showExportExtras = workspaceView === "export";

  return (
    <div className="expert-workplace" data-testid="expert-workplace">
      {selectedReport ? (
        <>
          <div className="expert-pack-bar">
            <label className="pack-switcher">
              {UI_COPY.packSwitcher}
              <select
                aria-label={UI_COPY.selectedPack}
                value={selectedReportId ?? ""}
                onChange={(event) => onSelectReport(event.target.value)}
              >
                {reports.map((report) => (
                  <option key={report.report_id} value={report.report_id}>
                    {report.project_name?.trim() || report.report_id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <ExportActionsBar reportId={selectedReport.report_id} />
          </div>
          <p className="compact-copy" data-testid="training-rules-banner" role="note">
            {UI_COPY.trainingRulesBanner}
          </p>
          <MachineGatewayStrip report={selectedReport} hitlDecisionState={hitlDecisionState} />
        </>
      ) : null}

      <ResizableWorkplace
        left={
          <section className="panel issue-panel" data-testid="expert-findings-pane">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">{UI_COPY.findingsKicker}</p>
                <h2>{UI_COPY.findingsTitle}</h2>
              </div>
            </div>
            {reportLoading ? (
              <div className="panel-empty">{UI_COPY.loadingReport}</div>
            ) : selectedReport === null ? (
              <div className="panel-empty">{UI_COPY.noReportSelected}</div>
            ) : (
              <FindingListPanel
                issues={filteredIssues}
                totalIssueCount={selectedReport.issues.length}
                selectedIssueIndex={selectedIssueIndex}
                issueSeverityFilter={issueSeverityFilter}
                hitlOnlyFilter={hitlOnlyFilter}
                hitlRegionCount={hitlRegionCount}
                groupBy={findingGroupBy}
                onSeverityChange={onSeverityChange}
                onHitlOnlyChange={onHitlOnlyChange}
                onGroupByChange={onGroupByChange}
                onSelectIssue={onSelectIssue}
              />
            )}
          </section>
        }
        center={
          <div className="side-stack" data-testid="expert-spatial-pane">
            {spatialViewer}
            <DrawingEvidencePanel report={selectedReport} activeIssue={activeIssue} />
            <section className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-kicker">{UI_COPY.clashKicker}</p>
                  <h2>{UI_COPY.clashTitle}</h2>
                </div>
              </div>
              {selectedReport === null ? (
                <p className="compact-copy">{UI_COPY.selectReportClash}</p>
              ) : selectedReport.clash_results.length === 0 ? (
                <p className="compact-copy">{UI_COPY.noClash}</p>
              ) : (
                <div className="collection-stack">
                  {selectedReport.clash_results.map((clash, index) => (
                    <button
                      key={`${clash.element_a_guid}-${clash.element_b_guid}-${index}`}
                      type="button"
                      className={`collection-card collection-card-button ${index === selectedClashIndex ? "active" : ""}`}
                      onClick={() => {
                        startTransition(() => {
                          onSelectClash(index === selectedClashIndex ? null : index);
                        });
                      }}
                    >
                      <div className="collection-card-row">
                        <strong>{clash.clash_type}</strong>
                        <span className="selection-badge">
                          {index === selectedClashIndex ? UI_COPY.viewerFocusOn : UI_COPY.focusClash}
                        </span>
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
            </section>
          </div>
        }
        right={
          <section className="panel provenance-panel" data-testid="expert-remark-pane">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">{UI_COPY.remarkKicker}</p>
                <h2>{UI_COPY.remarkCardTitle}</h2>
              </div>
            </div>
            {selectedReport === null ? (
              <div className="panel-empty">{UI_COPY.selectReportFirst}</div>
            ) : (
              <div className="provenance-stack">
                <RemarkCardPanel
                  reportId={selectedReport.report_id}
                  activeIssue={activeIssue}
                  remarkDraft={remarkDraft}
                  remarkSaveState={remarkSaveState}
                  hitlDecisionState={hitlDecisionState}
                  hitlEnabled={hitlEnabled}
                  onDraftChange={onDraftChange}
                  onSave={onSave}
                  onAccept={onAccept}
                  onReject={onReject}
                />
                <ProvenancePanel activeIssue={activeIssue} />
                <article className="detail-block">
                  <h3>{UI_COPY.matchingReqs}</h3>
                  {matchingRequirements.length === 0 ? (
                    <p className="compact-copy">{UI_COPY.noReqMatch}</p>
                  ) : (
                    <div className="collection-stack">
                      {matchingRequirements.map((requirement) => (
                        <div
                          key={`${requirement.rule_id}-${requirement.source_kind}`}
                          className="collection-card"
                        >
                          <strong>{requirement.rule_id}</strong>
                          <span>{requirement.source_kind}</span>
                          <p>
                            {requirement.property_set ??
                              requirement.ifc_entity ??
                              UI_COPY.noEntity}
                          </p>
                          <div className="collection-meta">
                            <span>{requirement.property_name ?? UI_COPY.noProperty}</span>
                            <span>{requirement.expected_value ?? UI_COPY.noExpected}</span>
                            <span>{requirement.unit ?? UI_COPY.noUnit}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </div>
            )}
          </section>
        }
      />

      {showExportExtras && selectedReport ? (
        <div className="export-preview" data-testid="export-preview">
          <VerticalSliceKt2 report={selectedReport} issue={activeIssue} />
          <CapabilityHonestyPanel
            capabilities={selectedReport.capabilities}
            divergences={selectedReport.divergences}
          />
          <CoverageMapPanel
            reportId={selectedReport.report_id}
            onNavigateToFindings={onNavigateToFindings}
          />
        </div>
      ) : null}
    </div>
  );
}
