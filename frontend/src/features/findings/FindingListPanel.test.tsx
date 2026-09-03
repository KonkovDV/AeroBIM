import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FindingListPanel from "./FindingListPanel";
import type { ValidationIssue } from "../../lib/types";

function issue(ruleId: string, index: number): { issue: ValidationIssue; index: number } {
  return {
    index,
    issue: {
      rule_id: ruleId,
      severity: "error",
      message: `${ruleId} message`,
      ifc_entity: "IFCWALL",
      category: "ids",
      target_ref: null,
      property_set: null,
      property_name: null,
      operator: null,
      expected_value: null,
      observed_value: null,
      unit: null,
      element_guid: `guid-${index}`,
      problem_zone: null,
      remark: null,
    },
  };
}

describe("FindingListPanel", () => {
  it("gives the selected card tabIndex 0 and others -1", () => {
    render(
      <FindingListPanel
        issues={[issue("R1", 0), issue("R2", 1)]}
        totalIssueCount={2}
        selectedIssueIndex={1}
        issueSeverityFilter="all"
        hitlOnlyFilter={false}
        hitlRegionCount={0}
        groupBy="none"
        onSeverityChange={() => undefined}
        onHitlOnlyChange={() => undefined}
        onGroupByChange={() => undefined}
        onSelectIssue={() => undefined}
      />,
    );
    const buttons = screen.getAllByRole("button");
    const cards = buttons.filter((button) => button.className.includes("issue-card"));
    expect(cards).toHaveLength(2);
    expect(cards[0]?.tabIndex).toBe(-1);
    expect(cards[1]?.tabIndex).toBe(0);
    expect(cards[1]?.className).toMatch(/active/);
  });
});
