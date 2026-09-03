import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AnalyzeRunPanel from "./AnalyzeRunPanel";
import type { ReportCapabilities } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";
import { RUN_JOURNAL_STORAGE_KEY } from "../lib/run-journal";

const { submitAnalyzeProjectPackageMock, cancelAnalyzeJobMock } = vi.hoisted(() => ({
  submitAnalyzeProjectPackageMock: vi.fn(),
  cancelAnalyzeJobMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  submitAnalyzeProjectPackage: (...args: unknown[]) => submitAnalyzeProjectPackageMock(...args),
  cancelAnalyzeJob: (...args: unknown[]) => cancelAnalyzeJobMock(...args),
}));

describe("AnalyzeRunPanel", () => {
  beforeEach(() => {
    submitAnalyzeProjectPackageMock.mockReset();
    cancelAnalyzeJobMock.mockReset();
    sessionStorage.removeItem(RUN_JOURNAL_STORAGE_KEY);
  });
  it("shows elapsed-timer copy without claiming SLA", () => {
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    const timer = screen.getByTestId("analyze-elapsed");
    expect(timer.textContent).toMatch(/Цель ТЗ записана как 30:00/);
    expect(timer.textContent).toMatch(/SLA не заявляем/);
  });

  it("offers a repeat run only after a terminal state", () => {
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    expect(screen.queryByRole("button", { name: "Повторный прогон" })).toBeNull();
  });

  it("shows engine groups as pending until capabilities exist", () => {
    render(<AnalyzeRunPanel ifcPath={null} />);
    const list = screen.getByTestId("analyze-engine-groups");
    expect(list.textContent).toMatch(/модель: ожидание/);
    expect(list.textContent).toMatch(/правила: ожидание/);
  });

  it("maps skipped and failed engines without calling them success", () => {
    const capabilities = {
      ifc_schema: { status: "ok" },
      ifc_validation: { status: "ok" },
      unit_scale: { status: "ok" },
      ids: { status: "ok" },
      clash: { status: "skipped" },
      raster: { status: "failed" },
    } as ReportCapabilities;
    render(<AnalyzeRunPanel ifcPath="walls.ifc" capabilities={capabilities} />);
    const list = screen.getByTestId("analyze-engine-groups");
    expect(list.textContent).toMatch(/модель: ok/);
    expect(list.textContent).toMatch(/правила: skipped/);
    expect(list.textContent).toMatch(/документы: failed/);
  });

  it("records a finished job in the tab journal without calling it a CDE audit", async () => {
    sessionStorage.removeItem(RUN_JOURNAL_STORAGE_KEY);
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-session-1",
      status: "succeeded",
      report_id: "r".repeat(32),
    });
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    const journal = await screen.findByTestId("run-journal");
    await waitFor(() => {
      expect(journal.textContent).toMatch(/job-session-1/);
      expect(journal.textContent).toMatch(/succeeded/);
    });
    expect(screen.getByText(UI_COPY.runJournalHonesty)).toBeTruthy();
  });

  it("asks before cancelling a running job", async () => {
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-running-1",
      status: "running",
    });
    cancelAnalyzeJobMock.mockResolvedValue({
      job_id: "job-running-1",
      status: "cancelled",
    });
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    expect(await screen.findByTestId("analyze-job-status")).toBeTruthy();
    expect(screen.getByTestId("analyze-job-status").textContent).toMatch(/job-running-1/);
    fireEvent.click(screen.getByRole("button", { name: "Отменить" }));
    expect(confirmSpy).toHaveBeenCalled();
    expect(cancelAnalyzeJobMock).not.toHaveBeenCalled();
    confirmSpy.mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: "Отменить" }));
    await waitFor(() => {
      expect(cancelAnalyzeJobMock).toHaveBeenCalledWith("job-running-1");
    });
    confirmSpy.mockRestore();
  });
});
