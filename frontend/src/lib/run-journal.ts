/** Журнал прогонов вкладки. sessionStorage, не СОД. */

export const RUN_JOURNAL_STORAGE_KEY = "aerobim-run-journal-v1";
const MAX_ROWS = 12;

export type RunJournalEntry = {
  job_id: string;
  status: string;
  elapsed_sec: number;
  recorded_at: string;
};

export function readRunJournal(storage?: Pick<Storage, "getItem"> | null): RunJournalEntry[] {
  if (!storage) {
    return [];
  }
  try {
    const raw = storage.getItem(RUN_JOURNAL_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .filter((row): row is RunJournalEntry => {
        if (!row || typeof row !== "object") {
          return false;
        }
        const entry = row as Partial<RunJournalEntry>;
        return typeof entry.job_id === "string" && typeof entry.status === "string";
      })
      .map((row) => ({
        job_id: row.job_id,
        status: row.status,
        elapsed_sec: typeof row.elapsed_sec === "number" ? row.elapsed_sec : 0,
        recorded_at: typeof row.recorded_at === "string" ? row.recorded_at : "",
      }))
      .slice(0, MAX_ROWS);
  } catch {
    return [];
  }
}

export function appendRunJournal(
  entry: RunJournalEntry,
  storage?: Pick<Storage, "getItem" | "setItem"> | null,
): RunJournalEntry[] {
  if (!storage) {
    return [entry];
  }
  const next = [entry, ...readRunJournal(storage).filter((row) => row.job_id !== entry.job_id)].slice(
    0,
    MAX_ROWS,
  );
  storage.setItem(RUN_JOURNAL_STORAGE_KEY, JSON.stringify(next));
  return next;
}
