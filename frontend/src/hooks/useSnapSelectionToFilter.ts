import { useEffect } from "react";
import { snapIssueIndexToVisible, type IndexedIssue } from "../lib/issue-triage";
import type { ValidationIssue } from "../lib/types";

/** Держит выбранную находку внутри видимого фильтра. Не пишет summary.passed. */
export function useSnapSelectionToFilter(
  filteredIssues: IndexedIssue[],
  selectedIssueIndex: number,
  selectIssue: (index: number, issue: ValidationIssue) => void,
): void {
  useEffect(() => {
    const nextIndex = snapIssueIndexToVisible(filteredIssues, selectedIssueIndex);
    if (nextIndex === null || nextIndex === selectedIssueIndex) {
      return;
    }
    const row = filteredIssues.find((item) => item.index === nextIndex);
    if (row) {
      selectIssue(row.index, row.issue);
    }
  }, [filteredIssues, selectedIssueIndex, selectIssue]);
}
