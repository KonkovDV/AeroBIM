import type {
  ClashResult,
  DrawingRegionRef,
  FindingLayer,
  ParsedRequirement,
  ValidationIssue,
  ValidationReport,
} from "./types";
import { UI_COPY } from "./ui-copy";

export const TRIAGE_BANDS = ["critical", "major", "minor", "negligible"] as const;
export type TriageBand = (typeof TRIAGE_BANDS)[number];

export type FindingGroupBy = "none" | "rule" | "storey" | "axis" | "discipline" | "clause";

/** Sentinel for the clause filter: show every finding. */
export const CLAUSE_FILTER_ALL = "all";
/** Sentinel: finding has no ИТЗ / СТО / СП stamp. */
export const CLAUSE_FILTER_MISSING = "";

export type IndexedIssue = { issue: ValidationIssue; index: number };

const HITL_AND_CAPABILITY = new Set([
  "AEROBIM-DRAWING-REGION-HITL",
  "AEROBIM-CLASH-CAPABILITY",
  "AEROBIM-IDS-CAPABILITY",
  "AEROBIM-UNIT-SCALE",
]);

/** Правило региона листа, требующего эксперта (HITL). Машинный идентификатор API. */
export const HITL_RULE_ID = "AEROBIM-DRAWING-REGION-HITL";

export type TriageSeverityFilter = "all" | "error" | "warning" | "info";

