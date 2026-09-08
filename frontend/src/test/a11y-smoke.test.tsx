import axe from "axe-core";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ErrorBanner from "../features/shell/ErrorBanner";
import ExportActionsBar from "../features/export/ExportActionsBar";
import FindingListPanel from "../features/findings/FindingListPanel";
import RemarkCardPanel from "../features/findings/RemarkCardPanel";
import ShellHeader from "../features/shell/ShellHeader";
import ViewerPlaceholder from "../features/shell/ViewerPlaceholder";
import CapabilityTopBanner from "../features/capabilities/CapabilityTopBanner";
import WorkspaceNav from "../components/WorkspaceNav";
import PackUploadPanel from "../components/PackUploadPanel";
import { UI_COPY } from "../lib/ui-copy";
import type { ValidationIssue } from "../lib/types";

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
        onSeverityChange={() => undefined}
        onHitlOnlyChange={() => undefined}
        onGroupByChange={() => undefined}
        onSelectIssue={() => undefined}
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
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(await seriousViolations(container)).toEqual([]);
  });

  it("has no critical/serious axe hits on shell, export, upload and banner", async () => {
    const { container: banner } = render(
      <ErrorBanner kind="forbidden" onRetry={() => undefined} />,
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
        onRoleChange={() => undefined}
      />,
    );
    expect(await seriousViolations(header)).toEqual([]);
    const { container: nav } = render(
      <WorkspaceNav workspaceView="review" onChange={() => undefined} reviewFindingsCount={2} />,
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
});
