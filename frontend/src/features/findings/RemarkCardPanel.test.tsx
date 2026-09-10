import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RemarkCardPanel from "./RemarkCardPanel";
import type { ValidationIssue } from "../../lib/types";

const baseIssue: ValidationIssue = {
  rule_id: "FIRE-1",
  severity: "error",
  message: "FireRating mismatch.",
  ifc_entity: "IFCWALL",
  category: "ids",
  target_ref: null,
  property_set: "Pset_WallCommon",
  property_name: "FireRating",
  operator: "eq",
  expected_value: "REI60",
  observed_value: "REI30",
  unit: null,
  element_guid: "1XYVUKGoDDbREfVxRKsHkl",
  problem_zone: null,
  remark: { title: "Стена", body: "REI" },
  finding_id: "fid-1",
  source_id: "ids:FIRE-1",
  evidence_refs: ["ids:FIRE-1#wall"],
  storey_name: null,
  grid_axis: null,
  norm_source: "СП 2.13130",
  norm_clause: "5.4",
};

describe("RemarkCardPanel", () => {
  it("shows TZ fields and does not invent storey or axis", () => {
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(screen.getByText("СП 2.13130 · 5.4")).toBeTruthy();
    expect(screen.getAllByText("нет в индексе")).toHaveLength(3);
    expect(screen.getByText("Пункт ИТЗ / СТО / СП")).toBeTruthy();
    expect(screen.getByText("1XYVUKGoDDbREfVxRKsHkl")).toBeTruthy();
    expect(screen.getByText("fid-1")).toBeTruthy();
    expect(screen.getByText("ids:FIRE-1")).toBeTruthy();
    expect(screen.getByTestId("evidence-stepper")).toBeTruthy();
    expect(screen.getByTestId("review-history")).toBeTruthy();
    expect(screen.getByLabelText("Текст замечания").getAttribute("spellcheck")).toBe("true");
  });

  it("does not show the engine priority score in the visible title", () => {
    render(
      <RemarkCardPanel
        activeIssue={{
          ...baseIssue,
          remark: {
            title: "Замечание по модели: FireRating REI30 вместо REI60 [приоритет 40]",
            body: "REI",
            essence: "Стена без REI60",
          },
        }}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(screen.queryByText(/приоритет 40/)).toBeNull();
    expect(screen.getAllByText("Стена без REI60").length).toBeGreaterThan(0);
  });

  it("filters cached HITL events for the active finding", () => {
    render(
      <RemarkCardPanel
        reportId="r1"
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        reviewEvents={[
          {
            event_id: "e1",
            event_type: "opened",
            created_at: "2026-09-03T00:00:00Z",
            finding_id: "fid-1",
            issue_rule_id: "FIRE-1",
          },
          {
            event_id: "e2",
            event_type: "accepted",
            created_at: "2026-09-03T00:01:00Z",
            finding_id: "other",
            issue_rule_id: "OTHER",
          },
        ]}
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(screen.getByText(/открыто/)).toBeTruthy();
    expect(screen.queryByText(/подтверждено/)).toBeNull();
  });

  it("saves the remark draft on Ctrl+Enter from the editor", () => {
    const onSave = vi.fn();
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={onSave}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    const editor = screen.getByLabelText("Текст замечания");
    fireEvent.keyDown(editor, { key: "Enter" });
    expect(onSave).not.toHaveBeenCalled();
    fireEvent.keyDown(editor, { key: "Enter", ctrlKey: true });
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it("copies the element GUID from the remark card", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Копировать GUID" }));
    expect(writeText).toHaveBeenCalledWith("1XYVUKGoDDbREfVxRKsHkl");
    expect(await screen.findByText("GUID скопирован")).toBeTruthy();
  });

  it("drops the copied hint when another finding becomes active", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const { rerender } = render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Копировать GUID" }));
    expect(await screen.findByText("GUID скопирован")).toBeTruthy();
    rerender(
      <RemarkCardPanel
        activeIssue={{ ...baseIssue, element_guid: "2ABCUKGoDDbREfVxRKsHkl" }}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    // Подпись относится к конкретному GUID и не должна переживать смену элемента.
    expect(screen.queryByText("GUID скопирован")).toBeNull();
    expect(screen.getByText("2ABCUKGoDDbREfVxRKsHkl")).toBeTruthy();
  });

  it("disables save, accept and reject while a HITL write is in flight", () => {
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="saving"
        hitlDecisionState="idle"
        onDraftChange={() => undefined}
        onSave={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect((screen.getByRole("button", { name: "Сохраняем…" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Подтвердить замечание" }) as HTMLButtonElement).disabled).toBe(
      true,
    );
    expect((screen.getByRole("button", { name: "Отклонить замечание" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("does not save from Ctrl+Enter while decision history is still loading", () => {
    const onSave = vi.fn();
    render(
      <RemarkCardPanel
        activeIssue={baseIssue}
        remarkDraft="REI"
        remarkSaveState="idle"
        hitlDecisionState="idle"
        historyPending
        onDraftChange={() => undefined}
        onSave={onSave}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );
    expect(screen.getByText("Загружаем историю решений")).toBeTruthy();
    fireEvent.keyDown(screen.getByLabelText("Текст замечания"), { key: "Enter", ctrlKey: true });
    expect(onSave).not.toHaveBeenCalled();
    expect((screen.getByRole("button", { name: "Сохранить правку" }) as HTMLButtonElement).disabled).toBe(true);
  });
});