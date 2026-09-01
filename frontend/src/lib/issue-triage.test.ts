import { describe, expect, it } from "vitest";
import { clauseLine, essenceLine, groupFindings, spatialOrMissing } from "./issue-triage";
import type { ValidationIssue } from "./types";

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
});
