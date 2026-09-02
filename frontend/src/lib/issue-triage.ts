import type { ClashResult, ValidationIssue } from "./types";
import { UI_COPY } from "./ui-copy";

export const TRIAGE_BANDS = ["critical", "major", "minor", "negligible"] as const;
export type TriageBand = (typeof TRIAGE_BANDS)[number];

export type FindingGroupBy = "none" | "rule" | "storey" | "axis" | "discipline";

export type IndexedIssue = { issue: ValidationIssue; index: number };

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
  return `P${issue.priority} · AEROBIM_PRIORITY_PROFILE (severity × discipline × stage), not product accuracy`;
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
  return sentence || "no one-sentence essence";
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
