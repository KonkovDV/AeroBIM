import { describe, expect, it } from "vitest";
import {
  clauseLine,
  essenceLine,
  filterTriageIssues,
  findIssueForDrawingRegion,
  groupFindings,
  HITL_RULE_ID,
  isHitlClickableRegion,
  issueMatchesSearch,
  spatialOrMissing,
} from "./issue-triage";
import type { ValidationIssue, ValidationReport } from "./types";

function issue(overrides: Partial<ValidationIssue>): ValidationIssue {
  return {
    rule_id: "R1",
    severity: "error",
    message: "First sentence. Second.",
    ifc_entity: "IFCWALL",
    category: "ids",
    target_ref: null,
    property_set: null,
    property_name: null,
    operator: null,
    expected_value: null,
    observed_value: null,
    unit: null,
    element_guid: "g1",
    problem_zone: null,
    remark: null,
    ...overrides,
  };
}

describe("issue-triage", () => {
  it("groups by storey and uses нет в индексе when unstamped", () => {
    const rows = [
      { issue: issue({ storey_name: "3 этаж" }), index: 0 },
      { issue: issue({ rule_id: "R2", storey_name: null }), index: 1 },
      { issue: issue({ rule_id: "R3", storey_name: "3 этаж" }), index: 2 },
    ];
    const grouped = groupFindings(rows, "storey");
    expect(grouped).toHaveLength(2);
    expect(grouped[0]?.key).toBe("3 этаж");
    expect(grouped[0]?.rows).toHaveLength(2);
    expect(grouped[1]?.key).toBe("нет в индексе");
  });

  it("does not invent a clause from empty norm fields", () => {
    expect(clauseLine(issue({}))).toMatch(/обязательное поле ТЗ/);
    expect(clauseLine(issue({ norm_source: "СП 63", norm_clause: "7.1" }))).toBe("СП 63 · 7.1");
  });

  it("uses remark essence before splitting the message", () => {
    expect(essenceLine(issue({ remark: { title: "T", body: "B", essence: "Стена REI" } }))).toBe(
      "Стена REI",
    );
    expect(essenceLine(issue({}))).toBe("First sentence.");
  });

  it("groups by axis and category without inventing tags", () => {
    const rows = [
      { issue: issue({ grid_axis: "А" }), index: 0 },
      { issue: issue({ rule_id: "R2", grid_axis: null }), index: 1 },
    ];
    const byAxis = groupFindings(rows, "axis");
    expect(byAxis[0]?.key).toBe("А");
    expect(byAxis[1]?.key).toBe("нет в индексе");
    const byCategory = groupFindings(rows, "discipline");
    expect(byCategory[0]?.key).toBe("ids");
  });

  it("never invents storey from empty string", () => {
    expect(spatialOrMissing("")).toBe("нет в индексе");
    expect(spatialOrMissing("  1 этаж ")).toBe("1 этаж");
  });

  it("matches search across rule, message, guid, storey and axis", () => {
    const row = issue({
      rule_id: "FIRE-1",
      message: "FireRating REI30 вместо REI60",
      element_guid: "1XYVUKGoDDbREfVxRKsHkl",
      storey_name: "3 этаж",
      grid_axis: "А-2",
    });
    expect(issueMatchesSearch(row, "")).toBe(true);
    expect(issueMatchesSearch(row, "  ")).toBe(true);
    expect(issueMatchesSearch(row, "fire-1")).toBe(true);
    expect(issueMatchesSearch(row, "rei60")).toBe(true);
    expect(issueMatchesSearch(row, "1xyvuk")).toBe(true);
    expect(issueMatchesSearch(row, "3 этаж")).toBe(true);
    expect(issueMatchesSearch(row, "а-2")).toBe(true);
    expect(issueMatchesSearch(row, "колонна")).toBe(false);
  });

  it("filterTriageIssues applies severity, hitl and search, then sorts by priority", () => {
    const report = {
      issues: [
        issue({ rule_id: "R1", severity: "warning", priority: 1 }),
        issue({ rule_id: HITL_RULE_ID, severity: "error", priority: 9, message: "Регион листа" }),
        issue({ rule_id: "R3", severity: "error", priority: 5, message: "Стена REI" }),
      ],
    } as unknown as ValidationReport;
    const all = filterTriageIssues(report, { severity: "all", hitlOnly: false, search: "" });
    expect(all.map((row) => row.issue.rule_id)).toEqual([HITL_RULE_ID, "R3", "R1"]);
    const errors = filterTriageIssues(report, { severity: "error", hitlOnly: false, search: "" });
    expect(errors.map((row) => row.issue.rule_id)).toEqual([HITL_RULE_ID, "R3"]);
    const hitl = filterTriageIssues(report, { severity: "all", hitlOnly: true, search: "" });
    expect(hitl.map((row) => row.issue.rule_id)).toEqual([HITL_RULE_ID]);
    const found = filterTriageIssues(report, { severity: "all", hitlOnly: false, search: "rei" });
    expect(found.map((row) => row.issue.rule_id)).toEqual(["R3"]);
    // Исходные индексы отчёта сохраняются — карточка и клавиатура работают по ним.
    expect(all[0]?.index).toBe(1);
  });

  it("matches a HITL region to a finding on the same sheet and ignores stamp priors", () => {
    const hitl = {
      issue: issue({
        rule_id: HITL_RULE_ID,
        problem_zone: {
          sheet_id: "A-101",
          page_number: 1,
          x: 1,
          y: 1,
          width: 2,
          height: 2,
          element_guid: null,
        },
      }),
      index: 0,
    };
    const other = {
      issue: issue({
        rule_id: "DRAW-001",
        problem_zone: {
          sheet_id: "A-102",
          page_number: 1,
          x: 1,
          y: 1,
          width: 2,
          height: 2,
          element_guid: null,
        },
      }),
      index: 1,
    };
    const region = {
      sheet_id: "A-101",
      bbox_xyxy: [0, 0, 1, 1] as [number, number, number, number],
      confidence: 0.4,
      modality: "raster",
      hitl_required: true,
    };
    expect(isHitlClickableRegion(region)).toBe(true);
    expect(isHitlClickableRegion({ ...region, layout_role: "stamp" })).toBe(false);
    expect(findIssueForDrawingRegion([hitl, other], region)?.index).toBe(0);
    expect(findIssueForDrawingRegion([other], region)).toBeNull();
  });
});
