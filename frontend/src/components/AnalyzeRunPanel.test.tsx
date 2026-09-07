import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AnalyzeRunPanel from "./AnalyzeRunPanel";
import type { ReportCapabilities } from "../lib/types";
import { UI_COPY } from "../lib/ui-copy";
import { RUN_JOURNAL_STORAGE_KEY } from "../lib/run-journal";

const { submitAnalyzeProjectPackageMock, cancelAnalyzeJobMock, fetchAnalyzeJobMock } = vi.hoisted(() => ({
  submitAnalyzeProjectPackageMock: vi.fn(),
  cancelAnalyzeJobMock: vi.fn(),
  fetchAnalyzeJobMock: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  submitAnalyzeProjectPackage: (...args: unknown[]) => submitAnalyzeProjectPackageMock(...args),
  cancelAnalyzeJob: (...args: unknown[]) => cancelAnalyzeJobMock(...args),
  fetchAnalyzeJob: (...args: unknown[]) => fetchAnalyzeJobMock(...args),
}));

describe("AnalyzeRunPanel", () => {
  beforeEach(() => {
    submitAnalyzeProjectPackageMock.mockReset();
    cancelAnalyzeJobMock.mockReset();
    fetchAnalyzeJobMock.mockReset();
    fetchAnalyzeJobMock.mockImplementation(async (jobId: string) => ({
      job_id: jobId,
      status: "running",
    }));
    sessionStorage.removeItem(RUN_JOURNAL_STORAGE_KEY);
  });
  it("shows elapsed-timer copy without claiming SLA", () => {
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    const timer = screen.getByTestId("analyze-elapsed");
    expect(timer.textContent).toMatch(/Цель ТЗ — до 30 минут/);
    expect(timer.textContent).toMatch(/на данных заказчика ещё не подтверждена/);
    expect(screen.getByTestId("analyze-size-honesty").textContent).toMatch(/256 МиБ/);
    expect(screen.getByTestId("analyze-size-honesty").textContent).toMatch(/1,5 ГБ/);
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
    expect(list.textContent).toMatch(/модель: выполнена/);
    expect(list.textContent).toMatch(/правила: пропущена/);
    expect(list.textContent).toMatch(/документы: не выполнена/);
  });

  it("hides the previous report matrix while a new job is still running", async () => {
    const capabilities = {
      ifc_schema: { status: "ok" },
      ifc_validation: { status: "ok" },
      unit_scale: { status: "ok" },
      ids: { status: "ok" },
      clash: { status: "ok" },
      raster: { status: "ok" },
    } as ReportCapabilities;
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-running-cap",
      status: "running",
    });
    render(
      <AnalyzeRunPanel
        ifcPath="walls.ifc"
        capabilities={capabilities}
        capabilitiesReportId={"a".repeat(32)}
      />,
    );
    expect(screen.getByTestId("analyze-engine-groups").textContent).toMatch(/модель: выполнена/);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    expect(await screen.findByTestId("analyze-job-status")).toBeTruthy();
    expect(screen.getByTestId("analyze-engine-groups").textContent).toMatch(/модель: ожидание/);
    expect(screen.getByTestId("run-status-strip").textContent).toContain(UI_COPY.runEvidenceNone);
    expect(screen.getByRole("button", { name: "Запустить анализ" })).toHaveProperty("disabled", true);
  });

  it("resumes GET of the same job after a poll error without a second POST", async () => {
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-resume-1",
      status: "running",
    });
    fetchAnalyzeJobMock.mockRejectedValue(new Error("Нет связи с сервером"));
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    expect(await screen.findByTestId("analyze-poll-error")).toBeTruthy();
    fireEvent.click(screen.getByTestId("analyze-resume-poll"));
    expect(submitAnalyzeProjectPackageMock).toHaveBeenCalledTimes(1);
    expect(fetchAnalyzeJobMock.mock.calls.some((call) => call[0] === "job-resume-1")).toBe(true);
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

  it("writes a terminal run to the journal once, not on every tick", async () => {
    submitAnalyzeProjectPackageMock.mockResolvedValue({
      job_id: "job-once-1",
      status: "succeeded",
      report_id: "r".repeat(32),
    });
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    const journal = await screen.findByTestId("run-journal");
    await waitFor(() => {
      expect(journal.textContent).toMatch(/job-once-1/);
    });
    // Запись шла и из start(), и из эффекта; сторож по job_id оставляет одну строку.
    expect(journal.querySelectorAll("li")).toHaveLength(1);
  });

  it("keeps the submit error and the poll error in separate alerts", async () => {
    submitAnalyzeProjectPackageMock.mockRejectedValueOnce(new Error("Отправка не удалась"));
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    const alert = await screen.findByTestId("analyze-error");
    expect(alert.textContent).toMatch(/Отправка не удалась/);
    // Канал опроса независим: своя область, а не общий тернарник.
    expect(screen.queryByTestId("analyze-poll-error")).toBeNull();
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
    render(<AnalyzeRunPanel ifcPath="walls.ifc" />);
    fireEvent.click(screen.getByRole("button", { name: "Запустить анализ" }));
    expect(await screen.findByTestId("analyze-job-status")).toBeTruthy();
    expect(screen.getByTestId("analyze-job-status").textContent).toMatch(/job-running-1/);
    fireEvent.click(screen.getByRole("button", { name: "Отменить" }));
    expect(screen.getByTestId("run-cancel-confirm")).toBeTruthy();
    expect(cancelAnalyzeJobMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Оставить прогон" }));
    expect(screen.queryByTestId("run-cancel-confirm")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Отменить" }));
    fireEvent.click(screen.getByRole("button", { name: "Да, отменить" }));
    await waitFor(() => {
      expect(cancelAnalyzeJobMock).toHaveBeenCalledWith("job-running-1");
    });
  });
});
