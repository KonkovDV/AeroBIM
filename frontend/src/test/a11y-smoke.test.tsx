import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorBanner from "../features/shell/ErrorBanner";
import ExportActionsBar from "../features/export/ExportActionsBar";
import FindingListPanel from "../features/findings/FindingListPanel";
import RemarkCardPanel from "../features/findings/RemarkCardPanel";
import ShellHeader from "../features/shell/ShellHeader";
import ViewerPlaceholder from "../features/shell/ViewerPlaceholder";
import CapabilityTopBanner from "../features/capabilities/CapabilityTopBanner";
import WorkspaceNav from "../components/WorkspaceNav";
import PackUploadPanel from "../components/PackUploadPanel";
import DrawingEvidencePanel from "../components/DrawingEvidencePanel";
import VersionDiffPanel from "../components/VersionDiffPanel";
import PackCycleStrip from "../features/workplace/PackCycleStrip";
import ExpertWorkplace from "../features/workplace/ExpertWorkplace";
import PackScreens from "../features/shell/PackScreens";
import UserScreen from "../features/shell/UserScreen";
import ReportListPanel from "../features/reports/ReportListPanel";
import { UI_COPY } from "../lib/ui-copy";
import { EMPTY_PACK_DRAFT } from "../lib/pack-draft";
import type { ValidationIssue } from "../lib/types";
import type { usePackDraft } from "../hooks/usePackDraft";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    fetchSystemCapabilities: vi.fn().mockResolvedValue({
      artifact_type: "system_capabilities",
      schema_version: "1.3.0",
      customer_intake_gate: {
        status: "BLOCKED_NO_CUSTOMER_DATA",
        claim_level: "not_ready",
        true_gates: [],
        checkpoint: "GO",
        source: "audit/evidence/customer-intake-gate.json",
      },
      samolet_mvp_answers: {
        closes_rt001: false,
        closes_rt002: false,
        closes_rt003: false,
        checkpoint: "GO",
      },
    }),
  };
});

const issue: ValidationIssue = {
  rule_id: "FIRE-1",
  severity: "error",
  message: "FireRating mismatch.",
  ifc_entity: "IFCWALL",
  category: "ids",
  target_ref: null,
  property_set: "Pset_WallCommon",
  property_name: "FireRating",
  operator: "eq",
  expected_value: "REI60",
  observed_value: "REI30",
  unit: null,
  element_guid: "1XYVUKGoDDbREfVxRKsHkl",
  problem_zone: null,
  remark: { title: "Стена", body: "REI" },
  finding_id: "fid-1",
  source_id: "ids:FIRE-1",
  evidence_refs: ["ids:FIRE-1#wall"],
  storey_name: null,
  grid_axis: null,
  norm_source: "СП 2.13130",
  norm_clause: "5.4",
};

const noop = (): void => undefined;

const stubPack: ReturnType<typeof usePackDraft> = {
  packDraft: EMPTY_PACK_DRAFT,
  draftApplyNote: null,
  pendingRole: null,
  applyUpload: () => ({ kind: "filled", slot: "ifc" }),
  chooseRole: noop,
};

async function seriousViolations(container: HTMLElement): Promise<string[]> {
  const results = await axe.run(container, {
    rules: {
      "color-contrast": { enabled: false },
    },
  });
  return results.violations
    .filter((row) => row.impact === "critical" || row.impact === "serious")
    .map((row) => row.id);
}

