import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSelectedReport } from "./useSelectedReport";
import type { ValidationIssue } from "../lib/types";

const api = vi.hoisted(() => ({
  fetchReport: vi.fn(), fetchReviewEvents: vi.fn(), postReviewEvent: vi.fn(),
}));
vi.mock("../lib/api", () => ({ ...api, ApiHttpError: class extends Error {} }));
const issues = ["first", "second"].map((id): ValidationIssue => ({
  finding_id: id, rule_id: id, severity: "error", message: id, category: "property",
  ifc_entity: null, target_ref: null, property_set: null, property_name: null,
  operator: null, expected_value: null, observed_value: null, unit: null,
  element_guid: null, problem_zone: null, remark: { title: id, body: id },
}));
const edited = (note: string, sequence = 2) => ({ event: {
  event_id: `edit-${sequence}`, event_type: "edited_remark", finding_id: "first",
  note, sequence_number: sequence,
} });

async function loadEditor() {
  const hook = renderHook(() => useSelectedReport("report"));
  await waitFor(() => expect(hook.result.current.selectedReport).not.toBeNull());
  await waitFor(() => expect(hook.result.current.historyPending).toBe(false));
  return hook;
}

beforeEach(() => {
  vi.resetAllMocks();
  api.fetchReport.mockResolvedValue({ report_id: "report", issues });
  api.fetchReviewEvents.mockResolvedValue({ events: [{
    event_id: "opened", event_type: "opened", finding_id: "first", sequence_number: 1,
  }] });
});

describe("remark save snapshots", () => {
  it("keeps newer typing dirty after an older save completes", async () => {
    let finish!: (value: ReturnType<typeof edited>) => void;
    api.postReviewEvent.mockReturnValue(new Promise((resolve) => { finish = resolve; }));
    const { result } = await loadEditor();
    act(() => result.current.setRemarkDraft("submitted"));
    let saving!: Promise<boolean>;
    act(() => { saving = result.current.saveRemarkEdit(issues[0]); });
    act(() => {
      result.current.setRemarkDraft("newer");
      result.current.setRemarkSaveState("idle");
    });
    await act(async () => {
      finish(edited("submitted"));
      expect(await saving).toBe(false);
    });
    expect(result.current.remarkDraft).toBe("newer");
    expect(result.current.remarkSaveState).toBe("idle");
    expect(result.current.isDirty).toBe(true);
    act(() => result.current.selectIssue(1, issues[1]));
    expect(result.current.pendingSelect?.index).toBe(1);
    const leave = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(leave);
    expect(leave.defaultPrevented).toBe(true);

    api.postReviewEvent.mockResolvedValue(edited("newer", 3));
    await act(async () => { expect(await result.current.saveRemarkEdit(issues[0])).toBe(true); });
    expect(result.current.isDirty).toBe(false);
    expect(result.current.remarkSaveState).toBe("saved");
  });

  it("derives dirty state from persisted text, not an old saved flag", async () => {
    api.postReviewEvent.mockResolvedValue(edited("submitted"));
    const { result } = await loadEditor();
    act(() => result.current.setRemarkDraft("submitted"));
    await act(async () => { await result.current.saveRemarkEdit(issues[0]); });
    expect(result.current.isDirty).toBe(false);
    act(() => result.current.setRemarkDraft("unsaved"));
    expect(result.current.isDirty).toBe(true);
    act(() => result.current.selectIssue(1, issues[1]));
    expect(result.current.selectedIssueIndex).toBe(0);
    expect(result.current.pendingSelect?.index).toBe(1);
    const leave = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(leave);
    expect(leave.defaultPrevented).toBe(true);
  });
});
