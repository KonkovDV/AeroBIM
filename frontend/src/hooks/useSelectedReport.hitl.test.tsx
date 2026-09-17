import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSelectedReport } from "./useSelectedReport";
import type { ValidationIssue } from "../lib/types";

const api = vi.hoisted(() => ({
  fetchReport: vi.fn(),
  fetchReviewEvents: vi.fn(),
  postReviewEvent: vi.fn(),
  ApiHttpError: class extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));
vi.mock("../lib/api", () => ({ ...api, ApiHttpError: api.ApiHttpError }));

const issue: ValidationIssue = {
  finding_id: "first",
  rule_id: "first",
  severity: "error",
  message: "first",
  category: "property",
  ifc_entity: null,
  target_ref: null,
  property_set: null,
  property_name: null,
  operator: null,
  expected_value: null,
  observed_value: null,
  unit: null,
  element_guid: null,
  problem_zone: null,
  remark: { title: "first", body: "machine" },
};

beforeEach(() => {
  vi.resetAllMocks();
  api.fetchReport.mockResolvedValue({ report_id: "report", issues: [issue] });
  api.fetchReviewEvents.mockResolvedValue({
    events: [{ event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" }],
  });
});

describe("D01 save then accept", () => {
  it("persists edited_remark before accepted and does not use draft as accept note", async () => {
    const calls: string[] = [];
    api.postReviewEvent.mockImplementation(async (_id: string, body: { event_type: string; note?: string }) => {
      calls.push(`${body.event_type}:${body.note ?? ""}`);
      return {
        event: {
          event_id: body.event_type,
          event_type: body.event_type,
          finding_id: "first",
          note: body.note ?? null,
          sequence_number: calls.length + 1,
          resulting_state: body.event_type === "edited_remark" ? "edited" : "accepted",
        },
      };
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    act(() => hook.result.current.setRemarkDraft("expert rewrite"));
    await act(async () => {
      await hook.result.current.decideRemark("accepted", issue);
    });
    expect(calls[0]).toBe("edited_remark:expert rewrite");
    expect(calls[1]).toBe("accepted:");
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.isDirty).toBe(false);
  });
});

describe("D02 persisted indicator", () => {
  it("restores accepted from history without a new decide call", async () => {
    api.fetchReviewEvents.mockResolvedValue({
      events: [
        { event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" },
        { event_id: "accepted", event_type: "accepted", finding_id: "first", sequence_number: 2, resulting_state: "accepted" },
      ],
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.hitlDecisionState).toBe("accepted");
    expect(api.postReviewEvent).not.toHaveBeenCalled();
    act(() => hook.result.current.changeDraft("typed after reload"));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.hitlDecisionState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe("typed after reload");
    expect(hook.result.current.hitlRequestState).toBe("idle");
  });
});

describe("D04 discard draft", () => {
  it("restores the last saved remark without posting", async () => {
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    act(() => hook.result.current.setRemarkDraft("unsaved dirty text"));
    expect(hook.result.current.isDirty).toBe(true);
    act(() => hook.result.current.discardRemarkDraft());
    expect(hook.result.current.remarkDraft).toBe("machine");
    expect(hook.result.current.isDirty).toBe(false);
    expect(api.postReviewEvent).not.toHaveBeenCalled();
  });
});

describe("D03 conflict keeps draft", () => {
  it("reloads history on 409 and keeps the typed draft", async () => {
    api.postReviewEvent.mockRejectedValue(new api.ApiHttpError(409, "conflict"));
    api.fetchReviewEvents
      .mockResolvedValueOnce({
        events: [{ event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" }],
      })
      .mockResolvedValueOnce({
        events: [
          { event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" },
          { event_id: "other", event_type: "edited_remark", finding_id: "first", sequence_number: 2, note: "other tab", resulting_state: "edited" },
        ],
      });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    act(() => hook.result.current.setRemarkDraft("local draft"));
    await act(async () => {
      await hook.result.current.saveRemarkEdit(issue);
    });
    expect(hook.result.current.conflictMessage).toBeTruthy();
    expect(hook.result.current.remarkDraft).toBe("local draft");
    expect(hook.result.current.reviewEvents.some((row) => row.event_id === "other")).toBe(true);
  });
});
