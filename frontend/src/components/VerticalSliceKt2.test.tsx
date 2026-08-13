import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import VerticalSliceKt2, { outcomeClass } from "./VerticalSliceKt2";
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
    expect(screen.getByText("pdf:techlab-a101-wall-thickness#page1")).toBeTruthy();
    expect(screen.getByText(/Quote: WALL-01 thickness 150 mm/)).toBeTruthy();
    expect(screen.getByText(/Sheet A-101/)).toBeTruthy();
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
});
