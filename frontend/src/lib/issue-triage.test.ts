import { describe, expect, it } from "vitest";
import {
  clauseLine,
  collapseDuplicateHitl,
  essenceLine,
  filterTriageIssues,
  findingCategoryLabel,
  findingListTitle,
  findIssueForDrawingRegion,
  groupFindings,
  HITL_RULE_ID,
  isAdvisoryIssue,
  isDocumentFinding,
  pickLandingIssueIndex,
  isEngineCapabilityIssue,
  isHitlClickableRegion,
  issueMatchesSearch,
  issueLayer,
  snapIssueIndexToVisible,
  spatialOrMissing,
  uniqueClauseKeys,
  CLAUSE_FILTER_MISSING,
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
    expect(clauseLine(issue({}))).toMatch(/Пункт нормы не указан/);
    expect(clauseLine(issue({ norm_source: "СП 63", norm_clause: "7.1" }))).toBe("СП 63 · 7.1");
  });

  it("uses remark essence before splitting the message", () => {
    expect(essenceLine(issue({ remark: { title: "T", body: "B", essence: "Стена REI" } }))).toBe(
      "Стена REI",
    );
    expect(essenceLine(issue({}))).toBe("First sentence.");
  });

  it("labels known categories in Russian and prefers essence as the list title", () => {
    expect(findingCategoryLabel("ids-validation")).toBe("IDS");
    expect(findingCategoryLabel("drawing-validation")).toBe("чертёж");
    expect(findingCategoryLabel("mystery-bucket")).toBe("mystery-bucket");
    expect(
      findingListTitle(
        issue({
          message: "English engine message",
          remark: { title: "IDS-Wall: FireRating", body: "", essence: "Стена без REI60" },
        }),
      ),
    ).toBe("Стена без REI60");
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

  it("snaps hidden selection to the first visible row and leaves empty lists alone", () => {
    const rows = [
      { issue: issue({ rule_id: "R2" }), index: 1 },
      { issue: issue({ rule_id: "R3" }), index: 2 },
    ];
    expect(snapIssueIndexToVisible(rows, 1)).toBe(1);
    expect(snapIssueIndexToVisible(rows, 0)).toBe(1);
    expect(snapIssueIndexToVisible([], 0)).toBeNull();
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
    expect(issueMatchesSearch(issue({ norm_source: "СП 63", norm_clause: "8.1" }), "сп 63")).toBe(
      true,
    );
    expect(issueMatchesSearch(issue({ norm_clause: "п. 4.4" }), "4.4")).toBe(true);
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

  it("filters by ИТЗ / СТО / СП stamp and lists unique keys", () => {
    const report = {
      issues: [
        issue({ rule_id: "A", norm_source: "СП 63", norm_clause: "8.1" }),
        issue({ rule_id: "B", norm_source: "СП 63", norm_clause: "8.1" }),
        issue({ rule_id: "C" }),
      ],
    } as unknown as ValidationReport;
    const stamped = filterTriageIssues(report, {
      severity: "all",
      hitlOnly: false,
      search: "",
      clause: "СП 63 · 8.1",
    });
    expect(stamped.map((row) => row.issue.rule_id)).toEqual(["A", "B"]);
    const missing = filterTriageIssues(report, {
      severity: "all",
      hitlOnly: false,
      search: "",
      clause: CLAUSE_FILTER_MISSING,
    });
    expect(missing.map((row) => row.issue.rule_id)).toEqual(["C"]);
    expect(uniqueClauseKeys(report.issues)).toEqual(["СП 63 · 8.1"]);
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

  it("hides engine capability rows and collapses HITL duplicates", () => {
    const rows = [
      { issue: issue({ rule_id: "REQ-FIRE-001" }), index: 0 },
      { issue: issue({ rule_id: "AEROBIM-CLASH-CAPABILITY" }), index: 1 },
      { issue: issue({ rule_id: HITL_RULE_ID, problem_zone: { sheet_id: "A-101", page_number: 1, x: 0, y: 0, width: 1, height: 1, element_guid: null } }), index: 2 },
      { issue: issue({ rule_id: HITL_RULE_ID, message: "other hitl", problem_zone: { sheet_id: "A-101", page_number: 1, x: 2, y: 2, width: 1, height: 1, element_guid: null } }), index: 3 },
      { issue: issue({ rule_id: "ADV-1", origin: "advisory" as const }), index: 4 },
    ];
    const documentRows = collapseDuplicateHitl(rows.filter((row) => isDocumentFinding(row.issue)));
    expect(documentRows.map((row) => row.issue.rule_id)).toEqual(["REQ-FIRE-001", HITL_RULE_ID]);
    expect(documentRows[1]?.index).toBe(2);
    expect(isAdvisoryIssue(rows[4]!.issue)).toBe(true);
    expect(isEngineCapabilityIssue(rows[1]!.issue)).toBe(true);
  });

  it("lands on the fire-rating GUID finding instead of an IfcSpace coverage note", () => {
    const space = issue({
      rule_id: "IDS-Space",
      message: "No elements found for entity IFCSPACE",
      element_guid: null,
    });
    const fire = issue({
      rule_id: "IDS-Wall Fire Rating Multi",
      message: "Pset_WallCommon.FireRating: expected REI60, observed REI30",
      property_name: "FireRating",
      element_guid: "1XYVUKGoDDbREfVxRKsHkl",
    });
    const reqFire = issue({
      rule_id: "REQ-FIRE-001",
      message: "Property Pset_WallCommon.FireRating does not match",
      element_guid: "other-guid",
    });
    expect(pickLandingIssueIndex([space, reqFire, fire])).toBe(2);
    expect(pickLandingIssueIndex([fire, space])).toBe(0);
  });

  it("prefers API layer over the local fallback and covers the ten volume classes", () => {
    expect(issueLayer(issue({ layer: "coverage_note", element_guid: "g1" }))).toBe("coverage_note");
    const fixtures: Array<{ layer: string; patch: Partial<ValidationIssue> }> = [
      {
        layer: "pack_finding",
        patch: {
          rule_id: "REQ-FIRE-001",
          message: "Property Pset_WallCommon.FireRating does not match the expected value",
          target_ref: "Wall-01",
        },
      },
      {
        layer: "advisory_candidate",
        patch: { rule_id: "AEROBIM-SPACE-EFFICIENCY-CANDIDATE", origin: "advisory" },
      },
      { layer: "service_record", patch: { rule_id: HITL_RULE_ID } },
      {
        layer: "coverage_note",
        patch: { rule_id: "REQ-FIRE-001", message: "No elements found for entity IFCWALL" },
      },
      { layer: "coverage_note", patch: { rule_id: "SAM-AR-001", message: "coverage" } },
      {
        layer: "coverage_note",
        patch: {
          rule_id: "REQ-FIRE-001",
          message: "Property Pset_WallCommon.FireRating does not match the expected value",
          element_guid: null,
          target_ref: null,
        },
      },
      { layer: "pack_finding", patch: { rule_id: "SAM-AR-020", element_guid: "g1" } },
      { layer: "service_record", patch: { rule_id: "AEROBIM-CLASH-CAPABILITY" } },
      { layer: "advisory_candidate", patch: { origin: "advisory", rule_id: "ADV-X" } },
      { layer: "coverage_note", patch: { rule_id: "AEROBIM-LOAD-FORMAT", element_guid: null } },
    ];
    for (const row of fixtures) {
      expect(issueLayer(issue(row.patch))).toBe(row.layer);
    }
  });
});
