import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DrawingEvidencePanel from "./DrawingEvidencePanel";
import type { DrawingAsset, ValidationIssue, ValidationReport } from "../lib/types";

function buildDrawingAsset(overrides: Partial<DrawingAsset>): DrawingAsset {
  return {
    asset_id: overrides.asset_id ?? "asset-001",
    sheet_id: overrides.sheet_id ?? "A-101",
    page_number: overrides.page_number ?? 1,
    media_type: overrides.media_type ?? "image/png",
    coordinate_width: overrides.coordinate_width ?? 320,
    coordinate_height: overrides.coordinate_height ?? 200,
    stored_filename: overrides.stored_filename ?? "asset-001.png",
  };
}

function buildIssue(overrides: Partial<ValidationIssue>): ValidationIssue {
  return {
    rule_id: overrides.rule_id ?? "DRAW-001",
    severity: overrides.severity ?? "error",
    message: overrides.message ?? "Drawing issue",
    ifc_entity: overrides.ifc_entity ?? "IFCWALL",
    category: overrides.category ?? "drawing-validation",
    target_ref: overrides.target_ref ?? "WALL-01",
    property_set: overrides.property_set ?? null,
    property_name: overrides.property_name ?? "thickness",
    operator: overrides.operator ?? "gte",
    expected_value: overrides.expected_value ?? "200",
    observed_value: overrides.observed_value ?? "150",
    unit: overrides.unit ?? "mm",
    element_guid: overrides.element_guid ?? null,
    problem_zone: overrides.problem_zone ?? {
      sheet_id: "A-102",
      page_number: 2,
      x: 10,
      y: 20,
      width: 100,
      height: 60,
      element_guid: null,
    },
    remark: overrides.remark ?? null,
  };
}

function buildReport(): ValidationReport {
  return {
    report_id: "r".repeat(32),
    request_id: "req-001",
    created_at: "2026-04-12T12:00:00Z",
    requirements: [],
    issues: [],
    summary: {
      requirement_count: 0,
      issue_count: 1,
      error_count: 1,
      warning_count: 0,
      passed: false,
      drawing_annotation_count: 1,
      generated_remark_count: 0,
    },
    drawing_annotations: [],
    drawing_assets: [
      buildDrawingAsset({ asset_id: "asset-openrebar", sheet_id: "A-101", page_number: 1, stored_filename: "asset-openrebar.png" }),
      buildDrawingAsset({ asset_id: "asset-a102", sheet_id: "A-102", page_number: 2, stored_filename: "asset-a102.png" }),
    ],
    clash_results: [],
  };
}

