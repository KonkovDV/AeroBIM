import type { ClashResult, DrawingRegionRef, ValidationIssue, ValidationReport } from "./types";
import { UI_COPY } from "./ui-copy";

export const TRIAGE_BANDS = ["critical", "major", "minor", "negligible"] as const;
export type TriageBand = (typeof TRIAGE_BANDS)[number];

export type FindingGroupBy = "none" | "rule" | "storey" | "axis" | "discipline";

export type IndexedIssue = { issue: ValidationIssue; index: number };

/** Правило региона листа, требующего эксперта (HITL). Машинный идентификатор API. */
export const HITL_RULE_ID = "AEROBIM-DRAWING-REGION-HITL";

export type TriageSeverityFilter = "all" | "error" | "warning" | "info";

export type TriageFilter = {
  severity: TriageSeverityFilter;
  hitlOnly: boolean;
  search: string;
};

/** Текстовый поиск по находке: правило, суть, GUID, цель, этаж, ось, категория. */
export function issueMatchesSearch(issue: ValidationIssue, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }
  const haystack = [
    issue.rule_id,
    issue.message,
    issue.category,
    issue.element_guid,
    issue.target_ref,
    issue.storey_name,
    issue.grid_axis,
    issue.finding_id,
    issue.remark?.title,
  ]
    .filter((part): part is string => Boolean(part && part.trim()))
    .join("\n")
    .toLowerCase();
  return haystack.includes(needle);
}

/**
 * Единая воронка триажа списка находок: серьёзность → HITL → поиск →
 * стабильная сортировка по приоритету (ничьи держат порядок отчёта).
 * Чистая функция: App.tsx только передаёт состояние фильтров.
 */
export function filterTriageIssues(
  report: ValidationReport,
  filter: TriageFilter,
): IndexedIssue[] {
  return report.issues
    .map((issue, index) => ({ issue, index }))
    .filter(({ issue }) => {
      if (filter.severity !== "all" && issue.severity !== filter.severity) {
        return false;
      }
      if (filter.hitlOnly && issue.rule_id !== HITL_RULE_ID) {
        return false;
      }
      return issueMatchesSearch(issue, filter.search);
    })
    .sort((a, b) => (b.issue.priority ?? 0) - (a.issue.priority ?? 0));
}

/** HITL-регион кликабелен; штамп и титул — только разметка, не выбор находки. */
export function isHitlClickableRegion(region: DrawingRegionRef): boolean {
  if (region.hitl_required !== true) {
    return false;
  }
  const role = (region.layout_role ?? "content").toLowerCase();
  return role !== "stamp" && role !== "title_block" && role !== "title";
}

/**
 * Связь регион → находка только по листу. DrawingRegionRef не несёт finding_id —
 * не выдумываем GUID и не матчим по bbox.
 */
export function findIssueForDrawingRegion(
  issues: IndexedIssue[],
  region: DrawingRegionRef,
): IndexedIssue | null {
  const sheet = region.sheet_id.trim();
  if (!sheet) {
    return null;
  }
  const onSheet = issues.filter(({ issue }) => issue.problem_zone?.sheet_id === sheet);
  const hitl = onSheet.find(({ issue }) => issue.rule_id === HITL_RULE_ID);
  return hitl ?? onSheet[0] ?? null;
}

/** Deterministic clash triage band carried in evidence_refs (backend Wave B). */
export function triageBand(issue: ValidationIssue): TriageBand | null {
  for (const ref of issue.evidence_refs ?? []) {
    if (ref.startsWith("triage:band=")) {
      const band = ref.slice("triage:band=".length);
      if ((TRIAGE_BANDS as readonly string[]).includes(band)) {
        return band as TriageBand;
      }
    }
  }
  return null;
}

export function spatialOrMissing(value: string | null | undefined): string {
  const text = value?.trim();
  return text ? text : "нет в индексе";
}

export function findingGroupKey(issue: ValidationIssue, groupBy: FindingGroupBy): string {
  if (groupBy === "rule") {
    return issue.rule_id;
  }
  if (groupBy === "storey") {
    return spatialOrMissing(issue.storey_name);
  }
  if (groupBy === "axis") {
    return spatialOrMissing(issue.grid_axis);
  }
  if (groupBy === "discipline") {
    return spatialOrMissing(issue.category);
  }
  return "";
}

export function groupFindings(
  rows: IndexedIssue[],
  groupBy: FindingGroupBy,
): Array<{ key: string; rows: IndexedIssue[] }> {
  if (groupBy === "none") {
    return [{ key: "", rows }];
  }
  const map = new Map<string, IndexedIssue[]>();
  for (const row of rows) {
    const key = findingGroupKey(row.issue, groupBy);
    const existing = map.get(key);
    if (existing) {
      existing.push(row);
    } else {
      map.set(key, [row]);
    }
  }
  return Array.from(map.entries()).map(([key, grouped]) => ({ key, rows: grouped }));
}

export function priorityCaption(issue: ValidationIssue): string | null {
  if (typeof issue.priority !== "number" || issue.priority <= 0) {
    return null;
  }
  return `P${issue.priority} · профиль AEROBIM_PRIORITY_PROFILE (серьёзность × раздел × стадия), не точность продукта`;
}

export function clauseLine(issue: ValidationIssue): string {
  const fromRemark = issue.remark?.clause_cite?.trim();
  if (fromRemark) {
    return fromRemark;
  }
  const parts = [issue.norm_source, issue.norm_edition, issue.norm_clause].filter(
    (part): part is string => Boolean(part && part.trim()),
  );
  if (parts.length > 0) {
    return parts.join(" · ");
  }
  return "в записи нет пункта нормы — обязательное поле ТЗ, не украшение";
}

export function essenceLine(issue: ValidationIssue): string {
  const fromRemark = issue.remark?.essence?.trim();
  if (fromRemark) {
    return fromRemark;
  }
  const title = issue.remark?.title?.trim();
  if (title) {
    return title;
  }
  const message = issue.message.trim();
  const sentence = message.split(/(?<=[.!?])\s+/)[0];
  return sentence || "нет одной фразы сути";
}

export type ViewerFocus = {
  mode: "none" | "issue" | "clash";
  guids: string[];
  heading: string;
  detail: string;
};

export function buildViewerFocus(
  activeIssue: ValidationIssue | null,
  activeClash: ClashResult | null,
): ViewerFocus {
  if (activeClash !== null) {
    const guids = [
      ...new Set(
        [activeClash.element_a_guid, activeClash.element_b_guid].filter((guid) => guid.length > 0),
      ),
    ];
    return {
      mode: "clash",
      guids,
      heading: UI_COPY.spatialClashHeading(activeClash.clash_type),
      detail: UI_COPY.spatialClashDetail(guids.length),
    };
  }

  if (activeIssue?.element_guid) {
    return {
      mode: "issue",
      guids: [activeIssue.element_guid],
      heading: activeIssue.rule_id,
      detail: UI_COPY.spatialIssueDetail(activeIssue.element_guid),
    };
  }

  return {
    mode: "none",
    guids: [],
    heading: UI_COPY.spatialNone,
    detail: UI_COPY.spatialNoneDetail,
  };
}
