import type { ReportListResponse, ValidationReport } from "./types";

export type ReportListFilters = {
  project?: string;
  discipline?: string;
  passed?: boolean;
};

const apiBaseUrl = (import.meta.env.VITE_AEROBIM_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "http://localhost:8080";

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}: ${response.statusText}`);
  }

  return (await response.json()) as T;
}

async function readBytes(url: string): Promise<Uint8Array> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}: ${response.statusText}`);
  }
  return new Uint8Array(await response.arrayBuffer());
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export function buildExportUrl(reportId: string, format: "json" | "html" | "bcf"): string {
  return `${apiBaseUrl}/v1/reports/${reportId}/export/${format}`;
}

export function buildReportIfcSourceUrl(reportId: string): string {
  return `${apiBaseUrl}/v1/reports/${reportId}/source/ifc`;
}

export function buildDrawingAssetPreviewUrl(reportId: string, assetId: string): string {
  return `${apiBaseUrl}/v1/reports/${reportId}/drawing-assets/${assetId}/preview`;
}

export async function fetchReports(filters: ReportListFilters = {}): Promise<ReportListResponse> {
  const query = new URLSearchParams();
  if (filters.project) {
    query.set("project", filters.project);
  }
  if (filters.discipline) {
    query.set("discipline", filters.discipline);
  }
  if (filters.passed !== undefined) {
    query.set("passed", String(filters.passed));
  }
  const queryString = query.toString();
  const url = queryString ? `${apiBaseUrl}/v1/reports?${queryString}` : `${apiBaseUrl}/v1/reports`;
  return readJson<ReportListResponse>(url);
}

export async function fetchReport(reportId: string): Promise<ValidationReport> {
  return readJson<ValidationReport>(`${apiBaseUrl}/v1/reports/${reportId}`);
}

export async function fetchReportIfcSource(reportId: string): Promise<Uint8Array> {
  return readBytes(buildReportIfcSourceUrl(reportId));
}