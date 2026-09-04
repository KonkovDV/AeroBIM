import { describe, expect, it } from "vitest";
import { asReviewEventRow, eventMatchesIssue, latestHitlState } from "./hitl-state";
import type { ReviewEventRow } from "./api";
import type { ValidationIssue } from "./types";

const issue: ValidationIssue = {
  rule_id: "FIRE-1",
  severity: "error",
  message: "mismatch",
  ifc_entity: "IFCWALL",
  category: "ids",
  target_ref: null,
  property_set: null,
  property_name: null,
  operator: null,
  expected_value: null,
  observed_value: null,
  unit: null,
  element_guid: null,
  problem_zone: null,
  remark: null,
  finding_id: "fid-1",
};

function row(overrides: Partial<ReviewEventRow>): ReviewEventRow {
  return {
    event_id: "e1",
    event_type: "opened",
    created_at: "2026-01-01T00:00:00Z",
    issue_rule_id: "FIRE-1",
    finding_id: "fid-1",
    ...overrides,
  };
}

describe("hitl-state", () => {
  it("matches by finding_id when both sides have it", () => {
    expect(eventMatchesIssue(row({}), issue)).toBe(true);
    expect(eventMatchesIssue(row({ finding_id: "other" }), issue)).toBe(false);
  });

  it("walks resulting_state and maps edited_remark to edited", () => {
    const events = [
      row({ event_id: "a", event_type: "opened", resulting_state: "opened" }),
      row({ event_id: "b", event_type: "edited_remark", resulting_state: "edited" }),
    ];
    expect(latestHitlState(events, issue)).toBe("edited");
  });

  it("ignores other findings", () => {
    const events = [
      row({ finding_id: "fid-2", event_type: "accepted", resulting_state: "accepted" }),
    ];
    expect(latestHitlState(events, issue)).toBeNull();
  });

  it("parses a posted event payload", () => {
    expect(
      asReviewEventRow({
        event_id: "x",
        event_type: "accepted",
        resulting_state: "accepted",
        created_at: "t",
      }),
    ).toMatchObject({ event_id: "x", resulting_state: "accepted" });
    expect(asReviewEventRow({ event_type: "opened" })).toBeNull();
  });
});