describe("DrawingEvidencePanel", () => {
  it("selects the exact matching asset for the active issue by default", () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);

    expect(screen.getByRole("img", { name: /drawing evidence preview for a-102/i })).toBeTruthy();
    expect(screen.getByText(/issue match/i)).toBeTruthy();
  });

  it("allows browsing another persisted asset while hiding the issue overlay message", () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);

    fireEvent.click(screen.getByRole("button", { name: /a-101/i }));

    expect(screen.getByRole("img", { name: /drawing evidence preview for a-101/i })).toBeTruthy();
    expect(screen.getByText(/you are browsing a-101/i)).toBeTruthy();
  });

  it("stays usable in plain preview mode when no active issue is selected", () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={null} />);

    expect(screen.getByRole("img", { name: /drawing evidence preview for a-101/i })).toBeTruthy();
    expect(screen.getByText(/plain drawing-preview mode/i)).toBeTruthy();
  });

  it("renders a problem-zone overlay rectangle after the preview image loads", async () => {
    const { container } = render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);
    const image = screen.getByRole("img", { name: /drawing evidence preview for a-102/i });

    Object.defineProperty(image, "naturalWidth", { configurable: true, value: 320 });
    Object.defineProperty(image, "naturalHeight", { configurable: true, value: 200 });
    fireEvent.load(image);

    await waitFor(() => {
      const overlay = container.querySelector(".drawing-evidence-rect");
      expect(overlay).toBeTruthy();
      expect((overlay as HTMLElement).style.width).not.toBe("");
      expect((overlay as HTMLElement).style.height).not.toBe("");
    });
  });

  it("explains missing overlay payload when problem zone lacks rectangle fields", () => {
    render(
      <DrawingEvidencePanel
        report={buildReport()}
        activeIssue={buildIssue({
          problem_zone: {
            sheet_id: "A-102",
            page_number: 2,
            x: null,
            y: null,
            width: null,
            height: null,
            element_guid: null,
          },
        })}
      />,
    );

    expect(screen.getByText(/does not yet have a complete rectangle payload/i)).toBeTruthy();
  });

  it("asks the operator to select a report when report is null", () => {
    render(<DrawingEvidencePanel report={null} activeIssue={null} />);
    expect(screen.getByText(/select a report to inspect drawing evidence/i)).toBeTruthy();
  });

  it("explains when no drawing assets were materialized", () => {
    const report = buildReport();
    report.drawing_assets = [];
    render(<DrawingEvidencePanel report={report} activeIssue={buildIssue({})} />);
    expect(screen.getByText(/no persisted drawing preview assets were materialized/i)).toBeTruthy();
  });

  it("keeps browsing usable when the issue sheet has no matching asset", () => {
    render(
      <DrawingEvidencePanel
        report={buildReport()}
        activeIssue={buildIssue({
          problem_zone: {
            sheet_id: "Z-999",
            page_number: 9,
            x: 1,
            y: 2,
            width: 3,
            height: 4,
            element_guid: null,
          },
        })}
      />,
    );
    expect(screen.getByText(/no persisted preview asset matches that sheet\/page exactly/i)).toBeTruthy();
  });

  it("lists HITL regions that require expert review", () => {
    const report = buildReport();
    report.drawing_regions = [
      {
        sheet_id: "A-101",
        modality: "raster",
        hitl_required: true,
        hitl_reason: "low_confidence_ocr",
        confidence: 0.41,
        bbox_xyxy: [0, 0, 10, 10],
      },
    ];
    render(<DrawingEvidencePanel report={report} activeIssue={null} />);
    expect(screen.getByLabelText(/regions requiring expert review/i)).toBeTruthy();
    expect(screen.getByText(/low_confidence_ocr/i)).toBeTruthy();
    expect(screen.getByText(/1 HITL region/i)).toBeTruthy();
  });

  it("draws DrawingRegionRef overlays for the selected sheet including stamp priors", async () => {
    const report = buildReport();
    report.drawing_regions = [
      {
        sheet_id: "A-101",
        modality: "layout_prior",
        confidence: 1,
        layout_role: "content",
        coordinate_system: "normalized-0-1",
        bbox_xyxy: [0, 0, 1, 0.85],
      },
      {
        sheet_id: "A-101",
        modality: "layout_prior",
        confidence: 1,
        layout_role: "stamp",
        coordinate_system: "normalized-0-1",
        bbox_xyxy: [0.55, 0.85, 1, 1],
      },
    ];
    const { container } = render(<DrawingEvidencePanel report={report} activeIssue={null} />);
    const image = screen.getByRole("img", { name: /drawing evidence preview for a-101/i });
    Object.defineProperty(image, "naturalWidth", { configurable: true, value: 320 });
    Object.defineProperty(image, "naturalHeight", { configurable: true, value: 200 });
    fireEvent.load(image);

    await waitFor(() => {
      expect(container.querySelectorAll(".drawing-evidence-rect-region").length).toBe(1);
      expect(container.querySelectorAll(".drawing-evidence-rect-stamp").length).toBe(1);
      expect(screen.getByText(/2 region overlay/i)).toBeTruthy();
    });
  });

  it("shows overlay target meta when the matched asset is selected", () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);
    expect(screen.getByText(/overlay target/i)).toBeTruthy();
    expect(screen.getByText("DRAW-001")).toBeTruthy();
  });

  it("shows browse mode meta after switching away from the matched asset", () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);
    fireEvent.click(screen.getByRole("button", { name: /a-101/i }));
    expect(screen.getByText(/browse mode/i)).toBeTruthy();
  });

  it("surfaces image load failures without claiming overlay success", async () => {
    render(<DrawingEvidencePanel report={buildReport()} activeIssue={buildIssue({})} />);
    const image = screen.getByRole("img", { name: /drawing evidence preview for a-102/i });
    fireEvent.error(image);
    await waitFor(() => {
      expect(screen.getByText(/failed to load the persisted drawing preview/i)).toBeTruthy();
    });
  });
});