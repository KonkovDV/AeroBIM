import type { ReviewEventRow } from "./api";
import type { ValidationIssue } from "./types";

/** Mirrors backend ``review_state_machine._EVENT_TO_STATE``. */
const EVENT_TO_STATE: Record<string, string> = {
  drawing_region_escalated: "escalated",
  escalated: "escalated",
  opened: "opened",
  triaged: "opened",
  accepted: "accepted",
  rejected: "rejected",
  edited: "edited",
  edited_remark: "edited",
  waived: "waived",
  superseded: "superseded",
};

const NORM_PACK_EVENT_TYPES = new Set(["norm_rule_proposed", "norm_rule_edited"]);

export function eventMatchesIssue(event: ReviewEventRow, issue: ValidationIssue): boolean {
  if (event.finding_id && issue.finding_id) {
    return event.finding_id === issue.finding_id;
  }
  if (event.issue_rule_id) {
    return event.issue_rule_id === issue.rule_id;
  }
  return false;
}

export function latestHitlState(
  events: readonly ReviewEventRow[],
  issue: ValidationIssue,
): string | null {
  const fid = issue.finding_id?.trim() || null;
  const rid = issue.rule_id?.trim() || null;
  let latest: string | null = null;
  for (const event of events) {
    if (NORM_PACK_EVENT_TYPES.has(event.event_type)) {
      continue;
    }
    const eventFid = event.finding_id?.trim() || null;
    const eventRid = event.issue_rule_id?.trim() || null;
    if (fid !== null) {
      if (eventFid !== fid) {
        continue;
      }
    } else if (rid !== null) {
      if (eventRid !== rid) {
        continue;
      }
    }
    const fromField = event.resulting_state?.trim() || "";
    const mapped = EVENT_TO_STATE[event.event_type] ?? "";
    const state = fromField || mapped || null;
    if (state) {
      latest = state;
    }
  }
  return latest;
}

export function asReviewEventRow(event: Record<string, unknown>): ReviewEventRow | null {
  if (typeof event.event_id !== "string" || typeof event.event_type !== "string") {
    return null;
  }
  return {
    event_id: event.event_id,
    event_type: event.event_type,
    created_at: typeof event.created_at === "string" ? event.created_at : "",
    issue_rule_id: typeof event.issue_rule_id === "string" ? event.issue_rule_id : null,
    finding_id: typeof event.finding_id === "string" ? event.finding_id : null,
    note: typeof event.note === "string" ? event.note : null,
    actor: typeof event.actor === "string" ? event.actor : null,
    resulting_state: typeof event.resulting_state === "string" ? event.resulting_state : null,
    previous_state: typeof event.previous_state === "string" ? event.previous_state : null,
  };
}
