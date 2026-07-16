import type { ReportListResponse, ValidationReport } from "./types";

export type ReportListFilters = {
  project?: string;
  discipline?: string;
  passed?: boolean;
};

const configuredBase = (import.meta.env.VITE_AEROBIM_API_BASE_URL as string | undefined)?.replace(
  /\/$/,
  ""
);
// Dev default: same-origin (Vite proxy injects bearer). Production: set VITE_AEROBIM_API_BASE_URL
// or terminate TLS at a reverse proxy that adds Authorization server-side.
const apiBaseUrl = configuredBase ?? (import.meta.env.DEV ? "" : "http://localhost:8080");
const useDevProxy = import.meta.env.DEV && !configuredBase;
const apiBearerToken = useDevProxy
  ? undefined
  : (import.meta.env.VITE_AEROBIM_API_BEARER_TOKEN as string | undefined)?.trim() || undefined;

function authHeaders(extra: Record<string, string> = {}): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...extra,
  };
  if (apiBearerToken) {
    headers.Authorization = `Bearer ${apiBearerToken}`;
  }
  return headers;
}

function throwForFailedResponse(response: Response): never {
  if (response.status === 401) {
    throw new Error(
      "Unauthorized (401): set VITE_AEROBIM_API_BEARER_TOKEN to match AEROBIM_API_BEARER_TOKEN (demo-only; token is public in the bundle)."
    );
  }
  if (response.status === 503) {
    throw new Error(
      "API unavailable (503): backend auth/config misconfigured outside development."
    );
  }
  throw new Error(`Request failed with ${response.status}: ${response.statusText}`);
}

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: authHeaders(),
  });

  if (!response.ok) {
    throwForFailedResponse(response);
  }

  return (await response.json()) as T;
}

async function readBytes(url: string): Promise<Uint8Array> {
  const response = await fetch(url, {
    headers: authHeaders({ Accept: "*/*" }),
  });
  if (!response.ok) {
    throwForFailedResponse(response);
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

export async function fetchDrawingAssetPreviewBlobUrl(reportId: string, assetId: string): Promise<string> {
  const bytes = await readBytes(buildDrawingAssetPreviewUrl(reportId, assetId));
  const blob = new Blob([bytes]);
  return URL.createObjectURL(blob);
}

export async function downloadExport(reportId: string, format: "json" | "html" | "bcf"): Promise<void> {
  const response = await fetch(buildExportUrl(reportId, format), {
    headers: authHeaders({ Accept: "*/*" }),
  });
  if (!response.ok) {
    throw new Error(`Export failed with ${response.status}: ${response.statusText}`);
  }
  const blob = await response.blob();
  const extension = format === "bcf" ? "bcfzip" : format;
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `aerobim-report-${reportId}.${extension}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export type ReviewEventType = "opened" | "accepted" | "rejected" | "edited_remark" | "triaged";

export async function postReviewEvent(
  reportId: string,
  body: {
    event_type: ReviewEventType;
    issue_rule_id?: string;
    actor?: string;
    note?: string;
    latency_ms?: number;
  },
): Promise<{ event: Record<string, unknown> }> {
  const response = await fetch(`${apiBaseUrl}/v1/reports/${reportId}/review-events`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Review event failed with ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as { event: Record<string, unknown> };
}

export async function uploadDocument(file: File): Promise<{
  upload_id: string;
  filename: string;
  path: string;
  size_bytes: number;
  content_type: string | null;
  object_key: string | null;
}> {
  const form = new FormData();
  form.append("file", file);
  const headers: Record<string, string> = {};
  if (apiBearerToken) {
    headers.Authorization = `Bearer ${apiBearerToken}`;
  }
  const response = await fetch(`${apiBaseUrl}/v1/uploads`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!response.ok) {
    throw new Error(`Upload failed with ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as {
    upload_id: string;
    filename: string;
    path: string;
    size_bytes: number;
    content_type: string | null;
    object_key: string | null;
  };
}
