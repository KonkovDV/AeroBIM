import { describe, expect, it } from "vitest";
import { appendRunJournal, readRunJournal, RUN_JOURNAL_STORAGE_KEY } from "./run-journal";

function memoryStorage(initial?: string): Pick<Storage, "getItem" | "setItem"> {
  let value = initial ?? null;
  return {
    getItem: (key: string) => (key === RUN_JOURNAL_STORAGE_KEY ? value : null),
    setItem: (_key: string, next: string) => {
      value = next;
    },
  };
}

describe("run-journal", () => {
  it("returns an empty list when storage is missing or corrupt", () => {
    expect(readRunJournal(null)).toEqual([]);
    expect(readRunJournal(memoryStorage("not-json"))).toEqual([]);
  });

  it("prepends a row and replaces the same job_id", () => {
    const storage = memoryStorage();
    appendRunJournal(
      { job_id: "a", status: "running", elapsed_sec: 1, recorded_at: "t1" },
      storage,
    );
    const next = appendRunJournal(
      { job_id: "a", status: "succeeded", elapsed_sec: 4, recorded_at: "t2" },
      storage,
    );
    expect(next).toHaveLength(1);
    expect(next[0]?.status).toBe("succeeded");
    expect(next[0]?.elapsed_sec).toBe(4);
  });
});
