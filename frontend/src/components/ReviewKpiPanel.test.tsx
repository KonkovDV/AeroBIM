import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ReviewKpiPanel from "./ReviewKpiPanel";
import { UI_COPY } from "../lib/ui-copy";

vi.mock("../lib/api", () => ({
  fetchReviewKpi: vi.fn(),
}));

import { fetchReviewKpi } from "../lib/api";

const fetchReviewKpiMock = vi.mocked(fetchReviewKpi);

describe("ReviewKpiPanel", () => {
  it("shows the empty-journal copy instead of a 0% chart", async () => {
    fetchReviewKpiMock.mockResolvedValue({
      report_id: "r".repeat(32),
      kpi: {
        event_count: 0,
        by_type: {},
        acceptance_rate: null,
        avg_latency_ms: null,
        opened_count: 0,
        triaged_count: 0,
      },
    });
    render(<ReviewKpiPanel reportId={"r".repeat(32)} />);
    expect(await screen.findByTestId("kpi-bars-empty")).toBeTruthy();
    expect(screen.getByTestId("kpi-bars-empty").textContent).toBe(UI_COPY.kpiBarsEmpty);
    expect(screen.queryByTestId("kpi-bars")).toBeNull();
  });

  it("renders CSS bars for HITL event types", async () => {
    fetchReviewKpiMock.mockResolvedValue({
      report_id: "r".repeat(32),
      kpi: {
        event_count: 4,
        by_type: { accepted: 3, rejected: 1 },
        acceptance_rate: 0.75,
        avg_latency_ms: 12,
        opened_count: 4,
        triaged_count: 4,
      },
    });
    render(<ReviewKpiPanel reportId={"r".repeat(32)} />);
    const bars = await screen.findByTestId("kpi-bars");
    expect(bars.textContent).toMatch(/подтверждено/);
    expect(screen.getByTestId("kpi-cycle-honesty").textContent).toMatch(/не дни цикла/);
    expect(screen.getByTestId("kpi-decision-split").textContent).toMatch(/Подтверждено 3, отклонено 1/);
    await waitFor(() => {
      expect(screen.getByRole("img", { name: /75/ })).toBeTruthy();
    });
  });
});
