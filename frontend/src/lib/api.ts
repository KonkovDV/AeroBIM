import type { ReportListResponse, ValidationReport } from "./types";
import type { AnalyzeSubmitBody } from "./pack-draft";
import {
  parseAuthBffResponse,
  parseAuthBffSession,
  type AuthBffDiscovery,
  type AuthBffSession,
} from "./auth-bff";
import { aerobimCsrfHeaders } from "./csrf";
import { WASM_IFC_VIEWER_CAP_BYTES, IfcViewerCapError } from "./wasm-cap";

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
// Здесь сознательно нет ветки Authorization: клиент его не отправляет вообще.
function authHeaders(extra: Record<string, string> = {}): HeadersInit {
  return {
    Accept: "application/json",
    ...extra,
    ...aerobimCsrfHeaders(),
  };
}

/** Обрезка детали ошибки: в баннер не должен уезжать весь HTML страницы прокси. */
const ERROR_DETAIL_MAX_CHARS = 400;

function compactDetail(raw: string): string {
  const detail = raw.replace(/\s+/g, " ").trim();
  if (!detail) {
    return "";
  }
  return detail.length > ERROR_DETAIL_MAX_CHARS
    ? `${detail.slice(0, ERROR_DETAIL_MAX_CHARS)}…`
    : detail;
}

/**
 * Деталь из тела ответа с ошибкой.
 *
 * Раньше тело не читалось вообще, и эксперт видел только «завершился ошибкой 422:
 * Unprocessable Entity» — без указания поля, из-за которого бэкенд отказал.
 */
async function readErrorDetail(response: Response): Promise<string> {
  if (typeof response.text !== "function") {
    return "";
  }
  let raw = "";
  try {
    raw = (await response.text()).trim();
  } catch {
    return "";
  }
  if (!raw) {
    return "";
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    const record =
      parsed !== null && typeof parsed === "object"
        ? (parsed as Record<string, unknown>)
        : null;
    const candidate = record ? (record.detail ?? record.message ?? record.error) : parsed;
    if (typeof candidate === "string") {
      return compactDetail(candidate);
    }
    if (candidate !== null && candidate !== undefined) {
      return compactDetail(JSON.stringify(candidate));
    }
  } catch {
    // Не JSON — показываем текст как есть.
  }
  return compactDetail(raw);
}

async function withResponseDetail(response: Response, base: string): Promise<string> {
  const detail = await readErrorDetail(response);
  return detail ? `${base} · ${detail}` : base;
}

async function failedResponseError(response: Response): Promise<Error> {
  if (response.status === 401) {
    return new Error(
      import.meta.env.PROD || useDevProxy
        ? "Нет авторизации (401): сессия через OIDC BFF или обратный прокси с TLS (клиентский Bearer отключён)."
        : "Нет авторизации (401): используйте dev-прокси Vite (тот же источник), чтобы Authorization подставлялся на сервере."
    );
  }
  if (response.status === 503) {
    return new Error(
      "API недоступен (503): авторизация или конфигурация бэкенда не настроены вне режима разработки."
    );
  }
  return new Error(
    await withResponseDetail(
      response,
      `Запрос завершился ошибкой ${response.status}: ${response.statusText}`,
    ),
  );
}

async function readJson<T>(url: string, init?: { signal?: AbortSignal }): Promise<T> {
  const response = await fetch(url, {
    headers: authHeaders(),
    credentials: "include",
    signal: init?.signal,
  });

  if (!response.ok) {
    throw await failedResponseError(response);
  }

  return (await response.json()) as T;
}

function concatBytes(chunks: Uint8Array[], total: number): Uint8Array {
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return out;
}

/** Предел на тело ответа и ошибка, которую бросаем при превышении. */
type ByteCap = { maxBytes: number; makeError: () => Error };

const IFC_VIEWER_CAP: ByteCap = {
  maxBytes: WASM_IFC_VIEWER_CAP_BYTES,
  makeError: () => new IfcViewerCapError(),
};

