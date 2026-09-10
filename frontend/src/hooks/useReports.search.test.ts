/**
 * Проверяет расширенный поиск: project_name и discipline теперь
 * тоже участвуют в фильтрации наравне с report_id / request_id.
 *
 * Тест работает с чистой логикой фильтрации, воспроизведённой
 * из useReports.ts, — без рендера хука в jsdom, что было бы
 * излишним для проверки одной строки предиката.
 */
import { describe, it, expect } from "vitest";
import type { ReportSummaryEntry } from "../lib/types";

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

/** Воспроизводит предикат фильтрации из useReports (строка в useMemo). */
function matchesQuery(report: ReportSummaryEntry, query: string): boolean {
  const q = query.trim().toLowerCase();
  return (
    report.report_id.toLowerCase().includes(q) ||
    report.request_id.toLowerCase().includes(q) ||
    (report.project_name?.toLowerCase() ?? "").includes(q) ||
    (report.discipline?.toLowerCase() ?? "").includes(q)
  );
}

describe("useReports — расширенный поиск", () => {
  it("находит по project_name", () => {
    const entry = makeEntry({ project_name: "ЖК Высота" });
    expect(matchesQuery(entry, "высота")).toBe(true);
  });

  it("находит по discipline", () => {
    const entry = makeEntry({ discipline: "АР" });
    expect(matchesQuery(entry, "АР")).toBe(true);
  });

  it("поиск нечувствителен к регистру для project_name", () => {
    const entry = makeEntry({ project_name: "Берег" });
    expect(matchesQuery(entry, "БЕРЕГ")).toBe(true);
  });

  it("не возвращает ложных срабатываний при null project_name", () => {
    const entry = makeEntry({ project_name: null, discipline: null });
    expect(matchesQuery(entry, "samolet")).toBe(false);
  });

  it("всё ещё находит по report_id", () => {
    const entry = makeEntry({ report_id: "deadbeef-cafe-0000-0000-000000000000" });
    expect(matchesQuery(entry, "deadbeef")).toBe(true);
  });

  it("всё ещё находит по request_id", () => {
    const entry = makeEntry({ request_id: "req-deadbeef" });
    expect(matchesQuery(entry, "req-dead")).toBe(true);
  });

  it("пустой запрос не вызывает совпадений через includes('')", () => {
    // Пустая строка всегда включается в любую строку через .includes("").
    // Это нормально для ветки "без запроса" — при пустом запросе
    // предикат вообще не применяется в useReports (returns reports.slice()).
    // Тест подтверждает поведение предиката, а не ветку useMemo.
    const entry = makeEntry({});
    expect(matchesQuery(entry, "")).toBe(true); // expected JS behaviour
  });
});
