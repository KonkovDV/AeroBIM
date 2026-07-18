import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ProvenancePanel, { isFindingAuditReady } from "./ProvenancePanel";
import type { ValidationIssue } from "../lib/types";

function issue(overrides: Partial<ValidationIssue> = {}): ValidationIssue {
  return {
    rule_id: "IDS-1",
    severity: "error",
    message: "Missing property",
    ifc_entity: "IFCWALL",
    category: "ifc-validation",
    target_ref: "WALL-01",
    property_set: "Pset_WallCommon",
    property_name: "IsExternal",
    operator: "exists",
    expected_value: "true",
    observed_value: null,
    unit: null,
    element_guid: "2O2Fr$t4X7Zf8NOew3FLOH",
    problem_zone: {
      sheet_id: "A-101",
      page_number: 1,
      x: 10,
      y: 20,
      width: 100,
      height: 50,
      element_guid: null,
    },
    remark: null,
    finding_id: "fid-001",
    source_id: "pkg-ifc-main",
    evidence_refs: ["pkg-ifc-main@r1#ifc:2O2Fr$t4X7Zf8NOew3FLOH"],
    evidence_modality: "ifc",
    confidence: 0.91,
    norm_source: "SP 54",
    norm_edition: "2016",
    norm_clause: "7.1",
    approval_status: "customer_approved",
    approval_ref: "SAM-NP-001",
    ...overrides,
  };
}

describe("ProvenancePanel", () => {
  it("marks incomplete provenance when evidence_refs missing", () => {
    expect(isFindingAuditReady(issue({ evidence_refs: [] }))).toBe(false);
    render(<ProvenancePanel activeIssue={issue({ evidence_refs: [] })} />);
    expect(screen.getByText(/Incomplete provenance/i)).toBeTruthy();
    expect(screen.getByText("Finding ID")).toBeTruthy();
  });

  it("shows audit-ready banner and GlobalId when complete", () => {
    expect(isFindingAuditReady(issue())).toBe(true);
    render(<ProvenancePanel activeIssue={issue()} />);
    expect(screen.getByText(/Audit-ready provenance present/i)).toBeTruthy();
    expect(screen.getByText("2O2Fr$t4X7Zf8NOew3FLOH")).toBeTruthy();
    expect(screen.getByText(/pkg-ifc-main@r1#ifc:/i)).toBeTruthy();
    expect(screen.getByText(/SAM-NP-001/)).toBeTruthy();
  });
});
