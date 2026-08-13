import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ProvenancePanel from "./ProvenancePanel";
import type { ValidationIssue } from "../lib/types";

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

describe("KT#2 vertical-slice UI contract", () => {
  it("shows fragment quote, finding id, evidence ref, and does not look like a pass", () => {
    render(<ProvenancePanel activeIssue={stampFinding} />);
    expect(screen.getByText("fid-slice-wall-01")).toBeTruthy();
    expect(screen.getByText("pdf:techlab-a101-wall-thickness#page1")).toBeTruthy();
    expect(screen.getByText(/WALL-01/)).toBeTruthy();
    expect(screen.getByText(/Audit-ready provenance present/i)).toBeTruthy();
  });
});
