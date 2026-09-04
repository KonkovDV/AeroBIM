import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
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

  it("shows storey and axis on the card or нет в индексе", () => {
    render(
      <FindingListPanel
        issues={[
          {
            ...issue("R1", 0),
            issue: {
              ...issue("R1", 0).issue,
              storey_name: "3 этаж",
              grid_axis: "А",
            },
          },
          issue("R2", 1),
        ]}
        totalIssueCount={2}
        selectedIssueIndex={0}
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
    const locations = screen.getAllByTestId("issue-location");
    expect(locations[0]?.textContent).toMatch(/эт\. 3 этаж/);
    expect(locations[0]?.textContent).toMatch(/ос\. А/);
    expect(locations[1]?.textContent).toMatch(/эт\. нет в индексе/);
    expect(locations[1]?.textContent).toMatch(/ос\. нет в индексе/);
  });

  it("exposes the clause filter and shows the stamp on the card", () => {
    const onClauseChange = vi.fn();
    render(
      <FindingListPanel
        issues={[
          {
            ...issue("R1", 0),
            issue: {
              ...issue("R1", 0).issue,
              norm_source: "СП 63",
              norm_clause: "8.1",
            },
          },
        ]}
        totalIssueCount={1}
        selectedIssueIndex={0}
        issueSeverityFilter="all"
        hitlOnlyFilter={false}
        hitlRegionCount={0}
        groupBy="none"
        clauseFilter="all"
        clauseOptions={["СП 63 · 8.1"]}
        onSeverityChange={() => undefined}
        onHitlOnlyChange={() => undefined}
        onGroupByChange={() => undefined}
        onClauseChange={onClauseChange}
        onSelectIssue={() => undefined}
      />,
    );
    expect(screen.getByTestId("issue-clause").textContent).toMatch(/СП 63/);
    expect(screen.getByTestId("clause-filter")).toBeTruthy();
  });
});
