import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ACTIVE_JOB_STORAGE_KEY } from "../lib/active-job";
import { ApiHttpError } from "../lib/api";
import { useRunPolling } from "./useRunPolling";

const { fetchAnalyzeJobMock } = vi.hoisted(() => ({
  fetchAnalyzeJobMock: vi.fn(),
}));

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    fetchAnalyzeJob: (...args: unknown[]) => fetchAnalyzeJobMock(...args),
  };
});

function Probe({ restoreWhen }: { restoreWhen: boolean }) {
  const polling = useRunPolling(undefined, restoreWhen);
  return (
    <div>
      <span data-testid="job-id">{polling.job?.job_id ?? "none"}</span>
      <span data-testid="elapsed">{polling.elapsedSec}</span>
      <span data-testid="poll-error">{polling.pollError ?? ""}</span>
    </div>
  );
}

describe("useRunPolling restore", () => {
  beforeEach(() => {
    sessionStorage.clear();
    fetchAnalyzeJobMock.mockReset();
  });

  it("restores the stored job_id after auth settles and uses created_at for the timer", async () => {
    const created = new Date(Date.now() - 90_000).toISOString();
    const jobId = "a".repeat(32);
    sessionStorage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ job_id: jobId }));
    fetchAnalyzeJobMock.mockResolvedValue({
      job_id: jobId,
      status: "running",
      created_at: created,
    });
    render(<Probe restoreWhen />);
    expect((await screen.findByTestId("job-id")).textContent).toBe(jobId);
    const elapsed = Number(screen.getByTestId("elapsed").textContent);
    expect(elapsed).toBeGreaterThanOrEqual(89);
    expect(elapsed).toBeLessThanOrEqual(92);
  });

  it("drops a stored id on 404 without enumerating other jobs", async () => {
    const missing = "b".repeat(32);
    sessionStorage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ job_id: missing }));
    fetchAnalyzeJobMock.mockRejectedValue(new ApiHttpError(404, "Объект не найден (404)."));
    render(<Probe restoreWhen />);
    await waitFor(() => {
      expect(sessionStorage.getItem(ACTIVE_JOB_STORAGE_KEY)).toBeNull();
    });
    expect(fetchAnalyzeJobMock.mock.calls).toEqual([
      [missing, expect.objectContaining({ signal: expect.any(AbortSignal) })],
    ]);
    expect(screen.getByTestId("job-id").textContent).toBe("none");
  });

  it("clears a malformed stored pointer without calling the jobs API", async () => {
    sessionStorage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({ job_id: "job-missing" }));
    render(<Probe restoreWhen />);
    await waitFor(() => {
      expect(sessionStorage.getItem(ACTIVE_JOB_STORAGE_KEY)).toBeNull();
    });
    expect(fetchAnalyzeJobMock).not.toHaveBeenCalled();
  });
});
