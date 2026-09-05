import { useDeferredValue, useMemo } from "react";
import {
  buildViewerFocus,
  filterTriageIssues,
  findMatchingRequirements,
  type IndexedIssue,
  type TriageSeverityFilter,
  type ViewerFocus,
} from "../lib/issue-triage";
import type { ClashResult, ParsedRequirement, ValidationIssue, ValidationReport } from "../lib/types";

export type TriageView = {
  activeIssue: ValidationIssue | null;
  filteredIssues: IndexedIssue[];
  hitlRegionCount: number;
  activeClash: ClashResult | null;
  matchingRequirements: ParsedRequirement[];
  viewerFocus: ViewerFocus;
};

/** Derived triage slice. UI does not write summary.passed. */
export function useTriageView(
  selectedReport: ValidationReport | null,
  selectedIssueIndex: number,
  selectedClashIndex: number | null,
  filters: {
    severity: TriageSeverityFilter;
    hitlOnly: boolean;
    search: string;
    clause: string;
  },
): TriageView {
  const deferredSearch = useDeferredValue(filters.search);
  return useMemo(() => {
    const activeIssue =
      selectedReport && selectedReport.issues.length > 0
        ? selectedReport.issues[Math.min(selectedIssueIndex, selectedReport.issues.length - 1)]
        : null;
    const filteredIssues =
      selectedReport === null
        ? []
        : filterTriageIssues(selectedReport, {
            severity: filters.severity,
            hitlOnly: filters.hitlOnly,
            search: deferredSearch,
            clause: filters.clause,
          });
    const hitlRegionCount = selectedReport
      ? (selectedReport.drawing_regions ?? []).filter((region) => region.hitl_required === true).length
      : 0;
    const activeClash =
      selectedReport && selectedClashIndex !== null && selectedReport.clash_results.length > 0
        ? selectedReport.clash_results[
            Math.min(selectedClashIndex, selectedReport.clash_results.length - 1)
          ]
        : null;
    const matchingRequirements = selectedReport
      ? findMatchingRequirements(selectedReport, activeIssue)
      : [];
    const viewerFocus = buildViewerFocus(activeIssue, activeClash);
    return {
      activeIssue,
      filteredIssues,
      hitlRegionCount,
      activeClash,
      matchingRequirements,
      viewerFocus,
    };
  }, [
    selectedReport,
    selectedIssueIndex,
    selectedClashIndex,
    filters.severity,
    filters.hitlOnly,
    filters.clause,
    deferredSearch,
  ]);
}
