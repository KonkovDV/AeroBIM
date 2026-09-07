import { describe, expect, it } from "vitest";
import { ACTIVE_JOB_STORAGE_KEY, clearActiveJobId, readActiveJobId, writeActiveJobId } from "./active-job";

const JOB = "a".repeat(32);

describe("active-job", () => {
  it("stores only a hex job_id and ignores other shapes", () => {
    const store = new Map<string, string>();
    const storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    };
    expect(readActiveJobId(storage)).toBeNull();
    writeActiveJobId("job-1", storage);
    expect(store.has(ACTIVE_JOB_STORAGE_KEY)).toBe(false);
    writeActiveJobId(JOB, storage);
    expect(JSON.parse(store.get(ACTIVE_JOB_STORAGE_KEY) ?? "{}")).toEqual({ job_id: JOB });
    expect(readActiveJobId(storage)).toBe(JOB);
    store.set(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ path: "secret.ifc" }));
    expect(readActiveJobId(storage)).toBeNull();
    store.set(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ job_id: "job-missing" }));
    expect(readActiveJobId(storage)).toBeNull();
    clearActiveJobId(storage);
    expect(store.has(ACTIVE_JOB_STORAGE_KEY)).toBe(false);
  });
});
