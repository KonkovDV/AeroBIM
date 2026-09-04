import type { ReportListResponse, ValidationReport } from "./types";
import type { AnalyzeSubmitBody } from "./pack-draft";

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
// Never default production builds to http://localhost:8080 (RT C17).
const apiBaseUrl = configuredBase ?? "";
const useDevProxy = import.meta.env.DEV && !configuredBase;
// Never embed a bearer token in client bundles (RTATOM-F02 / POST-05).
// Dev auth is injected only by the Vite loopback proxy (see vite.config.ts).
const apiBearerToken: string | undefined = undefined;

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
      import.meta.env.PROD || useDevProxy
        ? "Нет авторизации (401): сессия через OIDC BFF или обратный прокси с TLS (клиентский Bearer отключён)."
        : "Нет авторизации (401): используйте dev-прокси Vite (тот же источник), чтобы Authorization подставлялся на сервере."
    );
  }
  if (response.status === 503) {
    throw new Error(
      "API недоступен (503): авторизация или конфигурация бэкенда не настроены вне режима разработки."
    );
  }
  throw new Error(`Запрос завершился ошибкой ${response.status}: ${response.statusText}`);
}

async function readJson<T>(url: string, init?: { signal?: AbortSignal }): Promise<T> {
  const response = await fetch(url, {
    headers: authHeaders(),
    credentials: "include",
    signal: init?.signal,
  });

  if (!response.ok) {
    throwForFailedResponse(response);
  }

  return (await response.json()) as T;
}

async function readBytes(url: string): Promise<{ bytes: Uint8Array; contentType: string | null }> {
  const response = await fetch(url, {
    headers: authHeaders({ Accept: "*/*" }),
    credentials: "include",
  });
  if (!response.ok) {
    throwForFailedResponse(response);
  }
  return {
    bytes: new Uint8Array(await response.arrayBuffer()),
    contentType: response.headers.get("Content-Type"),
  };
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export type ExportFormat = "json" | "html" | "bcf" | "pdf";

export function buildExportUrl(
  reportId: string,
  format: ExportFormat,
  options?: { bcfVersion?: "2.1" | "3.0" },
): string {
  const url = `${apiBaseUrl}/v1/reports/${reportId}/export/${format}`;
  if (format === "bcf" && options?.bcfVersion) {
    return `${url}?version=${options.bcfVersion}`;
  }
  return url;
}

export function buildReportIfcSourceUrl(reportId: string): string {
  return `${apiBaseUrl}/v1/reports/${reportId}/source/ifc`;
}

export function buildDrawingAssetPreviewUrl(reportId: string, assetId: string): string {
  return `${apiBaseUrl}/v1/reports/${reportId}/drawing-assets/${assetId}/preview`;
}

export async function fetchReports(
  filters: ReportListFilters = {},
  init?: { signal?: AbortSignal },
): Promise<ReportListResponse> {
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
  return readJson<ReportListResponse>(url, init);
}

export async function fetchReport(
  reportId: string,
  init?: { signal?: AbortSignal },
): Promise<ValidationReport> {
  return readJson<ValidationReport>(`${apiBaseUrl}/v1/reports/${reportId}`, init);
}

export interface CheckCoverageSourceRow {
  source_id: string;
  families: Record<string, string>;
  operator_status?: Record<string, string>;
  presentation_status?: Record<string, string>;
  reasons?: Record<string, string>;
}

export interface TzGapRow {
  gap_id: string;
  label: string;
  status: string;
  reason: string;
  tz_matrix?: string;
}

export interface CheckCoverageMap {
  artifact: string;
  schema_version?: string;
  note?: string;
  operator_legend?: Record<string, string>;
  presentation_states?: string[];
  tz_gaps?: TzGapRow[];
  sources: CheckCoverageSourceRow[];
  summary?: Record<string, number>;
  operator_summary?: Record<string, number>;
}

export async function fetchReportCoverage(reportId: string): Promise<CheckCoverageMap> {
  return readJson<CheckCoverageMap>(`${apiBaseUrl}/v1/reports/${reportId}/coverage`);
}

export async function fetchReportIfcSource(reportId: string): Promise<Uint8Array> {
  const { bytes } = await readBytes(buildReportIfcSourceUrl(reportId));
  return bytes;
}

const _SAFE_PREVIEW_BLOB_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
  "application/pdf",
]);