/**
 * Предел для превью листа. Превью — это картинка или PDF одного листа, а не федерация,
 * поэтому 64 МиБ с запасом хватает. Раньше предела не было вовсе: response.arrayBuffer()
 * тянул в память ровно столько, сколько отдало хранилище.
 */
export const DRAWING_PREVIEW_CAP_BYTES = 64 * 1024 * 1024;

const DRAWING_PREVIEW_CAP: ByteCap = {
  maxBytes: DRAWING_PREVIEW_CAP_BYTES,
  makeError: () => new Error("Превью листа больше допустимого размера и не было открыто."),
};

async function readBodyUpTo(
  response: Response,
  cap: ByteCap,
  controller: AbortController,
): Promise<Uint8Array> {
  if (!response.body) {
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.byteLength > cap.maxBytes) {
      throw cap.makeError();
    }
    return bytes;
  }
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    total += value.byteLength;
    if (total > cap.maxBytes) {
      await reader.cancel();
      controller.abort();
      throw cap.makeError();
    }
    chunks.push(value);
  }
  return concatBytes(chunks, total);
}

async function readBytes(
  url: string,
  cap: ByteCap,
): Promise<{ bytes: Uint8Array; contentType: string | null }> {
  const controller = new AbortController();
  const response = await fetch(url, {
    headers: authHeaders({ Accept: "*/*" }),
    credentials: "include",
    signal: controller.signal,
  });
  if (!response.ok) {
    throw await failedResponseError(response);
  }
  // Number(null) === 0, поэтому отсутствующий content-length не срабатывает ложно.
  const declared = Number(response.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > cap.maxBytes) {
    controller.abort();
    throw cap.makeError();
  }
  return {
    bytes: await readBodyUpTo(response, cap, controller),
    contentType: response.headers.get("Content-Type"),
  };
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export type { AuthBffDiscovery, AuthBffSession };

export async function fetchAuthBff(): Promise<AuthBffDiscovery> {
  try {
    const response = await fetch(`${apiBaseUrl}/v1/auth/bff`, {
      headers: authHeaders(),
      credentials: "include",
    });
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    return parseAuthBffResponse(response.status, body);
  } catch {
    return { httpStatus: 0, status: "UNKNOWN" };
  }
}

export async function fetchAuthSession(): Promise<AuthBffSession | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/v1/auth/session`, {
      headers: authHeaders(),
      credentials: "include",
    });
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    return parseAuthBffSession(response.status, body);
  } catch {
    return null;
  }
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
  const { bytes } = await readBytes(buildReportIfcSourceUrl(reportId), IFC_VIEWER_CAP);
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
  const { bytes, contentType } = await readBytes(
    buildDrawingAssetPreviewUrl(reportId, assetId),
    DRAWING_PREVIEW_CAP,
  );
  // Copy into a fresh ArrayBuffer-backed view for DOM Blob typing (TS 5.x BlobPart).
  const copy = Uint8Array.from(bytes);
  // Never trust image/* / octet blindly from a user-controlled store without allowlist (RTATOM-F05).
  const blob = new Blob([copy], { type: safePreviewBlobType(contentType) });
  return URL.createObjectURL(blob);
}

/**
 * Отзыв object URL сразу после click() обрывает скачивание в Firefox и Safari:
 * браузер ещё не начал читать поток. Отдаём отзыв в таймаут, чтобы файл дошёл.
 */
const OBJECT_URL_TTL_MS = 60_000;

function triggerBlobDownload(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  if (typeof setTimeout === "function") {
    setTimeout(() => URL.revokeObjectURL(objectUrl), OBJECT_URL_TTL_MS);
    return;
  }
  URL.revokeObjectURL(objectUrl);
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

type SaveFilePicker = (options: { suggestedName: string }) => Promise<{
  createWritable: () => Promise<WritableStream<Uint8Array>>;
}>;

/** Stream to disk when the picker exists; otherwise buffer a blob. Not a 1.5 GB WASM raise. */
export async function saveResponseDownload(response: Response, filename: string): Promise<void> {
  const picker = (window as Window & { showSaveFilePicker?: SaveFilePicker }).showSaveFilePicker;
  const body = response.body;
  if (body && typeof picker === "function") {
    try {
      const handle = await picker({ suggestedName: filename });
      await body.pipeTo(await handle.createWritable());
      return;
    } catch (error: unknown) {
      if (isAbortError(error)) {
        return;
      }
      if (body.locked) {
        throw error instanceof Error ? error : new Error("Экспорт: поток уже закрыт");
      }
    }
  }
  triggerBlobDownload(await response.blob(), filename);
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
    throw new Error(
      await withResponseDetail(
        response,
        `Экспорт завершился ошибкой ${response.status}: ${response.statusText}`,
      ),
    );
  }
  const extension = format === "bcf" ? "bcfzip" : format;
  await saveResponseDownload(response, `aerobim-report-${reportId}.${extension}`);
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
    throw new Error(
      await withResponseDetail(
        response,
        `Событие ревью завершилось ошибкой ${response.status}: ${response.statusText}`,
      ),
    );
  }
  return (await response.json()) as { event: Record<string, unknown> };
}

type UploadDocumentResult = {
  upload_id: string;
  filename: string;
  path: string;
  size_bytes: number;
  content_type: string | null;
};

export async function uploadDocument(
  file: File,
  options?: { onProgress?: (percent: number) => void; signal?: AbortSignal },
): Promise<UploadDocumentResult> {
  if (!options?.onProgress && !options?.signal) {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${apiBaseUrl}/v1/uploads`, {
      method: "POST",
      headers: { ...aerobimCsrfHeaders() },
      credentials: "include",
      body: form,
    });
    if (!response.ok) {
      throw new Error(
        await withResponseDetail(
          response,
          `Загрузка завершилась ошибкой ${response.status}: ${response.statusText}`,
        ),
      );
    }
    return (await response.json()) as UploadDocumentResult;
  }

  return new Promise((resolve, reject) => {
    const signal = options?.signal;
    // Уже отменённый signal раньше игнорировался, и запрос всё равно уходил на бэкенд.
    if (signal?.aborted) {
      reject(new Error("Загрузка отменена"));
      return;
    }
    const xhr = new XMLHttpRequest();
    const onAbortSignal = () => xhr.abort();
    // Слушатель обязателен к снятию: signal живёт дольше запроса и накапливал ссылки.
    const detach = () => signal?.removeEventListener("abort", onAbortSignal);
    xhr.open("POST", `${apiBaseUrl}/v1/uploads`);
    xhr.withCredentials = true;
    const csrf = aerobimCsrfHeaders();
    for (const [name, value] of Object.entries(csrf)) {
      xhr.setRequestHeader(name, value);
    }
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && options?.onProgress) {
        options.onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      detach();
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as UploadDocumentResult);
        } catch {
          reject(new Error("Загрузка прошла, но ответ бэкенда не разобран"));
        }
        return;
      }
      const base = `Загрузка завершилась ошибкой ${xhr.status}: ${xhr.statusText}`;
      const detail = compactDetail(xhr.responseText || "");
      reject(new Error(detail ? `${base} · ${detail}` : base));
    };
    xhr.onerror = () => {
      detach();
      reject(new Error("Загрузка не удалась"));
    };
    xhr.onabort = () => {
      detach();
      reject(new Error("Загрузка отменена"));
    };
    signal?.addEventListener("abort", onAbortSignal);
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
    throw await failedResponseError(response);
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
    throw await failedResponseError(response);
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
    throw await failedResponseError(response);
  }
  return (await response.json()) as DemoSeedFixtureResponse;
}
