export const REPORT_FILTERS_STORAGE_KEY = "aerobim-report-filters-v1";
export const REPORT_FILTER_PRESETS_STORAGE_KEY = "aerobim-report-filter-presets-v1";

export type PersistedReportFilters = {
  project: string;
  discipline: string;
  status: "all" | "passed" | "failed";
};

export type PresetScope = "local" | "team";

export type ReportFilterPreset = {
  id: string;
  name: string;
  scope: PresetScope;
  filters: PersistedReportFilters;
};

export function normalizeStatus(value: string | null | undefined): "all" | "passed" | "failed" {
  return value === "passed" || value === "failed" ? value : "all";
}

export function normalizePresetScope(value: unknown, fallback: PresetScope = "local"): PresetScope {
  return value === "team" || value === "local" ? value : fallback;
}

export function readUrlReportId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const report = new URLSearchParams(window.location.search).get("report")?.trim();
  return report && /^[a-f0-9]{32}$/i.test(report) ? report.toLowerCase() : null;
}

export function readUrlReportFilters(): Partial<PersistedReportFilters> {
  if (typeof window === "undefined") {
    return {};
  }

  const params = new URLSearchParams(window.location.search);
  const project = params.get("project")?.trim();
  const discipline = params.get("discipline")?.trim();
  const status = params.get("status");

  return {
    project: project && project.length > 0 ? project : undefined,
    discipline: discipline && discipline.length > 0 ? discipline : undefined,
    status: status ? normalizeStatus(status) : undefined,
  };
}

export function readPersistedReportFilters(): PersistedReportFilters {
  if (typeof window === "undefined") {
    return { project: "", discipline: "", status: "all" };
  }

  try {
    const raw = window.localStorage.getItem(REPORT_FILTERS_STORAGE_KEY);
    if (!raw) {
      return { project: "", discipline: "", status: "all" };
    }
    const parsed = JSON.parse(raw) as Partial<PersistedReportFilters>;
    return {
      project: typeof parsed.project === "string" ? parsed.project : "",
      discipline: typeof parsed.discipline === "string" ? parsed.discipline : "",
      status: normalizeStatus(parsed.status),
    };
  } catch {
    return { project: "", discipline: "", status: "all" };
  }
}

export function initialReportFilters(): PersistedReportFilters {
  const persisted = readPersistedReportFilters();
  const fromUrl = readUrlReportFilters();

  return {
    project: fromUrl.project ?? persisted.project,
    discipline: fromUrl.discipline ?? persisted.discipline,
    status: fromUrl.status ?? persisted.status,
  };
}

export function persistReportFilters(filters: PersistedReportFilters): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(REPORT_FILTERS_STORAGE_KEY, JSON.stringify(filters));
}

export function readPersistedFilterPresets(): ReportFilterPreset[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(REPORT_FILTER_PRESETS_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as Array<Partial<ReportFilterPreset>>;
    return parsed
      .filter((preset) => typeof preset.name === "string" && typeof preset.id === "string" && preset.filters)
      .map((preset) => {
        const filters = preset.filters as Partial<PersistedReportFilters>;
        return {
          id: preset.id as string,
          name: preset.name as string,
          scope: normalizePresetScope((preset as { scope?: unknown }).scope, "local"),
          filters: {
            project: typeof filters.project === "string" ? filters.project : "",
            discipline: typeof filters.discipline === "string" ? filters.discipline : "",
            status: normalizeStatus(filters.status),
          },
        };
      });
  } catch {
    return [];
  }
}

export function persistFilterPresets(presets: ReportFilterPreset[]): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(REPORT_FILTER_PRESETS_STORAGE_KEY, JSON.stringify(presets));
}

export function withReportFilters(
  url: URL,
  filters: PersistedReportFilters,
  reportId?: string | null,
): URL {
  if (filters.project.trim()) {
    url.searchParams.set("project", filters.project.trim());
  } else {
    url.searchParams.delete("project");
  }

  if (filters.discipline.trim()) {
    url.searchParams.set("discipline", filters.discipline.trim());
  } else {
    url.searchParams.delete("discipline");
  }

  if (filters.status !== "all") {
    url.searchParams.set("status", filters.status);
  } else {
    url.searchParams.delete("status");
  }

  if (reportId) {
    url.searchParams.set("report", reportId);
  }

  return url;
}

export function syncReportFiltersToUrl(
  filters: PersistedReportFilters,
  reportId?: string | null,
): void {
  if (typeof window === "undefined") {
    return;
  }

  const url = withReportFilters(new URL(window.location.href), filters, reportId);

  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

export function buildReportFilterShareLink(filters: PersistedReportFilters): string {
  if (typeof window === "undefined") {
    return "";
  }

  return withReportFilters(new URL(window.location.href), filters).toString();
}