function safePreviewBlobType(raw: string | null): string {
  const value = (raw || "").split(";")[0]?.trim().toLowerCase() || "";
  return _SAFE_PREVIEW_BLOB_TYPES.has(value) ? value : "application/octet-stream";
}

export async function fetchDrawingAssetPreviewBlobUrl(reportId: string, assetId: string): Promise<string> {
  const { bytes, contentType } = await readBytes(buildDrawingAssetPreviewUrl(reportId, assetId));
  // Copy into a fresh ArrayBuffer-backed view for DOM Blob typing (TS 5.x BlobPart).
  const copy = Uint8Array.from(bytes);
  // Never trust image/* / octet blindly from a user-controlled store without allowlist (RTATOM-F05).
  const blob = new Blob([copy], { type: safePreviewBlobType(contentType) });
  return URL.createObjectURL(blob);
}

export async function downloadExport(
  reportId: string,
  format: ExportFormat,
  options?: { bcfVersion?: "2.1" | "3.0" },
): Promise<void> {
  const response = await fetch(buildExportUrl(reportId, format, options), {
    headers: authHeaders({ Accept: "*/*" }),
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Экспорт завершился ошибкой ${response.status}: ${response.statusText}`);
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

export type ReviewEventType =
  | "opened"
  | "accepted"
  | "rejected"
  | "edited_remark"
  | "edited"
  | "triaged"
  | "waived"
  | "superseded"
  | "escalated";

export type ReviewEventRow = {
  event_id: string;
  event_type: string;
  created_at: string;
  issue_rule_id?: string | null;
  finding_id?: string | null;
  note?: string | null;
  actor?: string | null;
  resulting_state?: string | null;
  previous_state?: string | null;
};

export async function fetchReviewEvents(
  reportId: string,
  init?: { signal?: AbortSignal },
): Promise<{ events: ReviewEventRow[]; count: number }> {
  return readJson<{ events: ReviewEventRow[]; count: number }>(
    `${apiBaseUrl}/v1/reports/${reportId}/review-events`,
    init,
  );
}

export type RevisionDiffPayload = {
  artifact: string;
  note: string;
  old_report_id: string;
  new_report_id: string;
  old_revision: string | null;
  new_revision: string | null;
  newly_reported: string[];
  no_longer_reported: string[];
  still_reported: string[];
  elements_only_in_old: string[];
  elements_only_in_new: string[];
  summary: {
    newly_reported: number;
    no_longer_reported: number;
    still_reported: number;
    elements_only_in_old: number;
    elements_only_in_new: number;
  };
};

export async function fetchRevisionDiff(
  baselineId: string,
  againstId: string,
  init?: { signal?: AbortSignal },
): Promise<RevisionDiffPayload> {
  const query = new URLSearchParams({ against: againstId });
  return readJson<RevisionDiffPayload>(
    `${apiBaseUrl}/v1/reports/${baselineId}/revision-diff?${query.toString()}`,
    init,
  );
}

export async function postReviewEvent(
  reportId: string,
  body: {
    event_type: ReviewEventType;
    issue_rule_id?: string;
    actor?: string;
    note?: string;
    latency_ms?: number;
    previous_state?: string;
    finding_id?: string;
    idempotency_key?: string;
  },
): Promise<{ event: Record<string, unknown> }> {
  const response = await fetch(`${apiBaseUrl}/v1/reports/${reportId}/review-events`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Событие ревью завершилось ошибкой ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as { event: Record<string, unknown> };
}

export async function uploadDocument(
  file: File,
  options?: { onProgress?: (percent: number) => void; signal?: AbortSignal },
): Promise<{
  upload_id: string;
  filename: string;
  path: string;
  size_bytes: number;
  content_type: string | null;
  object_key: string | null;
}> {
  if (!options?.onProgress && !options?.signal) {
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    if (apiBearerToken) {
      headers.Authorization = `Bearer ${apiBearerToken}`;
    }
    const response = await fetch(`${apiBaseUrl}/v1/uploads`, {
      method: "POST",
      headers,
      credentials: "include",
      body: form,
    });
    if (!response.ok) {
      throw new Error(`Загрузка завершилась ошибкой ${response.status}: ${response.statusText}`);
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

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${apiBaseUrl}/v1/uploads`);
    xhr.withCredentials = true;
    if (apiBearerToken) {
      xhr.setRequestHeader("Authorization", `Bearer ${apiBearerToken}`);
    }
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && options?.onProgress) {
        options.onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as {
          upload_id: string;
          filename: string;
          path: string;
          size_bytes: number;
          content_type: string | null;
          object_key: string | null;
        });
        return;
      }
      reject(new Error(`Загрузка завершилась ошибкой ${xhr.status}: ${xhr.statusText}`));
    };
    xhr.onerror = () => reject(new Error("Загрузка не удалась"));
    xhr.onabort = () => reject(new Error("Загрузка отменена"));
    options?.signal?.addEventListener("abort", () => xhr.abort());
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export type ReviewKpiPayload = {
  report_id: string;
  kpi: {
    event_count: number;
    by_type: Record<string, number>;
    acceptance_rate: number | null;
    avg_latency_ms: number | null;
    opened_count: number;
    triaged_count: number;
  };
};

