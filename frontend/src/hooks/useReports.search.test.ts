/**
 * Поиск в списке отчётов: имя проекта и раздел, не только идентификаторы.
 */
import { describe, it, expect } from "vitest";
import type { ReportSummaryEntry } from "../lib/types";
import { reportMatchesQuery } from "./useReports";

function makeEntry(overrides: Partial<ReportSummaryEntry>): ReportSummaryEntry {
  return {
    report_id: "aaaa-1111",
    request_id: "req-aaaa",
    created_at: "2026-09-10T10:00:00Z",
    passed: false,
    issue_count: 3,
    project_name: null,
    discipline: null,
    ...overrides,
  };
}

describe("reportMatchesQuery", () => {
  it("находит по имени проекта", () => {
    const entry = makeEntry({ project_name: "ЖК Высота" });
    expect(reportMatchesQuery(entry, "высота")).toBe(true);
  });

  it("находит по разделу", () => {
    const entry = makeEntry({ discipline: "АР" });
    expect(reportMatchesQuery(entry, "АР")).toBe(true);
  });

  it("не зависит от регистра имени проекта", () => {
    const entry = makeEntry({ project_name: "Берег" });
    expect(reportMatchesQuery(entry, "БЕРЕГ")).toBe(true);
  });

  it("не срабатывает ложно при пустых имени и разделе", () => {
    const entry = makeEntry({ project_name: null, discipline: null });
    expect(reportMatchesQuery(entry, "samolet")).toBe(false);
  });

  it("по-прежнему находит по report_id", () => {
    const entry = makeEntry({ report_id: "deadbeef-cafe-0000-0000-000000000000" });
    expect(reportMatchesQuery(entry, "deadbeef")).toBe(true);
  });

  it("по-прежнему находит по request_id", () => {
    const entry = makeEntry({ request_id: "req-deadbeef" });
    expect(reportMatchesQuery(entry, "req-dead")).toBe(true);
  });

  it("пустой запрос считает все отчёты подходящими", () => {
    const entry = makeEntry({});
    expect(reportMatchesQuery(entry, "")).toBe(true);
    expect(reportMatchesQuery(entry, "   ")).toBe(true);
  });
});
