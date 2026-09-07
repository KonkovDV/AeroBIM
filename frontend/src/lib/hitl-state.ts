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
  if (NORM_PACK_EVENT_TYPES.has(event.event_type)) {
    return false;
  }
  const fid = issue.finding_id?.trim() || null;
  const eventFid = event.finding_id?.trim() || null;
  if (fid !== null) {
    return eventFid === fid;
  }
  const rid = issue.rule_id?.trim() || null;
  const eventRid = event.issue_rule_id?.trim() || null;
  return rid !== null && eventRid === rid;
}

export function effectiveRemarkText(
  issue: ValidationIssue,
  events: readonly ReviewEventRow[],
): string {
  let latest = issue.review?.effective_text ?? issue.remark?.body ?? "";
  for (const event of events) {
    if (!eventMatchesIssue(event, issue)) {
      continue;
    }
    if (
      (event.event_type === "edited_remark" || event.event_type === "edited") &&
      event.note?.trim()
    ) {
      latest = event.note;
    }
  }
  return latest;
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

export function latestReviewSequence(
  events: readonly ReviewEventRow[],
  issue: ValidationIssue,
): number | null {
  let latest: number | null = null;
  for (const event of events) {
    if (!eventMatchesIssue(event, issue)) {
      continue;
    }
    if (typeof event.sequence_number === "number") {
      latest = event.sequence_number;
    }
  }
  return latest;
}

export function hitlOperationFingerprint(input: {
  reportId: string;
  findingId: string;
  eventType: string;
  note: string;
  previousState: string;
  expectedReviewVersion: number;
}): string {
  return [
    input.reportId,
    input.findingId,
    input.eventType,
    input.note,
    input.previousState,
    String(input.expectedReviewVersion),
  ].join("\0");
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
    sequence_number: typeof event.sequence_number === "number" ? event.sequence_number : null,
  };
}