export async function fetchReviewKpi(
  reportId: string,
  init?: { signal?: AbortSignal },
): Promise<ReviewKpiPayload> {
  return readJson<ReviewKpiPayload>(`${apiBaseUrl}/v1/reports/${reportId}/review-kpi`, init);
}

export type AnalyzeJobSnapshot = {
  job_id: string;
  status: string;
  status_url?: string;
  report_url?: string | null;
  report_id?: string | null;
  error_message?: string | null;
  stage_progress?: string | null;
  cancel_requested?: boolean;
  request_id?: string;
  created_at?: string;
};

export async function submitAnalyzeProjectPackage(
  body: AnalyzeSubmitBody & { request_id?: string },
): Promise<AnalyzeJobSnapshot> {
  const response = await fetch(`${apiBaseUrl}/v1/analyze/project-package/submit`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throwForFailedResponse(response);
  }
  return (await response.json()) as AnalyzeJobSnapshot;
}

export async function fetchAnalyzeJob(
  jobId: string,
  init?: { signal?: AbortSignal },
): Promise<AnalyzeJobSnapshot> {
  return readJson<AnalyzeJobSnapshot>(
    `${apiBaseUrl}/v1/analyze/project-package/jobs/${jobId}`,
    init,
  );
}

export async function cancelAnalyzeJob(jobId: string): Promise<AnalyzeJobSnapshot> {
  const response = await fetch(`${apiBaseUrl}/v1/analyze/project-package/jobs/${jobId}/cancel`, {
    method: "POST",
    headers: authHeaders(),
    credentials: "include",
  });
  if (!response.ok) {
    throwForFailedResponse(response);
  }
  return (await response.json()) as AnalyzeJobSnapshot;
}

export type DemoSeedFixtureResponse = {
  fixture: boolean;
  checkpoint: string;
  closes_rt001: boolean;
  closes_rt002?: boolean;
  closes_rt003?: boolean;
  note: string;
  report_id: string;
  issue_count: number;
};

export type SystemCapabilitiesPayload = {
  artifact_type: string;
  schema_version: string;
  customer_intake_gate: {
    status: string;
    claim_level: string;
    true_gates: string[];
    checkpoint: string;
    source: string | null;
  };
  auth_bff?: { status: string };
  bcf_t2?: { status: string; claim_allowed: boolean; raw_status?: string };
  honesty?: Record<string, { status: string; reason?: string | null }>;
  samolet_mvp_answers?: {
    closes_rt001: boolean;
    closes_rt002: boolean;
    closes_rt003: boolean;
    checkpoint: string;
    cde_integration_mvp?: boolean;
  };
};

export async function fetchSystemCapabilities(
  init?: { signal?: AbortSignal },
): Promise<SystemCapabilitiesPayload> {
  return readJson<SystemCapabilitiesPayload>(`${apiBaseUrl}/v1/system/capabilities`, init);
}

export async function seedDemoFixture(): Promise<DemoSeedFixtureResponse> {
  const response = await fetch(`${apiBaseUrl}/v1/demo/seed-fixture`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    credentials: "include",
  });
  if (!response.ok) {
    throwForFailedResponse(response);
  }
  return (await response.json()) as DemoSeedFixtureResponse;
}
