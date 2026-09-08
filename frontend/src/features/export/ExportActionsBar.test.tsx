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

  it("shows a category alert without leaking export diagnostics", async () => {
    downloadExportMock.mockRejectedValueOnce(Object.assign(new Error("http://secret-host/trace"), { status: 500 }));
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    fireEvent.click(screen.getByRole("button", { name: "HTML" }));
    const serverAlert = await screen.findByTestId("export-error");
    expect(serverAlert.textContent).toBe(UI_COPY.errorBannerServer);
    expect(serverAlert.textContent).not.toMatch(/500|http|secret-host|trace/i);

    downloadExportMock.mockRejectedValueOnce(new TypeError("Failed to fetch http://private-host"));
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    const networkAlert = await screen.findByTestId("export-error");
    expect(networkAlert.textContent).toBe(UI_COPY.errorBannerNetwork);
    expect(networkAlert.textContent).not.toMatch(/fetch|http|private-host/i);
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

  it("describes the pdf button by a single visible hint instead of a duplicate title", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    const pdfButton = screen.getByRole("button", { name: UI_COPY.exportPdf });
    // Подсказка больше не дублируется в title.
    expect(pdfButton.getAttribute("title")).toBeNull();
    const hintId = pdfButton.getAttribute("aria-describedby");
    expect(hintId).toBeTruthy();
    expect(document.getElementById(hintId as string)?.textContent).toBe(UI_COPY.exportPdfHint);
    expect(screen.getAllByText(UI_COPY.exportPdfHint)).toHaveLength(1);
  });

  it("warns before exporting when the remark draft is unsaved", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" unsavedRemark />);
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(downloadExportMock).not.toHaveBeenCalled();
    confirmSpy.mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    await waitFor(() => {
      expect(downloadExportMock).toHaveBeenCalledTimes(1);
    });
    confirmSpy.mockRestore();
  });

  it("does not claim a spreadsheet export exists", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" showLimits />);
    expect(screen.getByText(UI_COPY.xlsxNotMvp)).toBeTruthy();
    expect(screen.getByText(UI_COPY.exportSavedOnlyHint)).toBeTruthy();
    expect(UI_COPY.exportSavedOnlyHint).not.toMatch(/исправлено/);
  });

  it("keeps the spreadsheet limit off the review toolbar", () => {
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    expect(screen.queryByText(UI_COPY.xlsxNotMvp)).toBeNull();
    expect(screen.getByText(UI_COPY.exportSavedOnlyHint)).toBeTruthy();
  });

  it("marks the bar busy while an export runs", async () => {
    const deferred: { release?: () => void } = {};
    downloadExportMock.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          deferred.release = resolve;
        }),
    );
    render(<ExportActionsBar reportId="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />);
    const bar = screen.getByTestId("export-actions");
    expect(bar.getAttribute("aria-busy")).toBe("false");
    fireEvent.click(screen.getByRole("button", { name: "HTML" }));
    await waitFor(() => {
      expect(bar.getAttribute("aria-busy")).toBe("true");
    });
    deferred.release?.();
    await waitFor(() => {
      expect(bar.getAttribute("aria-busy")).toBe("false");
    });
  });
});