export type TriageFilter = {
  severity: TriageSeverityFilter;
  hitlOnly: boolean;
  search: string;
  /** `all` | empty (нет пункта) | exact clauseFilterKey. Default `all`. */
  clause?: string;
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
    issue.norm_source,
    issue.norm_edition,
    issue.norm_clause,
    issue.remark?.clause_cite,
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
      const clauseWanted = filter.clause ?? CLAUSE_FILTER_ALL;
      if (clauseWanted !== CLAUSE_FILTER_ALL && clauseFilterKey(issue) !== clauseWanted) {
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
  return text ? text : UI_COPY.spatialMissing;
}

/**
 * Если выбранная находка скрыта фильтром — перейти на первую видимую.
 * Пустой список не сдвигает выбор (карточка замечания остаётся).
 */
export function snapIssueIndexToVisible(
  filtered: IndexedIssue[],
  selectedIndex: number,
): number | null {
  if (filtered.length === 0) {
    return null;
  }
  if (filtered.some((row) => row.index === selectedIndex)) {
    return selectedIndex;
  }
  return filtered[0]?.index ?? null;
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
  if (groupBy === "clause") {
    const key = clauseFilterKey(issue);
    return key === CLAUSE_FILTER_MISSING ? UI_COPY.clauseMissing : key;
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
  return `P${issue.priority} · серьёзность × раздел × стадия, не точность продукта`;
}

const CATEGORY_LABELS: Record<string, string> = {
  "ids-validation": "IDS",
  ids: "IDS",
  "ifc-validation": "модель",
  "drawing-validation": "чертёж",
  "cross-document": "документы",
  spatial: "пространство",
};

export function findingCategoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

/** Заголовок строки списка: русская суть, не сырой английский message. */
export function findingListTitle(issue: ValidationIssue): string {
  const essence = issue.remark?.essence?.trim();
  if (essence && !essence.startsWith("[")) {
    return essence;
  }
  const title = issue.remark?.title?.trim();
  if (title) {
    const colon = title.indexOf(": ");
    const rest = colon >= 0 ? title.slice(colon + 2).replace(/\s*\[приоритет[^\]]*\]\s*$/u, "").trim() : title;
    if (rest && !rest.startsWith("[")) {
      return rest;
    }
  }
  return issue.message;
}

const ENGINE_CAPABILITY_RULES = new Set([
  "AEROBIM-CLASH-CAPABILITY",
  "AEROBIM-IDS-CAPABILITY",
  "AEROBIM-UNIT-SCALE",
]);

export function isEngineCapabilityIssue(issue: ValidationIssue): boolean {
  return ENGINE_CAPABILITY_RULES.has(issue.rule_id);
}

/** API ``layer`` wins; fallback mirrors backend volume→layer mapping. */
export function issueLayer(issue: ValidationIssue): FindingLayer {
  if (issue.layer) {
    return issue.layer;
  }
  return classifyFindingLayerFallback(issue);
}

function classifyFindingLayerFallback(issue: ValidationIssue): FindingLayer {
  if (issue.origin === "advisory" || issue.rule_id === "AEROBIM-SPACE-EFFICIENCY-CANDIDATE") {
    return "advisory_candidate";
  }
  if (HITL_AND_CAPABILITY.has(issue.rule_id) || isEngineCapabilityIssue(issue)) {
    return "service_record";
  }
  const message = issue.message ?? "";
  if (
    message.includes("No elements found for entity") ||
    message.includes("was not found on any") ||
    message.includes("is missing on") ||
    issue.rule_id.startsWith("SAM-AR-") && issue.rule_id !== "SAM-AR-020"
  ) {
    return "coverage_note";
  }
  if (issue.element_guid || issue.target_ref || issue.problem_zone?.sheet_id) {
    return "pack_finding";
  }
  return "coverage_note";
}

export function isAdvisoryIssue(issue: ValidationIssue): boolean {
  return issue.origin === "advisory";
}

export function isDocumentFinding(issue: ValidationIssue): boolean {
  return !isEngineCapabilityIssue(issue) && !isAdvisoryIssue(issue);
}

function looksLikeFireRating(issue: ValidationIssue): boolean {
  const haystack = `${issue.rule_id}\n${issue.property_name ?? ""}\n${issue.message}`;
  return /fire\s*rating|firerating|req-fire-001/i.test(haystack);
}

/**
 * First issue the expert should see after a report loads.
 * Coverage notes (IfcSpace absent, etc.) stay in the list; they must not
 * steal the landing from the IDS fire-rating example on the mentor fixture.
 */
export function pickLandingIssueIndex(issues: readonly ValidationIssue[]): number {
  if (issues.length === 0) {
    return 0;
  }
  const idsWall = issues.findIndex(
    (issue) => /ids-wall\s+fire\s+rating/i.test(issue.rule_id) && Boolean(issue.element_guid),
  );
  if (idsWall >= 0) {
    return idsWall;
  }
  const fireWithGuid = issues.findIndex(
    (issue) => looksLikeFireRating(issue) && Boolean(issue.element_guid),
  );
  if (fireWithGuid >= 0) {
    return fireWithGuid;
  }
  const fire = issues.findIndex((issue) => looksLikeFireRating(issue));
  if (fire >= 0) {
    return fire;
  }
  const guided = issues.findIndex(
    (issue) => isDocumentFinding(issue) && Boolean(issue.element_guid),
  );
  if (guided >= 0) {
    return guided;
  }
  const document = issues.findIndex((issue) => isDocumentFinding(issue));
  return document >= 0 ? document : 0;
}

/** Повторы HITL на одном листе — одна строка; индекс в отчёте не сдвигается. */
export function collapseDuplicateHitl(rows: IndexedIssue[]): IndexedIssue[] {
  const seen = new Set<string>();
  const out: IndexedIssue[] = [];
  for (const row of rows) {
    if (row.issue.rule_id !== HITL_RULE_ID) {
      out.push(row);
      continue;
    }
    const sheet = row.issue.problem_zone?.sheet_id?.trim() || row.issue.message;
    if (seen.has(sheet)) {
      continue;
    }
    seen.add(sheet);
    out.push(row);
  }
  return out;
}

export function clauseLine(issue: ValidationIssue): string {
  const key = clauseFilterKey(issue);
  if (key !== CLAUSE_FILTER_MISSING) {
    return key;
  }
  return UI_COPY.clauseMissingCard;
}

/** Stamp used for filter/group. Empty string = нет пункта. Does not invent from OCR. */
export function clauseFilterKey(issue: ValidationIssue): string {
  const fromRemark = issue.remark?.clause_cite?.trim();
  if (fromRemark) {
    return fromRemark;
  }
  const parts = [issue.norm_source, issue.norm_edition, issue.norm_clause].filter(
    (part): part is string => Boolean(part && part.trim()),
  );
  return parts.join(" · ");
}

export function uniqueClauseKeys(issues: ValidationIssue[]): string[] {
  const keys = new Set<string>();
  for (const issue of issues) {
    const key = clauseFilterKey(issue);
    if (key !== CLAUSE_FILTER_MISSING) {
      keys.add(key);
    }
  }
  return [...keys].sort((a, b) => a.localeCompare(b, "ru"));
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

/** Требования, связанные с выбранной находкой по rule_id. */
export function findMatchingRequirements(
  report: ValidationReport,
  issue: ValidationIssue | null,
): ParsedRequirement[] {
  if (issue === null) {
    return [...report.requirements];
  }
  return report.requirements.filter((requirement) => requirement.rule_id === issue.rule_id);
}
