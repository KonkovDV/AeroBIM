/** Active analyze job pointer for this tab. Not a document path store. */

export const ACTIVE_JOB_STORAGE_KEY = "aerobim-active-job-v1";

/** Same shape as backend ``REPORT_ID_RE`` / ``validate_job_id``. */
const JOB_ID_RE = /^[a-f0-9]{32}$/;

export function isActiveJobId(value: string): boolean {
  return JOB_ID_RE.test(value);
}

export function readActiveJobId(storage?: Pick<Storage, "getItem"> | null): string | null {
  if (!storage) {
    return null;
  }
  try {
    const raw = storage.getItem(ACTIVE_JOB_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    const jobId = (parsed as { job_id?: unknown }).job_id;
    return typeof jobId === "string" && isActiveJobId(jobId) ? jobId : null;
  } catch {
    return null;
  }
}

export function writeActiveJobId(
  jobId: string,
  storage?: Pick<Storage, "getItem" | "setItem"> | null,
): void {
  if (!storage || !isActiveJobId(jobId)) {
    return;
  }
  storage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ job_id: jobId }));
}

export function clearActiveJobId(storage?: Pick<Storage, "removeItem"> | null): void {
  storage?.removeItem(ACTIVE_JOB_STORAGE_KEY);
}