describe("a11y smoke (axe-core, not a WCAG certificate)", () => {
  it("has no critical/serious axe hits on the findings list", async () => {
    const { container } = render(
      <FindingListPanel
        issues={[{ issue, index: 0 }]}
        totalIssueCount={1}
        selectedIssueIndex={0}
        issueSeverityFilter="all"
        hitlOnlyFilter={false}
        hitlRegionCount={0}
        groupBy="none"
        onSeverityChange={noop}
        onHitlOnlyChange={noop}
        onGroupByChange={noop}
        onSelectIssue={noop}
      />,
    );
    expect(await seriousViolations(container)).toEqual([]);
  });

  it("has no critical/serious axe hits on the remark card", async () => {
    const { container } = render(
      <RemarkCardPanel
        activeIssue={issue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={noop}
        onSave={noop}
        onAccept={noop}
        onReject={noop}
      />,
    );
    expect(await seriousViolations(container)).toEqual([]);
  });

  it("keeps honesty banners as notes and one live status on the findings count", () => {
    const { container } = render(
      <>
        <ShellHeader
          apiBase=""
          reportCount={0}
          uiRole="expert"
          onRoleChange={noop}
        />
        <CapabilityTopBanner capabilities={null} />
        <FindingListPanel
          issues={[{ issue, index: 0 }]}
          totalIssueCount={1}
          selectedIssueIndex={0}
          issueSeverityFilter="all"
          hitlOnlyFilter={false}
          hitlRegionCount={0}
          groupBy="none"
          onSeverityChange={noop}
          onHitlOnlyChange={noop}
          onGroupByChange={noop}
          onSelectIssue={noop}
        />
      </>,
    );
    expect(container.querySelectorAll('[role="status"]')).toHaveLength(1);
    expect(container.querySelectorAll('[role="note"]').length).toBeGreaterThan(0);
  });

  it("has no critical/serious axe hits on shell, export, upload and banner", async () => {
    const { container: banner } = render(
      <ErrorBanner kind="forbidden" onRetry={noop} />,
    );
    expect(await seriousViolations(banner)).toEqual([]);
    const { container: exportBar } = render(
      <ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" showLimits />,
    );
    expect(await seriousViolations(exportBar)).toEqual([]);
    const { container: header } = render(
      <ShellHeader
        apiBase=""
        reportCount={0}
        uiRole="expert"
        onRoleChange={noop}
      />,
    );
    expect(await seriousViolations(header)).toEqual([]);
    const { container: nav } = render(
      <WorkspaceNav workspaceView="review" onChange={noop} reviewFindingsCount={2} />,
    );
    expect(await seriousViolations(nav)).toEqual([]);
    const { container: viewer } = render(
      <ViewerPlaceholder message={UI_COPY.viewerNeedReport} />,
    );
    expect(await seriousViolations(viewer)).toEqual([]);
    const { container: caps } = render(<CapabilityTopBanner capabilities={null} />);
    expect(await seriousViolations(caps)).toEqual([]);
    const { container: upload } = render(<PackUploadPanel />);
    expect(await seriousViolations(upload)).toEqual([]);
  });

  it("has no critical/serious axe hits on the eight TZ screens (stubs, not a WCAG certificate)", async () => {
    const { container: expert } = render(
      <ExpertWorkplace
        workspaceView="review"
        reports={[]}
        selectedReportId={null}
        selectedReport={null}
        reportLoading={false}
        filteredIssues={[]}
        selectedIssueIndex={-1}
        issueSeverityFilter="all"
        hitlOnlyFilter={false}
        hitlRegionCount={0}
        issueSearch=""
        findingGroupBy="none"
        clauseFilter=""
        activeIssue={null}
        matchingRequirements={[]}
        selectedClashIndex={null}
        remarkDraft=""
        remarkSaveState="idle"
        hitlDecisionState="idle"
        hitlEnabled={false}
        reviewEvents={[]}
        reviewEventsError={null}
        spatialViewer={<ViewerPlaceholder message={UI_COPY.viewerNeedReport} />}
        onSelectReport={noop}
        onSeverityChange={noop}
        onHitlOnlyChange={noop}
        onSearchChange={noop}
        onGroupByChange={noop}
        onClauseChange={noop}
        onSelectIssue={noop}
        onSelectClash={noop}
        onDraftChange={noop}
        onSave={noop}
        onAccept={noop}
        onReject={noop}
        onNavigateToFindings={noop}
        onOpenScreen={noop}
      />,
    );
    expect(await seriousViolations(expert)).toEqual([]);

    const { container: run } = render(
      <PackScreens
        workspaceView="run"
        pack={stubPack}
        capabilities={null}
        capabilitiesReportId={null}
        onReportReady={noop}
        onNavigate={noop}
      />,
    );
    expect(await seriousViolations(run)).toEqual([]);

    const { container: diff } = render(<VersionDiffPanel reports={[]} />);
    expect(await seriousViolations(diff)).toEqual([]);

    const { container: user } = render(
      <UserScreen
        selectedReportId={null}
        selectedReport={null}
        onOpenScreen={noop}
        onNavigateToFindings={noop}
      />,
    );
    expect(await screen.findByTestId("blocker-honesty-panel")).toBeTruthy();
    expect(await seriousViolations(user)).toEqual([]);

    const { container: projects } = render(
      <ReportListPanel
        reportsLoading={false}
        filteredReports={[]}
        groupedReports={new Map()}
        selectedReportId={null}
        search=""
        groupByProject={false}
        projectFilter=""
        disciplineFilter=""
        statusFilter="all"
        shareLinkState="idle"
        presetTransferState="idle"
        presetTransferDraft=""
        presetNameDraft=""
        presetScopeDraft="browser"
        filterPresets={[]}
        onSearchChange={noop}
        onGroupByProjectToggle={noop}
        onProjectFilterChange={noop}
        onDisciplineFilterChange={noop}
        onStatusFilterChange={noop}
        onSelectReport={noop}
        onCopyShareLink={noop}
        onPresetNameChange={noop}
        onPresetScopeChange={noop}
        onSavePreset={noop}
        onCopyPresets={noop}
        onDownloadPresets={noop}
        onImportPresets={noop}
        onImportPresetFile={noop}
        onPresetDraftChange={noop}
        onApplyPreset={noop}
        onRemovePreset={noop}
      />,
    );
    expect(await seriousViolations(projects)).toEqual([]);

    const { container: drawing } = render(
      <DrawingEvidencePanel report={null} activeIssue={null} />,
    );
    expect(await seriousViolations(drawing)).toEqual([]);

    const { container: cycle } = render(
      <PackCycleStrip
        workspaceView="review"
        packDraft={EMPTY_PACK_DRAFT}
        hasReport={false}
        onChange={noop}
      />,
    );
    expect(await seriousViolations(cycle)).toEqual([]);
  });
});
