import { useState } from "react";
import {
  CLAUSE_FILTER_ALL,
  type FindingGroupBy,
  type TriageSeverityFilter,
} from "../lib/issue-triage";

/** List-filter state for the expert finding pane. Not a router. */
export function useFindingFilters() {
  const [findingGroupBy, setFindingGroupBy] = useState<FindingGroupBy>("none");
  const [issueSeverityFilter, setIssueSeverityFilter] = useState<TriageSeverityFilter>("all");
  const [hitlOnlyFilter, setHitlOnlyFilter] = useState(false);
  const [issueSearch, setIssueSearch] = useState("");
  const [clauseFilter, setClauseFilter] = useState(CLAUSE_FILTER_ALL);
  return {
    findingGroupBy,
    setFindingGroupBy,
    issueSeverityFilter,
    setIssueSeverityFilter,
    hitlOnlyFilter,
    setHitlOnlyFilter,
    issueSearch,
    setIssueSearch,
    clauseFilter,
    setClauseFilter,
  };
}
