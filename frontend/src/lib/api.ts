import type { ReportListResponse, ValidationReport } from "./types";

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

export async function fetchReports(): Promise<ReportListResponse> {
  return readJson<ReportListResponse>(`${apiBaseUrl}/v1/reports`);
}

export async function fetchReport(reportId: string): Promise<ValidationReport> {
  return readJson<ValidationReport>(`${apiBaseUrl}/v1/reports/${reportId}`);
}

export async function fetchReportIfcSource(reportId: string): Promise<Uint8Array> {
  return readBytes(buildReportIfcSourceUrl(reportId));
}