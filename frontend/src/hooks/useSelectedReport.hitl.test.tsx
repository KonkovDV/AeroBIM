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

describe("D01 atomic decision", () => {
  it.each(["accepted", "rejected"] as const)(
    "persists the final draft in one %s event without an edited_remark append",
    async (eventType) => {
      const calls: Array<{ event_type: string; note?: string }> = [];
      api.postReviewEvent.mockImplementation(async (_id: string, body: { event_type: string; note?: string }) => {
        calls.push(body);
        return {
          event: {
            event_id: body.event_type,
            event_type: body.event_type,
            finding_id: "first",
            note: body.note ?? null,
            sequence_number: calls.length + 1,
            resulting_state: body.event_type,
          },
        };
      });
      const hook = renderHook(() => useSelectedReport("report"));
      await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
      act(() => hook.result.current.setRemarkDraft("expert rewrite"));
      await act(async () => {
        await hook.result.current.decideRemark(eventType, issue);
      });
      expect(calls).toHaveLength(1);
      expect(calls[0]).toMatchObject({ event_type: eventType, note: "expert rewrite" });
      expect(calls.some((call) => call.event_type === "edited_remark")).toBe(false);
      expect(hook.result.current.persistedHitlState).toBe(eventType);
      expect(hook.result.current.isDirty).toBe(false);
    },
  );

  it("requires final text for acceptance", async () => {
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    act(() => hook.result.current.setRemarkDraft("   "));
    await act(async () => {
      await hook.result.current.decideRemark("accepted", issue);
    });
    expect(api.postReviewEvent).not.toHaveBeenCalled();
    expect(hook.result.current.hitlRequestState).toBe("failed");
  });
});

describe("D02 persisted indicator", () => {
  it("restores accepted final text from history without a new decide call", async () => {
    api.fetchReviewEvents.mockResolvedValue({
      events: [
        { event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" },
        { event_id: "accepted", event_type: "accepted", finding_id: "first", sequence_number: 2, note: "expert rewrite", resulting_state: "accepted" },
      ],
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.hitlDecisionState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe("expert rewrite");
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
  it("reloads history on a decision 409 and keeps the typed draft", async () => {
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
      await hook.result.current.decideRemark("accepted", issue);
    });
    expect(api.postReviewEvent).toHaveBeenCalledTimes(1);
    expect(api.postReviewEvent.mock.calls[0][1]).toMatchObject({
      event_type: "accepted",
      note: "local draft",
    });
    expect(hook.result.current.conflictMessage).toBeTruthy();
    expect(hook.result.current.remarkDraft).toBe("local draft");
    expect(hook.result.current.reviewEvents.some((row) => row.event_id === "other")).toBe(true);
  });
});

describe("idle finding auto-open", () => {
  it("posts opened then one accepted decision with the final draft when history is empty", async () => {
    const calls: string[] = [];
    api.fetchReviewEvents.mockResolvedValue({ events: [], count: 0 });
    api.postReviewEvent.mockImplementation(async (_id: string, body: { event_type: string; note?: string }) => {
      calls.push(`${body.event_type}:${body.note ?? ""}`);
      return {
        event: {
          event_id: `${body.event_type}-${calls.length}`,
          event_type: body.event_type,
          finding_id: "first",
          note: body.note ?? null,
          sequence_number: calls.length,
          resulting_state: body.event_type === "opened" ? "opened" : "accepted",
        },
      };
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    await act(async () => {
      await hook.result.current.decideRemark("accepted", issue);
    });
    expect(calls).toEqual(["opened:", "accepted:machine"]);
    expect(hook.result.current.persistedHitlState).toBe("accepted");
  });
});
