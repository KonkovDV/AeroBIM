import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ExportActionsBar from "./ExportActionsBar";
import { downloadExport } from "../../lib/api";
import { UI_COPY } from "../../lib/ui-copy";

vi.mock("../../lib/api", () => ({
  downloadExport: vi.fn(),
}));

const downloadExportMock = vi.mocked(downloadExport);

describe("ExportActionsBar", () => {
  beforeEach(() => {
    downloadExportMock.mockReset();
    downloadExportMock.mockResolvedValue(undefined);
  });

  it("exposes html json bcf and pdf; xlsx is not rendered at all", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    const bar = screen.getByTestId("export-actions");
    expect(bar.querySelector("button")?.textContent).toBeTruthy();
    expect(screen.getByRole("button", { name: "HTML" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "JSON" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "BCF 3.0" })).toBeTruthy();
    expect(screen.getByRole("button", { name: UI_COPY.exportPdf })).toBeTruthy();
    // UI3 P0.2: XLSX не рендерим вовсе — эндпоинта нет, фальшивый успех хуже отсутствия.
    expect(screen.queryByRole("button", { name: /XLSX/i })).toBeNull();
  });

  it("shows an alert instead of swallowing a failed export", async () => {
    downloadExportMock.mockRejectedValueOnce(new Error("Экспорт завершился ошибкой 500"));
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    fireEvent.click(screen.getByRole("button", { name: "HTML" }));
    const alert = await screen.findByTestId("export-error");
    expect(alert.textContent).toContain("500");
  });

  it("disables buttons while a download is in flight", async () => {
    const deferred: { release?: () => void } = {};
    downloadExportMock.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          deferred.release = resolve;
        }),
    );
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: UI_COPY.exportInProgress })).toBeTruthy();
    });
    expect(
      screen.getAllByRole("button").every((button) => (button as HTMLButtonElement).disabled),
    ).toBe(true);
    deferred.release?.();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "JSON" })).toBeTruthy();
    });
  });
});
