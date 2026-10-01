import { describe, expect, it } from "vitest";
import { JOB_POLL_INTERVAL_MS, JOB_POLL_MAX_INTERVAL_MS, nextJobPollInterval } from "./useRunPolling";

describe("nextJobPollInterval", () => {
  it("grows from 2s toward 15s and does not claim SSE", () => {
    expect(JOB_POLL_INTERVAL_MS).toBe(2000);
    expect(nextJobPollInterval(2000)).toBe(3000);
    expect(nextJobPollInterval(14_000)).toBe(JOB_POLL_MAX_INTERVAL_MS);
    expect(nextJobPollInterval(JOB_POLL_MAX_INTERVAL_MS)).toBe(JOB_POLL_MAX_INTERVAL_MS);
  });
});
