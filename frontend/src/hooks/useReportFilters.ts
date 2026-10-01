import { useCallback, useEffect, useState } from "react";
import type { ShareLinkState } from "../features/reports/ReportListPanel";
import {
  buildReportFilterShareLink,
  initialReportFilters,
  persistReportFilters,
  syncReportFiltersToUrl,
  type ReportFilterPreset,
} from "../lib/report-filters";

export function useReportFilters(selectedReportId: string | null) {
  const persisted = initialReportFilters();
  const [search, setSearch] = useState("");
  const [groupByProject, setGroupByProject] = useState(false);
  const [shareLinkState, setShareLinkState] = useState<ShareLinkState>("idle");
  const [projectFilter, setProjectFilter] = useState(persisted.project);
  const [disciplineFilter, setDisciplineFilter] = useState(persisted.discipline);
  const [statusFilter, setStatusFilter] = useState<"all" | "passed" | "failed">(persisted.status);

  useEffect(() => {
    const currentFilters = {
      project: projectFilter,
      discipline: disciplineFilter,
      status: statusFilter,
    };
    persistReportFilters(currentFilters);
    syncReportFiltersToUrl(currentFilters, selectedReportId);
    setShareLinkState("idle");
  }, [projectFilter, disciplineFilter, statusFilter, selectedReportId]);

  const applyPreset = useCallback((preset: ReportFilterPreset) => {
    setProjectFilter(preset.filters.project);
    setDisciplineFilter(preset.filters.discipline);
    setStatusFilter(preset.filters.status);
  }, []);

  const copyShareLink = useCallback(async () => {
    if (typeof window === "undefined" || !window.navigator.clipboard) {
      setShareLinkState("failed");
      return;
    }

    const link = buildReportFilterShareLink({
      project: projectFilter,
      discipline: disciplineFilter,
      status: statusFilter,
    });

    try {
      await window.navigator.clipboard.writeText(link);
      setShareLinkState("copied");
    } catch {
      setShareLinkState("failed");
    }
  }, [projectFilter, disciplineFilter, statusFilter]);

  return {
    search,
    setSearch,
    groupByProject,
    setGroupByProject,
    shareLinkState,
    projectFilter,
    setProjectFilter,
    disciplineFilter,
    setDisciplineFilter,
    statusFilter,
    setStatusFilter,
    applyPreset,
    copyShareLink,
  };
}
