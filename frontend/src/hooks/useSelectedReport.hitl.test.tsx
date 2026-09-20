import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSelectedReport } from "./useSelectedReport";
import type { ValidationIssue } from "../lib/types";

const FINAL_REMARK_NOTE_PREFIX = "aerobim:final-remark:v1\n";

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
    "persists and decodes the exact final draft in one %s event without an edited_remark append",
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
      const exact = "  expert rewrite\nline 2  ";
      act(() => hook.result.current.setRemarkDraft(exact));
      await act(async () => {
        await hook.result.current.decideRemark(eventType, issue);
      });
      expect(calls).toHaveLength(1);
      expect(calls[0]).toMatchObject({
        event_type: eventType,
        note: `${FINAL_REMARK_NOTE_PREFIX}${exact}`,
      });
      expect(calls.some((call) => call.event_type === "edited_remark")).toBe(false);
      expect(hook.result.current.persistedHitlState).toBe(eventType);
      expect(hook.result.current.remarkDraft).toBe(exact);
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
  it("restores accepted exact final text from an enveloped history note", async () => {
    const exact = "  expert rewrite\nline 2  ";
    api.fetchReviewEvents.mockResolvedValue({
      events: [
        { event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" },
        { event_id: "accepted", event_type: "accepted", finding_id: "first", sequence_number: 2, note: `${FINAL_REMARK_NOTE_PREFIX}${exact}`, resulting_state: "accepted" },
      ],
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.hitlDecisionState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe(exact);
    expect(api.postReviewEvent).not.toHaveBeenCalled();
    act(() => hook.result.current.changeDraft("typed after reload"));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.hitlDecisionState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe("typed after reload");
    expect(hook.result.current.hitlRequestState).toBe("idle");
  });

  it("treats a plain accepted note as a legacy comment and keeps the prior edit", async () => {
    api.fetchReviewEvents.mockResolvedValue({
      events: [
        { event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1, resulting_state: "opened" },
        { event_id: "edited", event_type: "edited_remark", finding_id: "first", sequence_number: 2, note: "prior edit", resulting_state: "edited" },
        { event_id: "accepted", event_type: "accepted", finding_id: "first", sequence_number: 3, note: "legacy decision comment", resulting_state: "accepted" },
      ],
    });
    const hook = renderHook(() => useSelectedReport("report"));
    await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe("prior edit");
    expect(hook.result.current.isDirty).toBe(false);
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
      note: `${FINAL_REMARK_NOTE_PREFIX}local draft`,
    });
    expect(hook.result.current.conflictMessage).toBeTruthy();
    expect(hook.result.current.remarkDraft).toBe("local draft");
    expect(hook.result.current.reviewEvents.some((row) => row.event_id === "other")).toBe(true);
  });
});

describe("idle finding auto-open", () => {
  it("posts opened then one enveloped accepted decision with no edited_remark", async () => {
    const calls: Array<{ event_type: string; note?: string }> = [];
    api.fetchReviewEvents.mockResolvedValue({ events: [], count: 0 });
    api.postReviewEvent.mockImplementation(async (_id: string, body: { event_type: string; note?: string }) => {
      calls.push(body);
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
    expect(calls).toHaveLength(2);
    expect(calls[0]).toMatchObject({ event_type: "opened" });
    expect(calls[1]).toMatchObject({
      event_type: "accepted",
      note: `${FINAL_REMARK_NOTE_PREFIX}machine`,
    });
    expect(calls.filter((call) => call.event_type === "accepted")).toHaveLength(1);
    expect(calls.some((call) => call.event_type === "edited_remark")).toBe(false);
    expect(hook.result.current.persistedHitlState).toBe("accepted");
    expect(hook.result.current.remarkDraft).toBe("machine");
    expect(hook.result.current.isDirty).toBe(false);
  });
});
