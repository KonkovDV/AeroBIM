import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RemarkCardPanel from "./RemarkCardPanel";
import type { ValidationIssue } from "../../lib/types";

const baseIssue: ValidationIssue = {
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

describe("RemarkCardPanel", () => {
  it("shows TZ fields and does not invent storey or axis", () => {
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(screen.getByText("СП 2.13130 · 5.4")).toBeTruthy();
    expect(screen.getAllByText("нет в индексе")).toHaveLength(2);
    expect(screen.getByText("1XYVUKGoDDbREfVxRKsHkl")).toBeTruthy();
    expect(screen.getByText("fid-1")).toBeTruthy();
    expect(screen.getByText("ids:FIRE-1")).toBeTruthy();
    expect(screen.getByTestId("evidence-stepper")).toBeTruthy();
    expect(screen.getByTestId("review-history")).toBeTruthy();
  });
});
