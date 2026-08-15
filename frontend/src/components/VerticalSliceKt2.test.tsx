import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import VerticalSliceKt2, { formatPackageOutcome, outcomeClass, overlayRectStyle } from "./VerticalSliceKt2";
import type { ValidationIssue, ValidationReport } from "../lib/types";

/** KT#2 demo contract: stamp/title finding is visible with evidence + fail-closed verdict. */
const stampFinding: ValidationIssue = {
  rule_id: "AEROBIM-DRAWING-THICKNESS",
  severity: "error",
  message: "WALL-01 thickness 150 mm on sheet A-101 (PDF text layer)",
  ifc_entity: "IFCWALL",
  category: "drawing-measure",
  target_ref: "WALL-01",
  property_set: null,
  property_name: "thickness",
  operator: "eq",
  expected_value: "150",
  observed_value: "150",
  unit: "mm",
  element_guid: null,
  problem_zone: {
    sheet_id: "A-101",
    page_number: 1,
    x: 72,
    y: 62,
    width: 150,
    height: 12,
    element_guid: null,
  },
  remark: {
    title: "WALL-01 thickness",
    body: "Quote: WALL-01 thickness 150 mm",
  },
  finding_id: "fid-slice-wall-01",
  source_id: "sheet:A-101",
  evidence_refs: ["pdf:techlab-a101-wall-thickness#page1"],
  evidence_modality: "drawing",
  confidence: null,
  norm_source: null,
  norm_edition: null,
  norm_clause: null,
  approval_status: null,
  approval_ref: null,
};

function buildReport(outcome: ValidationReport["summary"]["outcome"] = "failed"): ValidationReport {
  return {
    report_id: "c".repeat(32),
    request_id: "req-slice",
    created_at: "2026-08-13T20:00:00Z",
    requirements: [],
    issues: [stampFinding],
    summary: {
      requirement_count: 0,
      issue_count: 1,
      error_count: 1,
      warning_count: 0,
      passed: false,
      drawing_annotation_count: 1,
      generated_remark_count: 1,
      outcome,
    },
    drawing_annotations: [],
    drawing_assets: [],
    clash_results: [],
  };
}

describe("KT#2 vertical-slice UI contract", () => {
  it("shows fragment quote, finding id, evidence ref, overlay, and a non-pass verdict", () => {
    render(<VerticalSliceKt2 report={buildReport("failed")} issue={stampFinding} />);
    expect(screen.getByTestId("kt2-vertical-slice")).toBeTruthy();
    expect(screen.getByText("fid-slice-wall-01")).toBeTruthy();
    expect(screen.getByText("sheet:A-101")).toBeTruthy();
    expect(screen.getByText(/Checkpoint NO_GO/i)).toBeTruthy();
    expect(screen.getByText(/file ingest only/i)).toBeTruthy();
    expect(screen.getByText("pdf:techlab-a101-wall-thickness#page1")).toBeTruthy();
    expect(screen.getByText(/Quote: WALL-01 thickness 150 mm/)).toBeTruthy();
    expect(screen.getByText(/Sheet A-101/)).toBeTruthy();
    expect(screen.getByTestId("kt2-overlay")).toBeTruthy();
    expect(screen.getByTestId("kt2-overlay-bbox")).toBeTruthy();
    expect(screen.getByText(/deterministic bbox, not CV/i)).toBeTruthy();
    const badge = screen.getByTestId("kt2-outcome");
    expect(badge.textContent).toMatch(/FAILED/);
    expect(badge.className).toContain("outcome-fail");
    expect(badge.className).not.toContain("outcome-pass");
    expect(screen.getByText(/Verdict is not PASS/i)).toBeTruthy();
  });

  it("keeps FAILED visually distinct from BLOCKED", () => {
    expect(outcomeClass("failed", false)).toBe("outcome-fail");
    expect(outcomeClass("blocked", false)).toBe("outcome-block");
    expect(outcomeClass("review_required", false)).toBe("outcome-review");
  });

  it("does not treat summary.passed as Published authorization", () => {
    expect(formatPackageOutcome("pass", true)).not.toMatch(/Published/i);
    expect(formatPackageOutcome("blocked", true)).not.toMatch(/Published/i);
    expect(formatPackageOutcome(undefined, true)).toBe("Passed (legacy)");
    expect(formatPackageOutcome(undefined, true)).not.toMatch(/Published/i);
  });

  it("places the bbox from problem_zone on the fixture letter page", () => {
    const style = overlayRectStyle(stampFinding.problem_zone);
    expect(style).not.toBeNull();
    expect(style?.left).toBe(`${(72 / 612) * 100}%`);
    expect(style?.top).toBe(`${(62 / 792) * 100}%`);
    expect(style?.width).toBe(`${(150 / 612) * 100}%`);
    expect(style?.height).toBe(`${(12 / 792) * 100}%`);
  });

  it("renders an overlay image when the CLI PNG href is provided", () => {
    render(
      <VerticalSliceKt2
        report={buildReport("failed")}
        issue={stampFinding}
        overlaySrc="overlay-problem-zone.png"
      />,
    );
    const img = screen.getByRole("img", { name: /problem-zone overlay/i });
    expect(img.getAttribute("src")).toBe("overlay-problem-zone.png");
    expect(screen.queryByTestId("kt2-overlay-bbox")).toBeNull();
  });
});
