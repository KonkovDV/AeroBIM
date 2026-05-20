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
});